
import math
import pygame
import euclid

pygame.font.init()
FONT = pygame.font.Font(None, 20)

PICK_DISTANCE_PIVOT = 20
PICK_DISTANCE_CROP = 5
activeBone = None

DRAG_PIVOT = "dragPivot"
DRAG_CROP = "dragCrop"
MOUSE = "mouse"

def lineToPoint(a, b, point):
    x1, y1 = a
    x2, y2 = b
    x3, y3 = point

    px = x2 - x1
    py = y2 - y1
    value = px*px + py*py

    u =  ((x3 - x1) * px + (y3 - y1) * py) / float(value)
    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py
    dx = x - x3
    dy = y - y3
    return math.sqrt(dx*dx + dy*dy)


class SkinnedEditor:
    def __init__(self, context, settings):
        self.context = context
        self.settings = settings
        self.mouse = (0, 0)
        self.transforms = context.renderer.computeBoneTransforms(context)

    def update(self):
        self.debugAnimate(self.settings["debugAnimate"])
        self.handleEvents()
        self.visualizeBones()

    def get(self, key):
        return self.context.store.get(key)

    def set(self, key, value):
        self.context.store[key] = value

    def debugAnimate(self, animate):
        context = self.context
        #TODO Rotate all bones that have a parent other than root
        BASE = "doll base"
        self.connectBone("doll lforearm", BASE)
        self.connectBone("doll larm", "doll lforearm")
        self.connectBone("doll lhand", "doll larm")
        self.connectBone("doll hair", BASE)
        self.connectBone("doll skirt", BASE)

        for name in ("doll hair", "doll lforearm", "doll larm", "doll lhand"):
            bone = context.renderer.bones[name]
            if animate:
                bone.rotation.z = math.sin(context.time * 0.5)
            else:
                bone.rotation.z = 0.0

    def drawText(self, text, color, pos):
        surface = FONT.render(text, True, color)
        self.context.overlayCanvas.get_surface().blit(surface, pos)

    def connectBone(self, boneName, parentName):
        bones = self.context.renderer.bones
        poseBone = bones[boneName]
        newParent = bones[parentName]
        oldParent = bones[poseBone.parent]

        if boneName not in newParent.children:
            oldParent.children.remove(boneName)
            newParent.children.append(boneName)
            poseBone.parent = newParent.name

    def handleEvents(self):
        self.mouse = self.get(MOUSE)

        for event, pos in self.context.events:
            self.mouse = pos
            #keyboard: h toggle hide, r rotate etc.
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.handleMouseDown(pos)
            elif event.type == pygame.MOUSEMOTION:
                self.handleMouseMotion(pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.handleMouseUp(pos)

        if self.mouse:
            self.set(MOUSE, self.mouse)

    def handleMouseDown(self, pos):
        global activeBone

        self.stopDrag()

        bone = self.pickPivot(pos)
        if bone:
            activeBone = bone
            self.set(DRAG_PIVOT, (bone, pos, bone.pivot))
        else:
            activeBone = None
            self.set(DRAG_PIVOT, None)

            bone = self.pickCrop(pos)
            if bone:
                self.set(DRAG_CROP, (bone, pos, bone.crop))
            else:
                self.set(DRAG_CROP, None)

    def handleMouseMotion(self, pos):
        dragPivot = self.get(DRAG_PIVOT)
        if dragPivot:
            bone, oldPos, oldHead = dragPivot
            delta = (oldPos[0] - pos[0], oldPos[1] - pos[1])
            pivot = bone.pivot
            bone.pivot = (oldHead[0] - delta[0], oldHead[1] - delta[1])

        dragCrop = self.get(DRAG_CROP)
        if dragCrop:
            bone, oldPos, oldCrop = dragCrop
            delta = (oldPos[0] - pos[0], oldPos[1] - pos[1])
            crop = bone.crop
            bone.crop = (oldCrop[0] - delta[0], oldCrop[1] - delta[1], oldCrop[2] - delta[0], oldCrop[3] - delta[1])

    def handleMouseUp(self, pos):
        self.stopDrag()

    def stopDrag(self):
        self.set(DRAG_PIVOT, None)
        self.set(DRAG_CROP, None)

    def pickPivot(self, pos):
        closest = None
        closestDistance = None
        for trans in self.transforms:
            bone = trans.bone
            pivot = trans.matrix.transform(self.getBonePivot(bone))
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
            lines = self.getCropLines(trans.bone)
            for i in range(len(lines) - 1):
                distance = lineToPoint(lines[i], lines[i + 1], pos)
                if distance < PICK_DISTANCE_CROP:
                    if not closest or distance < closestDistance:
                        closest = trans.bone
                        closestDistance = distance
        return closest

    def getCropLines(self, bone):
        crop = bone.crop
        lines = [
            (crop[0], crop[1]),
            (crop[0] + (crop[2] - crop[0]), crop[1]),
            (crop[0] + (crop[2] - crop[0]), crop[1] + (crop[3] - crop[1])),
            (crop[0], crop[1] + (crop[3] - crop[1])),
            (crop[0], crop[1])
        ]
        return lines

    def getBonePivot(self, bone):
        pivot = bone.pivot
        return euclid.Vector3(pivot[0],  pivot[1], 0)

    def getBonePos(self, bone):
        crop = bone.crop
        return euclid.Vector3(crop[0],  crop[1], 0)

    def getTransformsDict(self):
        mapping = {}
        for trans in self.transforms:
            mapping[trans.bone.name] = trans
        return mapping

    def visualizeBones(self):
        mapping = self.getTransformsDict()
        context = self.context
        mouse = self.mouse

        hoverPivotBone = None
        hoverCropBone = None
        if mouse:
            hoverPivotBone = self.pickPivot(mouse)
            hoverCropBone = self.pickCrop(mouse)

        for trans in self.transforms:
            bone = trans.bone
            bone.wireFrame = ((activeBone and bone.name == activeBone.name) or not activeBone) and self.settings["wireframe"]

            crop = bone.crop
            pos = self.getBonePos(bone)
            pivot = trans.matrix.transform(self.getBonePivot(bone))
            activeColor = (0, 255, 0)

            if self.settings["imageAreas"]:
                areaColor = (255, 255, 0)
                lines = self.getCropLines(bone)
                if not hoverPivotBone and hoverCropBone and bone.name == hoverCropBone.name:
                    self.drawText(hoverCropBone.name, "#fff", (mouse[0] + 20, mouse[1]))
                    areaColor = activeColor
                context.overlayCanvas.lines(areaColor, False, lines)

            if self.settings["pivots"]:
                if bone.parent:
                    parentTrans = mapping[bone.parent]
                    parentBone = parentTrans.bone
                    parentPos = parentTrans.matrix.transform(self.getBonePivot(parentBone))
                    context.overlayCanvas.line("#00f", (pivot.x, pivot.y), (parentPos.x, parentPos.y))

                context.overlayCanvas.circle((255, 0, 0), (pivot.x, pivot.y), 8)
                if hoverPivotBone and bone.name == hoverPivotBone.name:
                    context.overlayCanvas.circle(activeColor, (pivot.x, pivot.y), 4)

                textColor = "#fff"
                if activeBone and bone.name == activeBone.name:
                    textColor = activeColor

                self.drawText(bone.name, textColor, (pivot.x + 15, pivot.y - 10))
