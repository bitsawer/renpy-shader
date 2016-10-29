
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
            #xmaximum 150
            #xminimum 150
            text "Skinning image: '" + name + "'"

init python:
    import pygame
    import math
    from shader import euclid

    PICK_DISTANCE = 20
    WIREFRAME = 1

    pygame.font.init()
    FONT = pygame.font.Font(None, 20)

    def editUpdate(context):
        renderer = context.renderer
        transforms = renderer.computeBoneTransforms(context)
        mouse = context.store.get("mouse")

        debugTest(context)

        for event, pos in context.events:
            mouse = pos
            if event.type == pygame.MOUSEBUTTONDOWN:
                handleMouseDown(context, transforms, pos)
            if event.type == pygame.MOUSEMOTION:
                handleMouseMotion(context, transforms, pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                handleMouseUp(context, transforms, pos)

        drawBoneHeads(context, transforms, mouse)

        if mouse:
            context.store["mouse"] = mouse

    def debugTest(context):
        connectBone(context, "doll lforearm", "doll base")
        connectBone(context, "doll larm", "doll lforearm")
        connectBone(context, "doll lhand", "doll larm")

        for name in ("doll hair", "doll lforearm", "doll larm", "doll lhand"):
            context.renderer.bones[name].data["rotation"].z = math.sin(context.time * 0.5)

    def handleMouseDown(context, transforms, pos):
        bone = pickBone(context, transforms, pos)
        if bone:
            key = "head"
            context.store["dragged"] = (key, bone, pos, bone.data[key])
        else:
            stopDrag(context)

    def handleMouseMotion(context, transforms, pos):
        dragged = context.store.get("dragged")
        if dragged:
            key, bone, oldPos, oldValue = dragged
            delta = (oldPos[0] - pos[0], oldPos[1] - pos[1])
            head = bone.data[key]
            bone.data[key] = (oldValue[0] - delta[0], oldValue[1] - delta[1])

    def handleMouseUp(context, transforms, pos):
        stopDrag(context)

    def stopDrag(context):
        if "dragged" in context.store:
            del context.store["dragged"]

    def drawText(context, text, pos):
        surface = FONT.render(text, True, "#fff")
        context.overlayCanvas.get_surface().blit(surface, pos)

    def getBonePos(bone):
        head = bone.data["head"]
        crop = bone.data["crop"]
        return euclid.Vector3(head[0] - crop[0],  head[1] - crop[1], 0)

    def pickBone(context, transforms, pos):
        closest = None
        closestDistance = None
        for bone, transBase, trans in transforms:
            p = trans.transform(getBonePos(bone))
            distance = (p - euclid.Vector3(pos[0], pos[1])).magnitude()
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
        oldParent = bones[poseBone.data["parent"]]

        if boneName not in newParent.data["children"]:
            oldParent.data["children"].remove(boneName)
            newParent.data["children"].append(boneName)
            poseBone.data["parent"] = newParent.data["name"]

    def drawBoneHeads(context, transforms, mouse):
        for bone, transBase, trans in transforms:
            bone.wireFrame = WIREFRAME

            p = trans.transform(getBonePos(bone))
            context.overlayCanvas.circle((255, 0, 0), (p.x, p.y), 8)
            if mouse and (p - euclid.Vector3(mouse[0], mouse[1])).magnitude() < PICK_DISTANCE:
                context.overlayCanvas.circle((255, 255, 0), (p.x, p.y), 4)
            drawText(context, bone.data["name"], (p.x + 15, p.y - 10))


label start_skinned:
    #scene room
    #show doll

    call screen skinnedScreen("doll", shader.PS_SKINNED, {"tex1": "amy influence"}, update=editUpdate, _tag="amy", _layer="amy") #nopredict

    "The End"
