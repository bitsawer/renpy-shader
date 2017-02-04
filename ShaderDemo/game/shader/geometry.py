
import polygonoffset
import math
import random

def simplifyEdgePixels(pixels, minDistance):
    results = []

    i = 0
    while i < len(pixels):
        results.append((float(pixels[i][0]), float(pixels[i][1])))

        distance = 0
        i2 = i + 1
        while i2 < len(pixels):
            previous = (pixels[i2 - 1][0], pixels[i2 - 1][1])
            current = (pixels[i2][0], pixels[i2][1])
            distance += math.hypot(current[0] - previous[0], current[1] - previous[1])
            if distance > minDistance:
                break
            i2 += 1
        i = i2

    return results

def offsetPolygon(points, size):
    results = []
    for p in points:
        current = (float(p[0]) + random.random() * 0.00001, float(p[1]) + random.random() * 0.00001) #TODO Fix this
        results.append(current)
    return polygonoffset.offsetpolygon(results, size)

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

def _getNearby(surface, x, y, size):
    w, h = surface.get_size()
    xStart = max(x - size, 0)
    xEnd = min(x + size + 1, w - 1)
    yStart = max(y - size, 0)
    yEnd = min(y + size + 1, h - 1)

    pixels = []
    for yp in range(yStart, yEnd):
        for xp in range(xStart, xEnd):
            if xp != x or yp != y:
                point = (xp, yp)
                pixels.append((point, surface.get_at(point)))
    return pixels

def _isEdgePixel(surface, x, y, size):
    color = surface.get_at((x, y))
    if color[3] != 0:
        #Not transparent
        return False

    w, h = surface.get_size()
    isAlpha = False
    isColor = False

    pixels = _getNearby(surface, x, y, size)
    if len(pixels) < 8:
        return True

    for pixel in pixels:
        color = pixel[1]
        if color[3] > 0:
            isColor = True
        if color[3] == 0:
            isAlpha = True
    return isAlpha and isColor

def findEdgePixelsOrdered(surface):
    size = 1
    start = findEdge(surface, 0, 0, 0, 1, 1, 0)
    start = (start[0] - size, start[1]) #Must have empty alpha padding!
    current = start

    results = []
    seen = set()
    backtrack = []
    undo = []
    w, h = surface.get_size()

    steps = 0
    while current:
        if current in seen:
            if backtrack and current != start:
                current = backtrack.pop()
                index = undo.pop()
                results = results[:index]
            else:
                break
        else:
            seen.add(current)
            results.append(current)

            edges = []
            for pixel in _getNearby(surface, current[0], current[1], size):
                point = pixel[0]
                if _isEdgePixel(surface, point[0], point[1], size):
                    edges.append(point)

            if edges:
                current = edges.pop()
                backtrack.extend(edges)
                undo.extend([len(results)] * len(edges))

            steps += 1

    return results

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

def insidePolygon(x, y, poly):
    n = len(poly)
    inside = False

    p1x, p1y = poly[0]
    for i in range(n+1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside

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

def pointToLineDistance(point, a, b):
    x1, y1 = a
    x2, y2 = b
    x3, y3 = point

    px = x2 - x1
    py = y2 - y1
    value = px*px + py*py

    u =  ((x3 - x1) * px + (y3 - y1) * py) / float(value)
    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py
    dx = x - x3
    dy = y - y3
    return math.sqrt(dx*dx + dy*dy)

def pointDistance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def triangleArea(p1, p2, p3):
    a = pointDistance(p1, p2)
    b = pointDistance(p2, p3)
    c = pointDistance(p3, p1)

    #Heron's formula
    s = (a + b + c) / 2.0
    return (s * (s - a) * (s - b) * (s - c)) ** 0.5

def interpolate2d(p1, p2, s):
    x = _interpolate(p1[0], p2[0], s)
    y = _interpolate(p1[1], p2[1], s)
    return (x, y)

def shortenLine(a, b, relative):
    aShort = shortenLineEnd(a, b, relative)
    bShort = shortenLineEnd(b, a, relative)
    return aShort, bShort

def shortenLineEnd(a, b, relative):
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

def _triSign(p1, p2, p3):
    return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

def pointInTriangle(point, v1, v2, v3):
    b1 = _triSign(point, v1, v2) < 0.0
    b2 = _triSign(point, v2, v3) < 0.0
    b3 = _triSign(point, v3, v1) < 0.0
    return (b1 == b2) and (b2 == b3)
