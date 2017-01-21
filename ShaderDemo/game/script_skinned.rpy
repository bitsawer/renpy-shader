
image doll = LiveComposite(
    (800, 1000),
    (0, 0), "doll base.png",
    (249, 318), "doll skirt.png",
    #(0, 0), "doll lforearm.png",
    #(0, 0), "doll larm.png",
    #(0, 0), "doll lhand.png",
    #(0, 0), "doll hair.png",
)

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
                textbutton "Image areas" action ToggleDict(editorSettings, "imageAreas")
                textbutton "Bones" action ToggleDict(editorSettings, "pivots")
                textbutton "Bone names" action ToggleDict(editorSettings, "names")
                textbutton "Debug animate" action ToggleDict(editorSettings, "debugAnimate")

                text "Operations":
                    size 15

                textbutton "Rename" action [SetVariable("renameBoneFlag", True), RestartStatement()]
                textbutton "Subdivide" action [SetVariable("subdivideMesh", True), RestartStatement()]

                text "File":
                    size 15

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
            text "Animation: "

    frame:
        yalign 1.0
        hbox:
            spacing 10

            textbutton "Frame: %i" % frameNumber yalign 0.5 xsize 150
            bar value VariableValue("frameNumber", maxFrames)


init python:
    from shader import skinnededitor
    from shader import skinnedanimation

    #config.keymap["input_delete"] = []
    config.keymap["game_menu"].remove("mouseup_3")
    config.keymap["hide_windows"].remove("h")
    config.keymap["screenshot"].remove("s")

    editorSettings = {
        "wireframe": True,
        "imageAreas": True,
        "pivots": True,
        "names": False,
        "debugAnimate": False,
    }

    saveRig = False
    rigFile = "bones.rig"

    subdivideMesh = False

    renameBoneFlag = False

    frameNumber = 0
    maxFrames = 64

    def userInput(prompt, *args):
        #TODO Exclude invalid characters...
        return renpy.invoke_in_new_context(renpy.input, prompt, *args)

    def notify(text):
        renpy.notify(text)

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
        active = editor.getActiveBone()
        if active:
            if editor.subdivide(active, 500):
                notify("Subdivision done")
            else:
                notify("Subdivision not possible")
        else:
            notify("No mesh bone selected")

    def renameActiveBone(editor):
        active = editor.getActiveBone()
        if active:
            newName = userInput("Rename bone to...", active.name)
            if editor.renameBone(active, newName):
                notify("Bone renamed")
            else:
                notify("Renaming failed")
        else:
            notify("No bone selected")

    def editUpdate(context):
        global saveRig, subdivideMesh, renameBoneFlag

        editor = skinnededitor.SkinnedEditor(context, editorSettings)
        editor.update()

        animation.setFrameCount(maxFrames + 1)
        if not editor.isUserInteracting():
            animation.apply(frameNumber, editor.getBones())
            animation.update(frameNumber, editor.getBones(), editor)

        if subdivideMesh:
            subdivideMesh = False
            subdivideActiveMesh(editor)

        if renameBoneFlag:
            renameBoneFlag = False
            renameActiveBone(editor)

        if saveRig:
            saveRig = False
            saveRigFile(editor)


label start_skinned:
label main_menu: #TODO For fast testing
    $ _controllerContextStore._clear()

    $ animation = skinnedanimation.SkinnedAnimation()

    call screen skinnedScreen("doll", shader.PS_SKINNED, {"tex1": "amy influence"},
        update=editUpdate, args={"rigFile": rigFile}, _tag="amy", _layer="amy") #nopredict

    "The End"
