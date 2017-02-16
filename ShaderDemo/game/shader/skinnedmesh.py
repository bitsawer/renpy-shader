from OpenGL import GL as gl

import geometry
import utils


def makeArray(tp, values):
    return (tp * len(values))(*values)


def roundPoint(x, y):
    return int(round(x)), int(round(y))


class SkinnedMesh:
    jsonIgnore = ["uvs"]

    def __init__(self, vertices, indices, boneWeights=None, boneIndices=None):
        self.setGeometry(vertices, indices)
        self.boneWeights = boneWeights
        self.boneIndices = boneIndices

    def setGeometry(self, verts, indices):
        self.vertices = makeArray(gl.GLfloat, verts)
        self.indices = makeArray(gl.GLuint, indices)
        self.uvs = None
        self.boneWeights = None
        self.boneIndices = None

    def getTriangleIndices(self):
        triangles = []
        if self.indices:
            for i in range(0, len(self.indices), 3):
                triangles.append((self.indices[i], self.indices[i + 1], self.indices[i + 2]))
        return triangles

    def getIndexAdjacency(self, tris):
        adjacency = {}
        for i, tri in enumerate(tris):
            for i2, tri2 in enumerate(tris):
                if i != i2:
                    for index in tri:
                       if index in tri2:
                           adj = adjacency.get(index, [])
                           adj.append((tri2, i2))
                           adjacency[index] = adj
        return adjacency

    def getTriangleAdjacency(self, tris):
        adjacency = {}
        for i, tri in enumerate(tris):
            for i2, tri2 in enumerate(tris):
                if i != i2:
                    a, b, c = tri
                    for edge in ((a, b), (b, c), (c, a)):
                        if edge[0] in tri2 and edge[1] in tri2:
                            adj = adjacency.get(i, [])
                            adj.append(i2)
                            adjacency[i] = adj
                            break
        return adjacency

    def getVertexCount(self):
        return len(self.vertices) // 2

    def getVertex(self, index):
        return (self.vertices[index * 2], self.vertices[index * 2 + 1])

    def subdivideAdaptive(self, transforms):
        verts = self.vertices[:]
        indices = self.indices[:]
        tris = self.getTriangleIndices()
        adjacency = self.getTriangleAdjacency(tris)

        mapping = {}
        for trans in transforms:
            mapping[trans.bone.name] = trans

        subivisions = {}

        for trans in transforms:
            bone = trans.bone
            if bone.parent and bone.tessellate:
                for i, (a, b, c) in enumerate(tris):
                    v1 = self.getVertex(a)
                    v2 = self.getVertex(b)
                    v3 = self.getVertex(c)
                    if geometry.pointInTriangle(bone.pivot, v1, v2, v3):
                        subivisions[(a, b, c)] = (a, b, c, verts, indices, i)

                        for triIndex in adjacency.get(i, []):
                            n = tris[triIndex]
                            subivisions[n] = (n[0], n[1], n[2], verts, indices, triIndex)

        for sub in subivisions.values():
            self.subdivideTriangle(*sub)

        self.setGeometry(verts, [x for x in indices if x is not None])

    def subdivide(self, maxSize):
        verts = self.vertices[:]
        indices = self.indices[:]

        for i, (a, b, c) in enumerate(self.getTriangleIndices()):
            v1 = self.getVertex(a)
            v2 = self.getVertex(b)
            v3 = self.getVertex(c)
            area = geometry.triangleArea(v1, v2, v3)
            if area > maxSize:  # TODO Also if triangle has a too long side
                self.subdivideTriangle(a, b, c, verts, indices, i)

        self.setGeometry(verts, [x for x in indices if x is not None])

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

    def splitEdge(self, a, b, tri, verts, indices, index):
        v1 = self.getVertex(a)
        v2 = self.getVertex(b)

        new1 = geometry.interpolate2d(v1, v2, 0.5)

        indices[index * 3] = None
        indices[index * 3 + 1] = None
        indices[index * 3 + 2] = None

        verts.extend(new1)

        c = (len(verts) // 2) - 1
        d = set(tri).difference((a, b)).pop()

        indices.extend([d, a, c])
        indices.extend([d, b, c])

    def fixTJunctions(self):
        tris = self.getTriangleIndices()
        indexAdj = self.getIndexAdjacency(tris)

        split = {}
        for i, (a, b, c) in enumerate(tris):
            for edge in ((a, b), (b, c), (c, a)):
                start = self.getVertex(edge[0])
                end = self.getVertex(edge[1])
                if geometry.pointDistance(start, end) > 0.0:
                    for tri, index in indexAdj.get(edge[0], []):
                        for n in tri:
                            v2 = self.getVertex(n)
                            if geometry.pointDistance(start, v2) > 1.0 and geometry.pointDistance(end, v2) > 1.0:
                                edgeDist = geometry.pointToLineDistance(v2, start, end)
                                if edgeDist < 1.0:
                                    # Vertex is overlapping this edge
                                    splitting = split.get(i, set())
                                    splitting.add(edge)
                                    split[i] = splitting

        verts = self.vertices[:]
        indices = self.indices[:]
        for index, edges in split.items():
            edges = list(edges)
            tri = tris[index]
            if len(edges) == 1:
                self.splitEdge(edges[0][0], edges[0][1], tri, verts, indices, index)
            elif len(edges) > 1:
                # TODO This can create new edges to be splitted...
                self.subdivideTriangle(tri[0], tri[1], tri[2], verts, indices, index)

        self.setGeometry(verts, [x for x in indices if x is not None])

    def weldVertices(self):
        duplicates = {}
        verts = []
        indices = []

        for i in range(self.getVertexCount()):
            v = self.getVertex(i)
            v = roundPoint(v[0], v[1])
            if not v in duplicates:
                duplicates[v] = len(verts) // 2
                verts.extend(v)

        for tri in self.getTriangleIndices():
            for i in tri:
                v = self.getVertex(i)
                newIndex = duplicates[roundPoint(v[0], v[1])]
                indices.append(newIndex)

        self.setGeometry(verts, indices)

    def sortTriangles(self, transforms):
        triangles = []
        for a, b, c in self.getTriangleIndices():
            zSum = 0.0
            for i in (a, b, c):
                for x in range(4):
                    index = i * 4 + x
                    boneIndex = int(self.boneIndices[index])
                    boneWeight = self.boneWeights[index]
                    zSum += transforms[boneIndex].bone.zOrder * boneWeight
            triangles.append((zSum / (3.0 * 4.0), a, b, c))
        triangles.sort(key=lambda b: b[0])

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

    def updateVertexWeights(self, index, transforms, bones):
        mapping = {}
        for i, trans in enumerate(transforms):
            trans.index = i
            mapping[trans.bone.name] = trans

        blockers = findBlockerNames(transforms[index].bone, bones)

        weights = []
        indices = []
        for i in range(0, len(self.vertices), 2):
            x = self.vertices[i]
            y = self.vertices[i + 1]

            nearby = findBoneInfluences((x, y), mapping, blockers)
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


def findBoneImageBone(bone, bones):
    for parent in [bone] + bone.getParents(bones):
        if parent.image:
            return parent
    return None


def blockerFunc(bone, results):
    if bone.blocker:
        results.add(bone.name)
        return False
    return True


def findBlockerNames(meshBone, bones):
    blockers = set()
    meshBone.walkChildren(bones, blockerFunc, (blockers,))

    results = set()
    for name in blockers:
        blocker = bones[name]
        imageBone = findBoneImageBone(blocker, bones)
        children = blocker.getAllChildren(bones)
        if imageBone.name != meshBone.name:
            for child in children:
                results.add(child.name)
        else:
            names = set([b.name for b in children])
            for bone in bones.values():
                if bone.name not in names:
                    results.add(bone.name)

    return results


class BoneWeight:
    def __init__(self, distance, index, transform):
        self.distance = distance
        self.index = index
        self.transform = transform
        self.bone = transform.bone
        self.weight = 0.0

# Shorten bones, otherwise their points can be at the same position which
# can make weight calculation random and order-dependant.
SHORTEN_LINE = 0.95


def findBoneInfluences(vertex, transforms, blockers):
    weights = []
    nearest = findNearestBone(vertex, transforms, blockers)
    if nearest:
        nearest.weight = calculateWeight(vertex, nearest.transform, transforms[nearest.bone.parent])
        weights.append(nearest)

        parent = transforms[nearest.bone.parent]
        weights.append(BoneWeight(-1, parent.index, parent))
        weights[-1].weight = 1.0 - sum([w.weight for w in weights])

    weights.sort(key=lambda w: -w.weight)
    return weights[:4]


def calculateWeight(vertex, a, b, bendyLength=0.75):
    minWeight = 0.0
    maxWeight = 0.1

    distance = geometry.pointDistance(vertex, a.bone.pivot)
    boneLength = geometry.pointDistance(a.bone.pivot, b.bone.pivot) * bendyLength
    if boneLength == 0:
       return 0
    vertexDistance = min(distance / boneLength, 1.0)
    return utils.clamp(1 - vertexDistance, minWeight, maxWeight)


def findNearestBone(vertex, transforms, blockers):
    nearest = None
    minDistance = None

    for trans in transforms.values():
        if not trans.bone.parent or not transforms[trans.bone.parent].bone.parent:
            # Skip root bones
            continue
        if trans.bone.name in blockers:
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

