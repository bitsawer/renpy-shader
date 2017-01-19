
import math
from OpenGL import GL as gl

import geometry

def makeArray(tp, values):
    return (tp * len(values))(*values)

class SkinnedMesh:
    jsonIgnore = ["uvs"]

    def __init__(self, vertices, indices, boneWeights=None, boneIndices=None):
        self.vertices = vertices
        self.indices = indices
        self.uvs = None
        self.boneWeights = boneWeights
        self.boneIndices = boneIndices

    def getTriangleIndices(self):
        triangles = []
        if self.indices:
            for i in range(0, len(self.indices), 3):
                triangles.append((self.indices[i], self.indices[i + 1], self.indices[i + 2]))
        return triangles

    def getVertexCount(self):
        return len(self.vertices) // 2

    def getVertex(self, index):
        return (self.vertices[index * 2], self.vertices[index * 2 + 1])

    def subdivide(self, maxSize):
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

    def sortVertices(self, transforms):
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

    def updateUvs(self, bone):
        w = bone.image.width
        h = bone.image.height
        uvs = []
        for i in range(0, len(self.vertices), 2):
            xUv = (self.vertices[i] - bone.pos[0]) / float(w)
            yUv = (self.vertices[i + 1] - bone.pos[1]) / float(h)
            uvs.extend([xUv, yUv])
        self.uvs = makeArray(gl.GLfloat, uvs)

    def moveVertices(self, offset):
        for i in range(0, len(self.vertices), 2):
            self.vertices[i] = self.vertices[i] + offset[0]
            self.vertices[i + 1] = self.vertices[i + 1] + offset[1]

    def updateVertexWeights(self, index, transforms):
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
                for x in range(4):
                    if x < len(nearby):
                        weights.append(nearby[x].weight)
                        indices.append(float(nearby[x].index))
                    else:
                        weights.append(0.0)
                        indices.append(0.0)
            else:
                weights.extend([1.0, 0.0, 0.0, 0.0])
                indices.extend([float(index), 0.0, 0.0, 0.0])

        self.boneWeights = makeArray(gl.GLfloat, weights)
        self.boneIndices = makeArray(gl.GLfloat, indices)

    def mergeDuplicateVertices(self):
        pass

    def findDeformingFaceIndices(self, transforms):
        #TODO For subdivision, do it for faces that are close to bone pivots
        pass


class BoneWeight:
    def __init__(self, distance, index, transform):
        self.distance = distance
        self.index = index
        self.transform = transform
        self.bone = transform.bone
        self.weight = 0.0

#Shorten bones, otherwise their points can be at the same position which
#can make weight calculation random and order-dependant.
SHORTEN_LINE = 0.99

def findBoneInfluences(vertex, transforms):
    distances = []
    nearest = findNearestBone(vertex, transforms)
    if nearest:
        nearest.weight = 0.1
        distances.append(nearest)

        if nearest.bone.parent:
            parent = transforms[nearest.bone.parent]
            distances.append(BoneWeight(1000, parent.index, parent))
            distances[-1].weight = 0.9
        else:
            nearest.weight = 1.0

    distances.sort(key=lambda w: w.distance)
    return distances[:4]

def findNearestBone(vertex, transforms):
    nearest = None
    minDistance = None

    for trans in transforms.values():
        if not trans.bone.parent or not transforms[trans.bone.parent].bone.parent:
            #Skip root bones
            continue

        distance = pointToBoneDistance(vertex, trans.bone, transforms)
        if minDistance is None or distance < minDistance:
            minDistance = distance
            nearest = BoneWeight(distance, trans.index, trans)

    return nearest

def pointToBoneDistance(point, bone, transforms):
    return pointToShortenedLineDistance(point, bone.pivot, transforms[bone.parent].bone.pivot, SHORTEN_LINE)

def pointToShortenedLineDistance(point, start, end, shorten):
    startShort, endShort = geometry.shortenLine(start, end, shorten)
    return geometry.pointToLineDistance(point, startShort, endShort)

