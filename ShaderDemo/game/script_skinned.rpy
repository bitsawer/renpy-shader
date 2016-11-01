
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
            textbutton "Bone points" action ToggleDict(editorSettings, "pivots")
            textbutton "Bone names" action ToggleDict(editorSettings, "names")
            textbutton "Debug animate" action ToggleDict(editorSettings, "debugAnimate")

            text "Actions":
                size 15

            textbutton "Autoconnect" action NullAction() #TODO Set a flag and check in update
            textbutton "Reload" action Confirm("Are you sure you want to reload?", Jump("start_skinned"))
            #textbutton "Save" action Confirm("Are you sure you want to save?", Function(editSave))
            textbutton "Save" action SetVariable("saveEdits", True)


init python:
    from shader import skinnededitor

    #config.keymap["input_delete"] = []
    config.keymap["game_menu"].remove("mouseup_3")
    config.keymap["hide_windows"].remove("h")
    config.keymap["screenshot"].remove("s")

    editorSettings = {
        "wireframe": False,
        "imageAreas": True,
        "pivots": True,
        "names": True,
        "debugAnimate": False,
    }

    saveEdits = False

    def editUpdate(context):
        global saveEdits

        editor = skinnededitor.SkinnedEditor(context, editorSettings)
        editor.update()

        if saveEdits:
            saveEdits = False
            editor.saveToFile()


label start_skinned:
    $ _controllerContextStore._clear()

    call screen skinnedScreen("doll", shader.PS_SKINNED, {"tex1": "amy influence"}, update=editUpdate, _tag="amy", _layer="amy") #nopredict

    "The End"
