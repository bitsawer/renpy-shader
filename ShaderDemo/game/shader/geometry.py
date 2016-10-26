
def findEdge(surface, xStart, yStart, xStep, yStep, xDir, yDir):
    w = surface.get_width()
    h = surface.get_height()

    x = xStart
    y = yStart

    while 1:
        pixel = surface.get_at((x, y))
        if pixel[3] > 0:
            return x, y

        x += xStep
        y += yStep

        if x >= w:
            x = xStart
            y += yDir
        elif y >= h:
            y = yStart
            x += xDir

        if x < 0 or x >= w or y < 0 or y >= h:
            break

    return (xStart, yStart)

def findCropRect(surface, pad=0):
    w = surface.get_width()
    h = surface.get_height()

    x1 = max(findEdge(surface, 0, 0, 0, 1, 1, 0)[0] - pad, 0)
    y1 = max(findEdge(surface, 0, 0, 1, 0, 0, 1)[1] - pad, 0)
    x2 = min(findEdge(surface, w - 1, 0, 0, 1, -1, 0)[0] + pad, w)
    y2 = min(findEdge(surface, 0, h - 1, 1, 0, 0, -1)[1] + pad, h)
    return x1, y1, x2 - x1, y2 - y1

OFFSETS = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0),           (1, 0),
    (-1, 1),  (0, 1),  (1, 1)
]

def findEdgePixels(surface):
    edgePixels = []

    w, h = surface.get_size()

    for y in range(h):
        for x in range(w):
            pixel = surface.get_at((x, y))
            if pixel[3] > 0:
                #Not transparent, check nearby
                isEdge = False

                for offset in OFFSETS:
                    n = (x + offset[0], y + offset[1])
                    if n[0] > 0 and n[0] < w and n[1] > 0 and n[1] < h:
                        near = surface.get_at(n)
                        if near[3] == 0:
                            #Transparent near pixel, this is an edge
                            isEdge = True
                            break
                    else:
                        #Outside image bounds
                        isEdge = True
                        break

                if isEdge:
                    edgePixels.append((x, y))

    return edgePixels


TURN_LEFT, TURN_RIGHT, TURN_NONE = (1, -1, 0)

def _turn(p, q, r):
    return cmp((q[0] - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (q[1] - p[1]), 0)

def _keepLeft(hull, r):
    while len(hull) > 1 and _turn(hull[-2], hull[-1], r) != TURN_LEFT:
            hull.pop()
    if not len(hull) or hull[-1] != r:
        hull.append(r)
    return hull

def convexHull(points):
    """Returns points on convex hull of an array of points in CCW order using Graham scan."""
    points = sorted(points)
    l = reduce(_keepLeft, points, [])
    u = reduce(_keepLeft, reversed(points), [])
    return l.extend(u[i] for i in xrange(1, len(u) - 1)) or l


RIGHT = "RIGHT"
LEFT = "LEFT"

def insideConvexHull(point, vertices):
    previous_side = None
    n_vertices = len(vertices)
    for n in xrange(n_vertices):
        a, b = vertices[n], vertices[(n+1)%n_vertices]
        affine_segment = _vSub(b, a)
        affine_point = _vSub(point, a)
        current_side = _getSide(affine_segment, affine_point)
        if current_side is None:
            return False #outside or over an edge
        elif previous_side is None: #first segment
            previous_side = current_side
        elif previous_side != current_side:
            return False
    return True

def _getSide(a, b):
    x = _xProduct(a, b)
    if x < 0:
        return LEFT
    elif x > 0:
        return RIGHT
    else:
        return None

def _vSub(a, b):
    return (a[0]-b[0], a[1]-b[1])

def _xProduct(a, b):
    return a[0]*b[1]-a[1]*b[0]

def _interpolate(a, b, s):
    return a + s * (b - a)

def createGrid(rect, convex, xCount, yCount):
    vertices = []
    uvs = []
    indices = []

    for y in range(yCount):
        yUv = y / float(yCount - 1)
        yPos = _interpolate(rect[1], rect[1] + rect[3], yUv)
        for x in range(xCount):
            xUv = x / float(xCount - 1)
            xPos = _interpolate(rect[0], rect[0] + rect[2], xUv)
            vertices.append((xPos, yPos))
            uvs.append((xUv, yUv))

            if y < yCount -1 and x < xCount - 1:
                index = x * xCount + y
                indices.extend([index, index + 1, index + xCount])
                indices.extend([index + xCount, index + 1, index + xCount + 1])

    return vertices, uvs, indices