
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

IGNORES = [
    "color",
    "uvs",
    "points",
    "triangles",
]

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

    def getAllChildren(self, bones, results=None):
        if not results:
            results = []

        for name in self.children:
            child = bones[name]
            results.append(child)
            child.getAllChildren(bones, results)
        return results

    def getTriangleIndices(self):
        triangles = []
        if self.indices:
            for i in range(0, len(self.indices), 3):
                triangles.append((self.indices[i], self.indices[i + 1], self.indices[i + 2]))
        return triangles

    def getVertex(self, index):
        return (self.vertices[index * 2], self.vertices[index * 2 + 1])

    def subdivide(self, maxSize):
        if self.vertices:
            verts = self.vertices[:]
            indices = self.indices[:]

            for i, (a, b, c) in enumerate(self.getTriangleIndices()):
                v1 = self.getVertex(a)
                v2 = self.getVertex(b)
                v3 = self.getVertex(c)
                area = geometry.triangleArea(v1, v2, v3)
                if area > maxSize: #TODO Also if triangle has a too long side
                    self.subdivideTriangle(a, b, c, verts, indices, i)

            self.vertices = makeArray(gl.GLfloat, verts)
            self.indices = makeArray(gl.GLuint, [x for x in indices if x is not None])

    def subdivideTriangle(self, a, b, c, verts, indices, index):
        v1 = self.getVertex(a)
        v2 = self.getVertex(b)
        v3 = self.getVertex(c)

        new1 = geometry.interpolate2d(v1, v2, 0.5)
        new2 = geometry.interpolate2d(v2, v3, 0.5)
        new3 = geometry.interpolate2d(v3, v1, 0.5)

        indices[index * 3] = None
        indices[index * 3 + 1] = None
        indices[index * 3 + 2] = None

        for v in [new1, new2, new3]:
            verts.extend(v)

        vertexCount = len(verts) // 2
        d = vertexCount - 3
        e = vertexCount - 2
        f = vertexCount - 1

        indices.extend([d, e, f])
        indices.extend([a, d, f])
        indices.extend([d, b, e])
        indices.extend([f, e, c])

    def updateVerticesFromTriangles(self):
        verts = []
        indices = []
        for tri in self.triangles:
            for v in tri:
                verts.extend([v[0], v[1]])
                indices.append(len(verts) / 2 - 1)

        vCount = len(verts) / 2 / 3
        if vCount != len(self.triangles):
            raise RuntimeError("Invalid vertex count: %i of %i" % (vCount, len(self.triangles)))

        self.vertices = makeArray(gl.GLfloat, verts)
        self.indices = makeArray(gl.GLuint, indices)

    def sortVertices(self, transforms):
        if self.vertices:
            triangles = []
            for a, b, c in self.getTriangleIndices():
                boneIndex = int(self.boneIndices[a * 4])
                trans = transforms[boneIndex]
                triangles.append((trans.bone, a, b, c))
            triangles.sort(key=lambda b: b[0].zOrder)

            indices = []
            for tri in triangles:
                indices.extend(tri[1:])

            self.indices = makeArray(gl.GLuint, indices)

    def updateUvs(self):
        if self.vertices:
            w = self.image.width
            h = self.image.height
            uvs = []
            for i in range(0, len(self.vertices), 2):
                xUv = (self.vertices[i] - self.pos[0]) / float(w)
                yUv = (self.vertices[i + 1] - self.pos[1]) / float(h)
                uvs.extend([xUv, yUv])
            self.uvs = makeArray(gl.GLfloat, uvs)

    def moveVertices(self, offset):
        if self.vertices:
            for i in range(0, len(self.vertices), 2):
                self.vertices[i] = self.vertices[i] + offset[0]
                self.vertices[i + 1] = self.vertices[i + 1] + offset[1]

    def updateVertexWeights(self, index, transforms):
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
                    #influence = 1.0 / len(nearby)
                    for x in range(4):
                        if x < len(nearby):
                            weights.append(nearby[x].weight)
                            indices.append(float(nearby[x].transform.index))
                        else:
                            weights.append(0.0)
                            indices.append(0.0)
                else:
                    weights.extend([1.0, 0.0, 0.0, 0.0])
                    indices.extend([float(index), 0.0, 0.0, 0.0])

            self.boneWeights = makeArray(gl.GLfloat, weights)
            self.boneIndices = makeArray(gl.GLfloat, indices)

    def updatePoints(self, surface):
        points = geometry.findEdgePixelsOrdered(surface)
        distance = (surface.get_width() + surface.get_height()) / 10000.0 #TODO Magic
        simplified = geometry.simplifyEdgePixels(points, 40)
        self.points = geometry.offsetPolygon(simplified, -5) #TODO Increase this once better weighting is in?

    def triangulatePoints(self):
        pointsSegments = delaunay.ToPointsAndSegments()
        pointsSegments.add_polygon([self.points])
        triangulation = delaunay.triangulate(pointsSegments.points, pointsSegments.infos, pointsSegments.segments)

        expanded = self.points #geometry.offsetPolygon(self.points, -1) #TODO 0 better, do nothing?
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

class BoneWeight:
    def __init__(self, distance, transform):
        self.distance = distance
        self.transform = transform
        self.bone = transform.bone
        self.weight = 0.0

SHORTEN_LINE = 0.9

def findBoneInfluences(vertex, transforms):
    distances = []
    nearest = findNearestBone(vertex, transforms)
    if nearest:
        nearest.weight = 1.0
        distances.append(nearest)

    distances.sort(key=lambda w: w.distance)
    return distances[:4]

def findNearestBone(vertex, transforms):
    nearest = None
    minDistance = None

    for trans in transforms.values():
        if not trans.bone.parent:
            #Skip root bone
            continue

        start = trans.bone.pivot
        for child in trans.bone.children:
            end = transforms[child].bone.pivot
            distance = pointToShortenedLineDistance(vertex, start, end, SHORTEN_LINE)
            if minDistance is None or distance < minDistance:
                minDistance = distance
                nearest = BoneWeight(distance, trans)

    return nearest

def pointToShortenedLineDistance(point, start, end, shorten):
    startShort = shortenLine(start, end, shorten)
    endShort = shortenLine(end, start, shorten)
    return geometry.pointToLineDistance(point, startShort, endShort)

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
            d = obj.__dict__.copy()
            for ignore in IGNORES:
                if ignore in d:
                    del d[ignore]
            return d
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
        bone.indices = _getArray(gl.GLuint, raw, "indices")
        bone.boneWeights = _getArray(gl.GLfloat, raw, "boneWeights")
        bone.boneIndices = _getArray(gl.GLfloat, raw, "boneIndices")

        bones[bone.name] = bone

    return bones
