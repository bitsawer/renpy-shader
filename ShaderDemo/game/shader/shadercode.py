
VS_2D = """

ATTRIBUTE vec4 inVertex;

VARYING vec2 varUv;

UNIFORM mat4 projection;

void main()
{
    varUv = inVertex.zw;
    gl_Position = projection * vec4(inVertex.xy, 0.0, 1.0);
}
"""

PS_WALK_2D = """

VARYING vec2 varUv;

UNIFORM sampler2D tex0;
UNIFORM sampler2D tex1;
UNIFORM float shownTime;
UNIFORM float animationTime;

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

UNIFORM sampler2D tex0;
UNIFORM sampler2D tex1;

UNIFORM float mouseEnabled;
UNIFORM vec2 mousePos;

UNIFORM vec2 eyeShift;
UNIFORM vec2 mouthShift;

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

VARYING vec2 varUv;

UNIFORM float shownTime;
UNIFORM float animationTime;

void main()
{
    gl_FragColor = applyWind(varUv, shownTime);
}
"""

PS_BEAM_FADE_2D = """

VARYING vec2 varUv;

UNIFORM sampler2D tex0;
UNIFORM float shownTime;

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

VARYING vec2 varUv;

UNIFORM sampler2D tex0;
UNIFORM float blurSize;
UNIFORM float shownTime;
UNIFORM vec2 imageSize;

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

ATTRIBUTE vec4 inPosition;
ATTRIBUTE vec3 inNormal;
ATTRIBUTE vec2 inUv;

VARYING vec3 varNormal;
VARYING vec2 varUv;

UNIFORM mat4 worldMatrix;
UNIFORM mat4 viewMatrix;
UNIFORM mat4 projMatrix;

void main()
{
    varUv = inUv;
    varNormal = inNormal;
    gl_Position = projMatrix * viewMatrix * worldMatrix * inPosition;
}
"""

PS_3D_BAKED = """

VARYING vec2 varUv;

UNIFORM sampler2D tex0;

void main()
{
    gl_FragColor = texture2D(tex0, varUv);
}
"""

PS_3D_NORMALS = """

VARYING vec3 varNormal;
VARYING vec2 varUv;

UNIFORM sampler2D tex0;

void main()
{
    float r = (varNormal.x + 1.0) / 2.0;
    float g = (varNormal.y + 1.0) / 2.0;
    float b = (varNormal.z + 1.0) / 2.0;
    gl_FragColor = vec4(r, g, b, 1.0);
}
"""

VS_SKINNED = """

ATTRIBUTE vec2 inVertex;
ATTRIBUTE vec2 inUv;
ATTRIBUTE vec4 inBoneWeights;
ATTRIBUTE vec4 inBoneIndices;

VARYING vec2 varUv;
VARYING float varAlpha;

UNIFORM mat4 projection;
UNIFORM mat4 boneMatrices[MAX_BONES];
UNIFORM vec2 screenSize;
UNIFORM float shownTime;

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

VARYING vec2 varUv;
VARYING float varAlpha;

UNIFORM float wireFrame;
UNIFORM float shownTime;

void main()
{
    vec4 color = applyWind(varUv, shownTime);

    color.rgb *= 1.0 - wireFrame;
    color.a = (color.a * varAlpha) + wireFrame;
    gl_FragColor = color;
}
"""

DEFERRED_MAX_LIGHTS = 8

PS_DEFERRED = """

VARYING vec2 varUv;

UNIFORM sampler2D tex0;
UNIFORM sampler2D depthMap;
UNIFORM sampler2D normalMap;
UNIFORM sampler2D sprite;

UNIFORM vec2 imageSize;
UNIFORM vec2 mousePos;
UNIFORM float shownTime;

UNIFORM vec2 fogRange;
UNIFORM float fogRainEnabled;
UNIFORM vec3 fogColor;
UNIFORM vec2 dofRange;
UNIFORM vec3 ambientLight;
UNIFORM vec4 spriteArea;
UNIFORM float spriteDepth;
UNIFORM float shadowStrength;

UNIFORM mat4 lights[MAX_LIGHTS];
UNIFORM float lightCount;

const float minLightness = 0.25;
const float sunOffsetZ = -0.5;

vec2 readDepthAlpha(vec2 uv) {
    vec4 depth = texture2D(depthMap, uv);
    return vec2((depth.r + depth.g + depth.b) / 3.0, depth.a);
}

float remap(float value, float oldMin, float oldMax, float newMin, float newMax) {
    return (((value - oldMin) * (newMax - newMin)) / (oldMax - oldMin)) + newMin;
}

bool isPixelComposited(vec3 pos) {
    if (pos.z >= spriteDepth && spriteDepth > 0.0) {
        if (pos.x > spriteArea.x && pos.x < spriteArea.y && pos.y > spriteArea.z && pos.y < spriteArea.w) {
            return true;
        }
    }
    return false;
}

vec4 pixelCompositeLookup(vec2 uv) {
    float u = remap(uv.x, spriteArea.x, spriteArea.y, 0.0, 1.0);
    float v = remap(uv.y, spriteArea.z, spriteArea.w, 0.0, 1.0);
    return texture2D(sprite, vec2(u, v));
}

vec4 zComposite(vec3 pos, vec4 color, vec2 uv) {
    if (isPixelComposited(pos)) {
        vec4 diffuse = pixelCompositeLookup(uv);
        return mix(color, vec4(diffuse.rgb, 1.0), diffuse.a);
    }
    return color;
}

vec4 pixelPosRaw(vec2 uv) {
    vec2 za = readDepthAlpha(uv);
    return vec4(uv, za.x, za.y);
}

vec4 pixelPos(vec2 uv) {
    vec4 pos = pixelPosRaw(uv);
    if (isPixelComposited(pos.xyz) && pixelCompositeLookup(uv).a > 0.1) {
        return vec4(uv, spriteDepth, 1.0);
    }
    return pos;
}

vec3 pixelNormal(vec3 pos) {
    if (isPixelComposited(pos) && pos.z == spriteDepth) {
        return normalize(vec3(0.0, 0.0, 1.0));
    }

    vec3 normal = texture2D(normalMap, pos.xy).rgb;
    return normalize(vec3(
        (normal.x * 2.0 - 1.0),
        (normal.y * 2.0 - 1.0),
        (normal.z * 2.0 - 0.0) //Z is only half
    ));
}

vec3 unproject(vec3 pos) {
    vec4 screen;
    screen.xy = pos.xy * 2.0 - 1.0;
    screen.z = pos.z;
    screen.w = 1.0;

    screen.x *= imageSize.x / imageSize.y;

    //vec4 world = cameraMatrix * screen;
    //world /= world.w;
    //return world.xyz;

    return screen.xyz;
}

vec3 pointLight(vec3 pos, vec3 normal, vec3 lightPos, vec3 color, float dist) {
    vec3 light = pixelPosRaw(lightPos.xy).xyz;
    light.z += lightPos.z;

    vec3 posWorld = unproject(pos);
    vec3 lightWorld = unproject(light);

    vec3 delta = normalize(posWorld - lightWorld);
    delta.x = -delta.x;

    float strength = max(dot(normal, delta), 0.1);
    float att = dist < 0.0 ? 1.0 : max(1.0 - (distance(posWorld, lightWorld) * 1.0), 0.0);
    //float att = 1.0 - min( distance(posWorld, lightWorld) / dist, 1.0);

    return color * (strength * att);
}

float rand(vec2 co){
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

float shadow(vec3 pos, float alpha, vec3 light, float seed) {
    //light.z += sunOffsetZ * 0.1;
    light.z -= 0.1;

    const int steps = 10;
    float stepJitter = rand(pos.xy + vec2(seed, seed * seed)) * 1.0;

    for (int i=0; i < steps; ++i) {
        vec3 step = mix(pos, light, i / float(steps) * stepJitter);

        float jitter = rand(step.xy + pos.xy) * (step.z * 0.005);
        step.x += jitter;
        step.y += jitter;

        vec4 stepPos = pixelPos(step.xy);
        stepPos.z *= 1.05;
        float bias = rand(step.xy) * 0.01; //0;
        float finalZ = step.z - bias;

        if (finalZ > stepPos.z) {
            return 1.0 - max(alpha, 0.1) * shadowStrength;
        }
    }
    return 1.0;
}

float fog(vec3 pos, float alpha, float start, float end) {
    float depth = pos.z - (alpha * 0.1); //Window rain etc. better
    float f = 1.0 - clamp((end - depth) / (end - start), 0.0, 1.0);

    if (fogRainEnabled != 0.0) {
        return f * (rand(vec2(pos.x * depth, shownTime)) * 0.2 + 1.0);
    }
    return f;
}

vec4 depthOfField(vec4 data) {
    vec2 uv = data.xy;
    float focus = dofRange.x; // pixelPos(mousePos).z;
    if (focus > 0.0) {
        float depth = 1.0;
        float distance = abs((focus - data.z) * depth)  * 2.5;

        vec2 offset = vec2(2.0 / imageSize.x * distance, 2.0 / imageSize.y * distance);
        vec4 color = texture2D(tex0, uv);
        color += texture2D(tex0, uv + offset * vec2(0, 1));
        color += texture2D(tex0, uv + offset * vec2(-1, -1));
        color += texture2D(tex0, uv + offset * vec2(1, -1));
        return color / 4.0;
    }
    else {
        return texture2D(tex0, uv);
    }
}

void main()
{
    vec4 data = pixelPos(varUv);
    vec3 normal = pixelNormal(data.xyz);
    vec4 color = depthOfField(data);
    vec3 pos = data.xyz;
    float alpha = data.w;

    if (spriteDepth >= 0.0) {
        color.rgba = zComposite(pos, color, varUv).rgba;
    }

    vec3 light = ambientLight;
    for (int i=0; i < lightCount; ++i) {
        mat4 lightData = lights[i];
        vec3 lPos = vec3(lightData[0][0], lightData[1][0], lightData[2][0]);
        vec3 lColor = vec3(lightData[0][1], lightData[1][1], lightData[2][1]);
        float dist = lightData[0][2];
        light.rgb += pointLight(pos, normal, lPos, lColor, dist);
    }

    if (shadowStrength > 0.0) {
        vec3 mouse = pixelPos(mousePos).xyz;
        float w = 2.0 / imageSize.x;
        float h = 2.0 / imageSize.y;

        float strength = 1.0;
        strength *= shadow(pos, alpha, mouse, 0);
        strength *= shadow(pos, alpha, mouse + vec3(w, 0.0, 0.0), 1);
        strength *= shadow(pos, alpha, mouse + vec3(0.0, h, 0.0), 2);
        strength *= shadow(pos, alpha, mouse + vec3(w, h, 0.0), 3);
        color.rgb *= strength;
    }

    vec4 result = color * vec4(light.rgb, 1.0);

    if (abs(fogRange.x - fogRange.y) > 0.0) {
        result.rgb = mix(result.rgb, light * fogColor, fog(pos, alpha, fogRange.x, fogRange.y));
    }

    /*
    if (pos.z >= 0.5 && pos.z <= 0.51) {
        result.rgb += vec3(1.0, 0, 0);
    }*/

    gl_FragColor = result;
}

""".replace("MAX_LIGHTS", str(DEFERRED_MAX_LIGHTS))
