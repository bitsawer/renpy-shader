
import renpy
import renpy.display
import pygame_sdl2 as pygame
import ctypes

from OpenGL import GL as gl
import euclid
import math
import json

import shader
import shadercode
import mesh
import utils
import skin
import gpu

class TextureEntry:
    def __init__(self, image, sampler):
        self.sampler = sampler

        if isinstance(image, (pygame.Surface)):
            self.image = None
            surface = image
        else:
            self.image = image
            surface = renpy.display.im.load_surface(self.image)

        self.texture = gpu.Texture(surface)
        if not self.texture.valid():
            raise RuntimeError("Can't load gl texture from image: %s" % image)

    def free(self):
        self.texture.free()

class TextureMap:
    def __init__(self):
        self.textures = {}

    def free(self):
        for sampler, entry in self.textures.items():
            entry.free()
        self.textures.clear()

    def setTexture(self, sampler, image):
        entry = TextureEntry(image, sampler)
        old = self.textures.get(sampler)
        if old:
            old.free()
        self.textures[sampler] = entry

    def bindTextures(self, shader):
        index = 0
        for sampler, entry in self.textures.items():
            shader.uniformi(sampler, index)
            gl.glActiveTexture(gl.GL_TEXTURE0 + index)
            gl.glBindTexture(gl.GL_TEXTURE_2D, entry.texture.textureId)
            index += 1

    def unbindTextures(self):
        for i in range(len(self.textures)):
            gl.glActiveTexture(gl.GL_TEXTURE0 + i)
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glActiveTexture(gl.GL_TEXTURE0)


class BaseRenderer(object):
    def __init__(self):
        self.useDepth = False
        self.clearColor = (0, 0, 0, 0)

    def setUniforms(self, shader, uniforms):
        for key, value in uniforms.items():
            if isinstance(value, (int, float)):
                shader.uniformf(key, value)
            elif isinstance(value, euclid.Matrix4):
                shader.uniformMatrix4f(key, utils.matrixToList(value))
            elif len(value) == 16:
                shader.uniformMatrix4f(key, value)
            else:
                shader.uniformf(key, *value)

    def bindAttributeArray(self, shader, name, data, count):
        location = gl.glGetAttribLocation(shader.handle, name)
        if location != -1:
            gl.glVertexAttribPointer(location, count, gl.GL_FLOAT, False, 0, data)
            gl.glEnableVertexAttribArray(location)

    def unbindAttributeArray(self, shader, name):
        location = gl.glGetAttribLocation(shader.handle, name)
        if location != -1:
            gl.glDisableVertexAttribArray(location)

    def setTexture(self, sampler, image):
        raise NotImplementedError("Must be implemented")

    def free(self):
        raise NotImplementedError("Must be implemented")

    def getSize(self):
        raise NotImplementedError("Must be implemented")

    def render(self, context):
        raise NotImplementedError("Must be implemented")


class Renderer2D(BaseRenderer):
    def __init__(self):
        super(Renderer2D, self).__init__()
        self.shader = None
        self.verts = self.createVertexQuad()
        self.textureMap = TextureMap()

    def init(self, image, vertexShader, pixeShader):
        self.shader = gpu.ShaderProgram(vertexShader, pixeShader)

        self.textureMap.setTexture(shader.TEX0, image)

    def setTexture(self, sampler, image):
        self.textureMap.setTexture(sampler, image)

    def free(self):
        if self.textureMap:
            self.textureMap.free()
            self.textureMap = None

        if self.shader:
            self.shader.free()
            self.shader = None

    def getSize(self):
        entry = self.textureMap.textures[shader.TEX0]
        return entry.texture.width, entry.texture.height

    def createVertexQuad(self):
        tx2 = 1.0 #Adjust if rounding textures to power of two
        ty2 = 1.0
        vertices = [
            -1, -1, 0.0, 0.0, #Bottom left
            1, -1, tx2, 0.0, #Bottom right
            -1, 1, 0.0, ty2, #Top left
            1, 1, tx2, ty2, #Top right
        ]
        return (gl.GLfloat * len(vertices))(*vertices)

    def render(self, context):
        self.shader.bind()

        flipY = -1
        projection = utils.createPerspectiveOrtho(-1.0, 1.0, 1.0 * flipY, -1.0 * flipY, -1.0, 1.0)
        self.shader.uniformMatrix4f(shader.PROJECTION, projection)
        self.shader.uniformf("imageSize", *self.getSize())

        self.setUniforms(self.shader, context.uniforms)

        self.textureMap.bindTextures(self.shader)

        gl.glClearColor(*self.clearColor)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        self.bindAttributeArray(self.shader, "inVertex", self.verts, 4)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, len(self.verts) // 4);
        self.unbindAttributeArray(self.shader, "inVertex")

        self.textureMap.unbindTextures()

        self.shader.unbind()



def createDefaultMatrices(width, height, context):
    eye = euclid.Vector3(0, 0, -5)
    at = euclid.Vector3(0, 0, 0)
    up = euclid.Vector3(0, 1, 0)
    view = euclid.Matrix4.new_look_at(eye, at, up)
    projection = utils.createPerspective(60, width, height, 0.1, 100)
    return view, projection

class ModelEntry:
    def __init__(self, mesh, matrix):
        self.mesh = mesh
        self.matrix = matrix
        self.textureMap = TextureMap()

    def free(self):
        self.textureMap.free()
        self.textureMap = None

class Renderer3D(BaseRenderer):
    def __init__(self):
        super(Renderer3D, self).__init__()
        self.useDepth = True
        self.width = 0
        self.height = 0
        self.shader = None
        self.models = {}

    def init(self, vertexShader, pixelShader, width, height):
        self.width = width
        self.height = height
        self.shader = gpu.ShaderProgram(vertexShader, pixelShader)

    def setTexture(self, sampler, image):
        self.models.itervalues().next().textureMap.setTexture(sampler, image)

    def free(self):
        for tag, entry in self.models.items():
            entry.free()
        self.models.clear()

    def getModel(self, tag):
        return self.models.get(tag)

    def loadModel(self, tag, path, textures, matrix=None):
        if not matrix:
            matrix = euclid.Matrix4()

        m = mesh.MeshObj(path)
        m.load()

        entry = ModelEntry(m, matrix)
        for sampler, image in textures.items():
            entry.textureMap.setTexture(sampler, image)

        old = self.models.get(tag)
        if old:
            old.free()
        self.models[tag] = entry

        return entry

    def getSize(self):
        return self.width, self.height

    def render(self, context):
        self.shader.bind()

        gl.glDisable(gl.GL_BLEND)
        gl.glEnable(gl.GL_DEPTH_TEST)

        gl.glClearDepth(1.0)
        gl.glClearColor(*self.clearColor)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        view, projection = createDefaultMatrices(self.width, self.height, context)
        self.shader.uniformMatrix4f(shader.VIEW_MATRIX, view)
        self.shader.uniformMatrix4f(shader.PROJ_MATRIX, projection)

        self.setUniforms(self.shader, context.uniforms)

        for tag, entry in self.models.items():
            mesh = entry.mesh

            entry.textureMap.bindTextures(self.shader)

            self.shader.uniformMatrix4f(shader.WORLD_MATRIX, entry.matrix)

            self.bindAttributeArray(self.shader, "inPosition", mesh.vertices, 3)
            self.bindAttributeArray(self.shader, "inNormal", mesh.normals, 3)
            self.bindAttributeArray(self.shader, "inUv", mesh.uvs, 2)
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, len(mesh.vertices) // 3)
            self.unbindAttributeArray(self.shader, "inPosition")
            self.unbindAttributeArray(self.shader, "inNormal")
            self.unbindAttributeArray(self.shader, "inUv")

            entry.textureMap.unbindTextures()

        gl.glEnable(gl.GL_BLEND)
        gl.glDisable(gl.GL_DEPTH_TEST)

        self.shader.unbind()

class BoneTransform:
    def __init__(self, bone, matrix, damping, transparency):
        self.bone = bone
        self.matrix = matrix
        self.damping = damping
        self.transparency = transparency

class SkinnedFrameData:
    def __init__(self, time, transform):
        self.time = time
        self.transform = transform

class SkinnedRenderer(BaseRenderer):
    BLACK_TEXTURE = "__black"

    def __init__(self):
        super(SkinnedRenderer, self).__init__()
        self.shader = None
        self.skinTextures = TextureMap()
        self.size = None
        self.root = None
        self.bones = {}
        self.oldFrameData = {}
        self.pointResolution = 30
        self.gridResolution = 0

    def getBones(self):
        return self.bones

    def init(self, image, vertexShader, pixeShader, args):
        self.shader = gpu.ShaderProgram(vertexShader.replace("MAX_BONES", str(skin.MAX_BONES)), pixeShader)
        self.pointResolution = args.get("pointResolution", self.pointResolution)
        self.gridResolution = args.get("gridResolution", self.gridResolution)

        rig = args.get("rigFile")
        if rig:
            self.loadJson(image, rig)
        else:
            if self.isLiveComposite(image):
                self.loadLiveComposite(image)
            else:
                self.loadNormalImage(image)

            self.updateMeshes()
            self.updateBones()

        for bone in self.bones.values():
            if bone.mesh:
                bone.mesh.updateUvs(bone)

        self.loadInfluenceImages()

    def updateMeshes(self, autoSubdivide=False, sizeSubdivide=0):
        transforms = self.computeBoneTransforms()
        for transform in transforms:
            bone = transform.bone
            if bone.image and bone.points:
                tris = bone.triangulatePoints(self.gridResolution)
                bone.updateMeshFromTriangles(tris)
                bone.mesh.moveVertices(bone.pos)
                if autoSubdivide:
                    bone.mesh.subdivideAdaptive(transforms)
                    bone.mesh.weldVertices()
                    bone.mesh.fixTJunctions()
                bone.mesh.weldVertices()

    def updateBones(self):
        self.oldFrameData = {}

        transforms = self.computeBoneTransforms()
        for i, transform in enumerate(transforms):
            bone = transform.bone
            if bone.mesh:
                bone.mesh.updateVertexWeights(i, transforms, self.bones)
                bone.mesh.sortTriangles(transforms)
                bone.mesh.updateUvs(bone)

    def loadJson(self, image, path):
        self.bones, data = skin.loadFromFile(path)
        self.size = data["width"], data["height"]

        for name, bone in self.bones.items():
            if not bone.parent:
                self.root = bone

            if bone.image:
                surface = self.loadCroppedSurface(bone, bone.image.name)
                self.skinTextures.setTexture(bone.image.name, surface)

    def isLiveComposite(self, image):
        #TODO There must be a better way to get this...
        container = image.visit()[0]
        return container.style.xmaximum and container.style.ymaximum

    def loadLiveComposite(self, image):
        container = image.visit()[0]
        self.size = container.style.xmaximum, container.style.ymaximum
        self.root = self.createRootBone()

        for i, child in enumerate(container.children):
            placement = child.get_placement()
            base = child.children[0]
            boneName = base.filename.rsplit(".")[0]
            surface = renpy.display.im.load_surface(base)
            self.createImageBone(surface, boneName, base.filename, placement, i)

    def loadNormalImage(self, image):
        surface = renpy.display.im.load_surface(image)
        self.size = surface.get_size()
        self.root = self.createRootBone()
        name = " ".join(image.name)
        self.createImageBone(surface, name, name, (0, 0), 0)

    def createImageBone(self, surface, boneName, fileName, placement, zOrder):
        originalWidth, originalHeight = surface.get_size()
        crop = surface.get_bounding_rect()
        crop.inflate_ip(10, 10) #TODO For testing
        surface = self.cropSurface(surface, crop)
        x = placement[0] + crop[0]
        y = placement[1] + crop[1]

        bone = skin.SkinningBone(boneName)
        bone.parent = self.root.name
        bone.image = skin.SkinnedImage(fileName, crop[0], crop[1],
            surface.get_width(), surface.get_height(),
            originalWidth, originalHeight)
        bone.pos = (x, y)
        bone.pivot = (bone.pos[0] + bone.image.width / 2.0, bone.pos[1] + bone.image.height / 2.0)
        bone.zOrder = zOrder
        bone.updatePoints(surface, self.pointResolution)

        self.bones[bone.parent].children.append(boneName)
        self.bones[boneName] = bone

        self.skinTextures.setTexture(bone.image.name, surface)

    def createRootBone(self):
        root = skin.SkinningBone("root")
        root.pivot = (self.size[0] * 0.5, self.size[1] * 0.75)
        self.bones = {root.name: root}
        return root

    def cropSurface(self, surface, rect):
        cropped = pygame.Surface((rect[2], rect[3]), 0, surface)
        cropped.blit(surface, (0, 0), rect)
        return cropped

    def loadCroppedSurface(self, bone, name, resize=None):
        surface = renpy.display.im.load_surface(renpy.exports.displayable(name))
        image = bone.image
        scale = 1
        if resize:
            scale = surface.get_width() / float(resize.originalWidth)
        crop = tuple(int(round(x)) for x in (image.x * scale, image.y * scale, image.width * scale, image.height * scale))
        return self.cropSurface(surface, crop)

    def loadInfluenceImages(self):
        self.skinTextures.setTexture(self.BLACK_TEXTURE, shader.ZERO_INFLUENCE)

        for name, bone in self.bones.items():
            if bone.image:
                influence = self.getInfluenceName(bone.image.name)
                if renpy.exports.has_image(influence, exact=True):
                    surface = self.loadCroppedSurface(bone, influence, bone.image)
                    self.skinTextures.setTexture(influence, surface)

    def getInfluenceName(self, name):
        return name.split(".")[0] + " influence"

    def setTexture(self, sampler, image):
        pass

    def free(self):
        if self.skinTextures:
            self.skinTextures.free()
            self.skinTextures = None

        if self.shader:
            self.shader.free()
            self.shader = None

    def getSize(self):
        return self.size

    def getProjection(self):
        flipY = -1
        projection = utils.createPerspectiveOrtho(-1.0, 1.0, 1.0 * flipY, -1.0 * flipY, -1.0, 1.0)

        result = euclid.Matrix4()
        for i, attr in enumerate("abcdefghijklmnop"):
            setattr(result, attr, projection[i])
        return result

    def render(self, context):
        self.shader.bind()

        self.setUniforms(self.shader, context.uniforms)
        self.shader.uniformf("screenSize", *self.getSize())

        gl.glClearColor(*self.clearColor)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glDisable(gl.GL_DEPTH_TEST)

        transforms = self.computeBoneTransforms()

        boneMatrixArray = []
        for i, transform in enumerate(transforms):
            boneMatrix = transform.matrix
            boneMatrix.p = transform.transparency #Abuse unused matrix location

            overwrite = transform.damping > 0.0
            if overwrite and self.oldFrameData.get(transform.bone.name):
                overwrite = self.dampenBoneTransform(context, transform)

            if overwrite:
                self.oldFrameData[transform.bone.name] = SkinnedFrameData(context.shownTime, transform)

            boneMatrixArray.extend(utils.matrixToList(boneMatrix))
        self.shader.uniformMatrix4fArray("boneMatrices", boneMatrixArray)

        for transform in transforms:
            self.renderBoneTransform(transform, context)

        for i in range(2):
            gl.glActiveTexture(gl.GL_TEXTURE0 + i)
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        gl.glActiveTexture(gl.GL_TEXTURE0)

        self.shader.unbind()

    def dampenBoneTransform(self, context, transform):
        data = self.oldFrameData[transform.bone.name]
        old = data.transform.matrix

        #Abuse unused matrix locations
        boneMatrix = transform.matrix
        boneMatrix.m = 0
        boneMatrix.n = 0
        boneMatrix.o = 0
        old.m = 0
        old.n = 0
        old.o = 0

        pivot = transform.bone.pivot
        v = euclid.Vector3(pivot[0], pivot[1], 0.0)
        pos = boneMatrix.transform(v)
        posOld = old.transform(v)

        deltaX = posOld.x - pos.x
        deltaY = posOld.y - pos.y
        dampness = max(transform.damping - max(float(context.shownTime) - data.time, 0.0), 0.0)

        boneMatrix.m = deltaX
        boneMatrix.n = deltaY
        boneMatrix.o = dampness

        return dampness <= 0.0

    def renderBoneTransform(self, transform, context):
        bone = transform.bone
        mesh = bone.mesh

        if not bone.image or not mesh:
            #No image or mesh attached
            return

        if not bone.visible or transform.transparency >= 1.0:
            #Nothing to draw
            return

        tex = self.skinTextures.textures[bone.image.name]
        texInfluence = self.skinTextures.textures.get(self.getInfluenceName(bone.image.name))
        if not texInfluence:
            texInfluence = self.skinTextures.textures[self.BLACK_TEXTURE]

        self.shader.uniformi(shader.TEX0, 0)
        tex.texture.bind(0)

        self.shader.uniformi(shader.TEX1, 1)
        texInfluence.texture.bind(1)

        self.shader.uniformMatrix4f(shader.PROJECTION, self.getProjection())

        self.bindAttributeArray(self.shader, "inVertex", mesh.vertices, 2)
        self.bindAttributeArray(self.shader, "inUv", mesh.uvs, 2)
        self.bindAttributeArray(self.shader, "inBoneWeights", mesh.boneWeights, 4)
        self.bindAttributeArray(self.shader, "inBoneIndices", mesh.boneIndices, 4)

        self.shader.uniformf("wireFrame", 0)
        self.shader.uniformf("boneAlpha", max(1.0 - transform.transparency, 0))
        gl.glDrawElements(gl.GL_TRIANGLES, len(mesh.indices), gl.GL_UNSIGNED_INT, mesh.indices)

        if bone.wireFrame:
            self.shader.uniformf("wireFrame", 1)
            self.shader.uniformf("boneAlpha", 1.0)
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            gl.glDrawElements(gl.GL_TRIANGLES, len(mesh.indices), gl.GL_UNSIGNED_INT, mesh.indices)
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        self.unbindAttributeArray(self.shader, "inVertex")
        self.unbindAttributeArray(self.shader, "inUv")
        self.unbindAttributeArray(self.shader, "inBoneWeights")
        self.unbindAttributeArray(self.shader, "inBoneIndices")

    def computeBoneTransforms(self):
        transforms = []
        stack = []
        stack.append((None, euclid.Matrix4(), 0.0, 0.0))
        self.computeBoneTransformRecursive(self.root, transforms, stack)
        stack.pop()
        transforms.sort(key=lambda t: t.bone.zOrder)

        if len(stack) != 0:
            raise RuntimeError("Unbalanced stack size: %i" % len(stack))

        if len(transforms) > skin.MAX_BONES:
            raise RuntimeError("Too many bones, maximum is %i" % skin.MAX_BONES)

        return transforms

    def computeBoneTransformRecursive(self, bone, transforms, stack):
        parent, parentMatrix, parentDamping, parentTransparency = stack[-1]

        transform = euclid.Matrix4() * parentMatrix

        pivot = bone.pivot
        xMove = pivot[0]
        yMove = pivot[1]

        transform.translate(xMove, yMove, 0)
        transform.translate(bone.translation.x, bone.translation.y, 0)

        rotation = bone.rotation
        if rotation.y != 0.0:
            transform.rotatey(rotation.y)
        if rotation.x != 0.0:
            transform.rotatex(rotation.x)
        if rotation.z != 0.0:
            transform.rotatez(rotation.z)

        transform.scale(bone.scale.x, bone.scale.y, bone.scale.z)

        transform.translate(-xMove, -yMove, 0)

        damping = max(bone.damping, parentDamping)
        transparency = 1 - ((1 - bone.transparency) * (1 - parentTransparency))
        transforms.append(BoneTransform(bone, transform, damping, transparency))
        stack.append((bone, transform, damping, transparency))

        for childName in bone.children:
            self.computeBoneTransformRecursive(self.bones[childName], transforms, stack)

        stack.pop()
