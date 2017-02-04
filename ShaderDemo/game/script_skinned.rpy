
image doll = LiveComposite(
    (800, 1000),
    (0, 0), "doll base.png",
    (249, 318), "doll skirt.png",
    #(0, 0), "doll lforearm.png",
    #(0, 0), "doll larm.png",
    #(0, 0), "doll lhand.png",
    #(0, 0), "doll hair.png",
)

screen easingScreen(oldEasing):
    frame:
        xalign 0.5
        yalign 0.5
        vbox:
            spacing 5
            text "Set animation easing" xalign 0.5 yalign 0.3
            for name in easing.EASINGS:
                if name == oldEasing:
                    $ name = ">> " + name + " <<"
                textbutton name xalign 0.5 action Return(name)

screen skinnedScreen(name, pixelShader, textures={}, uniforms={}, update=None, args=None, xalign=0.5, yalign=0.5):
    modal True
    add ShaderDisplayable(shader.MODE_SKINNED, name, shader.VS_SKINNED, pixelShader, textures, uniforms, None, update, args):
        xalign xalign
        yalign yalign
        #rotate 45

    drag:
        drag_handle (0, 0, 1.0, 1.0)

        frame:
            xmargin 5
            ymargin 5
            xpadding 10
            ypadding 10

            vbox:
                spacing 10
                #xmaximum 150
                #xminimum 150
                text "Rig: " + name

                text "Visual":
                    size 15

                textbutton "Wireframes" action ToggleDict(editorSettings, "wireframe")
                textbutton "Edge points" action ToggleDict(editorSettings, "edgePoints")
                textbutton "Image areas" action ToggleDict(editorSettings, "imageAreas")
                textbutton "Bones" action ToggleDict(editorSettings, "pivots")
                textbutton "Bone names" action ToggleDict(editorSettings, "names")

                text "Modes":
                    size 15

                textbutton "Debug animate" action ToggleDict(editorSettings, "debugAnimate")
                textbutton "Autosubdivision" action ToggleDict(editorSettings, "autoSubdivide")

                text "Operations":
                    size 15

                textbutton "Rename bone" action [SetVariable("renameBoneFlag", True), RestartStatement()]
                textbutton "Subdivide mesh" action [SetVariable("subdivideMesh", True), RestartStatement()]
                textbutton "Reset pose" action [SetVariable("resetPoseFlag", True), RestartStatement()]

                text "File":
                    size 15

                #textbutton "Load rig" action SetVariable("loadRig", True)
                textbutton "Reload" action Confirm("Are you sure you want to reload?", Jump("start_skinned"))
                #textbutton "Save" action Confirm("Are you sure you want to save?", Function(editSave))
                textbutton "Save rig" action SetVariable("saveRig", True)


    drag:
        drag_handle (0, 0, 1.0, 1.0)
        xalign 1.0

        frame:
            xmargin 5
            ymargin 5
            xpadding 10
            ypadding 10
            vbox:
                spacing 10

                text "Animation: " + animation.name

                text "Operations":
                    size 15

                textbutton "Easing" action SetVariable("showEasingsFlag", True)

    frame:
        yalign 1.0
        hbox:
            spacing 10
            $ playText = "||" if framePlay else ">>"
            textbutton "Frame: %i" % frameNumber yalign 0.5 xsize 150 action Function(changeFrameCount)
            textbutton "<" yalign 0.5 keysym "j" action SetVariable("frameNumber", max(frameNumber - 1, 0))
            textbutton playText yalign 0.5 xsize 50 keysym "k" action SetVariable("framePlay", not framePlay)
            textbutton ">" yalign 0.5 keysym "l" action SetVariable("frameNumber", min(frameNumber + 1, maxFrames))

            timer 1.0 / shader.config.fps repeat True action If(framePlay, SetVariable("frameNumber", (frameNumber + 1) % (maxFrames + 1)), NullAction())

            bar value VariableValue("frameNumber", maxFrames)


init python:
    import shader
    from shader import skinnededitor
    from shader import skinnedanimation
    from shader import easing

    #config.keymap["input_delete"] = []
    config.keymap["game_menu"].remove("mouseup_3")
    config.keymap["hide_windows"].remove("h")
    config.keymap["screenshot"].remove("s")

    editorSettings = {
        "wireframe": True,
        "edgePoints": True,
        "imageAreas": False,
        "pivots": True,
        "names": False,
        "debugAnimate": False,
        "autoSubdivide": True,
    }

    saveRig = False
    rigFile = "bones.rig"

    subdivideMesh = False

    renameBoneFlag = False
    resetPoseFlag = False
    showEasingsFlag = False

    frameNumber = 0
    frameNumberLast = -1
    framePlay = False
    maxFrames = 60 * 2

    def userInput(prompt, *args, **kwargs):
        #TODO Exclude invalid characters...
        return renpy.invoke_in_new_context(renpy.input, prompt, *args, **kwargs)

    def notify(text):
        renpy.notify(text)

    def changeFrameCount():
        global maxFrames, frameNumber
        try:
            count = eval(userInput("Set animation frame count", str(maxFrames), allow=list("1234567890*/+-")))
            if count > 0 and count < 10000:
                maxFrames = count
                frameNumber = min(frameNumber, maxFrames)
        except:
            pass

    def saveRigFile(editor):
        global rigFile
        fileName = userInput("Save rig as...", rigFile)
        if fileName:
            if not fileName.strip().lower().endswith(".rig"):
                fileName = fileName + ".rig"
            editor.saveSkeletonToFile(fileName)
            notify("Rig saved to '%s'" % fileName)
            rigFile = fileName

    def subdivideActiveMesh(editor):
        if editorSettings["autoSubdivide"]:
            notify("Disable auto subdivision first")
            return

        active = editor.getActiveBone()
        if active and active.mesh:
            if editor.subdivide(active, 500):
                notify("Subdivision done")
            else:
                notify("Subdivision not possible")
        else:
            notify("No mesh bone selected")

    def renameActiveBone(editor, animation):
        active = editor.getActiveBone()
        if active:
            oldName = active.name
            newName = userInput("Rename bone to...", oldName)
            if editor.renameBone(active, newName):
                animation.renameBone(oldName, newName)
                editor.setActiveBone(active)
                notify("Bone renamed")
            else:
                notify("Renaming failed")
        else:
            notify("No bone selected")

    def askEasing(oldEasing):
        return renpy.call_screen("easingScreen", oldEasing)

    def setActiveEasing(editor, animation):
        active = editor.getActiveBone()
        if active:
            result = renpy.invoke_in_new_context(askEasing, animation.getBoneData(active.name).easing)
            animation.getBoneData(active.name).easing = result
        else:
            notify("No bone selected")

    def editUpdate(context):
        global saveRig, subdivideMesh, renameBoneFlag, resetPoseFlag, showEasingsFlag, frameNumberLast

        editor = skinnededitor.SkinnedEditor(context, editorSettings)
        editor.update()

        animation.setFrameCount(maxFrames + 1)
        animation.update(frameNumber, editor)
        if frameNumberLast != frameNumber or animation.dirty:
            frameNumberLast = frameNumber
            animation.apply(frameNumber, editor.getBones())

        if editorSettings["pivots"]:
            animation.drawDebugText(editor, frameNumber)
            animation.drawDebugKeyFrames(editor, frameNumber)
            animation.debugBake(editor)

        if subdivideMesh:
            subdivideMesh = False
            subdivideActiveMesh(editor)

        if renameBoneFlag:
            renameBoneFlag = False
            renameActiveBone(editor, animation)

        if resetPoseFlag:
            resetPoseFlag = False
            editor.resetPose()
            notify("Pose reset")

        if showEasingsFlag:
            showEasingsFlag = False
            setActiveEasing(editor, animation)

        if saveRig:
            saveRig = False
            saveRigFile(editor)


label start_skinned:
label main_menu: #TODO For fast testing
    $ _controllerContextStore._clear()

    $ animation = skinnedanimation.SkinnedAnimation("untitled")

    call screen skinnedScreen("doll", shader.PS_SKINNED, {"tex1": "amy influence"},
        update=editUpdate, args={"rigFile": rigFile}, _tag="amy", _layer="amy") #nopredict

    "The End"
