
import math
import pygame
import euclid

pygame.font.init()
FONT = pygame.font.Font(None, 20)

PICK_DISTANCE = 20
activeBone = None

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
        context = self.context
        self.mouse = context.store.get("mouse")

        for event, pos in context.events:
            self.mouse = pos
            #keyboard: h toggle hide, r rotate etc.
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.handleMouseDown(pos)
            elif event.type == pygame.MOUSEMOTION:
                self.handleMouseMotion(pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.handleMouseUp(pos)

        if self.mouse:
            context.store["mouse"] = self.mouse

    def handleMouseDown(self, pos):
        global activeBone
        bone = self.pickBone(pos)
        if bone:
            activeBone = bone
            self.context.store["dragged"] = (bone, pos, bone.pivot)
        else:
            activeBone = None
            self.stopDrag()

    def handleMouseMotion(self, pos):
        dragged = self.context.store.get("dragged")
        if dragged:
            bone, oldPos, oldHead = dragged
            delta = (oldPos[0] - pos[0], oldPos[1] - pos[1])
            pivot = bone.pivot
            bone.pivot = (oldHead[0] - delta[0], oldHead[1] - delta[1])

    def handleMouseUp(self, pos):
        self.stopDrag()

    def stopDrag(self):
        if "dragged" in self.context.store:
            del self.context.store["dragged"]

    def pickBone(self, pos):
        #if not editorSettings.get("pivots"):
        #    return

        closest = None
        closestDistance = None
        closestType = None
        for trans in self.transforms:
            bone = trans.bone
            pivot = trans.matrix.transform(self.getBonePivot(bone))
            distance = (pivot - euclid.Vector3(pos[0], pos[1])).magnitude()
            if distance < PICK_DISTANCE:
                if not closest:
                    closest = bone
                    closestDistance = distance
                elif distance < closestDistance:
                    closest = bone
                    closestDistance = distance
        return closest

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

        for trans in self.transforms:
            bone = trans.bone
            bone.wireFrame = ((activeBone and bone.name == activeBone.name) or not activeBone) and self.settings["wireframe"]

            crop = bone.crop
            pos = self.getBonePos(bone)
            pivot = trans.matrix.transform(self.getBonePivot(bone))
            activeColor = (0, 255, 0)

            if self.settings.get("imageAreas"):
                areaColor = (255, 255, 0)
                lines = [
                    (crop[0], crop[1]),
                    (crop[0] + (crop[2] - crop[0]), crop[1]),
                    (crop[0] + (crop[2] - crop[0]), crop[1] + (crop[3] - crop[1])),
                    (crop[0], crop[1] + (crop[3] - crop[1]))
                ]
                context.overlayCanvas.lines(areaColor, True, lines)

                context.overlayCanvas.circle(areaColor, (pos.x, pos.y), 8)
                if mouse and (pos - euclid.Vector3(mouse[0], mouse[1])).magnitude() < PICK_DISTANCE:
                    context.overlayCanvas.circle(activeColor, (pos.x, pos.y), 4)

            if self.settings.get("pivots"):
                if bone.parent:
                    parentTrans = mapping[bone.parent]
                    parentBone = parentTrans.bone
                    parentPos = parentTrans.matrix.transform(self.getBonePivot(parentBone))
                    context.overlayCanvas.line("#00f", (pivot.x, pivot.y), (parentPos.x, parentPos.y))

                context.overlayCanvas.circle((255, 0, 0), (pivot.x, pivot.y), 8)
                if mouse and (pivot - euclid.Vector3(mouse[0], mouse[1])).magnitude() < PICK_DISTANCE:
                    context.overlayCanvas.circle(activeColor, (pivot.x, pivot.y), 4)

                textColor = "#fff"
                if activeBone and bone.name == activeBone.name:
                    textColor = activeColor

                self.drawText(bone.name, textColor, (pivot.x + 15, pivot.y - 10))
