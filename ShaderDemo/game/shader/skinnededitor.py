
import math
import json
import ctypes

import pygame
import euclid
import skin
import geometry

PIVOT_SIZE = 4
PICK_DISTANCE_PIVOT = PIVOT_SIZE * 2
PICK_DISTANCE_CROP = 5

PIVOT_COLOR = (255, 0, 0)
MESH_COLOR = (128, 255, 255)
ACTIVE_COLOR = (0, 255, 0)
HOVER_COLOR = (255, 255, 0)

DRAG_POINT = "dragPoint"
DRAG_PIVOT = "dragPivot"
DRAG_POS = "dragPos"
ACTIVE_BONE_NAME = "activeBoneName"
MOUSE = "mouse"
MODE = "mode"

pygame.font.init()
FONT_SIZE = 20
FONT = pygame.font.Font(None, FONT_SIZE)

class Action:
    def start(self, editor):
        pass

    def cancel(self, editor):
        pass

    def apply(self, editor):
        pass

    def update(self, editor):
        pass

    def draw(self, editor):
        pass

class TranslationEdit(Action):
    def __init__(self, editor, mouse, bone, attributes):
        self.mouse = mouse
        self.bone = bone
        self.attributes = attributes
        self.original = None

    def start(self, editor):
        self.original = euclid.Vector3(*self.bone.translation)

    def cancel(self, editor):
        self.bone.translation = self.original

    def update(self, editor):
        if "x" in self.attributes:
            self.bone.translation.x = self.original.x + (editor.mouse[0] - self.mouse[0])
        if "y" in self.attributes:
            self.bone.translation.y = self.original.y + (editor.mouse[1] - self.mouse[1])

    def draw(self, editor):
        axes = []
        angles = []
        for axis in ["x", "y"]:
            if axis in self.attributes:
                axes.append(axis)
                angles.append("%.0f" % getattr(self.bone.translation, axis))

        pivot = editor.getBonePivotTransformed(self.bone)
        editor.context.overlayCanvas.line("#0f0", (pivot.x, pivot.y), editor.mouse)
        editor.drawText("T(%s): %s" % (", ".join(axes), ", ".join(angles)), "#fff", (editor.mouse[0] + 20, editor.mouse[1]))

class ScaleEdit(Action):
    def __init__(self, editor, mouse, bone, attributes):
        self.mouse = mouse
        self.bone = bone
        self.attributes = attributes
        self.pivot = None
        self.original = None
        self.values = {}

    def start(self, editor):
        self.pivot = editor.getBonePivotTransformed(self.bone)
        self.original = euclid.Vector3(self.bone.scale.x, self.bone.scale.y, self.bone.scale.z)
        for attr in self.attributes:
            self.values[attr] = getattr(self.original, attr) + math.atan2(self.mouse[0] - self.pivot[0], self.mouse[1] - self.pivot[1])

    def cancel(self, editor):
        self.bone.scale = self.original

    def update(self, editor):
        for attr in self.values:
            angle = math.atan2(editor.mouse[0] - self.pivot[0], editor.mouse[1] - self.pivot[1])
            setattr(self.bone.scale, attr, self.values[attr] - angle)

    def draw(self, editor):
        axes = []
        angles = []
        for axis in ["x", "y", "z"]:
            if axis in self.values:
                axes.append(axis)
                angles.append("%.2f" % getattr(self.bone.scale, axis))

        editor.context.overlayCanvas.line("#0f0", (self.pivot.x, self.pivot.y), editor.mouse)
        editor.drawText("S(%s): %s" % (", ".join(axes), ", ".join(angles)), "#fff", (editor.mouse[0] + 20, editor.mouse[1]))


class RotationEdit(Action):
    def __init__(self, editor, mouse, bone, attributes):
        self.mouse = mouse
        self.bone = bone
        self.attributes = attributes
        self.pivot = None
        self.original = None
        self.values = {}

    def start(self, editor):
        self.pivot = editor.getBonePivotTransformed(self.bone)
        self.original = euclid.Vector3(self.bone.rotation.x, self.bone.rotation.y, self.bone.rotation.z)
        for attr in self.attributes:
            self.values[attr] = getattr(self.original, attr) + math.atan2(self.mouse[0] - self.pivot[0], self.mouse[1] - self.pivot[1])

    def cancel(self, editor):
        self.bone.rotation = self.original

    def update(self, editor):
        for attr in self.values:
            angle = math.atan2(editor.mouse[0] - self.pivot[0], editor.mouse[1] - self.pivot[1])
            setattr(self.bone.rotation, attr, self.values[attr] - angle)

    def draw(self, editor):
        axes = []
        angles = []
        for axis in ["x", "y", "z"]:
            if axis in self.values:
                axes.append(axis)
                angles.append("%.1f" % math.degrees(getattr(self.bone.rotation, axis)))

        editor.context.overlayCanvas.line("#0f0", (self.pivot.x, self.pivot.y), editor.mouse)
        editor.drawText("R(%s): %s" % (", ".join(axes), ", ".join(angles)), "#fff", (editor.mouse[0] + 20, editor.mouse[1]))


class ExtrudeBone(Action):
    def __init__(self, editor, mouse, bone):
        self.mouse = mouse
        self.bone = bone
        self.pivot = editor.getBonePivotTransformed(bone)

    def findNextFreeBoneName(self, bones, base):
        index = 1
        while 1:
            name = "%s %i" % (base, index)
            if not name in bones:
                return name
            index += 1

    def findNextZOrder(self, bone, bones):
        zOrder = bone.zOrder + 1
        for name in bone.children:
            zOrder = max(zOrder, bones[name].zOrder + 1)
        return zOrder

    def cancel(self, editor):
        pass

    def apply(self, editor):
        bones = editor.context.renderer.bones
        parent = bones[self.bone.name]

        parts = parent.name.strip().split(" ")
        if parts[-1].isdigit():
            parts = parts[:-1]
        newName =  self.findNextFreeBoneName(bones, " ".join(parts))

        bone = skin.SkinningBone(newName)
        bone.pivot = editor.getBoneInverseTranslation(bones[self.bone.name], editor.mouse, False)
        bone.zOrder = self.findNextZOrder(parent, bones)
        bones[bone.name] = bone

        editor.connectBone(bone.name, parent.name)
        editor.setActiveBone(bone)

    def update(self, editor):
        pass

    def draw(self, editor):
        editor.context.overlayCanvas.line(PIVOT_COLOR, (self.pivot.x, self.pivot.y), editor.mouse)
        editor.context.overlayCanvas.circle(PIVOT_COLOR, editor.mouse, PIVOT_SIZE)

class ConnectBone(Action):
    def __init__(self, editor, mouse, bone):
        self.mouse = mouse
        self.bone = bone
        self.pivot = editor.getBonePivotTransformed(bone)

    def isValidParent(self, editor, parent):
        if parent and self.bone.name != parent.name:
            name = parent.name
            while name:
                bone = editor.getBone(name)
                if bone.name == self.bone.name:
                    #This bone connection would create a looping bone hierarchy
                    return False
                name = bone.parent
            return True
        return False

    def apply(self, editor):
        hover = editor.pickPivot(editor.mouse)
        if self.isValidParent(editor, hover):
            editor.connectBone(self.bone.name, hover.name)

    def draw(self, editor):
        color = (255, 255, 0)
        hover = editor.pickPivot(editor.mouse)
        if self.isValidParent(editor, hover):
            color = (0, 255, 0)
        editor.context.overlayCanvas.line(color, (self.pivot.x, self.pivot.y), editor.mouse)
        editor.context.overlayCanvas.circle(color, editor.mouse, PIVOT_SIZE)

class PoseMode:
    def __init__(self):
        self.editor = None
        self.active = None

    def update(self, editor):
        self.editor = editor

    def handleEvent(self, event):
        event, pos = event
        if event.type == pygame.KEYDOWN:
            key = event.key
            alt = event.mod & pygame.KMOD_ALT
            activeBone = self.editor.getActiveBone()

            rotAxis = "z"
            transAxes = ["x", "y"]
            scaleAxes = ["x", "y", "z"]
            if self.active and key in (pygame.K_x, pygame.K_y, pygame.K_z):
                if isinstance(self.active, TranslationEdit):
                    transAxes = [chr(key)]
                    key = pygame.K_g
                if isinstance(self.active, RotationEdit):
                    rotAxis = chr(key)
                    key = pygame.K_r
                elif isinstance(self.active, ScaleEdit):
                    scaleAxes = [chr(key)]
                    key = pygame.K_s

            if key == pygame.K_h and activeBone:
                activeBone.visible = not activeBone.visible
                return True
            if key == pygame.K_x:
                if activeBone:
                    self.editor.deleteBone(activeBone)
                else:
                    point = self.editor.pickPoint(pos)
                    if point:
                        del point[0].points[point[2]]
                        self.editor.updateBones()
                return True
            if key == pygame.K_g and activeBone:
                if alt:
                    activeBone.translation = euclid.Vector3(0.0, 0.0, 0.0)
                else:
                    self.newEdit(TranslationEdit(self.editor, pos, activeBone, transAxes))
                return True
            if key == pygame.K_r and activeBone:
                if alt:
                    activeBone.rotation = euclid.Vector3(0.0, 0.0, 0.0)
                else:
                    self.newEdit(RotationEdit(self.editor, pos, activeBone, [rotAxis]))
                return True
            if key == pygame.K_s and activeBone:
                if alt:
                    activeBone.scale = euclid.Vector3(1.0, 1.0, 1.0)
                else:
                    self.newEdit(ScaleEdit(self.editor, pos, activeBone, scaleAxes))
                return True
            if key == pygame.K_b and activeBone:
                activeBone.blocker = not activeBone.blocker
                self.editor.updateBones()
            if key == pygame.K_t and activeBone:
                activeBone.tessellate = not activeBone.tessellate
                self.editor.updateBones()
            if key == pygame.K_d and activeBone:
                activeBone.damping = 0.0 if activeBone.damping else 0.5
                self.editor.updateBones()
            if key == pygame.K_e and activeBone:
                self.newEdit(ExtrudeBone(self.editor, pos, activeBone))
                return True
            if key == pygame.K_c and activeBone:
                self.newEdit(ConnectBone(self.editor, pos, activeBone))
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.active:
                if event.button == 1:
                    self.active.apply(self.editor)
                if event.button == 3:
                    self.active.cancel(self.editor)
                self.active = None
                return True

        return False

    def newEdit(self, edit):
        if self.active:
            self.active.cancel(self.editor)
        self.active = edit
        self.active.start(self.editor)

    def draw(self):
        if self.active:
            self.active.update(self.editor)
            self.active.draw(self.editor)

    def isUserInteracting(self):
        return bool(self.active)


class SkinnedEditor:
    def __init__(self, context, settings):
        self.context = context
        self.settings = settings
        self.mouse = (0, 0)
        self.transforms = context.renderer.computeBoneTransforms()
        self.transformsMap = self.getTransformsDict()

        self.mode = self.get(MODE)
        if not self.mode:
            self.mode = PoseMode()
            self.set(MODE, self.mode)
        self.mode.update(self)
        self.userInteracting = self.mode.isUserInteracting()

    def update(self):
        self.handleEvents()
        self.visualizeBones()

    def saveSkeletonToFile(self, name):
        skin.saveToFile(self.context, self.context.renderer.bones, name)

    def get(self, key):
        return self.context.store.get(key)

    def set(self, key, value):
        self.context.store[key] = value

    def getActiveBone(self):
        bones = self.context.renderer.bones
        name = self.get(ACTIVE_BONE_NAME)
        if name in bones:
            return bones[name]
        return None

    def setActiveBone(self, bone):
        if bone:
            self.set(ACTIVE_BONE_NAME, bone.name)
        else:
            self.set(ACTIVE_BONE_NAME, None)

    def getBones(self):
        return self.context.renderer.bones

    def getBone(self, name):
        return self.context.renderer.bones[name]

    def debugAnimate(self, animate):
        context = self.context
        bones = context.renderer.bones
        for name, bone in bones.items():
            if animate and bone.parent:
                strength = len(self.getBone(bone.parent).children)
                bone.rotation.z = math.sin(context.time * 0.5) * min(0.5, strength / 10.0)
            else:
                bone.rotation.z = 0.0

    def drawText(self, text, color, pos, align=-1):
        surface = FONT.render(text, True, color)
        if align == 1:
            pos = (pos[0] - surface.get_width(), pos[1])
        self.context.overlayCanvas.get_surface().blit(surface, pos)

    def subdivide(self, bone, minSize):
        if bone.mesh and not self.settings["autoSubdivide"]:
            #TODO Not really needed?
            #bone.mesh.subdivide(minSize)
            #self.updateBones()
            return True
        return False

    def renameBone(self, bone, newName):
        bones = self.getBones()
        if newName not in bones:
            oldName = bone.name
            bone.name = newName

            if bone.parent:
                bones[bone.parent].children.remove(oldName)
                bones[bone.parent].children.append(newName)

            for child in bone.children:
                bones[child].parent = newName

            del bones[oldName]
            bones[newName] = bone

            return True
        return False

    def deleteBone(self, bone):
        if not bone.parent:
            return

        bones = self.context.renderer.bones
        for child in bone.children[:]:
            self.connectBone(child, bone.parent, False)

        bones[bone.parent].children.remove(bone.name)
        del bones[bone.name]

        self.updateBones()

    def connectBone(self, boneName, parentName, update=True):
        bones = self.context.renderer.bones
        poseBone = bones[boneName]
        newParent = bones[parentName]

        oldParent = None
        if poseBone.parent in bones:
            oldParent = bones[poseBone.parent]

        if boneName not in newParent.children:
            if oldParent:
                oldParent.children.remove(boneName)
            newParent.children.append(boneName)
            poseBone.parent = newParent.name

        if update:
            self.updateBones()

    def updateBones(self):
        self.context.renderer.updateMeshes(self.settings["autoSubdivide"])
        self.context.renderer.updateBones()

    def setBoneZOrder(self, bone, newZ):
        delta = newZ - bone.zOrder
        children = [bone] + bone.getAllChildren(self.getBones())
        for child in children:
            child.zOrder += delta

    def resetPose(self):
        for bone in self.getBones().values():
            bone.translation = euclid.Vector3(0.0, 0.0, 0.0)
            bone.scale = euclid.Vector3(1.0, 1.0, 1.0)
            bone.rotation = euclid.Vector3(0.0, 0.0, 0.0)
            bone.visible = True

    def handleEvents(self):
        self.mouse = self.get(MOUSE)

        for event, pos in self.context.events:
            self.mouse = pos

            handled = self.mode.handleEvent((event, pos))
            if not handled:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handleMouseDown(event, pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.handleMouseMotion(pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handleMouseUp(pos)

        if self.mouse:
            self.set(MOUSE, self.mouse)

    def handleMouseDown(self, event, pos):
        self.stopDrag()

        if event.button == 1:
            canDrag = not self.settings["disableDrag"]
            bone = None
            if self.settings["pivots"]:
                bone = self.pickPivot(pos)
                if bone:
                    self.setActiveBone(bone)
                    if canDrag:
                        self.set(DRAG_PIVOT, (bone, self.getBoneInverseTranslation(bone, pos), bone.pivot))
                else:
                    self.setActiveBone(None)
                    self.set(DRAG_PIVOT, None)

            point = None
            if self.settings["edgePoints"] and not bone:
                point = self.pickPoint(pos)
                if point and canDrag:
                    self.set(DRAG_POINT, (point, pos))

            if self.settings["imageAreas"] and not bone and not point:
                bone = self.pickCrop(pos)
                if bone:
                    self.setActiveBone(bone)
                    if canDrag:
                        self.set(DRAG_POS, (bone, pos, bone.pos))
                else:
                    self.set(DRAG_POS, None)
        elif event.button == 4:
            active = self.getActiveBone()
            if active:
                self.setBoneZOrder(active, active.zOrder + 1)
                self.updateBones()
        elif event.button == 5:
            active = self.getActiveBone()
            if active:
                self.setBoneZOrder(active, active.zOrder - 1)
                self.updateBones()

    def handleMouseMotion(self, pos):
        dragPoint = self.get(DRAG_POINT)
        if dragPoint:
            bone, oldPos, index = dragPoint[0]
            oldMouse = dragPoint[1]
            delta = (oldMouse[0] - pos[0], oldMouse[1] - pos[1])
            bone.points[index] = (oldPos[0] - delta[0], oldPos[1] - delta[1])

        dragPivot = self.get(DRAG_PIVOT)
        if dragPivot:
            bone, oldMouse, oldHead = dragPivot
            inverse = self.getBoneInverseTranslation(bone, pos)
            delta = (oldMouse[0] - inverse[0], oldMouse[1] - inverse[1])
            bone.pivot = (oldHead[0] - delta[0], oldHead[1] - delta[1])

        dragPos = self.get(DRAG_POS)
        if dragPos:
            bone, oldMouse, oldPos = dragPos
            delta = (oldMouse[0] - pos[0], oldMouse[1] - pos[1])
            pos = bone.pos
            #TODO Breaks uv generation...
            #bone.pos = (oldPos[0] - delta[0], oldPos[1] - delta[1])

    def handleMouseUp(self, pos):
        self.stopDrag()

    def stopDrag(self):
        if self.get(DRAG_POINT) or self.get(DRAG_PIVOT):
            self.updateBones()

        self.set(DRAG_POINT, None)
        self.set(DRAG_PIVOT, None)
        self.set(DRAG_POS, None)

    def isDragging(self):
        return self.get(DRAG_POINT) or self.get(DRAG_PIVOT) or self.get(DRAG_POS)

    def isUserInteracting(self):
        return self.isDragging() or self.userInteracting or self.mode.isUserInteracting()

    def pickPoint(self, pos):
        closest = None
        closestDistance = None
        for bone in self.getBones().values():
            for i, point in enumerate(self.getPolyPoints(bone)):
                distance = geometry.pointDistance(pos, point)
                if distance < PICK_DISTANCE_PIVOT:
                    if not closest or distance < closestDistance:
                        closest = (bone, bone.points[i], i)
                        closestDistance = distance
        return closest

    def pickPivot(self, pos):
        closest = None
        closestDistance = None
        for trans in self.transforms:
            bone = trans.bone
            pivot = self.getBonePivotTransformed(bone)
            distance = (pivot - euclid.Vector3(pos[0], pos[1])).magnitude()
            if distance < PICK_DISTANCE_PIVOT:
                if not closest or distance < closestDistance:
                    closest = bone
                    closestDistance = distance
        return closest

    def pickCrop(self, pos):
        closest = None
        closestDistance = None
        for trans in self.transforms:
            if trans.bone.image:
                lines = self.getImageLines(trans.bone)
                for i in range(len(lines) - 1):
                    distance = geometry.pointToLineDistance(pos, lines[i], lines[i + 1])
                    if distance < PICK_DISTANCE_CROP:
                        if not closest or distance < closestDistance:
                            closest = trans.bone
                            closestDistance = distance
        return closest

    def getImageLines(self, bone):
        pos = bone.pos
        image = bone.image
        lines = [
            pos,
            (pos[0] + image.width, pos[1]),
            (pos[0] + image.width, pos[1] + image.height),
            (pos[0], pos[1] + image.height),
            pos
        ]
        return lines

    def getPolyPoints(self, bone):
        points = []
        if bone.points:
            boneMatrix = self.transformsMap[bone.name].matrix
            for point in bone.points:
                pos = boneMatrix.transform(euclid.Vector3(bone.pos[0] + point[0], bone.pos[1] + point[1]))
                points.append((pos.x, pos.y))
        return points

    def getTriangles(self, bone):
        triangles = []
        if bone.triangles:
            boneMatrix = self.transformsMap[bone.name].matrix
            for tri in bone.triangles:
                for v in tri:
                    pos = boneMatrix.transform(euclid.Vector3(v[0], v[1]))
                    triangles.append((pos.x, pos.y))
        return triangles

    def getBoneInverseTranslation(self, bone, translation, parentSpace=True):
        source = bone
        if parentSpace and bone.parent:
            source = self.getBone(bone.parent)

        inverse = self.transformsMap[source.name].matrix.inverse()
        result = inverse.transform(euclid.Vector3(translation[0], translation[1]))
        return (result.x, result.y)

    def getBonePivotTransformed(self, bone):
        v = self.transformsMap[bone.name].matrix.transform(self.getBonePivot(bone))
        v.z = 0.0 #Clear any depth changes, we only care about 2D
        return v

    def getBonePivot(self, bone):
        pivot = bone.pivot
        return euclid.Vector3(pivot[0],  pivot[1], 0)

    def getBonePos(self, bone):
        pos = bone.pos
        return euclid.Vector3(pos[0],  pos[1], 0)

    def getTransformsDict(self):
        mapping = {}
        for trans in self.transforms:
            mapping[trans.bone.name] = trans
        return mapping

    def visualizeBones(self):
        context = self.context
        canvas = context.overlayCanvas
        mouse = self.mouse
        black = (0, 0, 0)
        shadow = 1
        activeBone = self.getActiveBone()

        hoverPoint = None
        hoverPivotBone = None
        hoverCropBone = None
        if mouse:
            hoverPoint = self.pickPoint(mouse)
            hoverPivotBone = self.pickPivot(mouse)
            hoverCropBone = self.pickCrop(mouse)

        for trans in reversed(self.transforms):
            bone = trans.bone
            #bone.wireFrame = ((activeBone and bone.name == activeBone.name) or not activeBone) and self.settings["wireframe"]
            bone.wireFrame = self.settings["wireframe"]

            pos = self.getBonePos(bone)
            pivot = self.getBonePivotTransformed(bone)

            if self.settings["imageAreas"] and bone.image and bone.visible:
                areaColor = (255, 255, 0)
                lines = self.getImageLines(bone)
                if not hoverPivotBone and hoverCropBone and bone.name == hoverCropBone.name:
                    self.drawText(hoverCropBone.name, "#fff", (mouse[0] + 20, mouse[1]))
                    areaColor = ACTIVE_COLOR
                canvas.lines(areaColor, False, lines)

                #triangles = self.getTriangles(bone)
                #for i in range(0, len(triangles), 3):
                #    tri = (triangles[i], triangles[i + 1], triangles[i + 2])
                #    context.overlayCanvas.lines("#0f0", True, tri)

            if self.settings["edgePoints"] and bone.visible:
                polyPoints = self.getPolyPoints(bone)
                if polyPoints:
                    canvas.lines("#ff0", True, polyPoints)
                    for i, p in enumerate(polyPoints):
                        #color = (0, int(float(i) / len(polyPoints) * 255), 0)
                        color = (0, 128, 0)
                        if hoverPoint and hoverPoint[0].name == bone.name and hoverPoint[2] == i:
                            color = (255, 255, 0)
                        canvas.circle(color, p, 3)

            if self.settings["pivots"]:
                if bone.parent:
                    parentTrans = self.transformsMap[bone.parent]
                    parentBone = parentTrans.bone
                    parentPos = self.getBonePivotTransformed(parentBone)
                    color = PIVOT_COLOR
                    if parentBone.damping > 0.0:
                        color = (0, 255, 255)
                    if geometry.pointDistance((pivot.x, pivot.y), (parentPos.x, parentPos.y)) > 1:
                        #TODO Line drawing hangs if passed same start and end?
                        canvas.line(color, (pivot.x, pivot.y), (parentPos.x, parentPos.y))

                x = pivot.x
                y = pivot.y
                color = PIVOT_COLOR
                if bone.mesh:
                    color = MESH_COLOR

                if bone.blocker:
                    s = PIVOT_SIZE + 1
                    canvas.rect(black, (x - s - shadow, y - s - shadow, (s + shadow) * 2 , (s + shadow) * 2))
                    canvas.rect(color, (x - s, y - s, s * 2, s * 2))
                elif bone.tessellate:
                    s = PIVOT_SIZE + 3
                    ty = y - 2
                    canvas.polygon(black, [(x - s, ty + s), (x, ty - s), (x + s, ty + s)])
                    s -= 2
                    canvas.polygon(color, [(x - s, ty + s), (x, ty - s), (x + s, ty + s)])
                else:
                    canvas.circle(black, (x, y), PIVOT_SIZE + shadow)
                    canvas.circle(color, (x, y), PIVOT_SIZE)

                if hoverPivotBone and bone.name == hoverPivotBone.name:
                    canvas.circle(HOVER_COLOR, (x, y), PIVOT_SIZE - 1)
                if activeBone and bone.name == activeBone.name:
                    canvas.circle(ACTIVE_COLOR, (x, y), PIVOT_SIZE - 2)

                textColor = "#fff"
                if activeBone and bone.name == activeBone.name:
                    textColor = ACTIVE_COLOR

                if self.settings["names"]:
                    self.drawText(bone.name, textColor, (x + 15, y - 10))

        if hoverPivotBone:
            self.visualizeBoneProperties(hoverPivotBone, mouse)

        self.mode.draw()

    def visualizeBoneProperties(self, bone, mouse):
        color = (0, 0, 0)
        x = 10
        y = 10

        name = bone.name
        if bone.mesh:
            name += " (%i polygons, %i vertices)" % (len(bone.mesh.indices) // 3, len(bone.mesh.vertices) // 2)
        self.drawText(name, color, (x, y))
        y += FONT_SIZE

        degrees = tuple([math.degrees(d) for d in (bone.rotation.x,  bone.rotation.y,  bone.rotation.z)])
        self.drawText("Rotation - x: %.1f, y: %.1f, z: %.1f" % degrees, color, (x, y))
        y += FONT_SIZE

        self.drawText("Scale     - x: %.1f, y: %.1f, z: %.1f" % (bone.scale.x,  bone.scale.y,  bone.scale.z), color, (x, y))
        y += FONT_SIZE

        self.drawText("Z-order  - %i" % bone.zOrder, color, (x, y))
