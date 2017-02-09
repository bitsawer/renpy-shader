
init python:
    import math
    from shader import skinnededitor
    from shader import skinnedplayer

    ARM_BONE = "doll base 14"
    IDLE = "breath"
    WAVE = "wave"

    #Indirection to make sure track information is not stored by saving the game.
    #Makes updating things after releasing the game easier.
    TRACKS = {
        IDLE: skinnedplayer.TrackInfo(IDLE),
        WAVE: skinnedplayer.TrackInfo(WAVE),
    }

    def rig(name, update=None, xalign=0.5, yalign=1.0):
        renpy.show_screen("rigScreen", name, shader.PS_SKINNED,
            update=update, args={"rigFile": shader.utils.findFile(name + ".rig")}, xalign=xalign, yalign=yalign,
            _tag=name, _layer="master")

    def visualizeRig(context):
        context.createOverlayCanvas()
        editor = skinnededitor.SkinnedEditor(context, editorSettings)
        editor.update()

    def animateArm(context):
        context.renderer.bones[ARM_BONE].rotation.z = math.sin(context.shownTime) + 0.5

    def playAnimations(context):
        player = skinnedplayer.AnimationPlayer(context)
        player.play([TRACKS[name] for name in anims])


screen rigScreen(name, pixelShader, textures={}, uniforms={}, update=None, args=None, xalign=0.5, yalign=1.0):
    add ShaderDisplayable(shader.MODE_SKINNED, name, shader.VS_SKINNED, pixelShader, textures, uniforms, None, update, args):
        xalign xalign
        yalign yalign


label start_rig_demo:

    # Active animation set. The update function uses this to play animations contained in the set.
    $ anims = set()

    #TODO Add a toggle button to visualize skeleton

    scene room

    jump rig_dev

    "This demo will show you how to use and animate rigged and skinned images."
    #TODO Link to docs and video.

    "First, let's show the image itself."

    $ rig("doll")
    with dissolve

    "It looks like a normal image because it is not being animated. Let's visualize it a bit more."

    $ rig("doll", update=visualizeRig)

    "There. Looks quite a bit more complex than a normal, static image."
    "Currently, the character is not moving. There are many ways to animate it."
    "First, we can manually force the bones to move. As an example, let's rotate the arm."

    $ rig("doll", update=animateArm)
    with dissolve

    "Now, the arm should be moving around."
    "Animating bones manually can be useful in many cases, but it can also be tedious and error-prone."

label rig_dev:

    $ rig("doll", update=playAnimations)
    with dissolve

    #"Let's stop the manual animation and change the way we animate the rig."
    #"Next, we use an animation that has been created and saved by using the rig editor."
    #"You can access the editor from the main screen and create your own rigs and animations."
    "Alright, let's play a hand waving animation."

    $ anims.add(WAVE)

    "You can wave back if you want to. Just don't do it if there are any people around you."
    "Next, we remove the wave animation from the active set and the character will return to the default pose."

    $ anims.remove(WAVE)

    "Back to where we started from."

    $ anims.update([IDLE, WAVE])

    #TODO Multiple animations
    #TODO Animations with code manipulation

    "The end"
