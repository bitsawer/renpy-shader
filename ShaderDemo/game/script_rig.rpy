
init python:
    import math
    import shader

    doll = "doll" #Image name. Also we add the .rig extension to this to find the rig file.
    debugAnimations = False #For debugging animation frames etc.

    ARM_BONE = "doll base 14" #Hardcoded bone name for the rig we will be using.

    #Indirection to make sure animation track information is not stored by saving the game.
    #Makes things easier to update after releasing the game. Note that if you
    #rename, delete etc. animations make sure you still keep the entries for them
    #in here if you want to support old save games.
    IDLE = "breath"
    WAVE = "wave"
    TRACKS = {
        IDLE: shader.TrackInfo("breath.anim"),
        WAVE: shader.TrackInfo("wave.anim", repeat=True, cyclic=True, autoEnd=0),
    }

    def rig(name, update=None, xalign=0.5, yalign=1.0):
        renpy.show_screen("rigScreen", name, shader.PS_SKINNED,
            update=update, args={"rigFile": shader.utils.findFile(name + ".rig")}, xalign=xalign, yalign=yalign,
            _tag=name, _layer="master")

    def visualizeRig(context):
        context.createOverlayCanvas()
        editor = shader.SkinnedEditor(context, editorSettings)
        editor.update()

    def animateArm(context):
        context.renderer.bones[ARM_BONE].rotation.z = math.sin(context.shownTime) + 0.5

    def playAnimations(context):
        #Animate all active tracks.
        player = shader.AnimationPlayer(doll, context, debugAnimations)
        player.play([TRACKS[name] for name in anims])


screen rigScreen(name, pixelShader, textures={}, uniforms={}, update=None, args=None, xalign=0.5, yalign=1.0):
    add ShaderDisplayable(shader.MODE_SKINNED, name, shader.VS_SKINNED, pixelShader, textures, uniforms, None, update, args):
        xalign xalign
        yalign yalign


label start_rig_demo:

    # Active animation set. The update function uses this to play animations contained in the set.
    # If you use multiple rigs, each one should have its own set of active animations.
    $ anims = set()

    #TODO Add a toggle button to visualize skeleton

    scene room

    jump rig_dev

    "This demo will show you how to use and animate rigged and skinned images."
    #TODO Link to docs and video.

    "First, let's show the image itself."

    $ rig(doll)
    with dissolve

    "It looks like a normal image because it is not being animated. Let's visualize it a bit more."

    $ rig(doll, update=visualizeRig)

    "There. Looks quite a bit more complex than a normal, static image."
    "Currently, the character is not moving. There are many ways to animate it."
    "First, we can manually force the bones to move. As an example, let's rotate the arm."

    $ rig(doll, update=animateArm)
    with dissolve

    "Now, the arm should be moving around."
    "Animating bones manually can be useful in many cases, but it can also be tedious and error-prone."

label rig_dev:

    $ rig(doll, update=playAnimations)
    with dissolve

    #"Let's stop the manual animation and change the way we animate the rig."
    #"Next, we use an animation that has been created and saved by using the rig editor."
    #"You can access the editor from the main screen and create your own rigs and animations."
    "Alright, let's play a hand waving animation."

    # Enable animation debug stats and start the animation.
    $ debugAnimations = True
    $ anims.add(WAVE)

    "You can wave back if you want to. Just don't do it if there are any people around you."
    "Next, we remove the wave animation from the active set and the character will return to the default pose."

    $ anims.remove(WAVE)

    "Back to where we started from."

    $ anims.update([IDLE, WAVE])

    #TODO Multiple animations
    #TODO Animations with code manipulation

    "The end"
