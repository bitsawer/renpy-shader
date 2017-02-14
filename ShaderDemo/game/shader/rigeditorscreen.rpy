
#Rig editor. As a normal user you don't have to understand anything in this file,
#but this can prove useful if you want to learn how the internals work.

style edit_button is default
style edit_button_text is button_text

style edit_button:
    properties gui.button_properties("quick_button")

style edit_button_text:
    properties gui.button_text_properties("quick_button")
    size 20

image editorBackground = LiveTile("editorbackground.png")

screen editorListScreen(title, items, current=None, cancel=None):
    modal True
    frame:
        $ listWidth = 500
        xalign 0.5
        yalign 0.5
        xpadding 10
        ypadding 10

        vbox:
            spacing 5
            text title xalign 0.5

            vpgrid id "vp":
                style_prefix "edit"
                cols 1
                spacing 10
                mousewheel True
                scrollbars "vertical"
                xminimum listWidth
                ymaximum config.screen_height - 200

                for name in items:
                    if current and name == current:
                        textbutton name action Return(name) xsize listWidth text_color "#080"
                    else:
                        textbutton name action Return(name) xsize listWidth

            textbutton (cancel if cancel else "Cancel") xalign 0.5 action Return("")

screen editorMainScreen(name, pixelShader, textures={}, uniforms={}, update=None, args=None, xalign=0.5, yalign=0.5):
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
                style_prefix "edit"
                spacing 5
                #xmaximum 150
                #xminimum 150
                text editorRigFile:
                    size 15
                    color "ff0"

                text "{a=https://github.com/bitsawer/renpy-shader/doc/rigeditor.md}(Help){/a}":
                    size 15

                text "UI":
                    size 15

                textbutton "Wireframes" action ToggleDict(editorSettings, "wireframe")
                textbutton "Edge points" action ToggleDict(editorSettings, "edgePoints")
                textbutton "Image areas" action ToggleDict(editorSettings, "imageAreas")
                textbutton "Bones" action ToggleDict(editorSettings, "pivots")
                textbutton "Bone names" action ToggleDict(editorSettings, "names")

                text "Modes":
                    size 15

                textbutton "Pause wind" action ToggleVariable("editorPauseTimeFlag", True, False)
                textbutton "Disable dragging" action ToggleDict(editorSettings, "disableDrag")
                textbutton "Debug animate" action ToggleDict(editorSettings, "debugAnimate")

                text "Operations":
                    size 15

                textbutton "Rename bone" action [SetVariable("editorRenameBoneFlag", True), Jump("update_editor_ui")]
                #textbutton "Mesh tesselation" action [SetVariable("editorTesselationFlag", True), Jump("update_editor")] TODO Use levels?
                textbutton "Reset pose" action [SetVariable("editorResetPoseFlag", True), Jump("update_editor_ui")]

                text "File":
                    size 15

                textbutton "Reload" action Confirm("Are you sure you want to reload?", Jump("reset_editor"))
                #textbutton "Save" action Confirm("Are you sure you want to save?", Function(editSave))
                textbutton "Load rig" action Confirm("Are you sure you want to load another rig?", Jump("start_editor"))
                textbutton "Save rig" action SetVariable("editorSaveRigFlag", True)


    drag:
        drag_handle (0, 0, 1.0, 1.0)
        xalign 1.0

        frame:
            xmargin 5
            ymargin 5
            xpadding 10
            ypadding 10
            vbox:
                style_prefix "edit"
                spacing 5

                text editorAnimation.name:
                    size 15
                    color "ff0"

                text "UI":
                    size 15

                textbutton "Frame info" action ToggleVariable("editorShowFrameInfo")

                text "Operations":
                    size 15

                textbutton "Easing" action SetVariable("editorShowEasingsFlag", True)
                textbutton "Clip end" action Function(clipAnimation)

                if shader.utils.findFile(editorAnimation.name):
                    text "Track info":
                        size 15

                    textbutton ("Stop" if editorPlayTrack else "Play") action ToggleVariable("editorPlayTrack")
                    textbutton "Repeat" action [ToggleDict(editorTrackSettings, "repeat"), Jump("update_editor_ui")]
                    textbutton "Cyclic" action [ToggleDict(editorTrackSettings, "cyclic"), Jump("update_editor_ui")]
                    textbutton "Reverse" action [ToggleDict(editorTrackSettings, "reverse"), Jump("update_editor_ui")]
                    textbutton "Auto end" action [ToggleDict(editorTrackSettings, "autoEnd"), Jump("update_editor_ui")]
                    textbutton "Clip" action [ToggleDict(editorTrackSettings, "clip"), Jump("update_editor_ui")]

                text "File":
                    size 15

                textbutton "New animation" action Confirm("Create a new animation?", SetVariable("editorNewAnimationFlag", True))
                textbutton "Load animation" action SetVariable("editorLoadAnimationFlag", True)
                textbutton "Save animation" action SetVariable("editorSaveAnimationFlag", True)

    frame:
        yalign 1.0
        hbox:
            spacing 10
            $ playText = "||" if editorPlayAnimation else ">>"
            textbutton "Frame: %i" % editorFrameNumber yalign 0.5 xsize 150 action Function(changeFrameCount)
            textbutton "<" yalign 0.5 keysym "j" action SetVariable("editorFrameNumber", (editorMaxFrames -1 if editorFrameNumber - 1 < 0 else editorFrameNumber - 1))
            textbutton playText yalign 0.5 xsize 50 keysym "k" action SetVariable("editorPlayAnimation", not editorPlayAnimation)
            textbutton ">" yalign 0.5 keysym "l" action SetVariable("editorFrameNumber", (editorFrameNumber + 1) % editorMaxFrames)

            timer 1.0 / shader.config.fps repeat True action If(editorPlayAnimation, SetVariable("editorFrameNumber", (editorFrameNumber + 1) % editorMaxFrames), NullAction())

            bar value VariableValue("editorFrameNumber", editorMaxFrames - 1)


init python:
    import os
    import shader
    from shader import skinnededitor, skinnedanimation, skinnedplayer
    from shader import easing, utils

    editorSettings = {
        "wireframe": True,
        "edgePoints": False,
        "imageAreas": False,
        "pivots": True,
        "names": False,
        "debugAnimate": False,
        "disableDrag": False,
        "tesselation": 0
    }
    editorDebugSettings = editorSettings.copy()
    editorDebugSettings.update({"edgePoints": False})

    editorDrawableName = ""
    editorRigFile = ""
    editorAnimFile = ""
    editorAnimation = None
    editorWasReset = True

    editorSaveRigFlag = False
    editorTesselationFlag = False
    editorRenameBoneFlag = False
    editorResetPoseFlag = False
    editorShowEasingsFlag = False
    editorNewAnimationFlag = False
    editorLoadAnimationFlag = False
    editorSaveAnimationFlag = False
    editorPauseTimeFlag = False

    editorShowFrameInfo = True
    editorFrameNumber = 0
    editorFrameNumberLast = -1
    editorPlayAnimation = False
    editorMaxFrames = 1

    editorPlayTrack = False
    editorTrackSettings = {
        "repeat": False,
        "cyclic": True,
        "reverse": False,
        "autoEnd": False,
        "clip": False,
    }

    def clearKeymapForEditor():
        #Remove mappings that would conflict with our editor
        shortcuts = ["mouseup_3", "mousedown_4", "mousedown_5", "h", "s", "v"]
        for key, values in config.keymap.items():
            for name in shortcuts:
                if name in values:
                    values.remove(name)
        renpy.clear_keymap_cache()

    def userInput(prompt, *args, **kwargs):
        #TODO Exclude invalid characters...
        return renpy.invoke_in_new_context(renpy.input, prompt, *args, **kwargs)

    def numberInput(text, old):
        return userInput(text, old, allow=list("1234567890"))

    def notify(text):
        renpy.notify(text)

    def _askListInputContext(*args):
        return renpy.call_screen("editorListScreen", *args)

    def askListInput(title, items, current=None, cancel=None):
        return renpy.invoke_in_new_context(_askListInputContext, title, items, current, cancel)

    def restartEditor():
        renpy.jump("reset_editor")

    def updateEditor():
        renpy.jump("update_editor")

    def changeFrameCount():
        global editorMaxFrames, editorFrameNumber
        try:
            count = eval(userInput("Set animation frame count", str(editorMaxFrames), allow=list("1234567890*/+-")))
            if count > 0 and count < 10000:
                editorMaxFrames = count
                editorFrameNumber = min(editorFrameNumber, editorMaxFrames - 1)
        except:
            pass

    def saveRigFile(editor):
        global editorRigFile
        name = editorRigFile
        if not name:
            name = editorDrawableName + ".rig"

        fileName = userInput("Save rig as...", name)
        if fileName:
            fileName, path = getSavePath(fileName, ".rig")
            editor.saveSkeletonToFile(path)
            notify("Rig saved to '%s'" % path)
            editorRigFile = fileName

    def setTesselation(editor):
        try:
            size = int(numberInput("Minimum tesselation pixel size (0 to disable)", editorSettings["tesselation"]))
            editorSettings["tesselation"] = size
            editor.updateBones()
            notify("Set tesselation to %i" % size)
        except:
            notify("Error")

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
        global editorAnimFile
        editorAnimFile = ""
        notify("New animation")
        updateEditor()

    def loadAnimation():
        global editorAnimFile
        result = askListInput("Animation", scanForFileNames("anim"))
        if result:
            editorAnimFile = result
            notify("Loaded: '%s'" % editorAnimFile)
            updateEditor()

    def scanForFileNames(extension):
        names = list(set([n.split("/")[-1] for n in shader.utils.scanForFiles(extension)]))
        names.sort()
        return names

    def getSavePath(fileName, extension):
        if not fileName.strip().lower().endswith(extension):
            fileName = fileName + extension
        directory = skinnededitor.getSaveDir()
        return fileName, os.path.join(directory, fileName)

    def saveAnimation(animation):
        global editorAnimFile
        rigBase = editorRigFile.rsplit(".", 1)[0]
        name = animation.name
        if not name.startswith(rigBase):
            name = rigBase + " " + name

        fileName = userInput("Save animation as...", name)
        if fileName:
            fileName, path = getSavePath(fileName, ".anim")
            animation.name = fileName
            skinnedanimation.saveAnimationToFile(path, animation)
            editorAnimFile = fileName
            notify("Animation saved to '%s'" % path)
            updateEditor()

    def clipAnimation():
        global editorMaxFrames, editorFrameNumber
        editorMaxFrames = editorAnimation.clipEnd()
        editorFrameNumber = min(editorFrameNumber, editorMaxFrames - 1)

    def rigEditorUpdate(context):
        global editorSaveRigFlag, editorTesselationFlag, editorRenameBoneFlag, editorResetPoseFlag, editorShowEasingsFlag, \
            editorNewAnimationFlag, editorLoadAnimationFlag, editorSaveAnimationFlag, editorFrameNumberLast, \
            editorWasReset

        context.createOverlayCanvas()

        editor = skinnededitor.SkinnedEditor(context, editorSettings)
        editor.update()
        editor.visualizeBones()

        editorAnimation.setFrameCount(editorMaxFrames)
        editorAnimation.update(editorFrameNumber, editor)

        if editorPlayTrack:
            player = shader.AnimationPlayer(context, "Player", editorWasReset)
            player.setDebug(editorShowFrameInfo)
            player.play([shader.TrackInfo(editorAnimation.name, **editorTrackSettings)])
            editorWasReset = False
        elif editorFrameNumberLast != editorFrameNumber or editorAnimation.dirty:
            editorFrameNumberLast = editorFrameNumber
            keys = editorAnimation.interpolate(editorFrameNumber, editor.getBones())
            editorAnimation.apply(keys, editor.getBones())

        if editorSettings["debugAnimate"]:
            editor.debugAnimate(True)

        if editorSettings["pivots"]:
            editorAnimation.drawDebugKeyFrames(editor, editorFrameNumber)
            if editorShowFrameInfo:
                editorAnimation.drawDebugText(editor, editorFrameNumber)

        if editorTesselationFlag:
            editorTesselationFlag = False
            setTesselation(editor)

        if editorRenameBoneFlag:
            editorRenameBoneFlag = False
            renameActiveBone(editor, editorAnimation)

        if editorResetPoseFlag:
            editorResetPoseFlag = False
            editor.resetPose()
            notify("Pose reset")

        if editorShowEasingsFlag:
            editorShowEasingsFlag = False
            setActiveEasing(editor, editorAnimation)

        if editorNewAnimationFlag:
            editorNewAnimationFlag = False
            newAnimation()

        if editorLoadAnimationFlag:
            editorLoadAnimationFlag = False
            loadAnimation()

        if editorSaveAnimationFlag:
            editorSaveAnimationFlag = False
            saveAnimation(editorAnimation)

        if editorSaveRigFlag:
            editorSaveRigFlag = False
            saveRigFile(editor)

        if editorPauseTimeFlag:
            context.uniforms["shownTime"] = 1.0
            context.uniforms["animationTime"] = 1.0

    def listImageTags():
        ignores = ["black", "text", "vtext", "editorBackground", shader.ZERO_INFLUENCE.split(".")[0]]
        tags = renpy.get_available_image_tags()
        for ignore in ignores:
            if ignore in tags:
                tags.remove(ignore)
        return sorted(tags)

#label main_menu: #TODO For fast testing
label start_editor:
    python:
        #Removes the quick menu permanently...
        if "quick_menu" in config.overlay_screens:
            config.overlay_screens.remove("quick_menu")

    scene
    show editorBackground

    call screen editorListScreen("Select an Image or a LiveComposite", listImageTags())
    $ editorDrawableName = _return
    if not editorDrawableName:
        return

    python:
        if 1: #Useful, but resolution changes are not always wanted.
            renpy.show(editorDrawableName)
            bounds = renpy.get_image_bounds(editorDrawableName)
            config.screen_width = max(bounds[2] + 500, 1280)
            config.screen_height = max(bounds[3] + 150, 720)
            renpy.hide(editorDrawableName)
            renpy.reset_physical_size()

    call screen editorListScreen("Load a rig for the image", scanForFileNames("rig"), editorDrawableName.split(".")[0] + ".rig", "Create a new rig")
    $ editorRigFile = _return
    $ editorAnimFile = ""

    $ clearKeymapForEditor() #TODO Mouse scrolling lists goes away, too...

label reset_editor:
    $ shader._controllerContextStore._clear()

label update_editor:
    python:
        if editorAnimFile:
            editorAnimation = skinnedanimation.loadAnimationFromFile(utils.findFile(editorAnimFile))
            editorMaxFrames = len(editorAnimation.frames)
        else:
            editorAnimation = skinnedanimation.SkinnedAnimation("untitled.anim")
            editorMaxFrames = 60 * 2
        editorFrameNumber = min(editorFrameNumber, editorMaxFrames)

label update_editor_ui:
    $ editorWasReset = True
    call screen editorMainScreen(editorDrawableName, shader.PS_SKINNED, {},
        update=rigEditorUpdate, args={"rigFile": utils.findFile(editorRigFile), "persist": True}, _layer="master") #nopredict

    $ shader._controllerContextStore._clear()
    return
