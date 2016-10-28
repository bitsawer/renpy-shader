
image doll = LiveComposite(
    (800, 1000),
    (0, 0), "doll base.png",
    (0, 0), "doll hair.png",
    (249, 318), "doll skirt.png"
)

screen skinnedScreen(name, pixelShader, textures={}, uniforms={}, update=None, xalign=0.5, yalign=1.0):
    modal False
    add ShaderDisplayable(shader.MODE_SKINNED, name, shader.VS_SKINNED, pixelShader, textures, uniforms, None, update):
        xalign xalign
        yalign yalign

label start_skinned:
    scene room
    #show doll

    call screen skinnedScreen("doll", shader.PS_SKINNED, {"tex1": "amy influence"}, _tag="amy", _layer="amy")

    "The End"
