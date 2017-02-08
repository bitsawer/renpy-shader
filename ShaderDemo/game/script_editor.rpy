
image doll = LiveComposite(
    (800, 1000),
    (0, 0), "doll base.png",
    (249, 318), "doll skirt.png",
    #(0, 0), "doll lforearm.png",
    #(0, 0), "doll larm.png",
    #(0, 0), "doll lhand.png",
    (0, 0), "doll hair.png",
)

screen listScreen(title, items, current=None, cancel=None):
    modal True
    frame:
        xalign 0.5
        yalign 0.5
        xpadding 10
        ypadding 10

        vbox:
            spacing 5
            text title xalign 0.5

            vpgrid id "vp":
                cols 1
                spacing 10
                mousewheel True
                scrollbars "vertical"
                xminimum 400
                ymaximum config.screen_height - 300

                for name in items:
                    if current and name == current:
                        textbutton name action Return(name) text_color "#080"
                    else:
                        textbutton name action Return(name)

            textbutton (cancel if cancel else "Cancel") xalign 0.5 action Return("")

screen skinnedScreen(name, pixelShader, textures={}, uniforms={}, update=None, args=None, xalign=0.5, yalign=0.5):
    modal True
    add ShaderDisplayable(shader.MODE_SKINNED, name, shader.VS_SKINNED, pixelShader, textures, uniforms, None, update, args):
        xalign xalign
        yalign yalign

    if 0: #For debugging and comparison
        add name:
            xalign xalign
            yalign yalign
            alpha 0.5

    drag:
        drag_handle (0, 0, 1.0, 1.0)

        frame:
            xmargin 5
            ymargin 5
            xpadding 10
            ypadding 10

            vbox:
                spacing 5
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

                textbutton "Pause wind" action ToggleVariable("pauseTimeFlag", True, False)
                textbutton "Disable dragging" action ToggleDict(editorSettings, "disableDrag")
                textbutton "Debug animate" action ToggleDict(editorSettings, "debugAnimate")
                textbutton "Autotessellate" action ToggleDict(editorSettings, "autoSubdivide")

                text "Operations":
                    size 15

                textbutton "Rename bone" action [SetVariable("renameBoneFlag", True), Jump("update_editor")]
                textbutton "Subdivide mesh" action [SetVariable("subdivideMesh", True), Jump("update_editor")]
                textbutton "Reset pose" action [SetVariable("resetPoseFlag", True), Jump("update_editor")]

                text "File":
                    size 15

                textbutton "Reload" action Confirm("Are you sure you want to reload?", Jump("reset_editor"))
                #textbutton "Save" action Confirm("Are you sure you want to save?", Function(editSave))
                textbutton "Load rig" action Confirm("Are you sure you want to load another rig?", Jump("start_editor"))
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
                spacing 5

                text animation.name

                text "Operations":
                    size 15

                textbutton "Easing" action SetVariable("showEasingsFlag", True)

                text "File":
                    size 15

                textbutton "New animation" action Confirm("Create a new animation?", SetVariable("newAnimationFlag", True))
                textbutton "Load animation" action SetVariable("loadAnimationFlag", True)
                textbutton "Save animation" action SetVariable("saveAnimationFlag", True)

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

            bar value VariableValue("frameNumber", maxFrames - 1)


init python:
    import shader
    from shader import skinnededitor
    from shader import skinnedanimation
    from shader import easing

    editorSettings = {
        "wireframe": True,
        "edgePoints": True,
        "imageAreas": False,
        "pivots": True,
        "names": False,
        "debugAnimate": False,
        "autoSubdivide": True,
        "disableDrag": False,
    }

    drawableName = ""
    rigFile = "bones.rig"
    animFile = ""

    saveRig = False
    subdivideMesh = False
    renameBoneFlag = False
    resetPoseFlag = False
    showEasingsFlag = False
    newAnimationFlag = False
    loadAnimationFlag = False
    saveAnimationFlag = False
    pauseTimeFlag = False

    frameNumber = 0
    frameNumberLast = -1
    framePlay = False
    maxFrames = 1

    def clearKeymapForEditor():
        #Remove mappings that would conflict with our editor
        shortcuts = ["mouseup_3", "h", "s"]
        for key, values in config.keymap.items():
            for name in shortcuts:
                if name in values:
                    values.remove(name)
        renpy.clear_keymap_cache()

    def userInput(prompt, *args, **kwargs):
        #TODO Exclude invalid characters...
        return renpy.invoke_in_new_context(renpy.input, prompt, *args, **kwargs)

    def notify(text):
        renpy.notify(text)

    def _askListInputContext(*args):
        return renpy.call_screen("listScreen", *args)

    def askListInput(title, items, current=None, cancel=None):
        return renpy.invoke_in_new_context(_askListInputContext, title, items, current, cancel)

    def restartEditor():
        renpy.jump("reset_editor")

    def updateEditor():
        renpy.jump("update_editor")

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

    def setActiveEasing(editor, animation):
        active = editor.getActiveBone()
        if active:
            result = askListInput("Bone easing", easing.getNames(), animation.getBoneData(active.name).easing)
            if result:
                animation.getBoneData(active.name).easing = result
        else:
            notify("No bone selected")

    def newAnimation():
        global animFile
        animFile = ""
        notify("New animation")
        updateEditor()

    def loadAnimation():
        global animFile
        result = askListInput("Animation", shader.utils.scanForFiles(".", "anim"))
        if result:
            animFile = result
            notify("Loaded: '%s'" % animFile)
            updateEditor()

    def saveAnimation(animation):
        global animFile
        fileName = userInput("Save animation as...", animation.name)
        if fileName:
            if not fileName.strip().lower().endswith(".anim"):
                fileName = fileName + ".anim"
            animation.name = fileName
            skinnedanimation.saveAnimationToFile(fileName, animation)
            animFile = fileName
            notify("Animation saved to '%s'" % animFile)
            updateEditor()

    def editUpdate(context):
        global saveRig, subdivideMesh, renameBoneFlag, resetPoseFlag, showEasingsFlag, \
            newAnimationFlag, loadAnimationFlag, saveAnimationFlag, frameNumberLast

        context.createOverlayCanvas()

        editor = skinnededitor.SkinnedEditor(context, editorSettings)
        editor.update()

        animation.setFrameCount(maxFrames + 1)
        animation.update(frameNumber, editor)
        if frameNumberLast != frameNumber or animation.dirty:
            frameNumberLast = frameNumber
            animation.apply(frameNumber, editor.getBones())

        if editorSettings["debugAnimate"]:
            editor.debugAnimate(True)

        if editorSettings["pivots"]:
            animation.drawDebugText(editor, frameNumber)
            animation.drawDebugKeyFrames(editor, frameNumber)

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

        if newAnimationFlag:
            newAnimationFlag = False
            newAnimation()

        if loadAnimationFlag:
            loadAnimationFlag = False
            loadAnimation()

        if saveAnimationFlag:
            saveAnimationFlag = False
            saveAnimation(animation)

        if saveRig:
            saveRig = False
            saveRigFile(editor)

        if pauseTimeFlag:
            context.uniforms["shownTime"] = 1.0
            context.uniforms["animationTime"] = 1.0

label main_menu: #TODO For fast testing
label start_editor:
    $ clearKeymapForEditor()

    call screen listScreen("Select Image or LiveComposite", sorted(renpy.get_available_image_tags()))
    $ drawableName = _return

    if not drawableName:
        return

    call screen listScreen("Load a rig", shader.utils.scanForFiles(".", "rig"), None, "Create a new rig")
    $ rigFile = _return
    $ animFile = ""

label reset_editor:
    $ shader._controllerContextStore._clear()

label update_editor:
    python:
        if animFile:
            animation = skinnedanimation.loadAnimationFromFile(animFile)
            maxFrames = len(animation.frames)
        else:
            animation = skinnedanimation.SkinnedAnimation("untitled.anim")
            maxFrames = 60 * 2
        frameNumber = min(frameNumber, maxFrames)

    call screen skinnedScreen(drawableName, shader.PS_SKINNED, {},
        update=editUpdate, args={"rigFile": rigFile, "persist": True}, _layer="master") #nopredict

    $ shader._controllerContextStore._clear()
    return
