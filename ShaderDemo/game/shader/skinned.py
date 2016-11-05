
import math
import ctypes
import json
from OpenGL import GL as gl

import rendering
import euclid
import geometry
import delaunay

VERSION = 1

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
        self.wireFrame = False
        self.color = (0, 0, 0) #Not serialized

        self.vertices = None
        self.indices = None
        self.weights = None

        self.points = []
        self.triangles = []

    def updateVertices(self):
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

    def updateWeights(self):
        if self.indices:
            weights = [1.0] * (len(self.indices) / 2)
            self.weights = {self.name: (gl.GLfloat * len(weights))(*weights)}

    def updatePoints(self, surface):
        points = geometry.findEdgePixelsOrdered(surface)
        simplified = geometry.simplifyEdgePixels(points, 10)
        offseted = geometry.offsetPolygon(simplified, -5)
        self.points = geometry.simplifyEdgePixels(offseted, 40)

    def triangulate(self):
        pointsSegments = delaunay.ToPointsAndSegments()
        pointsSegments.add_polygon([self.points])
        triangulation = delaunay.triangulate(pointsSegments.points, pointsSegments.infos, pointsSegments.segments)

        expanded = geometry.offsetPolygon(self.points, -1)
        shorten = 0.5

        self.triangles = []
        for tri in delaunay.TriangleIterator(triangulation, True):
            a, b, c = tri.vertices

            inside = 0
            for line in [(a, b), (b, c), (c, a)]:
                short1 = shortenLine(line[0], line[1], shorten)
                short2 = shortenLine(line[1], line[0], shorten)
                if geometry.insidePolygon(short1[0], short1[1], expanded) and geometry.insidePolygon(short2[0], short2[1], expanded):
                    inside += 1

            if inside >= 2:
                self.triangles.append((a, b, c))


def shortenLine(a, b, relative):
    x1, y1 = a
    x2, y2 = b

    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    if length > 0:
        dx /= length
        dy /= length

    dx *= length - (length * relative)
    dy *= length - (length * relative)
    x3 = x1 + dx
    y3 = y1 + dy
    return x3, y3

class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (Bone, Image)):
            return obj.__dict__
        elif isinstance(obj, euclid.Vector3):
            return (obj.x, obj.y, obj.z)
        elif isinstance(obj, ctypes.Array):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

def saveToFile(bones, path):
    data = {
        "version": VERSION,
        "bones": bones
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=1, cls=JsonEncoder, separators=(",", ": "), sort_keys=True)

def loadFromFile(path):
    data = None
    with open(path, "r") as f:
        data = json.load(f)

    if data["version"] != VERSION:
        raise RuntimeError("Invalid version, should be %i" % VERSION)

    bones = {}
    for name, raw in data["bones"].items():
        bone = Bone(raw["name"])
        bone.children = raw["children"]
        bone.parent = raw["parent"]

        image = raw.get("image")
        if image:
            bone.image = Image(image["name"], image["x"], image["y"], image["width"], image["height"])

        bone.pos = raw["pos"]
        bone.pivot = raw["pivot"]
        bone.rotation = euclid.Vector3(*raw["rotation"])
        bone.scale = euclid.Vector3(*raw["scale"])
        bone.zOrder = raw["zOrder"]
        bone.visible = raw["visible"]
        bone.wireFrame = raw["wireFrame"]

        verts = raw.get("vertices")
        if verts:
            bone.vertices = (gl.GLfloat * len(verts))(*verts)

        indices = raw.get("indices")
        if indices:
            bone.indices = (gl.GLuint * len(indices))(*indices)

        bones[bone.name] = bone

    return bones
