
init python:
    import math

    ARM_BONE = "doll base 14"

    def animate(name, update=None, xalign=0.5, yalign=1.0):
        renpy.show_screen("rigScreen", name, shader.PS_SKINNED,
            update=update, args={"rigFile": name + ".rig"}, xalign=xalign, yalign=yalign,
            _tag=name, _layer="master")

    def animateArm(context):
        context.renderer.bones[ARM_BONE].rotation.z = math.sin(context.shownTime) + 0.5


screen rigScreen(name, pixelShader, textures={}, uniforms={}, update=None, args=None, xalign=0.5, yalign=1.0):
    modal True
    add ShaderDisplayable(shader.MODE_SKINNED, name, shader.VS_SKINNED, pixelShader, textures, uniforms, None, update, args):
        xalign xalign
        yalign yalign


label start_rig_demo:
    scene room

    "This demo will show you how to use and animate rigged and skinned images."
    "First, let's show the image itself."

    $ animate("doll")
    with dissolve

    "Currently, the character is not moving. There are many ways to animate it."
    "First, we can manually force the bones to move. For example moving the hand."

    $ animate("doll", update=animateArm)

    "Now, the arm should be moving around."
    "Animating bones manually can be useful, but it can also be tedious and error-prone."

    "The end"
