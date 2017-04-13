
VS_2D = """

in vec4 inVertex;

out vec2 varUv;

uniform mat4 projection;

void main()
{
    varUv = inVertex.zw;
    gl_Position = projection * vec4(inVertex.xy, 0.0, 1.0);
}
"""

PS_WALK_2D = """

in vec2 varUv;

uniform sampler2D tex0;
uniform sampler2D tex1;
uniform float shownTime;
uniform float animationTime;

void main()
{
    vec4 color1 = texture2D(tex0, varUv);
    vec4 weights = texture2D(tex1, varUv);
    float influence = weights.r;

    if (influence > 0.0) {
        float speed = sin(animationTime * 5.0);
        float xShift = sin(speed + varUv.x * varUv.y * 10) * influence * 0.01;
        float yShift = cos(speed + varUv.x * varUv.y * 5) * influence * 0.01;

        gl_FragColor = texture2D(tex0, varUv + vec2(xShift, yShift));
    }
    else {
        gl_FragColor = color1;
    }
}
"""

LIB_WIND = """

uniform sampler2D tex0;
uniform sampler2D tex1;

uniform float mouseEnabled;
uniform vec2 mousePos;

uniform vec2 eyeShift;
uniform vec2 mouthShift;

const float WIND_SPEED = 5.0;
const float DISTANCE = 0.0075;
const float FLUIDNESS = 0.75;
const float TURBULENCE = 15.0;
const float FADE_IN = 1.0; //In seconds

vec4 applyWind(vec2 uv, float time)
{
    float movement = 0.1;

    vec4 weights = texture2D(tex1, uv);

    if (weights.g > 0.0) {
        vec2 eyeCoords = uv + (eyeShift * weights.g);
        if (texture2D(tex1, eyeCoords).g > 0.0) {
            return texture2D(tex0, eyeCoords);
        }
    }

    if (weights.b > 0.0) {
        vec2 smileCoords = uv + (mouthShift * weights.b);
        if (texture2D(tex1, smileCoords).b > 0.0) {
            return texture2D(tex0, smileCoords);
        }
    }

    float timeFade = min(time / FADE_IN, 1.0);
    float influence = weights.r * (0.5 + (movement * 1.25)) * timeFade;

    if (mouseEnabled > 0.0) {
        //Use mouse position to set influence
        influence = (1.0 - distance(mousePos, uv) * 5.0) * 2.0;
    }

    if (influence > 0.0) {
        float modifier = sin(uv.x + time) / 2.0 + 1.5;
        float xShift = sin((uv.y * 20.0) * FLUIDNESS + (time * WIND_SPEED)) * modifier * influence * DISTANCE;
        float yShift = cos((uv.x * 50.0) * FLUIDNESS + (time * WIND_SPEED)) * influence * DISTANCE;
        return texture2D(tex0, uv + vec2(xShift, yShift));
    }
    else {
        return texture2D(tex0, uv);
    }
}
"""

PS_WIND_2D = LIB_WIND + """

in vec2 varUv;

uniform float shownTime;
uniform float animationTime;

void main()
{
    gl_FragColor = applyWind(varUv, shownTime);
}
"""

PS_BEAM_FADE_2D = """

in vec2 varUv;

uniform sampler2D tex0;
uniform float shownTime;

const float intensity = 1.0;

float rand(vec2 co){
    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

void main()
{
    float f = rand(vec2(0.0, varUv.y)) * rand(vec2(0.0, gl_FragCoord.y + shownTime));
    float fade = shownTime / 2.0;

    vec4 color = vec4(-f * 0.5, f * 0.5, f, 0.0);
    vec4 diffuse = texture2D(tex0, varUv);
    gl_FragColor = vec4((diffuse * gl_Color + color * intensity).rgb, max(diffuse.a - fade, 0.0));
}
"""

PS_BLUR_2D = """

in vec2 varUv;

uniform sampler2D tex0;
uniform float blurSize;
uniform float shownTime;
uniform vec2 imageSize;

vec4 blur(sampler2D image, vec2 uv, vec2 resolution, vec2 direction) {
    vec4 color = vec4(0.0);
    vec2 off1 = vec2(1.411764705882353) * direction;
    vec2 off2 = vec2(3.2941176470588234) * direction;
    vec2 off3 = vec2(5.176470588235294) * direction;
    color += texture2D(image, uv) * 0.1964825501511404;
    color += texture2D(image, uv + (off1 / resolution)) * 0.2969069646728344;
    color += texture2D(image, uv - (off1 / resolution)) * 0.2969069646728344;
    color += texture2D(image, uv + (off2 / resolution)) * 0.09447039785044732;
    color += texture2D(image, uv - (off2 / resolution)) * 0.09447039785044732;
    color += texture2D(image, uv + (off3 / resolution)) * 0.010381362401148057;
    color += texture2D(image, uv - (off3 / resolution)) * 0.010381362401148057;
    return color;
}

void main()
{
    gl_FragColor = blur(tex0, varUv, imageSize.xy, vec2(blurSize, blurSize));
}
"""

VS_3D = """

in vec4 inPosition;
in vec3 inNormal;
in vec2 inUv;

out vec3 varNormal;
out vec2 varUv;

uniform mat4 worldMatrix;
uniform mat4 viewMatrix;
uniform mat4 projMatrix;

void main()
{
    varUv = inUv;
    varNormal = inNormal;
    gl_Position = projMatrix * viewMatrix * worldMatrix * inPosition;
}
"""

PS_3D_BAKED = """

in vec2 varUv;

uniform sampler2D tex0;

void main()
{
    gl_FragColor = texture2D(tex0, varUv);
}
"""

PS_3D_NORMALS = """

in vec3 varNormal;
in vec2 varUv;

uniform sampler2D tex0;

void main()
{
    float r = (varNormal.x + 1.0) / 2.0;
    float g = (varNormal.y + 1.0) / 2.0;
    float b = (varNormal.z + 1.0) / 2.0;
    gl_FragColor = vec4(r, g, b, 1.0);
}
"""

VS_SKINNED = """

in vec2 inVertex;
in vec2 inUv;
in vec4 inBoneWeights;
in vec4 inBoneIndices;

out vec2 varUv;
out float varAlpha;

uniform mat4 projection;
uniform mat4 boneMatrices[MAX_BONES];
uniform vec2 screenSize;
uniform float shownTime;

vec2 toScreen(vec2 point)
{
    return vec2(point.x / (screenSize.x / 2.0) - 1.0, point.y / (screenSize.y / 2.0) - 1.0);
}

void main()
{
    varUv = inUv;

    vec2 pos = vec2(0.0, 0.0);
    float transparency = 0.0;
    vec4 boneWeights = inBoneWeights;
    ivec4 boneIndex = ivec4(inBoneIndices);

    for (int i = 0; i < 4; i++) {
        mat4 boneMatrix = boneMatrices[boneIndex.x];
        pos += (boneMatrix * vec4(inVertex, 0.0, 1.0) * boneWeights.x).xy;

        //Apply damping
        vec2 boneDelta = vec2(boneMatrix[0][3], boneMatrix[1][3]);
        pos += (boneDelta * boneWeights.x) * boneMatrix[2][3];

        //Apply transparency
        transparency += boneMatrix[3][3] * boneWeights.x;

        boneWeights = boneWeights.yzwx;
        boneIndex = boneIndex.yzwx;
    }
    varAlpha = max(1.0 - transparency, 0.0);

    gl_Position = projection * vec4(toScreen(pos.xy), 0.0, 1.0);
}
"""

PS_SKINNED = LIB_WIND + """

in vec2 varUv;
in float varAlpha;

uniform float wireFrame;
uniform float shownTime;

void main()
{
    vec4 color = applyWind(varUv, shownTime);

    color.rgb *= 1.0 - wireFrame;
    color.a = (color.a * varAlpha) + wireFrame;

    gl_FragColor = color;
}
"""
