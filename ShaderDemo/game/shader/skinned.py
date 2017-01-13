
import math
import ctypes
import json
from OpenGL import GL as gl

import rendering
import euclid
import geometry
import delaunay

VERSION = 1

def makeArray(tp, values):
    return (tp * len(values))(*values)

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
        self.uvs = None
        self.indices = None
        self.boneWeights = None
        self.boneIndices = None

        self.points = []
        self.triangles = []

    def updateVerticesFromTriangles(self):
        w = self.image.width
        h = self.image.height

        verts = []
        uvs = []
        indices = []

        for tri in self.triangles:
            for v in tri:
                xUv = v[0] / float(w)
                yUv = v[1] / float(h)
                verts.extend([v[0], v[1]])
                uvs.extend([xUv, yUv])
                indices.append(len(verts) / 2 - 1)

        vCount = len(verts) / 2 / 3
        if vCount != len(self.triangles):
            raise RuntimeError("Invalid vertex count: %i of %i" % (vCount, len(self.triangles)))

        self.vertices = makeArray(gl.GLfloat, verts)
        self.uvs = makeArray(gl.GLfloat, uvs)
        self.indices = makeArray(gl.GLuint, indices)

    def moveVertices(self, offset):
        if self.vertices:
            for i in range(0, len(self.vertices), 2):
                self.vertices[i] = self.vertices[i] + offset[0]
                self.vertices[i + 1] = self.vertices[i + 1] + offset[1]

    def updateWeights(self, index, transforms):
        if self.vertices:
            mapping = {}
            for i, trans in enumerate(transforms):
                trans.index = i
                mapping[trans.bone.name] = trans

            weights = []
            indices = []
            for i in range(0, len(self.vertices), 2):
                x = self.vertices[i]
                y = self.vertices[i + 1]

                nearby = findBoneInfluences((x, y), mapping)
                if len(nearby) > 0:
                    nearest = nearby[0][1]
                    weights.extend([1.0, 0.0, 0.0, 0.0])
                    indices.extend([float(nearest.index), 0.0, 0.0, 0.0])
                else:
                    weights.extend([1.0, 0.0, 0.0, 0.0])
                    indices.extend([float(index), 0.0, 0.0, 0.0])

            #TODO bone index must never change at the moment...
            self.boneWeights = makeArray(gl.GLfloat, weights)
            self.boneIndices = makeArray(gl.GLfloat, indices)

    def updatePoints(self, surface):
        points = geometry.findEdgePixelsOrdered(surface)
        simplified = geometry.simplifyEdgePixels(points, 10)
        offseted = geometry.offsetPolygon(simplified, -5)
        self.points = geometry.simplifyEdgePixels(offseted, 40)

    def triangulate(self):
        pointsSegments = delaunay.ToPointsAndSegments()
        pointsSegments.add_polygon([self.points])
        triangulation = delaunay.triangulate(pointsSegments.points, pointsSegments.infos, pointsSegments.segments)

        expanded = geometry.offsetPolygon(self.points, -1) #TODO 0 better, do nothing?
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
                self.triangles.append(((a[0], a[1]), (b[0], b[1]), (c[0], c[1])))

def findBoneInfluences(vertex, transforms):
    distances = []
    for trans in transforms.values():
        if not trans.bone.parent:
            #Skip root bone
            continue

        start = trans.bone.pivot
        for child in trans.bone.children:
            childTrans = transforms[child]
            end = childTrans.bone.pivot
            distances.append((geometry.pointToLineDistance(vertex, start, end), trans))

    distances.sort(key=lambda x: x[0])
    return distances[:4]

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

def _getArray(tp, obj, key):
    data = obj.get(key)
    if data:
        return makeArray(tp, data)
    return None

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

        bone.vertices = _getArray(gl.GLfloat, raw, "vertices")
        bone.uvs = _getArray(gl.GLfloat, raw, "uvs")
        bone.indices = _getArray(gl.GLuint, raw, "indices")
        bone.boneWeights = _getArray(gl.GLfloat, raw, "boneWeights")
        bone.boneIndices = _getArray(gl.GLfloat, raw, "boneIndices")

        bones[bone.name] = bone

    return bones
