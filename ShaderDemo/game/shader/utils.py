
import os
import math
import ctypes
import euclid
from OpenGL import GL as gl

def createTransform2d():
    eye = euclid.Vector3(0, 0, 1)
    at = euclid.Vector3(0, 0, 0)
    up = euclid.Vector3(0, 1, 0)
    view = euclid.Matrix4.new_look_at(eye, at, up)
    perspective = euclid.Matrix4.new_perspective(math.radians(90), 1.0, 0.1, 10)
    return perspective * view

def createPerspective(fov, width, height, zMin, zMax):
    #TODO This negates fov to flip y-axis in the framebuffer.
    return euclid.Matrix4.new_perspective(-math.radians(fov), width / float(height), zMin, zMax)

def createPerspectiveBlender(lens, xResolution, yResolution, width, height, zMin, zMax):
    factor = lens / 32.0
    ratio = xResolution / float(yResolution)
    fov = math.atan(0.5 / ratio / factor)
    fov = fov * 360 / math.pi
    return createPerspective(fov, width, height, zMin, zMax)

def createPerspectiveOrtho(left, right, bottom, top, near, far):
    projection = [0] * 16
    projection[0] = 2 / (right - left)
    projection[4] = 0
    projection[8] = 0
    projection[12] = -(right + left) / (right - left)

    projection[1] = 0
    projection[5] = 2 / (top - bottom)
    projection[9] = 0
    projection[13] = -(top + bottom) / (top - bottom)

    projection[2] = 0
    projection[6] = 0
    projection[10] = -2 / (far - near)
    projection[14] = -(far + near) / (far - near)

    projection[3] = 0
    projection[7] = 0
    projection[11] = 0
    projection[15] = 1

    return projection

def interpolate(a, b, s):
    #Simple linear interpolation
    return a + s * (b - a)

def interpolate2d(p1, p2, s):
    x = interpolate(p1[0], p2[0], s)
    y = interpolate(p1[1], p2[1], s)
    return (x, y)

def interpolate3d(p1, p2, s):
    x = interpolate(p1[0], p2[0], s)
    y = interpolate(p1[1], p2[1], s)
    z = interpolate(p1[2], p2[2], s)
    return (x, y, z)

def makeFloatArray(elements, count):
    raw = (gl.GLfloat * (len(elements) * count))()
    for i in range(len(elements)):
        v = elements[i]
        for x in range(count):
            raw[(i * count) + x] = v[x]
    return raw

def matrixToList(m):
    return [m.a, m.e, m.i, m.m,
            m.b, m.f, m.j, m.n,
            m.c, m.g, m.k, m.o,
            m.d, m.h, m.l, m.p]

def glTextureFromSurface(surface):
    width = surface.get_width()
    height = surface.get_height()

    textureId = (gl.GLuint * 1) ()

    surface.lock()

    BYTEP = ctypes.POINTER(ctypes.c_ubyte)
    ptr = ctypes.cast(surface._pixels_address, BYTEP)

    gl.glGenTextures(1, textureId)
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glActiveTexture(gl.GL_TEXTURE0)

    gl.glPixelStorei(gl.GL_UNPACK_ROW_LENGTH, surface.get_pitch() // surface.get_bytesize())
    gl.glBindTexture(gl.GL_TEXTURE_2D, textureId[0])
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, ptr)
    gl.glBindTexture(gl.GL_TEXTURE_2D, 0);
    gl.glPixelStorei(gl.GL_UNPACK_ROW_LENGTH, 0)

    surface.unlock()

    return textureId[0], width, height

def getTexParameteriv(glTex, param):
    result = ctypes.c_int(0)
    gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, param, ctypes.byref(result))
    return result.value

def scanForFiles(path, extension):
    results = []
    for root, folders, files in os.walk(path):
        for f in files:
            if f.split(".")[-1].lower() == extension.lower():
                results.append(os.path.join(root, f))
    return results

class Shader:
    def __init__(self, vsCode, psCode):
        self.handle = gl.glCreateProgram()
        self.linked = False

        self.createShader(vsCode, gl.GL_VERTEX_SHADER)
        self.createShader(psCode, gl.GL_FRAGMENT_SHADER)

        self.link()

        if not self.linked:
            raise RuntimeError("Shader not linked")

    def createShader(self, shaderCode, type):
        shader = gl.glCreateShader(type)
        gl.glShaderSource(shader, shaderCode)
        gl.glCompileShader(shader)

        status = ctypes.c_int(0)
        gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS, ctypes.byref(status))

        if not status:
            raise RuntimeError("Compile error: %s" % gl.glGetShaderInfoLog(shader))
        else:
            gl.glAttachShader(self.handle, shader)

    def link(self):
        gl.glLinkProgram(self.handle)

        status = ctypes.c_int(0)
        gl.glGetProgramiv(self.handle, gl.GL_LINK_STATUS, ctypes.byref(status))

        if not status:
            raise RuntimeError("Link error: %s" % gl.glGetShaderInfoLog(shader))
        else:
            self.linked = True

    def free(self):
        if self.handle:
            gl.glDeleteProgram(self.handle)
            self.handle = 0
        self.linked = False

    def bind(self):
        gl.glUseProgram(self.handle)

    def unbind(self):
        gl.glUseProgram(0)

    def uniformf(self, name, *values):
        {1 : gl.glUniform1f,
         2 : gl.glUniform2f,
         3 : gl.glUniform3f,
         4 : gl.glUniform4f
        }[len(values)](gl.glGetUniformLocation(self.handle, name), *values)

    def uniformi(self, name, *values):
        {1 : gl.glUniform1i,
         2 : gl.glUniform2i,
         3 : gl.glUniform3i,
         4 : gl.glUniform4i
        }[len(values)](gl.glGetUniformLocation(self.handle, name), *values)

    def uniformMatrix4f(self, name, matrix):
        loc = gl.glGetUniformLocation(self.handle, name)
        gl.glUniformMatrix4fv(loc, 1, False, (ctypes.c_float * 16)(*matrix))

    def uniformMatrix4fArray(self, name, values):
        loc = gl.glGetUniformLocation(self.handle, name)
        count = len(values) / 16
        gl.glUniformMatrix4fv(loc, count, False, (ctypes.c_float * len(values))(*values))
