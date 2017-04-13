
import renpy
import pygame
import os
import math
import ctypes
import euclid
from OpenGL import GL as gl

FONT_SIZE = 18
FONT = None

def drawText(canvas, text, pos, color, align=-1, background=(128, 128, 128)):
    global FONT
    if FONT is None:
        pygame.font.init()
        FONT = pygame.font.Font(None, FONT_SIZE)

    surface = FONT.render(text, True, color, background)
    if align == 1:
        pos = (pos[0] - surface.get_width(), pos[1])
    canvas.get_surface().blit(surface, pos)
    return surface.get_size()

def drawLinesSafe(canvas, color, connect, points, width=1):
    #Workaround for hang if two points are the same
    safe = []
    i = 0
    while i < len(points):
        p = (round(points[i][0]), round(points[i][1]))
        safe.append(p)
        i2 = i + 1
        while i2 < len(points):
            p2 = (round(points[i2][0]), round(points[i2][1]))
            if p != p2:
                break
            i2 += 1
        i = i2

    if connect and len(safe) > 0:
        first = safe[0]
        safe.append((first[0], first[1] - 1)) #Wrong by one pixel to be sure...

    canvas.lines(color, False, safe, width)

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

def clamp(value, small, large):
    return max(min(value, large), small)

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

def getTexParameteriv(glTex, param):
    result = ctypes.c_int(0)
    gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, param, ctypes.byref(result))
    return result.value

def listFiles():
    results = []
    for root, dirs, files in os.walk(renpy.config.gamedir):
        dirs[:] = [d for d in dirs if not d[0] == "."] #Ignore dot directories
        for f in files:
            match = os.path.join(root, f).replace("\\", "/")
            results.append(match)
    results.sort()
    return results

def scanForFiles(extension):
    results = []
    for f in listFiles():
        if f.split(".")[-1].lower() == extension.lower():
            results.append(f)
    results.sort()
    return results

def findFile(name):
    #First try fast and bundle supporting listing
    for f in renpy.exports.list_files():
        if f.split("/")[-1] == name:
            return f

    #Scan all game directories
    for f in listFiles():
        if f.split("/")[-1] == name:
            return f
    return None

def openFile(path):
    return renpy.exports.file(path)
