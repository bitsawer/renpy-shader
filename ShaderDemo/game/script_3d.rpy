
#Generic screen for showing 3d-content.

screen shaderScreen3d(name, create=None, update=None, uniforms={}, pixelShader=shader.PS_3D_BAKED):
    modal False
    add ShaderDisplayable(shader.MODE_3D, name, shader.VS_3D, pixelShader, None, uniforms, create, update):
        xalign 0.5
        yalign 0.5

init python:
    import os
    import shader
    from shader import euclid

    TAG_ROOM = "room scene"
    TAG_CUBE = "cube"

    def create3dCube(context):
        renderer = context.renderer
        renderer.loadModel(TAG_CUBE, os.path.join(renpy.config.gamedir, "mesh", "cube.obj"), {})

    def update3dCube(context):
        cube = context.renderer.getModel(TAG_CUBE)
        cube.matrix = euclid.Matrix4()
        cube.matrix.rotatez(math.sin(context.shownTime))
        cube.matrix.rotatey(math.cos(context.shownTime))

    def create3dRoomScene(context):
        #This function will be called when the scene renderer has been created or reset.
        #For example showing the screen and changing the window size etc. can trigger this.
        renderer = context.renderer
        textures = {shader.TEX0: "room baked.jpg"}
        renderer.loadModel(TAG_ROOM, os.path.join(renpy.config.gamedir, "mesh", "room.obj"), textures)

    def update3dRoomScene(context):
        #This function will be called when we need to update the scene for rendering.
        #We can hardcode the matching camera settings that were used
        #to render the actual static background image. In more serious use
        #this information should be exported and imported along with the models.
        eye = euclid.Vector3(1.78016, 0.91875, -3.4134)
        lookAt = euclid.Vector3(0, eye.y, -1.2)
        up = euclid.Vector3(0, 1, 0)
        zMin = 0.1
        zMax = 100.0

        if cameraDrive:
            eye, lookAt = animate3dRoomCameraDrive(context, eye, lookAt)

        if cameraUserControl:
            eye, lookAt = handle3dUserInput(context, eye, lookAt)

        if True:
            #Values taken from the rendered Blender scene camera.
            lens = 30
            #Use the rendered image size used so the 3D-view matches up to the 2D-image.
            #In most cases they would be the same as renpy.config.screen_width etc. but
            #they don't have to be. You could also use an aspect ratio instead of explicit size.
            xResolution = 1280
            yResolution = 720
            projection = shader.utils.createPerspectiveBlender(lens, xResolution, yResolution,
                context.width, context.height, zMin, zMax)
        else:
            #If you have no camera information, use whatever looks good.
            fieldOfView = 34
            projection = shader.utils.createPerspective(fieldOfView, context.width, context.height, zMin, zMax)

        #Use our custom view and projection matrices
        view = euclid.Matrix4.new_look_at(eye, lookAt, up)
        context.uniforms[shader.VIEW_MATRIX] = view
        context.uniforms[shader.PROJ_MATRIX] = projection

    def animate3dRoomCameraDrive(context, eye, lookAt):
        store = context.store
        start = store.get("start")
        if start:
            animationTimeSeconds = 2.0
            delta = min((context.shownTime - start) / animationTimeSeconds, 1.0)

            eyeTarget = euclid.Vector3(-2, 1, -1)
            atTarget = eyeTarget + euclid.Vector3(0.4, 0.0, 0.5)
            eye = shader.utils.interpolate(eye, eyeTarget, delta)
            lookAt = shader.utils.interpolate(lookAt, atTarget, delta)
        else:
            store["start"] = context.shownTime
        return eye, lookAt

    def handle3dUserInput(context, eye, lookAt):
        return eye, lookAt
