
import json
import ctypes
from OpenGL import GL as gl

import rendering
import euclid
import geometry

class Image:
    def __init__(self, name, x, y, width, height):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height

class Bone:
    def __init__(self, name):
        self.name = name
        self.children = []
        self.parent = None
        self.image = None
        self.pos = (0, 0)
        self.pivot = (0, 0)
        self.rotation = euclid.Vector3(0, 0, 0)
        self.scale = euclid.Vector3(1, 1, 1)
        self.zOrder = -1
        self.visible = True

        self.vertices = None
        self.indices = None
        self.wireFrame = False

    def updateQuad(self, surface):
        w = self.image.width
        h = self.image.height

        gridSize = 10
        vertices, uvs, indices = geometry.createGrid((0, 0, w, h), None, gridSize, gridSize)

        verts = []
        for i in range(len(vertices)):
            verts.append(vertices[i][0])
            verts.append(vertices[i][1])

            xUv = uvs[i][0]
            yUv = uvs[i][1]
            verts.append(xUv)
            verts.append(yUv)

        self.vertices = (gl.GLfloat * len(verts))(*verts)
        self.indices = (gl.GLuint * len(indices))(*indices)

class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (Bone, Image)):
            return obj.__dict__
        elif isinstance(obj, euclid.Vector3):
            return (obj.x, obj.y, obj.z)
        elif isinstance(obj, ctypes.Array):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

def saveBonesToFile(bones, path):
    with open(path, "w") as f:
        json.dump(bones, f, indent=2, cls=JsonEncoder)

def loadBonesFromFile(path):
    data = None
    with open(path, "r") as f:
        data = json.load(f)

    bones = {}

    return bones
