
image amy = "amy.png"
image eileen = "eileen.png"
image sky = "sky.jpg"
image cg = "cg.jpg"

#TODO Links

define a = Character("Amy", color="#BE795C", image="amy")
define e = Character("Eileen", color="#FFFFFF", image="eileen")

#Add custom "bottom", "middle" and "top" layers which we can use for more flexibility.
#They are only needed if you want to do some fancy 3D-overlaying etc. like in this demo.
#Also add a layer for the "amy"-character. In some cases it might be a good idea to create a layer for
#each character to to simplify show/hide logic or if you want to use RenPy animations on them.
define config.layers = ["bottom", "master", "middle", "amy", "top", "transient", "screens", "overlay"]

init python:
    import math
    import shader

    #Can help in debugging
    renpy.display.log.flush = True

    #A simple, custom pixel shader. Feel free to edit this and
    #see what changes. Also check out the shaders bundled with this library if you want to.
    PS_COLOR_WAVE = """
        in vec2 varUv; //Texture coordinates

        uniform sampler2D tex0; //Texture bound to slot 0
        uniform float shownTime; //RenPy provided displayable time

        void main()
        {
            vec4 color = texture2D(tex0, varUv);
            float red = color.r * ((sin(shownTime) + 1.0) / 2.0);
            float green = color.g * ((sin(shownTime + 2.0) + 1.0) / 2.0);
            float blue = color.b * ((sin(shownTime + 4.0) + 1.0) / 2.0);
            gl_FragColor = vec4(red, green, blue, color.a);
        }
    """

    #Callback functions for creating and updating shader screens.
    #You should be very careful when modifying any global game state from
    #these callbacks unless you are sure you can do it safely.
    #Reading variables etc. is usually fine.

    def interpolate2d(a, b, value):
        return (shader.utils.interpolate(a[0], float(b[0]), value), shader.utils.interpolate(a[1], float(b[1]), value))

    #Scale eye and mouth targets from -1 to 1 to a relative pixel range. There is no
    #hard science about how much you should scale them, use what looks good.
    #Also if your eyes or mouth are not horizontally aligned, this is a good place
    #to rotate that 2D point.

    def relativeEye(point):
        return (point[0] * 0.015, point[1] * 0.01)

    def relativeMouth(point):
        return (point[0] * 0.005, point[1] * 0.005)

    def animateEyesAndMouth(context):
        eye = context.store.get("eyeShift")
        mouth = context.store.get("mouthShift")
        if eye and mouth:
            speed = 0.1
            eye = interpolate2d(eye, relativeEye(eyeTarget), speed)
            mouth = interpolate2d(mouth, relativeMouth(mouthTarget), speed)
        context.uniforms["eyeShift"] = context.store["eyeShift"] = eye or (0, 0)
        context.uniforms["mouthShift"] = context.store["mouthShift"] = mouth or (0, 0)

    def animateEyesAndMouthRandom(context):
        st = context.shownTime
        context.uniforms["eyeShift"] = relativeEye((math.cos(st), math.sin(st)))
        context.uniforms["mouthShift"] = relativeMouth((math.cos(st), math.sin(st)))

    def animateTransform2d(context):
        matrix = shader.utils.createTransform2d()
        matrix.rotatey(math.radians(math.sin(context.shownTime) * 10))
        context.uniforms[shader.PROJECTION] = matrix

    def animateBlurSize(context):
        context.uniforms["blurSize"] = math.sin(context.shownTime) * 2.0

    #Replacement for renpy.config.scene See below.
    def clearScene(layer="master"):
        renpy.scene(layer)
        if layer == "master":
            #Clearing the master layer should also clear our custom layers.
            for name in ["bottom", "middle", "amy", "top"]:
                renpy.scene(name)

#Set our custom scene-callback handler which also
#clears our custom layers. We could do it manually, but
#it is much more easier this way and you are less likely
#to forget some layer which then stays buried under all other images
#but keeps burning memory and resources.
define config.scene = clearScene

#Generic screen for showing 2d-images. In some cases it might be wise
#to create more specific screens which know the images and
#parameters they want to use instead of passing them all in every time you
#want to show the screen. Also remember the screen "tag"-attribute, it can come in handy.

screen shaderScreen(name, pixelShader, textures={}, uniforms={}, update=None, xalign=0.5, yalign=0.1):
    modal False
    add ShaderDisplayable(shader.MODE_2D, name, shader.VS_2D, pixelShader, textures, uniforms, None, update):
        xalign xalign
        yalign yalign

label start:

    $ cameraDrive = False
    $ cameraUserControl = False

    # Relative values (from -1 to +1) as a 2D-point (x and y axis). For easier
    # use you might want to define constants for certain expressions, for example
    # in our case FULL_SMILE would be something like (0, 1).
    $ eyeTarget = (0, 0)
    $ mouthTarget = (0, 0)

    scene room
    show amy:
        default
        yalign 0.1

    a "Hello, everyone! Welcome to the shader demo!"
    a "If this application crashes at some point or you don't see anything... Well, this is still experimental."
    a "Also, remember to check out the {a=https://github.com/bitsawer/renpy-shader}project homepage!{/a}"
    a "First, let's check if your system is supported and ready to go..."
    "..."

    if shader.isSupported(True):
        a "Everything looks good!"
    else:
        a "Too bad, looks like we can't run on this system."
        a "The more specific reason should have been logged into the log.txt file."
        a "At the moment, there is nothing we can do. The end. For now."
        return

    a "The user can also manually disable shader effects in the Preferences screen."
    a "If you or your users can't see the effects, make sure that setting is on."
    a "Current value of that setting is: '[persistent.shader_effects_enabled]'."
    a "Either way, feedback would be useful. What kind of computer, OS and graphics card you have etc."
    a "First, I'm going to show you how to make my hair and skirt wavy. Like in a wind."
    a "To do that, we are going to use a simple influence image. Let's check it out."

    show amy influence at right as influence:
        default
        xalign 0.9
        yalign 0.4
    with dissolve

    a "Eek! Looks freaky! But don't worry, I'll explain what that image does."
    a "The red color tells where a wind-like distortion effect should be applied."
    a "The green color tells - you guessed it - where the eyes are."
    a "And finally, the blue color tells where the mouth and its corners are."
    a "The brighter the color, the more strongly the effects will be applied."
    a "Naturally, a black color means that no effect should be applied to that location in the image."
    a "Also note that the influence image is smaller than my actual color image."
    a "That is because only the relative proportions must be the same."
    a "This means you can save A LOT of memory by using smaller images. And by this I mean runtime memory."
    a "The relatively small image files must be uncompressed when loaded and that can take a lot of memory."
    a "The quality might decrease a bit when using small images, but in this use scenario it is not critical."
    a "Not too complex, right? I doodled that image in about 5 minutes (and it probably shows)."

    hide influence
    with dissolve

    a "I'm now going to hide this text box, so you can see the effect on my skirt better. Ready?"

    #Hide the normal sprite Amy...
    hide amy

    #...And replace her with the shader version.
    #We could use the shader version all the time, but I wanted to make
    #sure user has read previous lines in case the app crashes here.
    #You could also use normal "show screen YYY(...)" statements.
    #For example the next line...

    $ show("amy", update=animateEyesAndMouth).dissolve()

    #... just uses some helper functions to make things more readable.
    #That call does roughly the same as this:
        #show screen shaderScreen("amy", shader.PS_WIND_2D, {"tex1": "amy influence"}, _tag="amy", _layer="amy")
        #with dissolve

    #One thing to keep in mind is that show() and other Python calls will create shader versions of the images and
    #if those images don't have any influence maps the result will be visually identical to a
    #normal sprite image, but they will consume much more memory and processing power. So it is
    #recommended to use normal RenPy statements with normal images.

    #One of the disadvantages of using Python to do this is that we lose RenPy screen prediction.
    #This can affect image loading performance. You can manully give hints
    #by using:
    #   -renpy.start_predict_screen() and renpy.stop_predict_screen()
    #   -renpy.predict() and renpy.stop_predict()
    #if you think those help.

    window hide
    pause 5

    a "Wee! Windy! Even indoors! My hair and skirt should now move around a bit."
    a "If you can't see anything different, something went wrong. Oops!"
    a "Let's try simple facial animation using that influence image. Keep your eyes on my face!"
    a "Now, I'm going to look to my right..."

    $ eyeTarget = (1.0, 0)

    "..."
    a "I'll smile more, too..."

    $ mouthTarget = (0, 0.8)

    "..."
    a "Sadness incoming..."

    $ eyeTarget = (0, -1)
    $ mouthTarget = (0, -1)

    "..."
    a "And neutral..."

    $ eyeTarget = (0, 0)
    $ mouthTarget = (0, 0)

    "..."
    a "And now for something else..."

    $ eyeTarget = (-1.0, 1)
    $ mouthTarget = (0, -1) #Maximum frown/sadness

    a "Ugh... Haven't you had enough fun, already?"
    "..."
    a "I can also change my image easily."

    $ show("amy sad").dissolve()

    a "Now I'm sad... But I don't have an influence image for this 'pose', so there are no effects."
    a "I don't like being sad, so let's change back."

    $ show("amy").dissolve()

    a "Yes! This feels a lot better!"
    a "Let's also do some simple image projection stuff along with the wind effect!"

    $ show("amy", update=animateTransform2d).dissolve()

    a "Slightly transforming the image perspective can create some interesting effects."
    a "You can also do other, more complex operations with it."
    a "Now, I'll move to the left to demonstrate simple transformations."

    $ warp("amy", xalign=0.2)

    a "There! I moved."
    a "Next, we'll have a special quest! [e]!"

    $ show("eileen", xalign=0.8, yalign=1.0).dissolve()

    window hide
    pause 5

    e "Thanks! Nice to be here! Pretty windy, though!"
    a "Bad windows, I think. Now that we are both here... I have an idea!"
    a "Let's make faces!"
    "..."
    e "What a great idea!"

    $ show("amy", xalign=0.2, update=animateEyesAndMouthRandom)
    $ show("eileen", xalign=0.8, yalign=1.0, update=animateEyesAndMouthRandom)
    with dissolve

    window hide
    pause 5

    a "Heh! Look at your eyes!"
    e "And your mouth! Ha!"
    "..."
    e "Sorry, but I'm afraid I'll have to go. It was fun, but you know me, always busy..."
    a "Just one more thing! Let's relax for a moment in a nice, calming forest!"

    $ scene().show("forest").fade()

    window hide
    pause 5

    "..."

    $ show("amy", xalign=0.2).dissolve()

    a "Aah... Sometimes, it's good to just sit down and admire the nature."

    $ show("eileen", xalign=0.8, yalign=1.0).dissolve()

    e "True..."
    a "Feeling better?"
    e "A lot."
    a "I'm always happy to help."
    e "Still, I really have to go before I'm late. See you!"
    a "Bye!"
    e "And good luck with your visual novel! Break a leg!"

    # Hide Eileen and stop Amy face animations
    $ hide("eileen").dissolve().show("amy").dissolve()

    a "There she goes, always busy helping others... Well, back to the topic!"
    a "Next, you are going to see me in a full screen CG! Ready? Go!"

    #We could also use normal "scene"-statement here, but this is just to demonstrate
    #the functionality. It also reads better when normal RenPy statements are not mixed
    #with Python calls, but the functionality is still the same. Use what you prefer.
    $ scene("cg").fade()

    window hide
    pause 10

    a "I'm so pretty in this picture, right!?"
    a "I hope you noticed how the background trees and the grass is moving, too."
    a "In the next part, you can use your mouse cursor to influence the waviness."
    a "Just move your mouse cursor over the image. Ready?"

    $ show("cg", uniforms={"mouseEnabled": 1}).fade()

    window hide
    pause 5

    a "Pretty cool, eh? Onwards!"

    scene room
    $ show("amy").fade()

    a "Now, I will show you how to use a custom shader for the background."
    a "At the moment, the background is a normal, static image."
    a "In the next step, the background will be replaced with a blurred version."

    #Show this screen in "bottom"-layer so it will always below other sprites.
    hide room
    $ show("room", pixelShader=shader.PS_BLUR_2D, update=animateBlurSize, layer="bottom")

    a "The blur effect should now be affecting the background image. Notice how the blur strength is animated."
    a "Now the background is being blurred and I'm still being affected by the wind effect."
    a "Seen enough? I'm going to disable the blurring now, it is a pretty resource intensive operation at the moment."

    #Hide the blurring screen and show the basic image version.
    #Be careful that you properly hide shader images you don't want to use anymore instead of just placing
    #other images on top of them, forcing them to be rendered even thought they are not visible to the user.
    $ hide("room", layer="bottom")
    show room

    a "There! I can already feel the graphics card sigh in relief."
    a "At the moment, I'm on a custom layer. This means we can also animate me using RenPy transforms without affecting others. Ready?"

    #We need to animate the whole layer. A bit clumsy, but this is one limitation we currently have.
    show layer amy:
        default
        ease 1.0 xpos 0.25
        ease 1.0 xpos 0.75
        ease 1.0 xpos 0.5
        repeat

    a "Wee! I'm moving!"
    "..."
    a "I'm getting dizzy, so let's move on!"

    scene room
    $ show("amy").fade()

    a "Next, we are going to try out some 3D-rendering!"
    a "If you have an older computer or a slow graphics card, they might struggle with this."
    a "Anyway, let's try it out! We will now transition from 2D to 3D."

    $ hide("amy").dissolve()

    #Create the 3D room screen and put it in the "middle"-layer.
    #Use the the normal RenPy "show screen"-statement here for a change. We could also
    #use our Python helper functions for the 3D stuff, but in the end
    #they just make things shorter and easier to read, they are not black magic.
    show screen shaderScreen3d("room", create3dRoomScene, update3dRoomScene, _layer="middle")
    show sky
    with dissolve

    a "Doesn't look like much, right? Well, check this out!"

    # The rollback can sometimes behave a bit strangely with complex 3D-stuff.
    $ cameraDrive = True

    #Ugly and fake looking sky movement. A real 3D skybox would be better.
    show sky:
        default
        xanchor 0.5
        yanchor 1.0
        parallel:
            easeout 2 zoom 2.0
        parallel:
           easeout 2 xpos 0.0

    "..."
    a "That's right, this is real 3D-scene you can look around in."

    #We could hide shaderScreen3d at this point, but the "scene"-statement will take care of it for us
    #because we replaced it earlier with our custom version which will also clear our custom layers.
    scene
    show room onlayer bottom
    $ show("amy").dissolve()

    a "If you ever wanted or needed to use 3D with RenPy, now you can."
    a "We can also render 3D-objects into the scene between layers. Like this!"

    #Create a cube into the middle layer. Visualize it's vertex normals instead of any other shading.
    show screen shaderScreen3d("cube", create3dCube, update3dCube, {}, shader.PS_3D_NORMALS, _layer="middle")

    #Animate the whole cube layer.
    show layer middle:
        default
        parallel:
            ease 1.0 xpos 0.25
            ease 1.0 xpos 0.75
            ease 1.0 xpos 0.5
            repeat
        parallel:
            ease 0.4 ypos 1.2
            ease 1.2 ypos 0.8
            repeat

    a "Aww... What a cute little cube!"
    a "That was all! Remember, you can always write your own shaders if you want to."
    a "Or make someone else write them for you. The internet is full of interesting ones. The possibilities are endless."
    a "For example, check out this simple effect you can easily modify in the source file."

    #Change the pixel shader
    $ show("amy", pixelShader=PS_COLOR_WAVE)

    a "Yee! I have always wanted to be cheerfully colored! Party hard!"
    "..."
    a "This can't be healthy... I need to stop."
    a "So, that's about it for now. Bye!"
    a "Beam me up, Scotty!"

    #Change the pixel shader
    $ show("amy", pixelShader=shader.PS_BEAM_FADE_2D)

    #Note that Amy is still technically visible and rendered even thought you can't see her.
    #In normal use it would be wise to hide() her soon to avoid wasting computing power.

    ":: The End ::"

    return
