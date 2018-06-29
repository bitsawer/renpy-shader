
init python:
    import math
    import shader
    from shader import euclid

    def placeSprite(name, x, y, scale=1.0):
        imageWidth = 467 #Hardcoded image size, it would be better to look this up during runtime
        imageHeight = 780
        width = (imageWidth / float(config.screen_width)) * scale
        height = (imageHeight / float(config.screen_height)) * scale
        return (x, x + width, y, y + height)

    def setUniforms(context, lights):
        lightData = []
        for light in lights:
            l = light.copy()
            if l["behavior"]:
                l = l["behavior"](context, l) #Callback behavior function
            #Pass light data to pixel shader in a 4x4 matrix. Some fields
            #are unused, but this leaves room for additions.
            m = euclid.Matrix4()
            m.a, m.b, m.c = l["position"]
            m.e, m.f, m.g = l["color"]
            m.i = l["distance"]
            lightData.append(m)

        context.uniforms["lights"] = lightData
        context.uniforms["lightCount"] = len(lightData)
        context.uniforms["ambientLight"] = rawColor(ambientLight)
        context.uniforms["dofRange"] = (depthOfField / 100.0, 0)
        context.uniforms["fogRange"] = (fogStart / 100.0, 1.0)
        context.uniforms["fogColor"] = rawColor(fogColor)
        context.uniforms["fogRainEnabled"] = fogRainEnabled
        context.uniforms["shadowStrength"] = shadowStrength / 100.0

    def getMousePos(context):
        pos = context.mousePos
        #Normalize mouse position to 0.0 - 1.0 range
        return (pos[0] / float(context.width), pos[1] /  float(context.height))

    def createMouseLight(context):
        mouse = getMousePos(context)
        return createLight((mouse[0], mouse[1], -0.1), rawColor(mouseLightColor), 2)

    def createMouseSun(context):
        mouse = getMousePos(context)
        strength = 1.1
        rgb = rawColor(mouseSunColor)
        return createLight((mouse[0], mouse[1], -1.0), (rgb[0] * strength, rgb[1] * strength, rgb[2] * strength), -1)

    def createInteractiveLight():
        offset = -(addLightZOffset / 1000.0)
        return createLight((addLightX / 1000.0, addLightY / 1000.0, offset), rawColor(addLightColor))

    def updateDeferred(context):
        spriteDepth = -1
        spriteScale = 1.0
        if spriteDepthMerge:
            spriteDepth = (math.sin(context.shownTime) + 1.0) * 0.5
            spriteScale = 0.5 + ((1.0 - spriteDepth) * 0.2)
        context.uniforms["spriteDepth"] = spriteDepth
        context.uniforms["spriteArea"] = placeSprite("", 0.4, 0.3, spriteScale)

        lightsCopy = lights[:]
        if mouseLight:
            lightsCopy.append(createMouseLight(context))
        if mouseSun:
            lightsCopy.append(createMouseSun(context))
        if addLightInteractive:
            lightsCopy.append(createInteractiveLight())

        #Use the last n lights no matter how many we currently have.
        setUniforms(context, lightsCopy[-shader.DEFERRED_MAX_LIGHTS:])

        #If you only need to render the scene once per interaction and you don't need to
        #interactively update anything, you can uncomment the next line.
        #This will reduce CPU and GPU usage massively.
        #context.continueRendering = False

    def createLight(position, color, distance=1.0, behavior=None):
        return {
            "position": position,
            "color": color,
            "distance": distance,
            "behavior": behavior
        }

    def lightBlinkBehavior(context, light):
        blinkPattern = [1, 0, 1, 0.5, 1, 0.75, 0]
        speed = 1.0
        strength = blinkPattern[(int(context.shownTime * speed) % len(blinkPattern))]
        color = light["color"]
        light["color"] = (color[0] * strength, color[1] * strength, color[2] * strength)
        return light

    def rgb(r, g, b):
        #Use a dict and scale value to range 0 - 100 so we can use RenPy screen variable value handlers (DictValue etc.)
        #Otherwise we could easily just use 3-item tuples with values from 0.0 to 1.0
        return {"red": r * 100, "green": g * 100, "blue": b * 100, "strength": 500}

    def rawColor(rgb):
        #Convert a color dict created by color() into a normalized 3-tuple
        s = rgb["strength"] / 500.0
        return (rgb["red"] / 100.0 * s, rgb["green"] / 100.0 * s, rgb["blue"] / 100.0 * s)

    def addNewLight():
        lights.append(createInteractiveLight())

    addLightX = 500 #From 0 to 1000
    addLightY = 500
    addLightZOffset = 200
    addLightColor = rgb(1, 1, 1)
    addLightInteractive = False

screen setColorScreen(colorDict):
    frame:
        xalign 0.5
        yalign 0.5
        xpadding 10
        ypadding 10

        vbox:
            xmaximum 400
            ymaximum 400
            spacing 5
            hbox:
                textbutton "Red:" xsize 150
                bar value DictValue(colorDict, "red", 100)
            hbox:
                textbutton "Green:" xsize 150
                bar value DictValue(colorDict, "green", 100)
            hbox:
                textbutton "Blue:" xsize 150
                bar value DictValue(colorDict, "blue", 100)
            hbox:
                textbutton "Strength:" xsize 150
                bar value DictValue(colorDict, "strength", 1000)
            hbox:
                textbutton "Back" action Hide("setColorScreen")

screen addLightScreen():
    on "show" action SetVariable("addLightInteractive", True)
    on "hide" action SetVariable("addLightInteractive", False)

    frame:
        yalign 1.0
        xpadding 10
        ypadding 10
        $ textWidth = 250
        vbox:
            spacing 2
            hbox:
                textbutton "Light x-position:" xsize textWidth
                bar value VariableValue("addLightX", 1000)
            hbox:
                textbutton "Light y-position:" xsize textWidth
                bar value VariableValue("addLightY", 1000)
            hbox:
                textbutton "Light z-offset:" xsize textWidth
                bar value VariableValue("addLightZOffset", 1000)
            hbox:
                textbutton "Light color" action Show("setColorScreen", None, addLightColor)
            hbox:
                textbutton "Add light" action [Function(addNewLight), Hide("addLightScreen")]
                textbutton "|"
                textbutton "Cancel" action Hide("addLightScreen")

screen deferredEditorScreen():
    frame:
        xpadding 10
        ypadding 10
        hbox:
            textbutton "Exit" action Return("")
            textbutton "|"
            vbox:
                textbutton "Mouse light" action ToggleVariable("mouseLight")
                if mouseLight:
                    textbutton "Light color" action Show("setColorScreen", None, mouseLightColor)
            textbutton "|"
            vbox:
                textbutton "Mouse sun" action ToggleVariable("mouseSun")
                if mouseSun:
                    textbutton "Sun color" action Show("setColorScreen", None, mouseSunColor)
            textbutton "|"
            textbutton "Ambient" action Show("setColorScreen", None, ambientLight)
            textbutton "|"
            textbutton "Add light" action Show("addLightScreen")
            textbutton "|"
            vbox:
                textbutton "DOF"
                bar value VariableValue("depthOfField", 100) xsize 100
            textbutton "|"
            vbox:
                textbutton "Shadow"
                bar value VariableValue("shadowStrength", 100) xsize 100
            textbutton "|"
            vbox:
                textbutton "Fog" action Show("setColorScreen", None, fogColor)
                bar value VariableValue("fogStart", 100) xsize 100
            if fogStart < 100:
                vbox:
                    textbutton ""
                    textbutton "Rain" action ToggleVariable("fogRainEnabled")

image room_normals = "room normal"
image room_depth = "room depth"

label start_deferred_demo:

    python:
        lights = [] #Used to store lights
        ambientLight = rgb(1, 1, 1) #RGB color
        mouseLight = False # Show a spot light at mouse position
        mouseLightColor = rgb(1, 0, 0)
        mouseSun = False #Show a sun light at mouse position
        mouseSunColor = rgb(1, 1, 1)
        fogStart = 100 #From 0 to 100
        fogColor = rgb(0.5, 0.5, 0.5)
        fogRainEnabled = 1 #Rain effect if fog is used
        depthOfField = 0 #From 1 to 100. 0 means disabled
        spriteDepthMerge = False #Demo depth merge
        shadowStrength = 0.0 #From 0 to 100

    scene room

    "This demo shows how to use deferred shading with 2D-images created using a 3D-modelling software."
    "Current background image is a perfectly normal .jpg image that was rendered using Blender."
    "However, Blender (and other similar software) can also produce two other additional images."

    scene room_normals

    "The first one is a normal map which uses image RGB-channels to encode the x, y and z normals of the pixels."

    scene room_depth

    "The other one is a depth map which encodes pixel depth into image RGB-channels."
    "This depth image also stores the alpha channel (windows) that can be used in certain masking effects."

    scene room

    "Together, those two images can be used to create a simple 3D-representation of the normal color image."
    "This makes it possible to add shading effects afterwards. Thus the name: deferred shading."
    "You can use smaller, downscaled images, but beware of shading artifacts, especially near edges."
    "But enough theory, lets show things in action."

    $ ambientLight = rgb(1, 0.5, 0.5)
    $ scene().deferred("room", updateDeferred)

    "You should now see a room background tinted with red color."
    "Current background is now drawn using deferred techniques (if supported and enabled in settings)."
    "Deferred shading requires more from the GPU than simpler effects, but most modern cards should work fine."
    "The next screen you see should be completely black, but don't worry."

    $ ambientLight = rgb(0, 0, 0)

    "Dark, huh? This is because we are now using deferred shading, but there are no lights in the scene."
    "So, lets add a green light on the left side of the scene, near the two lamps."

    $ lights.append(createLight((0.13, 0.5, -0.5), (0, 2, 0)))

    "Ah, better. And one more light at the center, also next to a lamp."

    $ lights.append(createLight((0.57, 0.5, -0.5), (0, 1, 2), behavior=lightBlinkBehavior))

    "There. We also attached a behavior callback function to the lamp which makes it blink like a defective light."
    "The scene is now treated as a 3D box with x, y, and z dimensions."
    "X starts from left (0.0) and increases towards right (1.0)"
    "Y starts from top (0.0) and increases towards bottom (1.0)"
    "Z (the depth) starts from 'near' the screen (0.0) and increases 'away' from the screen (towards 1.0)"
    "The coordinates are all normalized (from 0.0 to 1.0), so the game resolution or aspect ratio can be easily changed."
    "Lights can be placed using 2D-coordinates, in which case the optimal depth is automatically determined."
    "However, you can also specify the light z-location manually if you want better control."
    "Light color values are also normalized RGB tuples, for example (1.0, 0.0, 0.0) is fully red."
    "You can use larger light values than 1.0 if you want brighter lights."
    "Next, you can use the mouse to control one additional light. Note how the shading uses the scene 3D information."

    $ mouseLight = True
    $ preferences.afm_enable = False

    window hide
    pause

    "Lets reset the lights and add normal ambient lightning. You can still use the mouse light."

    $ lights = []
    $ ambientLight = rgb(1, 1, 1)

    "There. Ambient lightning affects everything in the scene at the same intensity."
    "For example, we can tint the overall color of the image..."

    $ ambientLight = rgb(0.5, 0.5, 1)

    "...like this. This can be used to enhance dusk or night scenes. But lets reset things for now."

    $ ambientLight = rgb(1, 1, 1)

    "Next, we will disable the mouse spot light and instead use the mouse to control a large sun light."

    $ ambientLight = rgb(0.2, 0.2, 0.2)
    $ mouseLight = False
    $ mouseSun = True
    $ preferences.afm_enable = False

    window hide
    pause

    "This sun lamp has no distance limit and we offset it towards the screen so it will light the scene well from our point of view."
    "We also removed ambient lightning almost completely. Usually it is useful to keep a small amount of it to avoid completely dark areas."
    "The next effect in line is depth of field (DOF). With it we can put certain areas in the scene out of focus."

    $ ambientLight = rgb(1, 1, 1)
    $ mouseSun = False
    $ depthOfField = 1

    "Now the foreground is in focus and background items are slightly blurred."

    $ depthOfField = 100

    "And now the background should be in focus instead."
    "Another effect you can apply is fog and rain-like distortion, like this."

    $ depthOfField = 0
    $ fogStart = 99

    "See the effect in the window. In outdoor scenes we can bring the effect closer..."

    $ fogStart = 0

    "...like this. However, we have a good roof in this room, so let's remove the effect for now."

    $ fogStart = 100

    "It is also possible to depth merge other sprites into the scene."

    $ spriteDepthMerge = True
    $ deferred("room", updateDeferred, sprite="amy")

    "The sprite is now moved back and forth by changing its depth. Notice how it interacts with the background depth."
    "It is usually easier to use normal, z-ordered images to emulate this behavior, but some effects are only possible like this."

    $ spriteDepthMerge = False

    "Depth information also makes it possible to fake some shadows."
    "In the next scene, move you cursor around the scene and note how the shadows behave."

    $ mouseLight = True
    $ mouseLightColor = rgb(1, 1, 1)
    $ ambientLight = rgb(0.2, 0.2, 0.2)
    $ shadowStrength = 50.0
    $ preferences.afm_enable = False

    window hide
    pause

    "Shadows are done by simple ray stepping, so the effect is relatively heavy and not always very good looking without post-processing."
    "It is usually best to make sure the scene is relatively dark to hide artifacts."
    "Another solution to improve shadow appearance would be to increase step count in the shader."

    $ mouseLight = False
    $ ambientLight = rgb(1, 1, 1)
    $ shadowStrength = 0

    "Next, you can play with some of the parameters using an UI."
    "The current hard limit for lights is [shader.DEFERRED_MAX_LIGHTS]."
    "You can increase the limit, but every light you use will require more from the GPU."
    "Have fun!"

    call screen deferredEditorScreen

    "That was all!"
    return
