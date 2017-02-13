
init python:
    import math
    import shader

    #Our LiveComposite image name (defined in images/doll/doll.rpy).
    #We add the .rig extension to this to find the rig file associated with the image.
    doll = "doll"

    #Another, simpler rig and its image.
    amyDoll = "amypose"

    debugRig = False #For debugging rig bones etc.
    debugAnimations = False #For debugging animation frames etc.

    #Hardcoded bone name for the rig we will be using
    ARM_BONE = "basecrop 13"

    #Hardcoded image names
    CLOTH_BASE = "basecrop"
    CLOTH_SKIRT = "skirtcrop"
    CLOTH_SHIRT = "shirtcrop"
    CLOTH_HAIR = "haircrop"

    #Indirection to make sure animation track information is not stored by saving the game.
    #Makes things easier to update after releasing the game. Note that if you
    #rename, delete etc. animations make sure you still keep the entries for them
    #in here if you want to support old save games.
    FLAIL = "flail"
    SQUAT = "squat"
    DOLL_TRACKS = {
        FLAIL: shader.TrackInfo("doll flail.anim", cyclic=True),
        SQUAT: shader.TrackInfo("doll squat.anim", cyclic=True),
    }

    AMY_IDLE = "idle"
    AMY_ARM_LEFT = "waveLeft"
    AMY_ARM_RIGHT = "waveRight"
    AMY_TRACKS = {
        AMY_IDLE: shader.TrackInfo("amypose idle.anim", repeat=True),
        AMY_ARM_LEFT: shader.TrackInfo("amypose leftarm.anim", cyclic=True),
        AMY_ARM_RIGHT: shader.TrackInfo("amypose rightarm.anim", cyclic=True),
    }

    def visualizeRig(context):
        #Draw some useful debug visualizations
        if debugRig:
            context.createOverlayCanvas()
            editor = shader.SkinnedEditor(context, editorDebugSettings)
            editor.visualizeBones()

        #Only show the wireframes in debug mode
        for name, bone in context.renderer.getBones().items():
            bone.wireFrame = debugRig

    def showDollClothes(show=True):
        for name in clothes:
            clothes[name] = show

    def updateDollClothes(context):
        for name, visible in clothes.items():
            fullName = "images/doll/" + name
            context.renderer.bones[fullName].visible = visible

    def animateDollArm(context):
        bone = context.renderer.bones[ARM_BONE]
        targetRotation = math.sin(context.time) + 0.5 #In radians, not in degrees.
        bone.rotation.z = shader.utils.interpolate(bone.rotation.z, targetRotation, 0.1)
        visualizeRig(context)

    def playDollAnimations(context):
        #Animate all active tracks. Look up the track infos using the animation names.
        player = shader.AnimationPlayer(context, doll)
        player.setDebug(debugAnimations) #Enable visual debug help
        player.play([DOLL_TRACKS[name] for name in anims])
        updateDollClothes(context)
        visualizeRig(context)

    def playAmyAnimations(context):
        #Mostly same as playDollAnimations(), exepct this doll doesn't have "clothes"
        player = shader.AnimationPlayer(context, amyDoll)
        player.setDebug(debugAnimations) #Enable visual debug help
        player.play([AMY_TRACKS[name] for name in amyAnims])
        visualizeRig(context)

#The screen for showing rigged images. It is usually best to use the rig() function which will show this.
screen rigScreen(name, pixelShader, textures={}, uniforms={}, update=None, args=None, xalign=0.5, yalign=1.0):
    add ShaderDisplayable(shader.MODE_SKINNED, name, shader.VS_SKINNED, pixelShader, textures, uniforms, None, update, args):
        xalign xalign
        yalign yalign

screen animationDebugScreen():
    frame:
        xalign 1.0
        yalign 0.0
        xpadding 10
        ypadding 10
        vbox:
            textbutton "Animation debug" action ToggleVariable("debugAnimations")
            textbutton "Rig debug" action ToggleVariable("debugRig")

label start_rig_demo:

    # Active animation set. The update function uses this to play animations contained in the set.
    # If you use multiple rigs, each one should have its own set of active animations.
    $ anims = set()
    $ amyAnims = set()

    # Visible "clothes" for the doll. By default make them all visible.
    $ clothes = {CLOTH_BASE : True, CLOTH_SKIRT: True, CLOTH_SHIRT: True, CLOTH_HAIR: True}

    scene room

    #jump rig_dev

    "This demo will show you how to use and animate rigged and skinned images."
    #TODO Link to docs and video.
    "First, let's show the image itself."

    $ rig(doll, update=visualizeRig).dissolve()

    "It looks like a normal image because it is not being animated. Let's visualize it a bit more."

    $ debugRig = True

    "There. Looks quite a bit more complex than a normal, static image."
    "Currently, the character is not moving. There are many ways to animate it."
    "First, we can manually force the bones to move. As an example, let's rotate the arm."

    $ rig(doll, update=animateDollArm)

    "Now, the arm should be moving around."
    "Animating bones manually can be useful in many cases, but it can also be tedious and error-prone."
    "We will hide the rig debug visualization for now. It can slow things down quite a bit."

    $ debugRig = False
    $ rig(doll, update=playDollAnimations)

    "Let's stop the manual animation and change the way we animate the rig."
    "Next, we use an animation that has been created and saved by using the rig editor."
    "You can access the editor from the main screen and create your own rigs and animations."
    "Alright, let's play a more complex animation."

    # Enable animation debug stats and start the animation.
    $ debugAnimations = True
    $ anims.add(FLAIL)

    # Allow the user to toggle animation debug stats on and off
    show screen animationDebugScreen()

    "The buttons at the top right can now be used to toggle debug visualization on and off."
    "You can wave back if you want to. Just don't do it if there are any people around you."
    "Next, we remove the animation from the active set and the character will return to the default pose."

    $ anims.remove(FLAIL)

    "We can also \"change\" the clothes of the doll by toggling bone visibility."
    "Let's hide her shirt first."

    $ clothes[CLOTH_SHIRT] = False

    "There. Let's make her bald, too!"

    $ clothes[CLOTH_HAIR] = False

    "And the skirt, too."

    $ clothes[CLOTH_SKIRT] = False

    "All right, I think that is enough for now. Lets put them all back."

    $ showDollClothes()

    "Now, let's mix some animations together. Let's start flailing around again."

    $ anims.add(FLAIL)

    "There. And now lets add a squatting animation into the mix."

    $ anims.add(SQUAT)

    "..."
    "Active lifestyle is important, don't you think?"
    "If you have watched that modern dance long enough, we can proceed and let her rest."

    $ anims.clear()

    "That was a complex rig, but you don't have to create complex LiveComposite setups to animate images."
    "Often it is enough to rig a single, static image."
    "First, lets hide the doll completely..."

    $ hide(doll)

label rig_dev:

    "... And show a simpler rig which contains only one image."

    $ rig(amyDoll, yalign=0.1, update=playAmyAnimations).dissolve()

    "There. A pretty basic rig."
    "To make it look a bit more alive, lets play an idle animation."

    $ amyAnims.add(AMY_IDLE)

    "Ideally idling should be reasonably subtle. As a hint you can use TrackInfo.weight to adjust animation strength."
    "You can also mix different idling tracks or even add some manual bone control to make it look good and non-repeating."
    "Let's animate it a bit more. Arm movement is always a fan favorite."

    $ amyAnims.add(AMY_ARM_RIGHT)

    "Yeah, smooth moves. Let's move the second hand, too."

    $ amyAnims.add(AMY_ARM_LEFT)

    "There you go... A lot of movement going on."
    "That is about it for now. Go and make your own rigs and animations now! Good luck!"
