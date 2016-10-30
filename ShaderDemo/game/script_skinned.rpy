
image doll = LiveComposite(
    (800, 1000),
    (0, 0), "doll base.png",
    (249, 318), "doll skirt.png",
    (0, 0), "doll lforearm.png",
    (0, 0), "doll larm.png",
    (0, 0), "doll lhand.png",
    (0, 0), "doll hair.png",
)

screen skinnedScreen(name, pixelShader, textures={}, uniforms={}, update=None, xalign=0.5, yalign=1.0):
    modal True
    add ShaderDisplayable(shader.MODE_SKINNED, name, shader.VS_SKINNED, pixelShader, textures, uniforms, None, update):
        xalign xalign
        yalign yalign
        #rotate 45

    frame:
        xpadding 10
        ypadding 10


        vbox:
            spacing 10
            #xmaximum 150
            #xminimum 150
            text name

            text "Toggles":
                size 15

            textbutton "Wireframes" action ToggleDict(editorSettings, "wireframe")
            textbutton "Image areas" action ToggleDict(editorSettings, "imageAreas")
            textbutton "Pivot points" action ToggleDict(editorSettings, "pivots")
            textbutton "Debug animate" action ToggleDict(editorSettings, "debugAnimate")

            text "Actions":
                size 15

            textbutton "Autoconnect" action NullAction() #TODO Set a flag and check in update
            textbutton "Reload" action Confirm("Are you sure you want to reload?", Jump("start_skinned"))


init python:
    import pygame
    import math
    from shader import euclid

    editorSettings = {
        "wireframe": False,
        "imageAreas": True,
        "pivots": True,
        "debugAnimate": True,
    }

    PICK_DISTANCE = 20

    pygame.font.init()
    FONT = pygame.font.Font(None, 20)

    activeBone = None #TODO should be a list to allow multiple

    #TODO Move this to a class SkinnedEditor

    def editUpdate(context):
        renderer = context.renderer
        transforms = renderer.computeBoneTransforms(context)
        mouse = context.store.get("mouse")

        debugAnimate(context, editorSettings.get("debugAnimate"))

        for event, pos in context.events:
            mouse = pos
            #keyboard: h toggle hide, r rotate etc.
            if event.type == pygame.MOUSEBUTTONDOWN:
                handleMouseDown(context, transforms, pos)
            if event.type == pygame.MOUSEMOTION:
                handleMouseMotion(context, transforms, pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                handleMouseUp(context, transforms, pos)

        visualizeBones(context, transforms, mouse)

        if mouse:
            context.store["mouse"] = mouse

    def debugAnimate(context, animate):
        #TODO Rotate all bones that have a parent other than root
        BASE = "doll base"
        connectBone(context, "doll lforearm", BASE)
        connectBone(context, "doll larm", "doll lforearm")
        connectBone(context, "doll lhand", "doll larm")
        connectBone(context, "doll hair", BASE)
        connectBone(context, "doll skirt", BASE)

        for name in ("doll hair", "doll lforearm", "doll larm", "doll lhand"):
            bone = context.renderer.bones[name]
            if animate:
                bone.rotation.z = math.sin(context.time * 0.5)
            else:
                bone.rotation.z = 0.0

    def handleMouseDown(context, transforms, pos):
        global activeBone
        bone = pickBone(context, transforms, pos)
        if bone:
            activeBone = bone
            context.store["dragged"] = (bone, pos, bone.pivot)
        else:
            activeBone = None
            stopDrag(context)

    def handleMouseMotion(context, transforms, pos):
        dragged = context.store.get("dragged")
        if dragged:
            bone, oldPos, oldHead = dragged
            delta = (oldPos[0] - pos[0], oldPos[1] - pos[1])
            pivot = bone.pivot
            bone.pivot = (oldHead[0] - delta[0], oldHead[1] - delta[1])

    def handleMouseUp(context, transforms, pos):
        stopDrag(context)

    def stopDrag(context):
        if "dragged" in context.store:
            del context.store["dragged"]

    def drawText(context, text, color, pos):
        surface = FONT.render(text, True, color)
        context.overlayCanvas.get_surface().blit(surface, pos)

    def getBonePivot(bone):
        pivot = bone.pivot
        return euclid.Vector3(pivot[0],  pivot[1], 0)

    def getBonePos(bone):
        crop = bone.crop
        return euclid.Vector3(crop[0],  crop[1], 0)

    def pickBone(context, transforms, pos):
        #if not editorSettings.get("pivots"):
        #    return

        closest = None
        closestDistance = None
        closestType = None
        for trans in transforms:
            bone = trans.bone
            pivot = trans.matrix.transform(getBonePivot(bone))
            distance = (pivot - euclid.Vector3(pos[0], pos[1])).magnitude()
            if distance < PICK_DISTANCE:
                if not closest:
                    closest = bone
                    closestDistance = distance
                elif distance < closestDistance:
                    closest = bone
                    closestDistance = distance
        return closest

    def connectBone(context, boneName, parentName):
        bones = context.renderer.bones
        poseBone = bones[boneName]
        newParent = bones[parentName]
        oldParent = bones[poseBone.parent]

        if boneName not in newParent.children:
            oldParent.children.remove(boneName)
            newParent.children.append(boneName)
            poseBone.parent = newParent.name

    def getTransformsDict(transforms):
        mapping = {}
        for trans in transforms:
            mapping[trans.bone.name] = trans
        return mapping

    def visualizeBones(context, transforms, mouse):
        mapping = getTransformsDict(transforms)

        for trans in transforms:
            bone = trans.bone
            bone.wireFrame = ((activeBone and bone.name == activeBone.name) or not activeBone) and editorSettings["wireframe"]

            crop = bone.crop
            pos = getBonePos(bone)
            pivot = trans.matrix.transform(getBonePivot(bone))
            activeColor = (0, 255, 0)

            if editorSettings.get("imageAreas"):
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

            if editorSettings.get("pivots"):
                if bone.parent:
                    parentTrans = mapping[bone.parent]
                    parentBone = parentTrans.bone
                    parentPos = parentTrans.matrix.transform(getBonePivot(parentBone))
                    context.overlayCanvas.line("#00f", (pivot.x, pivot.y), (parentPos.x, parentPos.y))

                context.overlayCanvas.circle((255, 0, 0), (pivot.x, pivot.y), 8)
                if mouse and (pivot - euclid.Vector3(mouse[0], mouse[1])).magnitude() < PICK_DISTANCE:
                    context.overlayCanvas.circle(activeColor, (pivot.x, pivot.y), 4)

                textColor = "#fff"
                if activeBone and bone.name == activeBone.name:
                    textColor = activeColor

                drawText(context, bone.name, textColor, (pivot.x + 15, pivot.y - 10))


label start_skinned:
    #scene room
    #show doll

    $ _controllerContextStore._clear()

    call screen skinnedScreen("doll", shader.PS_SKINNED, {"tex1": "amy influence"}, update=editUpdate, _tag="amy", _layer="amy") #nopredict

    "The End"
