
import math
import json
import ctypes

import pygame
import euclid
import skinned
import geometry

PIVOT_SIZE = 4
PICK_DISTANCE_PIVOT = PIVOT_SIZE * 2
PICK_DISTANCE_CROP = 5

PIVOT_COLOR = (255, 0, 0)
ACTIVE_COLOR = (0, 255, 0)
HOVER_COLOR = (255, 255, 0)

DRAG_PIVOT = "dragPivot"
DRAG_POS = "dragPos"
ACTIVE_BONE_NAME = "activeBoneName"
MOUSE = "mouse"
MODE = "mode"

pygame.font.init()
FONT_SIZE = 20
FONT = pygame.font.Font(None, FONT_SIZE)

class Action:
    def cancel(self, editor):
        pass

    def apply(self, editor):
        pass

    def update(self, editor):
        pass

    def draw(self, editor):
        pass

class AttributeEdit(Action):
    def __init__(self, editor, mouse, bone, attribute, duplicates=None):
        self.mouse = mouse
        self.bone = bone
        self.attribute = attribute
        self.duplicates = duplicates
        self.original = self.getValue()
        self.pivot = editor.getBonePivotTransformed(bone)
        self.value = self.original + math.atan2(mouse[0] - self.pivot[0], mouse[1] - self.pivot[1])

    def getValue(self):
        v = self.bone
        for attr in self.attribute.split("."):
            v = getattr(v, attr)
        return v

    def setValue(self, value):
        v = self.bone
        attrs = self.attribute.split(".")
        for attr in attrs[:-1]:
            v = getattr(v, attr)
        setattr(v, attrs[-1], value)

        if self.duplicates:
            for dup in self.duplicates:
                setattr(v, dup, value)

    def cancel(self, editor):
        self.setValue(self.original)

    def apply(self, editor):
        pass

    def update(self, editor):
        angle = math.atan2(editor.mouse[0] - self.pivot[0], editor.mouse[1] - self.pivot[1])
        self.setValue(self.value - angle)

    def draw(self, editor):
        name = self.attribute[0].upper()
        axis = " (%s)" % self.attribute.split(".")[-1]

        value = self.getValue()
        if "rotation" in self.attribute:
            value = math.degrees(value)

        editor.context.overlayCanvas.line("#0f0", (self.pivot.x, self.pivot.y), editor.mouse)
        editor.drawText("%s%s: %.1f" % (name, axis, value), "#fff", (editor.mouse[0] + 20, editor.mouse[1]))


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

    def cancel(self, editor):
        pass

    def apply(self, editor):
        bones = editor.context.renderer.bones
        parent = bones[self.bone.name]

        parts = parent.name.strip().split(" ")
        if parts[-1].isdigit():
            parts = parts[:-1]
        newName =  self.findNextFreeBoneName(bones, " ".join(parts))

        bone = skinned.Bone(newName)
        bone.pivot = editor.getBoneInverseTranslation(bones[self.bone.name], editor.mouse)
        bone.zOrder = parent.zOrder + 1
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
            key = event.unicode
            activeBone = self.editor.getActiveBone()
            hover = self.editor.pickPivot(pos)

            rotAxis = "z"
            scaleAxis = "y"
            scaleDup = ["x", "z"]

            if self.active and key in ("x", "y", "z"):
                if "rotation" in self.active.attribute:
                    rotAxis = key
                    key = "r"
                elif "scale" in self.active.attribute:
                    scaleAxis = key
                    key = "s"
                    scaleDup = []

            if key == "h" and hover:
                hover.visible = not hover.visible
                return True
            if key == "x" and hover:
                self.editor.deleteBone(hover)
                return True
            if key == "r" and activeBone:
                self.newEdit(AttributeEdit(self.editor, pos, activeBone, "rotation." + rotAxis))
                return True
            if key == "s" and activeBone:
                #TODO Cancel bug does not undo all values...
                self.newEdit(AttributeEdit(self.editor, pos, activeBone, "scale." + scaleAxis, scaleDup))
                return True
            if key == "e" and activeBone:
                self.newEdit(ExtrudeBone(self.editor, pos, activeBone))
                return True
            if key == "c" and activeBone:
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

    def draw(self):
        if self.active:
            self.active.update(self.editor)
            self.active.draw(self.editor)


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


    def update(self):
        #self.debugAnimate(self.settings["debugAnimate"])
        self.handleEvents()
        self.visualizeBones()

    def saveToFile(self):
        skinned.saveToFile(self.context.renderer.bones, "bones.json")

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
                bone.rotation.z = math.sin(context.time * 0.5)
            else:
                bone.rotation.z = 0.0

    def drawText(self, text, color, pos):
        surface = FONT.render(text, True, color)
        self.context.overlayCanvas.get_surface().blit(surface, pos)

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
        self.context.renderer.updateBones()

    def setBoneZOrder(self, bone, newZ):
        delta = newZ - bone.zOrder
        children = [bone] + bone.getAllChildren(self.getBones())
        for child in children:
            child.zOrder += delta

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
            bone = None
            if self.settings["pivots"]:
                bone = self.pickPivot(pos)
                if bone:
                    self.setActiveBone(bone)
                    self.set(DRAG_PIVOT, (bone, self.getBoneInverseTranslation(bone, pos), bone.pivot))
                else:
                    self.setActiveBone(None)
                    self.set(DRAG_PIVOT, None)

            if self.settings["imageAreas"] and not bone:
                bone = self.pickCrop(pos)
                if bone:
                    self.set(DRAG_POS, (bone, pos, bone.pos))
                else:
                    self.set(DRAG_POS, None)
        elif event.button == 4:
            hover = self.pickPivot(pos)
            if hover:
                self.setBoneZOrder(hover, hover.zOrder + 1)
                self.updateBones()
        elif event.button == 5:
            hover = self.pickPivot(pos)
            if hover:
                self.setBoneZOrder(hover, hover.zOrder - 1)
                self.updateBones()

    def handleMouseMotion(self, pos):
        dragPivot = self.get(DRAG_PIVOT)
        if dragPivot:
            bone, oldMouse, oldHead = dragPivot
            #TODO Save the bone start transform, otherwise precision error accumulate while dragging...
            inverse = self.getBoneInverseTranslation(bone, pos)
            delta = (oldMouse[0] - inverse[0], oldMouse[1] - inverse[1])
            pivot = bone.pivot
            bone.pivot = (oldHead[0] - delta[0], oldHead[1] - delta[1])

        dragPos = self.get(DRAG_POS)
        if dragPos:
            bone, oldMouse, oldPos = dragPos
            delta = (oldMouse[0] - pos[0], oldMouse[1] - pos[1])
            pos = bone.pos
            bone.pos = (oldPos[0] - delta[0], oldPos[1] - delta[1])

    def handleMouseUp(self, pos):
        self.stopDrag()

    def stopDrag(self):
        if self.get(DRAG_PIVOT):
            self.updateBones()

        self.set(DRAG_PIVOT, None)
        self.set(DRAG_POS, None)

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

    def getBoneInverseTranslation(self, bone, translation):
        inverse = self.transformsMap[bone.name].matrix.inverse()
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
        mouse = self.mouse
        activeBone = self.getActiveBone()

        hoverPivotBone = None
        hoverCropBone = None
        if mouse:
            hoverPivotBone = self.pickPivot(mouse)
            hoverCropBone = self.pickCrop(mouse)

        for trans in self.transforms:
            bone = trans.bone
            #bone.wireFrame = ((activeBone and bone.name == activeBone.name) or not activeBone) and self.settings["wireframe"]
            bone.wireFrame = self.settings["wireframe"]

            pos = self.getBonePos(bone)
            pivot = self.getBonePivotTransformed(bone)

            if self.settings["imageAreas"] and bone.image:
                areaColor = (255, 255, 0)
                lines = self.getImageLines(bone)
                if not hoverPivotBone and hoverCropBone and bone.name == hoverCropBone.name:
                    self.drawText(hoverCropBone.name, "#fff", (mouse[0] + 20, mouse[1]))
                    areaColor = ACTIVE_COLOR
                context.overlayCanvas.lines(areaColor, False, lines)

                #triangles = self.getTriangles(bone)
                #for i in range(0, len(triangles), 3):
                #    tri = (triangles[i], triangles[i + 1], triangles[i + 2])
                #    context.overlayCanvas.lines("#0f0", True, tri)

                polyPoints = self.getPolyPoints(bone)
                if polyPoints:
                    context.overlayCanvas.lines("#ff0", True, polyPoints)

                    for i, p in enumerate(polyPoints):
                        color = (0, int(float(i) / len(polyPoints) * 255), 0)
                        context.overlayCanvas.circle(color, p, 3)

            if self.settings["pivots"]:
                if bone.parent:
                    parentTrans = self.transformsMap[bone.parent]
                    parentBone = parentTrans.bone
                    parentPos = self.getBonePivotTransformed(parentBone)
                    context.overlayCanvas.line(PIVOT_COLOR, (pivot.x, pivot.y), (parentPos.x, parentPos.y))

                context.overlayCanvas.circle(PIVOT_COLOR, (pivot.x, pivot.y), PIVOT_SIZE)
                if hoverPivotBone and bone.name == hoverPivotBone.name:
                    context.overlayCanvas.circle(HOVER_COLOR, (pivot.x, pivot.y), PIVOT_SIZE - 1)
                if activeBone and bone.name == activeBone.name:
                    context.overlayCanvas.circle(ACTIVE_COLOR, (pivot.x, pivot.y), PIVOT_SIZE - 2)

                textColor = "#fff"
                if activeBone and bone.name == activeBone.name:
                    textColor = ACTIVE_COLOR

                if self.settings["names"]:
                    self.drawText(bone.name, textColor, (pivot.x + 15, pivot.y - 10))

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
