import shader
import utils


def loadObj(filename):
    verts = []
    norms = []
    uvs = []
    vertsOut = []
    normsOut = []
    uvsOut = []
    flipX = shader.config.flipMeshX

    for line in utils.openFile(filename):
        values = line.split()
        if values[0] == "v":
            v = map(float, values[1:4])
            if flipX:
                v[0] = -v[0]
            verts.append(v)
        elif values[0] == "vt":
            t = map(float, values[1:3])
            t[1] = 1.0 - t[1]  # Flip texture y
            uvs.append(t)
        elif values[0] == "vn":
            n = map(float, values[1:4])
            if flipX:
                n[0] = -n[0]
            norms.append(n)
        elif values[0] == "f":
            if len(values) != 4:
                raise RuntimeError("Mesh is not triangulated?")

            for face in values[1:]:
                pointers = face.split("/")
                vertsOut.append(list(verts[int(pointers[0]) - 1]))
                if pointers[1]:
                    # Has texture coordinates
                    uvsOut.append(list(uvs[int(pointers[1]) - 1]))
                else:
                    uvsOut.append((0, 0))
                normsOut.append(list(norms[int(pointers[2]) - 1]))

    return vertsOut, normsOut, uvsOut


class MeshObj(object):
    def __init__(self, path):
        self.path = path
        self.vertices = None
        self.normals = None
        self.uvs = None

    def load(self):
        if self.vertices:
            return

        verts, normals, uvs = loadObj(self.path)
        self.vertices = utils.makeFloatArray(verts, 3)
        self.normals = utils.makeFloatArray(normals, 3)
        self.uvs = utils.makeFloatArray(uvs, 2)

