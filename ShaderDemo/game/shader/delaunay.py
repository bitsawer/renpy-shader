from math import hypot, sqrt, ceil, pi, sin, cos
from random import random, randint
import warnings
from operator import itemgetter
import time
from random import shuffle
from itertools import chain
from datetime import datetime
from collections import defaultdict
import logging

# try:
#     from predicates import orient2d, incircle
# except ImportError:
#     warnings.warn(
#     "Robust predicates not available, falling back on non-robust implementation"
#     )

def orient2d(pa, pb, pc):
    """Direction from pa to pc, via pb, where returned value is as follows:

    left:     + [ = ccw ]
    straight: 0.
    right:    - [ = cw ]

    returns twice signed area under triangle pa, pb, pc
    """
    detleft = (pa[0] - pc[0]) * (pb[1] - pc[1])
    detright = (pa[1] - pc[1]) * (pb[0] - pc[0])
    det = detleft - detright
    return det

def incircle(pa, pb, pc, pd):
    """Tests whether pd is in circle defined by the 3 points pa, pb and pc
    """
    adx = pa[0] - pd[0]
    bdx = pb[0] - pd[0]
    cdx = pc[0] - pd[0]
    ady = pa[1] - pd[1]
    bdy = pb[1] - pd[1]
    cdy = pc[1] - pd[1]
    bdxcdy = bdx * cdy
    cdxbdy = cdx * bdy
    alift = adx * adx + ady * ady
    cdxady = cdx * ady
    adxcdy = adx * cdy
    blift = bdx * bdx + bdy * bdy
    adxbdy = adx * bdy
    bdxady = bdx * ady
    clift = cdx * cdx + cdy * cdy
    det = alift * (bdxcdy - cdxbdy) + \
            blift * (cdxady - adxcdy) + \
            clift * (adxbdy - bdxady)
    return det

# FIXME
#
# * When to remove external triangle and infinite triangles?
#   And should they be stored in the Triangulation object?
#
# * hcpo methods are not robust against small counts of points
#
# * grouping of methods and triangulation data structure
#   - finding a triangle could go with triangulation data structure
#   - constrained triangulation, API
#
# * Improve obtaining voronoi diagram from triangulated set of points
#   (where topology of Voronoi is obtained in topological data structure)
#
# * Functions for scaling and translation of
#   coordinates so that triangulation takes place
#   in [-1,1] range: more floating point precision available



# ------------------------------------------------------------------------------
# Iterators
#

class FiniteEdgeIterator(object):
    def __init__(self, triangulation, constraints_only = False):
        self.triangulation = triangulation
        self.constraints_only = constraints_only
        self.current_idx = 0 # this is index in the list
        self.pos = -1 # this is index in the triangle (side)

    def __iter__(self):
        return self

    def next(self):
        ret = None
        while self.current_idx < len(self.triangulation.triangles):
            triangle = self.triangulation.triangles[self.current_idx]
            self.pos += 1
            neighbour = triangle.neighbours[self.pos]
            if id(triangle) < id(neighbour):
                if self.constraints_only and triangle.constrained[self.pos]:
                    ret = Edge(triangle, self.pos)
                elif not self.constraints_only:
                    ret = Edge(triangle, self.pos)
            if self.pos == 2:
                self.pos = -1
                self.current_idx += 1
            if ret is not None:
                return ret
        else:
            raise StopIteration()



class TriangleIterator(object):
    """Iterator over all triangles that are in the triangle data structure.
    The finite_only parameter determines whether only the triangles in the
    convex hull of the point set are iterated over, or whether also infinite
    triangles are considered.

    """
    def __init__(self, triangulation, finite_only=False):
        self.triangulation = triangulation
        self.finite_only = finite_only
        self.visited = set()
        self.to_visit_stack = [self.triangulation.external]

    def __iter__(self):
        return self

    def next(self):
        ret = None
        while self.to_visit_stack:
            triangle = self.to_visit_stack.pop()
            # determine whether we should 'emit' the triangle
            if self.finite_only == True and id(triangle) not in self.visited and triangle.is_finite:
                ret = triangle
            elif self.finite_only == False and id(triangle) not in self.visited:
                ret = triangle
            self.visited.add(id(triangle))
            # NOTE: from an external triangle we can get
            # to a triangle in the triangulation multiple times
            for i in xrange(3):
                neighbour = triangle.neighbours[i]
                if neighbour is None:
                    continue
                elif id(neighbour) not in self.visited:
                    self.to_visit_stack.append(neighbour)
            if ret is not None:
                return ret
        else:
            raise StopIteration()


class ConvexHullTriangleIterator(TriangleIterator):
    """Iterator over all triangles that are in the convex hull of the
    point set (excludes infinite triangles).

    """
    def __init__(self, triangulation):
        # Actually, we are an alias for TriangleIterator
        # with finite_only set to True
        super(ConvexHullTriangleIterator, self).__init__(triangulation, True)


class InteriorTriangleIterator(object):
    """Iterator over all triangles that are enclosed by constraints

    Assumes that a polygon has been triangulated which is closed properly
    and that the polygon consists of *exactly one* connected component!
    """
    def __init__(self, triangulation):
        constrained = False
        self.triangulation = triangulation
        self.visited = set([id(self.triangulation.external)])
        self.to_visit_stack = [self.triangulation.external.neighbours[2]]
        # walk to an interior triangle
        while not constrained and self.to_visit_stack:
            triangle = self.to_visit_stack.pop()
            assert triangle is not None
            self.visited.add(id(triangle))
            # NOTE: from an external triangle we can get
            # to a triangle in the triangulation multiple times
            for i in xrange(3):
                constrained = triangle.constrained[i]
                neighbour = triangle.neighbours[i]
                if constrained:
                    self.to_visit_stack = [neighbour]
                    self.visited = set()
                    break
                if neighbour is not None and id(neighbour) not in self.visited:
                    self.to_visit_stack.append(neighbour)

    def __iter__(self):
        return self

    def next(self):
        ret = None
        constrained = False
        while self.to_visit_stack:
            triangle = self.to_visit_stack.pop()
            if id(triangle) not in self.visited:
                ret = triangle
            self.visited.add(id(triangle))
            # NOTE: from an external triangle we can get
            # to a triangle in the triangulation multiple times
            for i in xrange(3):
                constrained = triangle.constrained[i]
                if constrained:
                    continue
                neighbour = triangle.neighbours[i]
                if id(neighbour) not in self.visited:
                    self.to_visit_stack.append(neighbour)
            if ret is not None:
                return ret
        else:
            raise StopIteration()



class RegionatedTriangleIterator(object):
    """Iterator over all triangles that are fenced off by constraints.
    The constraints fencing off triangles determine the regions.
    The iterator yields a tuple: (region number, depth, triangle).

    Note:

    - The region number can increase in unexpected ways, e.g. 0, 1, 476, 1440,
    ..., etc.
    - The depth gives the nesting of the regions.

    The first group is always the infinite part (at depth 0) of the domain
    around the feature (the parts of the convex hull not belonging to any
    interior part).
    """
    def __init__(self, triangulation):
        # start at the exterior
        self.triangulation = triangulation
        self.visited = set([id(self.triangulation.external)])
        self.to_visit_stack = [(self.triangulation.external.neighbours[2], 0)]
        self.later = []
        self.group = 0

    def __iter__(self):
        return self

    def next(self):
        while self.to_visit_stack or self.later:
            # visit all triangles in the exterior, subsequently visit
            # all triangles that are enclosed by a set of segments
            while self.to_visit_stack:
                triangle, depth = self.to_visit_stack.pop()
                assert triangle is not None
                if triangle in self.visited:
                    continue
                self.visited.add(triangle)
                for i in xrange(3):
                    constrained = triangle.constrained[i]
                    neighbour = triangle.neighbours[i]
                    if constrained and neighbour not in self.visited:
                        self.later.append((neighbour, depth + 1))
                    elif neighbour is not None and neighbour not in self.visited:
                        self.to_visit_stack.append((neighbour, depth))
                return (self.group, depth, triangle)
            # flip the next level with this
            if self.later:
                self.group += 1
                for _ in xrange(len(self.later)):
                    t, d = self.later.pop()
                    if id(t) not in self.visited:
                        self.to_visit_stack = [(t, d)]
                        break
        else:
            raise StopIteration()


class StarEdgeIterator(object):
    """Returns iterator over edges in the star of the vertex

    The edges are returned in counterclockwise order around the vertex.
    The triangles that the edges are associated with share the vertex
    that this iterator is constructed with.
    """
    def __init__(self, vertex): #, finite_only = True):
        self.vertex = vertex
        self.start = vertex.triangle
        self.triangle = self.start
        self.side = ccw(self.start.vertices.index(self.vertex))
        self.done = False

    def __iter__(self):
        return self

    def next(self):
        if not self.done:
            self.triangle = self.triangle.neighbours[self.side]
            assert self.triangle is not None
            #self.visited.append(self.triangle)
            #try:
            side = self.triangle.vertices.index(self.vertex)
            #except ValueError, err:
            #    print err
            #    print [id(t) for t in self.visited]
            #    raise
            #side = (self.side + 1) % 3
            assert self.triangle.vertices[side] is self.vertex
            e = Edge(self.triangle, side)
            self.side = ccw(side)
            if self.triangle is self.start:
                self.done = True
            return e
        else: # we are at start again
            raise StopIteration()

# ------------------------------------------------------------------------------
# Custom Exceptions
#

class DuplicatePointsFoundError(Exception):
    pass

class TopologyViolationError(Exception):
    pass


# ------------------------------------------------------------------------------
# Helpers
#

# -- helper functions, could be inlined in Cythonized version
def box(points):
    """Obtain a tight fitting axis-aligned box around point set"""
    xmin = min(points, key = lambda x: x[0])[0]
    ymin = min(points, key = lambda x: x[1])[1]
    xmax = max(points, key = lambda x: x[0])[0]
    ymax = max(points, key = lambda x: x[1])[1]
    return (xmin, ymin), (xmax, ymax)

def ccw(i):
    """Get index (0, 1 or 2) increased with one (ccw)"""
    return (i + 1) % 3

def cw(i):
    """Get index (0, 1 or 2) decreased with one (cw)"""
    return (i - 1) % 3

def apex(side):
    """Given a side, give the apex of the triangle """
    return side % 3

def orig(side):
    """Given a side, give the origin of the triangle """
    return (side + 1) % 3 # ccw(side)

def dest(side):
    """Given a side, give the destination of the triangle """
    return (side - 1) % 3 # cw(side)

def output_vertices(V, fh):
    """Output list of vertices as WKT to text file (for QGIS)"""
    fh.write("id;wkt\n")
    for v in V:
        fh.write("{0};POINT({1})\n".format(id(v), v))

def output_triangles(T, fh):
    """Output list of triangles as WKT to text file (for QGIS)"""
    fh.write("id;wkt;n0;n1;n2;v0;v1;v2\n")
    for t in T:
        if t is None:
            continue
        fh.write("{0};{1};{2[0]};{2[1]};{2[2]};{3[0]};{3[1]};{3[2]}\n".format(id(t), t, [id(n) for n in t.neighbours], [id(v) for v in t.vertices]))

def output_edges(E, fh):
    fh.write("id;side;wkt\n")
    for e in E:
        fh.write("{0};{1};LINESTRING({2[0][0]} {2[0][1]}, {2[1][0]} {2[1][1]})\n".format(id(e.triangle), e.side, e.segment))
# -- unused helper functions
# def left_or_right(area):
#     if area > 0:
#         return "ccw / left / +"
#     elif area < 0:
#         return "cw / right / -"
#     else:
#         return "undetermined (straight)"
#
# def common(t0, side0, t1):
#     """Given t0 and its side0 check which side of t1 is common
#
#     returns
#         * side1 if t1 has a common edge with t0
#         * None otherwise
#     """
#     orig0, dest0 = orig(side0), dest(side0) #aod(side0)
#     for side1 in xrange(3):
#         apex1, orig1, dest1 = apex(side1), orig(side1), dest(side1)
#         if t0.vertices[orig0] is t1.vertices[dest1] and \
#             t0.vertices[dest0] is t1.vertices[orig1]:
#             return apex1
#     return None
#
# def link(t0, t1):
#     """Given 2 triangles t0 and t1
#
#     returns:
#         * True if t0 and t1 can be linked (have a common side)
#         * False if t0 and t1 cannot be linked (do not have a common side)
#     """
#     # Note, not used in the triangulation code, useful for building test cases
#     result = False
#     for side0 in xrange(3):
#         apex0, orig0, dest0 = apex(side0), orig(side0), dest(side0)
#         for side1 in xrange(3):
#             apex1, orig1, dest1 = apex(side1), orig(side1), dest(side1)
#             if t0.vertices[orig0] is t1.vertices[dest1] and \
#                 t0.vertices[dest0] is t1.vertices[orig1]:
#                 #print "", apex0, t0.vertices[orig0], t1.vertices[dest1]
#                 #print "", apex1, t0.vertices[dest0], t1.vertices[orig1]
#                 result = True
#                 break
#         if result:
#             t0.neighbours[apex0] = t1
#             t1.neighbours[apex1] = t0
#             #print t0.neighbours
#             #print t1.neighbours
#             break
#     return result



# ------------------------------------------------------------------------------
# Data structures
# * Vertex
# * InfiniteVertex
# * Triangle
# * Triangulation
#


class Vertex(object):
    """A vertex in the triangulation.
    Can carry extra information via its info property.
    """
    __slots__ = ('x', 'y', 'info', 'triangle')

    def __init__(self, x, y, info = None):
        self.x = float(x)
        self.y = float(y)
        self.info = info
        self.triangle = None

    def __str__(self):
        return "{0} {1}".format(self.x, self.y)

    def __getitem__(self, i):
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        else:
            raise IndexError("No such ordinate: {}".format(i))

    def distance(self, other):
        """Cartesian distance to other point """
        # only used in triangle.__str__
        return hypot(self.x -other.x, self.y - other.y)

    def distance2(self, other):
        """Cartesian distance *squared* to other point """
        # Used for distances in random triangle close to point
        return pow(self.x -other.x, 2) + pow(self.y - other.y, 2)

    @property
    def is_finite(self):
        return True


class InfiniteVertex(Vertex):
    __slots__ = ('x', 'y', 'info', 'triangle')

    def __init__(self, x, y, info = None):
        super(InfiniteVertex, self)
        self.x = float(x)
        self.y = float(y)
        self.info = info
        self.triangle = None

    @property
    def is_finite(self):
        return False

#     @property
#     def x(self):
#         raise ValueError("Infinite vertex has no geometric embedding")
#
#     @property
#     def y(self):
#         raise ValueError("Infinite vertex has no geometric embedding")

#     def __str__(self):
#         return u"Inf Inf"


class Triangle(object):
    """Triangle for which its vertices should be oriented CCW
    """

    __slots__ = ('vertices', 'neighbours','constrained', 'info')

    def __init__(self, a, b, c):
        self.vertices = [a, b, c] # orig, dest, apex -- ccw
        self.neighbours = [None] * 3
        self.constrained = [False] * 3 # FIXME: could be coded as a bitmask on an integer
        self.info = None

    def __str__(self):
        """Conversion to WKT string

        Defines a geometric embedding of the Infinite vertex
        so that the vertex lies perpendicular halfway convex hull segment
        """
        vertices = []
        for idx in range(3):
            v = self.vertices[idx]
            if v is not None:
                vertices.append(str(v))
            else:
                orig_idx, dest_idx = (idx - 1) % 3, (idx + 1) % 3
                orig, dest = self.vertices[orig_idx], self.vertices[dest_idx]
                halfway = (orig.x + dest.x) * .5, (orig.y + dest.y) * .5
                d = orig.distance(dest)
                dx = dest.x - orig.x
                dx /= d
                dy = dest.y - orig.y
                dy /= d
                O = halfway[0] + dy, halfway[1] - dx
                vertices.append("{0[0]} {0[1]}".format(O))
        vertices.append(vertices[0])
        return "POLYGON(({0}))".format(", ".join(vertices))

    @property
    def is_finite(self):
#         return self.vertices[2] is not None
        return not any([isinstance(v, InfiniteVertex) for v in self.vertices])

    @property
    def is_ccw(self):
        return orient2d(self.vertices[0], self.vertices[1], self.vertices[2]) > 0.


class Edge(object):
    """An edge is a Triangle and an integer [0, 1, 2] that indicates the
    side of the triangle to use as the Edge"""

    def __init__(self, triangle, side):
        self.triangle = triangle
        self.side = side

#     def __str__(self):
#         return "{}={}={}".format(self.side, ", ".join(map(str, self.segment)), self.triangle)

    @property
    def segment(self):
        return self.triangle.vertices[ccw(self.side)], self.triangle.vertices[cw(self.side)]

    @property
    def constrained(self):
        return self.triangle.constrained[self.side]

#     @property
#     def is_finite(self):
#         # FIXME:
#         # not use triangle here, but check if vertices are finite or infinite
#         return self.triangle.is_finite


class Triangulation(object):
    """Triangulation data structure"""
    # This represents the mesh
    def __init__(self):
        self.vertices = []
        self.triangles = []
        self.external = None # infinite, external triangle (outside convex hull)


# -----------------------------------------------------------------------------
# Delaunay triangulation using Lawson's incremental insertion
#
def triangulate(points, infos=None, segments=None):
    """Triangulate a list of points, and if given also segments are
    inserted in the triangulation.
    """
    # FIXME: also embed info for points, if given as 3rd value in tuple
    # for every point
    if len(points) == 0:
        raise ValueError("we cannot triangulate empty point list")
    logging.debug( "start "+ str(datetime.now()) )
    logging.debug( "" )
    logging.debug( "pre-processing" )
    start = time.clock()
    # points without info
    points = [(pt[0], pt[1], key) for key, pt in enumerate(points)]
    # this randomizes the points and then sorts them for spatial coherence
    points = hcpo(points)
    # get the original position and the new position in the sorted list
    # to build a lookup table for segment indices
    if infos is not None or segments is not None:
        index_translation = dict([(pos, newpos) for (newpos, (_, _, pos)) in enumerate(points)])
        if segments is not None:
            # -- translate the segments
            segments = [(index_translation[segment[0]], index_translation[segment[1]]) for segment in segments]
        if infos is not None:
            infos= [(index_translation[info[0]], info[1]) for info in infos]
    end = time.clock()
    logging.debug( str(end - start) + " secs" )
    logging.debug( "" )
    logging.debug( "triangulating " + str(len(points)) + " points" )
    # add points, using incremental construction triangulation builder
    dt = Triangulation()
    start = time.clock()
    incremental = PointInserter(dt)
    incremental.insert(points)
    end = time.clock()
    logging.debug( str(end - start) + " secs")
    logging.debug( str(len(dt.vertices)) + " vertices")
    logging.debug( str(len(dt.triangles)) + " triangles")
    logging.debug( str(incremental.flips) + " flips")
    if len(dt.vertices) > 0:
        logging.debug( str( float(incremental.flips) / len(dt.vertices)) + " flips per insert")

    # check links of triangles
#     check_consistency(dt.triangles)

    # insert segments
    if segments is not None:
        start = time.clock()
        logging.debug( "" )
        logging.debug( "inserting " + str(len(segments)) + " constraints")
        constraints = ConstraintInserter(dt)
        constraints.insert(segments)
        end = time.clock()
        logging.debug( str(end - start) + " secs")
        logging.debug( str(len(dt.vertices)) + " vertices")
        logging.debug( str(len(dt.triangles)) + " triangles")
        constraints = len([_ for _ in FiniteEdgeIterator(dt, constraints_only=True)])
        logging.debug( str(constraints) + " constraints")

    if infos is not None:
        logging.debug( "" )
        logging.debug( "inserting " + str( len(infos) ) + " info")
        for info in infos:
            dt.vertices[info[0]].info = info[1]

    if infos is not None:
        logging.debug( "" )
        logging.debug( "inserting " + str( len(infos) ) + " info")
        for info in infos:
            dt.vertices[info[0]].info = info[1]
    logging.debug( "" )
    logging.debug( "fin " + str(datetime.now()) )
    if False:
        with open("/tmp/alltris.wkt", "w") as fh:
                    output_triangles([t for t in TriangleIterator(dt,
                                                                  finite_only=False)],
                                     fh)
        with open("/tmp/allvertices.wkt", "w") as fh:
            output_vertices(dt.vertices, fh)
    return dt


class PointInserter(object):
    """Class to insert points into a Triangulation.

    It is ensured that the triangles that are made, are obeying the Delaunay
    criterion by flipping (Lawson's incremental algorithm is used
    to construct the triangulation).
    """

    __slots__ = ('triangulation', 'queue', 'flips', 'visits', 'last')

    def __init__(self, triangulation):
        self.triangulation = triangulation
        self.flips = 0
        self.visits = 0
        self.queue = []
        self.last = None # last triangle used for finding triangle

    def insert(self, points):
        """Insert a list of points into the triangulation.
        """
        self.initialize(points)
        for j, pt in enumerate(points):
            self.append(pt)
            if (j % 10000) == 0:
                logging.debug( " " +str( datetime.now() ) + str( j ))
            #check_consistency(triangles)

    def initialize(self, points):
        """Initialize large triangle around point and external / dummy triangle
        from where we can always start point location
        """
        (xmin, ymin), (xmax, ymax) = box(points)
        width = abs(xmax - xmin)
        height = abs(ymax - ymin)
        if height > width:
            width = height
        if width == 0:
            width = 1.
        vertices = [InfiniteVertex(xmin - 50.0 * width, ymin - 40.0 * width),
                    InfiniteVertex(xmax + 50.0 * width, ymin - 40.0 * width),
                    InfiniteVertex(0.5 * (xmin + xmax), ymax + 60.0 * width)]
        large = Triangle(vertices[0], vertices[1], vertices[2])
        self.triangulation.external = Triangle(vertices[1], vertices[0], None)
        triangles = self.triangulation.triangles
        triangles.append(large)
        self.link_2dir(large, 2, self.triangulation.external, 2)
        for v in vertices:
            v.triangle = large

    def append(self, pt):
        """Appends one point to the triangulation.

        This method assumes that the triangulation is initialized
        and the point lies inside the bounding box used for initializing.
        """
        v = Vertex(pt[0], pt[1])
        t0 = self.get_triangle_contains(v)
        # skip insertion of point, if it is on same location already there
        for corner in t0.vertices:
            if corner.x == v.x and corner.y == v.y:
                raise ValueError("Duplicate point found for insertion")
        self.triangulation.vertices.append(v)
        a, b, c = t0.vertices
        # neighbours outside triangle to insert to
        neighbours = [t0.neighbours[0], t0.neighbours[1]]
        neighbouridx = [n.neighbours.index(t0) if n is not None else None for n in neighbours]
        # make new triangles
        t1 = Triangle(b, c, v)
        t2 = Triangle(c, a, v)
        t0.vertices[2] = v
        # update triangle pointers of vertices
        a.triangle = t0
        b.triangle = t0
        v.triangle = t0
        c.triangle = t1
        # link them up properly -- use neighbours outside triangle to insert to
        # external links
        # 2 * 2
        if neighbours[0] is not None:
            side = neighbouridx[0]
            self.link_1dir(neighbours[0], side, t1)
        self.link_1dir(t1, 2, neighbours[0])
        if neighbours[1] is not None:
            side = neighbouridx[1]
            self.link_1dir(neighbours[1], side, t2)
        self.link_1dir(t2, 2, neighbours[1])
        # internal links
        # 3 * 2
        self.link_2dir(t0, 0, t1, 1)
        self.link_2dir(t1, 0, t2, 1)
        self.link_2dir(t2, 0, t0, 1)
        #
        triangles = self.triangulation.triangles
        triangles.extend([t1, t2])
        # check if triangles are delaunay, and flip
        # edges of triangle just inserted into are queued for checking
        # Delaunay criterion
        self.queue.append((t2, 2))
        self.queue.append((t1, 2))
        self.queue.append((t0, 2))
        self.delaunay()

    def get_triangle_contains(self, p):
        """Gets the triangle on which point p is located from the triangulation
        """
        ini = self.random_triangle_close_to_p(p)
        t0 = self.visibility_walk(ini, p)
        # remember this triangle as it might be close to next wanted point
        self.last = t0
        return t0

    def random_triangle_close_to_p(self, p):
        """Samples a list of triangles and returns closest of these triangles
        to the given point p
        """
        # FIXME: should we cache result of random triangles
        # as long as sample size is the same
        # we could use the same set of triangles
        # O(n/3) would be good where n is the number of triangles
        candidate = self.triangulation.external
        min_dist = None # candidate.vertices[0].distance(p)
        triangles = self.triangulation.triangles
        size = len(triangles)
        #
        if size != 0:
            k = int(sqrt(size) / 25)
            #k = int(size ** (1 / 3.0)) # -- samples more triangles
            if self.last is not None: # set by triangle_contains
                dist = self.last.vertices[0].distance2(p)
                if min_dist is None or dist < min_dist:
                    min_dist = dist
                    candidate = self.last
            for _ in xrange(k):
                triangle = triangles[int(random() * size) ]
                dist = triangle.vertices[0].distance2(p)
                if min_dist is None or dist < min_dist:
                    min_dist = dist
                    candidate = triangle
        return candidate

    def visibility_walk(self, ini, p):
        """ Walk from triangle ini to triangle containing p

        Note, because this walk can cycle for a non-Delaunay triangulation
        we pick a random edge to continue the walk
        (this is a remembering stochastic walk, see RR-4120.pdf,
        Technical report from HAL-Inria by
        Olivier Devillers, Sylvain Pion, Monique Teillaud.
        Walking in a triangulation,
        https://hal.inria.fr/inria-00072509)

        For speed we do not check if we stay inside the bounding box
        that was used when initializing the triangulation, so make sure
        that a point given fits inside this box!
        """
        t = ini
        previous = None
        if t.vertices[2] is None:
            t = t.neighbours[2]
        n = len(self.triangulation.triangles)
        for _ in xrange(n):
            # get random side to continue walk, this way the walk cannot get
            # stuck by always picking triangles in the same order
            # (and get stuck in a cycle in case of non-Delaunay triangulation)
            e = randint(0, 2)
            if t.neighbours[e] is not previous and \
                orient2d(t.vertices[ccw(e)], t.vertices[ccw(e+1)], p) < 0:
                previous = t
                t = t.neighbours[e]
                continue
            e = ccw(e + 1)
            if t.neighbours[e] is not previous and \
                orient2d(t.vertices[ccw(e)], t.vertices[ccw(e+1)], p) < 0:
                previous = t
                t = t.neighbours[e]
                continue
            e = ccw(e + 1)
            if t.neighbours[e] is not previous and \
                orient2d(t.vertices[ccw(e)], t.vertices[ccw(e+1)], p) < 0:
                previous = t
                t = t.neighbours[e]
                continue
            return t
        return t

    def delaunay(self):
        """Flips triangles if Delaunay criterion does not hold.

        If 2 triangles were flipped, the 4 triangles around the quadrilateral
        are queued for checking if these are Delaunay.
        """
        while self.queue:
            t0, side0 = self.queue.pop()
            # -- skip constrained edge - these should not be flipped
            if t0.constrained[side0]:
                continue
            t1 = t0.neighbours[side0]
            # -- skip if we are going to flip the external dummy triangle
            # or when the triangle is an infinite triangle
            if t1 is self.triangulation.external or t1 is None:
                continue
            # -- get the opposite vertex/side index
            # it's an error if we cannot find t0
            side1 = t1.neighbours.index(t0)
            if side1 is None:
                raise ValueError("No opposite triangle found")
            if incircle(t0.vertices[0], t0.vertices[1], t0.vertices[2], t1.vertices[side1]) > 0:
#                 # flip triangles without creating new triangle objects
                self.flip(t0, side0, t1, side1)
                # check if all 4 edges around quadrilateral just flipped
                # are now good: i.e. delaunay criterion applies
                self.queue.append((t0, 0))
                self.queue.append((t0, 2))
                self.queue.append((t1, 0))
                self.queue.append((t1, 2))

    def flip(self, t0, side0, t1, side1):
        """Performs the flip of triangle t0 and t1

        If t0 and t1 are two triangles sharing a common edge AB,
        the method replaces ABC and BAD triangles by DCA and DBC, respectively.

        Pre-condition: triangles t0/t1 share a common edge and the edge is known
        """
        self.flips += 1

        apex0, orig0, dest0 = apex(side0), orig(side0), dest(side0)
        apex1, orig1, dest1 = apex(side1), orig(side1), dest(side1)

        # side0 and side1 should be same edge
        assert t0.vertices[orig0] is t1.vertices[dest1]
        assert t0.vertices[dest0] is t1.vertices[orig1]
        # assert both triangles have this edge unconstrained
        assert t0.constrained[apex0] == False
        assert t1.constrained[apex1] == False

        # -- vertices around quadrilateral in ccw order starting at apex of t0
        A, B, C, D = t0.vertices[apex0], t0.vertices[orig0], t1.vertices[apex1], t0.vertices[dest0]
        # -- triangles around quadrilateral in ccw order, starting at A
        AB, BC, CD, DA = t0.neighbours[dest0], t1.neighbours[orig1], t1.neighbours[dest1], t0.neighbours[orig0]

        # link neighbours around quadrilateral to triangles as after the flip
        # -- the sides of the triangles around are stored in apex_around
        apex_around = []
        for neighbour, corner in zip([AB, BC, CD, DA],
                                     [A, B, C, D]):
            if neighbour is None:
                apex_around.append(None)
            else:
                apex_around.append(ccw(neighbour.vertices.index(corner)))
        # the triangles around we link to the correct triangle *after* the flip
        for neighbour, side, t in zip([AB, BC, CD, DA],
                                      apex_around,
                                      [t0, t0, t1, t1]):
            if neighbour is not None:
                self.link_1dir(neighbour, side, t)

        # -- set new vertices and neighbours
        # for t0
        t0.vertices = [A, B, C]
        t0.neighbours = [BC, t1, AB]
        # for t1
        t1.vertices = [C, D, A]
        t1.neighbours = [DA, t0, CD]
        # -- update coordinate to triangle pointers
        for v in t0.vertices:
            v.triangle = t0
        for v in t1.vertices:
            v.triangle = t1

    def link_2dir(self, t0, side0, t1, side1):
        """Links two triangles to each other over their common side
        """
        assert t0 is not None
        assert t1 is not None
        t0.neighbours[side0] = t1
        t1.neighbours[side1] = t0

    def link_1dir(self, t0, side0, t1):
        """Links triangle t0 to t1 for side0"""
        t0.neighbours[side0] = t1

def check_consistency(triangles):
    """Check a list of triangles for consistent neighbouring relationships

    For every triangle in the list
    it checks whether the triangle its neighbours also
    point back to this triangle.
    """
    errors = []
    for t in triangles:
        for n in t.neighbours:
            if n is not None:
                if t not in n.neighbours:
                    errors.append("{} {}".format(id(t), id(n)))
    if len(errors) > 0:
        raise ValueError("\n".join(errors))


# -----------------------------------------------------------------------------
# Constraints
#     The algorithm is described in:
#         Fast Segment Insertion and
#         Incremental Construction of Constrained Delaunay Triangulations
#         Jonathan Richard Shewchuk and Brielin C. Brown
#
#     Available from:
#         http://www.cs.berkeley.edu/~jrs/papers/inccdt.pdf
#

def triangle_overlaps_ray(vertex, towards):
    """Returns the triangle that overlaps the ray.
    In case there are multiple candidates,
    then the triangle with the right
    leg overlapping the ray is returned.
    It's a ValueError if no or multiple candidates are found.
    """
    candidates = []
    for edge in StarEdgeIterator(vertex):
        #if edge.isFinite:
        start, end = edge.segment
        # start: turns ccw
        # end: turns cw
        ostart = orient2d(start, towards, vertex)
        oend = orient2d(end, towards, vertex)
        if ostart >= 0 and oend <= 0:
            candidates.append((edge, ostart, oend))
    # the default, exactly one candidate
    if len(candidates) == 1:
        return candidates[0][0]
    # no candidates found,
    # this would be the case if towards lies outside
    # currently triangulated convex hull
    elif len(candidates) == 0:
        raise ValueError("No overlap found (towards outside triangulated convex hull?)")
    # the ray overlaps the legs of multiple triangles
    # only return the triangle for which the right leg overlaps with the ray
    # it is an error if there is not exactly one candidate that we can return
    else:
        ostartct = 0
        candidateIdx = None
        for i, (edge, ostart, oend) in enumerate(candidates):
            if ostart == 0:
                ostartct += 1
                candidateIdx = i
        if ostartct != 1 or candidateIdx is None:
            for i, (edge, ostart, oend) in enumerate(candidates):
                print ostart, oend
            raise ValueError("Incorrect number of triangles found")
        return candidates[candidateIdx][0]


def mark_cavity(P, Q, triangles):
    """Returns two lists: Edges above and below the list of triangles.
    These lists are sorted clockwise around the triangles
    (this is needed for CavityCDT).
    """
    # From a list of triangles make two lists of edges:
    # above and below...
    # It is made sure that the edges that are put
    # here are forming a polyline
    # that runs *clockwise* around the cavity
    assert len(triangles) != 0
    above = []
    below = []
    if len(triangles) == 1:
        t = triangles[0]
        pidx = t.vertices.index(P)
        lidx = (pidx + 1) % 3
        ridx = (pidx + 2) % 3
        l = t.vertices[lidx]
        #r = t.vertices[ridx]
#         print "p", P
#         print "q", Q
#         print "l", l
#         print "r", r
        assert l is Q
#         if l is Q:
#             print "L IS Q"
        below = []
        for i in (ridx,):
            n = t.neighbours[i]
            b = Edge(n, n.neighbours.index(t))
            #b = Edge(n, common(t, i, n))
            below.append(b)
        above = []
        for i in (lidx, pidx,):
            n = t.neighbours[i]
            #b = Edge(n, common(t, i, n))
            b = Edge(n, n.neighbours.index(t))
            above.append(b)
#             below = [Edge(t.getNeighbour(pidx), t.getOppositeSide(pidx))]
#             above = [Edge(t.getNeighbour(ridx), t.getOppositeSide(ridx)),
#                      Edge(t.getNeighbour(lidx), t.getOppositeSide(lidx))]

#         elif r is Q:
#             print "R IS Q"
#             below = []
#             for i in (pidx, lidx,):
#                 n = t.neighbours[i]
#                 b = Edge(n, common(t, i, n))
#                 below.append(b)
#             above = []
#             for i in (ridx,):
#                 n = t.neighbours[i]
#                 b = Edge(n, common(t, i, n))
#                 above.append(b)
#             above = [Edge(t.getNeighbour(ridx), t.getOppositeSide(ridx))]
#             below = [Edge(t.getNeighbour(lidx), t.getOppositeSide(lidx)),
#                      Edge(t.getNeighbour(pidx), t.getOppositeSide(pidx))
#         else:
#             raise ValueError("Combinations exhausted")
    else:
        # precondition here is that triangles their legs
        # do NOT overlap with the segment that goes
        # from P -> Q
        # thus: left and right orientation cannot both be 0
        # -> this is an error
        for t in triangles:
            for side in xrange(3):
                edge = Edge(t, side)
                R, L = edge.segment
                left = orient2d(L, Q, P)
                right = orient2d(R, Q, P)
                # in case both are 0 ... not allowed
                if (left == 0 and right == 0):
                    raise ValueError("Overlapping triangle leg found, not allowed")
                n = t.neighbours[side]
                e = Edge(n, n.neighbours.index(t))
                        # common(t, side, t.neighbours[side]))
                if left >= 0 and right >= 0:
                    below.append(e)
                elif right <= 0 and left <= 0:
                    above.append(e)
        below.reverse()
    return above, below

def straight_walk(P, Q):
    """Obtain the list of triangles that overlap
    the line segment that goes from Vertex P to Q.

    Note that P and Q must be Vertex objects that are in the Triangulation
    already.

    Raises a ValueError when either a Constrained edge is crossed in the
    interior of the line segment or when another Vertex lies on the
    segment.
    """
    edge = triangle_overlaps_ray(P, Q)
    t = edge.triangle
    side = edge.side
    R, L = edge.segment
    out = [t]
    if Q in t.vertices:
        # we do not need to go into walking mode if we found
        # the exact triangle with the end point already
        return out
    # perform walk
    #pos = t.vertices.index(R)

    # from end via right to left makes right turn (negative)
    # if line is collinear with end point then orientation becomes 0

    # FIXME:
    # The way that we now stop the rotation around the vertex
    # does that make a problem here --> we can get either the lower
    # or the upper triangle, this depends on the arbitrary start triangle
    while orient2d(Q, R, L) < 0.:
        # check if we do not prematurely have a orientation of 0
        # at either side, which means that we collide a vertex
        if (L is not Q and orient2d(L, P, Q) == 0) or \
            (R is not Q and orient2d(R, P, Q) == 0):
            raise TopologyViolationError("Unwanted vertex collision detected")

        # based on the position of R take next triangle
        # FIXME:
        # TEST THIS: check here if taking the neighbour does not take
        # place over a constrained side of the triangle -->
        # raise ValueError("Unwanted constrained segment collision detected")
#         if triangle.getEdgeType(side):
#             raise TopologyViolationError("Unwanted constrained segment collision detected")
        if t.constrained[side]:
            raise TopologyViolationError("Unwanted constrained segment collision detected")
        t = t.neighbours[side]
        out.append(t)

        side = t.vertices.index(R)
        S = t.vertices[ccw(side)]
        O = orient2d(S, Q, P)
        #
        if O < 0:
            L = S
            side = ccw(side+1)
        else:
            R = S
        # check if we do not prematurely have a orientation of 0
        # at either side, which means that we collide a vertex
        if (L is not Q and orient2d(L, P, Q) == 0) or \
            (R is not Q and orient2d(R, P, Q) == 0):
            raise TopologyViolationError("Unwanted vertex collision detected")

    return out

def permute(a, b, c):
    """Permutation of the triangle vertex indices from lowest to highest,
    i.e. a < b < c

    This order makes sure that a triangle is always addressed in the same way

    Used in CavityCDT.
    """
    return tuple(sorted([a, b, c]))


class ConstraintInserter(object):
    """Constraint Inserter

    Insert segments into a Delaunay Triangulation.
    """

    def __init__(self, triangulation):
        self.triangulation = triangulation

    def insert(self, segments):
        """Insert constraints into triangulation

        Parameter: segments - list of 2-tuples, with coordinate indexes
        """
        for j, segment in enumerate(segments):
            p, q = self.triangulation.vertices[segment[0]], self.triangulation.vertices[segment[1]]
            try:
                self.insert_constraint(p, q)
            except Exception, err:
                print err
            if (j % 10000) == 0:
                logging.debug( " " + str( datetime.now() ) + str( j ) )
        self.remove_empty_triangles()

    def remove_empty_triangles(self):
        """Removes empty triangles (not pointing to any vertex) by filtering
        the triangles that have one of its vertex members set
        """
        new = filter(lambda x: not(x.vertices[0] is None or x.vertices[1] is None or x.vertices[2] is None), self.triangulation.triangles)
        logging.debug( str( len(self.triangulation.triangles) ) + " (before) versus " + str( len(new) ) + " (after) triangle clean up" )
        self.triangulation.triangles = new

    def insert_constraint(self, P, Q):
        """Insert constraint into triangulation.

        It leaves the triangles that are removed inside the cavity of
        the constraint inserted in the triangles array
        """
        if P is Q:
            raise DuplicatePointsFoundError("Equal points found for inserting constraint")
        cavity = straight_walk(P, Q)
        above, below = mark_cavity(P, Q, cavity)
        # change triangle pointers of vertices around the cavity to point to
        # triangles that lie outside the cavity (as these will be removed later)
        for edge in chain(above, below):
            for vertex in edge.segment:
                vertex.triangle = edge.triangle
        # Re-triangulate upper half
        cavA = CavityCDT(self.triangulation, above)
        A = cavA.edge
        # Re-triangulate bottom half
        cavB = CavityCDT(self.triangulation, below)
        B = cavB.edge
        # link up the two triangles at both sides of the segment
        A.triangle.neighbours[A.side] = B.triangle
        B.triangle.neighbours[B.side] = A.triangle
        # constrained edges
        A.triangle.constrained[A.side] = True
        B.triangle.constrained[B.side] = True
        for t in cavity:
            t.vertices = [None, None, None]
            t.neighbours = [None, None, None]


class CavityCDT(object):
    """Class to triangulate an `evacuated' cavity adjacent to a constraint
    """

    def __init__(self,
                 triangulation,
                 cavity_edges):
        """
        triangulation - the triangulation data structure
        cavity_edges - the edges that bound the cavity
        in *CLOCKWISE* order
        around the cavity. Note: these edges do not include the segment
        to be inserted.
        """
        # WARNING: The ordering of vertices
        # around the cavity is important to function correctly!
        self.vertices = []
        self.edge = None
        self.triangulation = triangulation

        # If we found exactly one cavity edge, there is no
        # area between ray and cavity polygon. Hence this edge
        # should be the one that will be linked to (after that we've
        # set the type of this edge to constrained).
        if len(cavity_edges) == 1:
            edge = cavity_edges[0]
            # will be carried out by caller
            # edge.triangle.setEdgeType(edge.side, True)
            self.edge = edge
            return
        self._preprocess(cavity_edges)
        self._retriangulate()
        self._push_back_triangles()

    def _preprocess(self, cavity_edges):
        """Set up data structures needed for the re-triangulation part of the
        algorithm.
        """
        self.constraints = set()
        for i, edge in enumerate(cavity_edges):
            xx, yy = edge.segment
            # Both directions are needed, as this is used
            # for internal dangling edges inside the cavity,
            # which are traversed both sides.
            self.constraints.add((id(xx), id(yy)))
            self.constraints.add((id(yy), id(xx)))
            if i:
                self.vertices.append(yy)
            else:
                self.vertices.extend([xx, yy])
        # Make the vertices list COUNTERCLOCKWISE here
        # The algorithm depends on this orientation!
        self.vertices.reverse()
        self.surroundings = {}
        for i, edge in enumerate(cavity_edges):
            s = edge.segment
            self.surroundings[id(s[0]), id(s[1])] = edge
        # Make a "linked list" of polygon vertices
        self.next = {}
        self.prev = {}
        # Relative size of distances to the segment
        self.distance = {}
        # Adjacency: third point of a triangle by given oriented side
        self.adjacency = {}
        # Set of resulting triangles (vertex indices)
        self.triangles = set()
        # Initialization for the algorithm
        m = len(self.vertices)
        # Make random permutation of point indices
        self.pi = range(1, m - 1)
        # Randomize processing order
        shuffle(self.pi)
        # Link all vertices in a circular list that
        # describes the polygon outline of the cavity
        for i in range(m):
            self.next[i] = (i + 1) % m
            self.prev[i] = (i - 1) % m
            # Distance to the segment from [0-m]
            self.distance[i] = orient2d(self.vertices[0],
                                        self.vertices[i],
                                        self.vertices[m-1])

    def _retriangulate(self):
        """Re-triangulate the cavity, the result is a collection of
        triangles that can be pushed back into the original triangulation data
        structure that replaces the old triangles inside the cavity.
        """
        # Now determine how to `remove' vertices
        # from the outline in random order
        #
        # Go over pi from back to start; quit at *second* item in pi
        # This determines order of removal of vertices from
        # the cavity outline polygon
        m = len(self.vertices)
        for i in range(len(self.pi) - 1, 0, -1):
            while self.distance[self.pi[i]] < self.distance[self.prev[self.pi[i]]] and \
                self.distance[self.pi[i]] < self.distance[self.next[self.pi[i]]]:
                # FIXME: is j correct ??? should i be i + 1 ?
                j = randint(0, i)
                self.pi[i], self.pi[j] = self.pi[j], self.pi[i]
            # take a vertex out of the circular list
            self.next[self.prev[self.pi[i]]] = self.next[self.pi[i]]
            self.prev[self.next[self.pi[i]]] = self.prev[self.pi[i]]
        # add an initial triangle
        self._add_triangle(0, self.pi[0], m-1)
        # Work through the settled order of vertex additions
        # Now in forward direction, keep adding points until all points
        # are added to the triangulation of this part of the cavity
        for i in range(1, len(self.pi)):
            a = self.pi[i]
            b, c = self.next[a], self.prev[a]
            self._insert_vertex(a,b,c)

    def _push_back_triangles(self):
        """Make new triangles that are inserted in the data structure
        and that are linked up properly with each other and the surroundings.
        """

        # First make new triangles
        newtris = {}
        for three in self.triangles:
            a, b, c, = three
            # Index triangle by temporary sorted list of vertex indices
            #
            # By indexing triangles this way, we
            T = Triangle(self.vertices[a],
                       self.vertices[b],
                       self.vertices[c])
            newtris[permute(id(T.vertices[0]), id(T.vertices[1]), id(T.vertices[2]))] = T
        for x in newtris.itervalues():
            assert orient2d(x.vertices[0], x.vertices[1], x.vertices[2]) > 0
        # Translate adjacency table to new indices of triangles
        # Note that vertices that are used twice (because of dangling edge
        # in the cavity) will get the same identifier again
        # (while previously they would have different id's).
        adj = {}
        for (f, t), v in self.adjacency.iteritems():
            adj[id(self.vertices[f]), id(self.vertices[t])] = id(self.vertices[v])
        # Link all the 3 sides of the new triangles properly
        for T in newtris.itervalues():
            for i in range(3):
                segment = Edge(T, i).segment
                side = (id(segment[1]), id(segment[0]))
                constrained = False
                # The side is adjacent to another new triangle
                # The neighbouring triangle at this side will be linked later
                # In case this is a dangling segment we constrain the segment
                if side in adj:
                    neighbour = newtris[permute(side[0], side[1], adj[side])]
                    if side in self.constraints:
                        constrained = True
                # the side is adjacent to an exterior triangle
                # that lies outside the cavity and will
                # remain after the re-triangulation
                # therefore also change the neighbour of this triangle
                elif side in self.surroundings:
                    neighbour_side = self.surroundings[side].side
                    neighbour = self.surroundings[side].triangle
                    neighbour.neighbours[neighbour_side] = T # MM fixed
                    constrained = neighbour.constrained[neighbour_side] #getEdgeType(neighbour_side)
                # the triangle is the bottom of the evacuated cavity
                # hence it should be linked later to the other
                # re-triangulation of the cavity
                else:
                    assert self.edge is None
                    neighbour = None
                    self.edge = Edge(T, i)
                T.neighbours[i] = neighbour #setNeighbour(i, neighbour)
                # T.setEdgeType(i, constrained)
                T.constrained[i] = constrained
            # Append the new triangles to the triangle list of the
            # triangulation
            self.triangulation.triangles.append(T)
        assert self.edge is not None

    def _insert_vertex(self, u, v, w):
        """Insert a vertex to the triangulated area,
        while keeping the area of the current polygon triangulated
        """
        x = -1
        # Find third vertex in the triangle that has edge (w, v)
        if (w, v) in self.adjacency:
            x = self.adjacency[(w, v)]
        # See if we have to remove some triangle(s) already there,
        # or that we can add just a new one
        if x != -1 and \
            (orient2d(self.vertices[u],
                      self.vertices[v],
                      self.vertices[w]) <= 0 or \
            incircle(self.vertices[u],
                     self.vertices[v],
                     self.vertices[w],
                     self.vertices[x]) > 0):
            # Remove triangle (w,v,x), also from adjacency dict
            self.triangles.remove(permute(w, v, x))
            del self.adjacency[(w, v)]
            del self.adjacency[(v, x)]
            del self.adjacency[(x, w)]
            # Recurse
            self._insert_vertex(u, v, x)
            self._insert_vertex(u, x, w)
        else:
            # Add a triangle (this triangle could be removed later)
            self._add_triangle(u, v, w)

    def _add_triangle(self, a, b, c):
        """Add a triangle to the temporary set of triangles

        It is not said that a triangle that is added,
        survives until the end of the algorithm
        """
        t = permute(a, b, c)
        P = {}
        P[(a, b)] = c
        P[(b, c)] = a
        P[(c, a)] = b
        # .update() overwrites existing keys
        # (but these should not exist anyway)
        self.adjacency.update(P)
        # A triangle is stored with vertices in ordered indices
        self.triangles.add(t)



class VoronoiTransformer(object):
    """Class to transform a Delaunay triangulation into a Voronoi diagram
    """

    def __init__(self, triangulation):
        self.triangulation = triangulation

    def transform(self):
        self.centers = {}
        for t in self.triangulation.triangles:
            self.centers[id(t)] = self.incenter(t)
        segments = []
        for t in self.triangulation.triangles:
            for n in t.neighbours:
                if n is not None and \
                    n is not self.triangulation.external and \
                    id(t) < id(n):
                    segment = id(t), id(n)
                    segments.append(segment)
        self.segments = segments

    def incenter(self, t):
        p0, p1, p2, = t.vertices
        ax, ay, bx, by, cx, cy, = p0.x, p0.y, p1.x, p1.y, p2.x, p2.y
        a2 = pow(ax, 2) + pow(ay, 2)
        b2 = pow(bx, 2) + pow(by, 2)
        c2 = pow(cx, 2) + pow(cy, 2)
        UX = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by))
        UY = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax))
        D = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        ux = UX / D
        uy = UY / D
        return (ux, uy)

# ------------------------------------------------------------------------------
# Preprocessing methods to randomize points, but give enough spatial coherence
# to be robust against worst case behaviour of Lawson's flipping algorithm
#
# If all is well, this limits the number of flips that have to be executed,
# improving runtime performance
#
# The algorithm is described in:
#
# HCPO: an efficient insertion order for incremental Delaunay triangulation
# Sheng Zhou and Christopher B. Jones
# Information Processing Letters
# Volume 93 Issue 1, 16 January 2005
# Pages 37-42
# https://users.cs.cf.ac.uk/C.B.Jones/ZhouJonesIPL.pdf
# doi: 10.1016/j.ipl.2004.09.020
#

def cpo(points, c=0.5):
    """Column prime order for a set of points"""
    result = []
    (xmin, ymin), (xmax, ymax) = box(points)
    # width, height
    W = float(xmax - xmin)
    H = float(ymax - ymin)
    if H == 0:
        # prevents division by zero when calculating m
        H = 1.
    # sort on widest axis
    if W < H:
        axis = 1
    else:
        axis = 0
    points.sort(key=itemgetter(axis))
    # number of points to sort
    n = len(points)
    # determine bin size: how many bins do we need?
    m = int(ceil(c * ceil(sqrt( n * W / H ))))
    if m == 0:
        # pathological case, no sampled points, so make it same as
        # number of points left
        m = n
    M = int(ceil(float(n) / float(m)))
    for i in xrange(m):
        j = i + 1
        # get bounds for this slot
        f, t = i * M, j * M
        slot = points[f:min(t, n)]
        # sort on other axis, in case even slot, in reversed order
        even = (j % 2) == 0
        slot.sort(key=itemgetter((axis+1)%2), reverse=even)

        # taking the same axis for sorting
#         slot.sort(key=itemgetter(axis), reverse=even) # twice as slow
        result.extend(slot)
    return result

def _hcpo(points, out, sr = 0.75, minsz = 10):
    """Constructs a hierarchical set of ordered points `out'

    Every level in the hierarchy is ordered along a column prime curve,
    similar to:

    >-------------------+
                        |
    +-------------------+
    |
    +-------------------+
                        |
    <-------------------+
    """
    # shuffle(points) # always randomize even for small points
    stack = [points]
    while stack:
        # split the remaining list in 2 pieces
        # tail will be processed (sorted and cut into slots)
        # head will be recursed on if it has enough points
        points = stack.pop()
        N = len(points)
        up = int(ceil(N*sr))
        head, tail = points[0:up], points[up:]
        if tail:
            ordered = cpo(tail)
            out.extend(ordered)
        if len(head) >= ceil(minsz / sr):
            shuffle(head)
            stack.append(head)
        else:
            ordered = cpo(head)
            out.extend(ordered)

def hcpo(points, sr = 0.75, minsz = 10):
    """Based on list with points, return a new, randomized list with points
    where the points are randomly ordered, but then sorted with enough spatial
    coherence to be useful to not get worst case flipping behaviour
    """
    # Build a new list with points, ordered along hierarchical curve
    # with levels
    if len(points) == 0:
        raise ValueError("not enough points")
    out = []
    _hcpo(points, out, sr, minsz)
    return out

# def show_circ():
#     print "circle ccw"
#     for i in range(3):
#         print "", i, "next", ccw(i)
#     print "circle cw"
#     for i in range(2, -1, -1):
#         print "", i, "prev", cw(i)
#
# def out(v):
#     with open("/tmp/vertices.wkt", "w") as fh:
#         print >> fh, "x;y"
#         print >> fh, "\n".join(["{x};{y}".format(x=x,y=y) for (x,y) in v])


# ------------------------------------------------------------------------------
# Generate randomized point sets (for testing purposes)
#

def random_sorted_vertices(n = 10):
    """Returns a list with n random vertices
    """
    from random import randint
    W = float(n)
    vertices = []
    for _ in xrange(n):
        x = randint(0, W)
        y = randint(0, W)
        x /= W
        y /= W
        vertices.append((x,y))
    vertices = list(set(vertices))
    vertices.sort()
    return vertices

def random_circle_vertices(n = 10, cx = 0, cy = 0):
    """Returns a list with n random vertices in a circle

    Method according to:

    http://www.anderswallin.net/2009/05/uniform-random-points-in-a-circle-using-polar-coordinates/
    """
    vertices = []
    for _ in xrange(n):
        r = sqrt(random()) #
        t = 2 * pi * random() #
        x = r * cos(t)
        y = r * sin(t)
        vertices.append((x+cx, y+cy))
    vertices = list(set(vertices))
    vertices.sort()
    return vertices


# -----------------------------------------------------------------------------
# Test methods
#

def test_circle():
    """Test points in some clusters.
    """
    n = 15000
    vertices = random_circle_vertices(n, 0, 0)
    vertices.extend(random_circle_vertices(n, 3, 4.5))
    vertices.extend(random_circle_vertices(n, 4.6, 0.2))
    vertices.extend(random_circle_vertices(n, 7, 2.5))
    vertices.extend(random_circle_vertices(n, 5, -5))
    vertices.extend(random_circle_vertices(n, 10, 5))
    vertices.extend(random_circle_vertices(n, 9, -1))
    vertices.extend(random_circle_vertices(n, 15, -5))
    triangulate(vertices)

def test_incremental():
    L = random_sorted_vertices(n = 125000)
    tds = triangulate(L)
    with open("/tmp/alltris.wkt", "w") as fh:
                output_triangles([t for t in TriangleIterator(tds,
                                                              finite_only=False)],
                                 fh)
    with open("/tmp/allvertices.wkt", "w") as fh:
        output_vertices(tds.vertices, fh)

def test_cpo():
    # i = 1, j = 100 -> worst case, all end up as 1 point in slot
    # --> would be better to switch then to other order
    points = []
    idx = 0
    for i in range(400):
        for j in range(400):
            points.append((i, j, None, idx))
            idx += 1
    points_hcpo = hcpo(points)
    assert len(points) == len(points_hcpo)
    #print points
    # build a translation table for indices in the points list
#     index_translation = dict([(newpos, pos) for (newpos, (_, _, _, pos)) in enumerate(points_hcpo)])
    #print index_translation
    with open("/tmp/points.txt", "w") as fh:
        print >> fh, "i;wkt"
        for i, pt in enumerate(points_hcpo):
            print >> fh, i, ";POINT({0[0]} {0[1]})".format(pt)

def test_square():
    triangulate([(0.,0.), (10.,0.), (10., 10.), (0.,10.)],
                [(0,1), (1,2), (2,3), (3,0)])


class ToPointsAndSegments(object):
    """Helper class to convert a set of polygons to points and segments.
    De-dups duplicate points.
    """

    def __init__(self):
        self.points = []
        self.segments = []
        self.infos = []
        self._points_idx = {}

    def add_polygon(self, polygon):
        """Add a polygon its points and segments to the global collection
        """
        for ring in polygon:
            for pt in ring:
                self.add_point(pt)
            for start, end in zip(ring[:-1], ring[1:]):
                self.add_segment(start, end)

    def add_point(self, point, info = None):
        """Add a point and its info.

        Note that if a point already is present,
        it is not appended nor is its info added to the infos list.
        """
        if point not in self._points_idx:
            idx = len(self.points)
            self._points_idx[point] = idx
            self.points.append(point)
            if info is not None:
                self.infos.append((idx, info))
        else:
            idx = self._points_idx[point]
        return idx

    def add_segment(self, start, end):
        """Add a segment. Note that points should have been added before
        """
        self.segments.append((self._points_idx[start], self._points_idx[end]))

def test_poly():
    from connection import connection
    db = connection(True)

    def polygon_input(lines):
        points = []
        segments = []
        points_idx = {}
        for line in lines:
            for pt in line:
                if pt not in points_idx:
                    points_idx[pt] = len(points)
                    points.append(pt)
            for start, end in zip(line[:-1], line[1:]):
                segments.append((points_idx[start], points_idx[end]))
        return points, segments

    lines = []
    sql = 'select geometry from clc_edge where left_face_id in (45347) or right_face_id in (45347)'
    #sql = 'select geometry from clc_edge where left_face_id in (28875) or right_face_id in (28875)'
    # 45270
    sql = 'select geometry from clc_edge where left_face_id in (45270) or right_face_id in (45270)'
    for geom, in db.recordset(sql):
        lines.append(geom)
    points, segments = polygon_input(lines)
    dt = triangulate(points, segments)
    #
    if False:
        trafo = VoronoiTransformer(dt)
        trafo.transform()
        with open("/tmp/centers.wkt", "w") as fh:
            fh.write("wkt\n")
            for incenter in trafo.centers.itervalues():
                fh.write("POINT({0[0]} {0[1]})\n".format(incenter))
        with open("/tmp/segments.wkt", "w") as fh:
            fh.write("wkt\n")
            for segment in trafo.segments:
                # FIXME: why are some not coming through?
                try:
                    fh.write("LINESTRING({0[0]} {0[1]}, {1[0]} {1[1]})\n".format(trafo.centers[segment[0]],
                                                                             trafo.centers[segment[1]]))
                except:
                    pass
    if True:
        with open("/tmp/alltris.wkt", "w") as fh:
                    output_triangles([t for t in TriangleIterator(dt,
                                                                  finite_only=False)],
                                     fh)
        with open("/tmp/allvertices.wkt", "w") as fh:
            output_vertices(dt.vertices, fh)
        with open("/tmp/interiortris.wkt", "w") as fh:
                    output_triangles([t for t in InteriorTriangleIterator(dt)], fh)

def test_small():
#     pts = [(3421275.7657, 3198467.4977),
#            (3421172.5598, 3198197.546)
#            ]
#     triangulate(pts)
    # triangulate([(0,0), (0, -1)])
    #triangulate([(0,0)])
#     buggy = [(-120,90),(-60,40), (0,0),]# (-45, 35)]
#     triangulate(buggy)
#     triangulate([(0,0), (0,-20)])
    triangulate([(0,0), (10, 6), (6.5, 1.5), (2,3),(40,-20), (15, -4), (-120,90), (-60,40), (-45, 35)])
    #triangulate([(0,0), (-10, 6)])
#     triangulate([(0,0), (0, -6)])

if __name__ == "__main__":
#     test_small()
    test_poly()
#     test_square()
#     test_circle()
#     test_incremental()

#     test_cpo()
#     test_flip()
#    test_sorted()
#     test_tds()
#    test_sorted()
#     main()
#     test_link()
