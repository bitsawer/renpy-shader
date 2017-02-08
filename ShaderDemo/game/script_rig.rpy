
init python:
    import math
    from shader import skinnededitor

    ARM_BONE = "doll base 14"

    def animate(name, update=None, xalign=0.5, yalign=1.0):
        renpy.show_screen("rigScreen", name, shader.PS_SKINNED,
            update=update, args={"rigFile": name + ".rig"}, xalign=xalign, yalign=yalign,
            _tag=name, _layer="master")

    def visualizeRig(context):
        context.createOverlayCanvas()
        editor = skinnededitor.SkinnedEditor(context, editorSettings)
        editor.update()

    def animateArm(context):
        context.renderer.bones[ARM_BONE].rotation.z = math.sin(context.shownTime) + 0.5

    def playAnimations(context):
        pass

screen rigScreen(name, pixelShader, textures={}, uniforms={}, update=None, args=None, xalign=0.5, yalign=1.0):
    modal True
    add ShaderDisplayable(shader.MODE_SKINNED, name, shader.VS_SKINNED, pixelShader, textures, uniforms, None, update, args):
        xalign xalign
        yalign yalign


label start_rig_demo:

    $ anims = set()

    scene room

    "This demo will show you how to use and animate rigged and skinned images."
    "First, let's show the image itself."

    $ animate("doll")
    with dissolve

    "It looks like a normal image because it is not being animated. Let's visualize it a bit more."

    $ animate("doll", update=visualizeRig)

    "There. Looks quite a bit more complex than a normal, static image."
    "Currently, the character is not moving. There are many ways to animate it."
    "First, we can manually force the bones to move. For example by moving the arm."

    $ animate("doll", update=animateArm)
    with dissolve

    "Now, the arm should be moving around."
    "Animating bones manually can be useful, but it can also be tedious and error-prone."

    $ animate("doll", update=playAnimations)
    with dissolve

    "Let's stop the manual animation and change the way we animate the rig."
    "Next, we use an animation that has been created and saved by using the rig editor."
    "You can access the editor from the main screen and create your own rigs and animations."
    "Alright, let's play a hand waving animation."

    $ anims.add("wave")

    "You can wave back if you want to. Just don't do it if there are any people around you."

    "The end"
