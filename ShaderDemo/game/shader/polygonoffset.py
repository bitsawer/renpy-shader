
import math

def calcoffsetpoint(pt1, pt2, offset):
    """
    Get a point offset from the line
    segment pt1-pt2 distance "offset".

    Return two tuple of coordinates.
    """
    theta = math.atan2(pt2[1] - pt1[1],
                       pt2[0] - pt1[0])
    theta += math.pi/2.0
    return (pt1[0] - math.cos(theta) * offset,
            pt1[1] - math.sin(theta) * offset)

def getoffsetintercept(pt1, pt2, m, offset):
    """
    From points pt1 and pt2 defining a line
    in the Cartesian plane, the slope of the
    line m, and an offset distance,
    calculates the y intercept of
    the new line offset from the original.
    """
    x, y = calcoffsetpoint(pt1, pt2, offset)
    return y - m * x

def getpt(pt1, pt2, pt3, offset):
    """
    Gets intersection point of the two
    lines defined by pt1, pt2, and pt3;
    offset is the distance to offset
    the point from the polygon.

    Valid for lines with slopes other
    than zero or infinity.

    Returns a two tuple of coordinates.
    """
    # get first offset intercept
    m = (pt2[1] - pt1[1])/(pt2[0] - pt1[0])
    boffset = getoffsetintercept(pt1, pt2, m, offset)
    # get second offset intercept
    mprime = (pt3[1] - pt2[1])/(pt3[0] - pt2[0])
    boffsetprime = getoffsetintercept(pt2, pt3, mprime, offset)
    # get intersection of two offset lines
    newx = (boffsetprime - boffset)/(m - mprime)
    newy = m * newx + boffset
    return newx, newy

def getslopeandintercept(pt1, pt2, offset):
    """
    Gets the slope and the intercept of the
    offset line.
    Result returned as a two tuple.
    """
    m = (pt2[1] - pt1[1])/(pt2[0] - pt1[0])
    b = getoffsetintercept(pt1, pt2, m, offset)
    return m, b

def getoffsetcornerpoint(pt1, pt2, pt3, offset):
    """
    Gets intersection point of the two
    lines defined by pt1, pt2, and pt3;
    offset is the distance to offset
    the point from the polygon.

    Returns a two tuple of coordinates.
    """
    # starting out with horizontal line
    if (pt2[1] - pt1[1]) == 0.0:
        ycoord = pt1[1] - math.cos(math.atan2(0.0, pt2[0] - pt1[0])) * offset
        # a vertical line follows
        if (pt3[0] - pt2[0]) == 0.0:
            xcoord = pt2[0] + math.sin(math.atan2(pt3[1] - pt2[1], 0.0)) * offset
        # a sloped line follows
        else:
            m, offsetintercept = getslopeandintercept(pt2, pt3, offset)
            # calculate for x with ycoord
            xcoord = (ycoord - offsetintercept)/m
    # starting out with a vertical line
    if (pt2[0] - pt1[0]) == 0.0:
        xcoord = pt1[0] + math.sin(math.atan2(pt2[1] - pt1[1], 0.0)) * offset
        # a horizontal line follows
        if (pt3[1] - pt2[1]) == 0.0:
            ycoord = pt2[1] - math.cos(math.atan2(0.0, pt3[0] - pt2[0])) * offset
        # a sloped line follows
        else:
            m, offsetintercept = getslopeandintercept(pt2, pt3, offset)
            # calculate for y with xcoord
            ycoord = m * xcoord + offsetintercept
    # starting out with sloped line
    if (pt2[1] - pt1[1]) != 0.0 and (pt2[0] - pt1[0]) != 0.0:
        # if second line is horizontal
        if (pt3[1] - pt2[1]) == 0.0:
            ycoord = pt2[1] - math.cos(math.atan2(0.0, pt3[0] - pt2[0])) * offset
            m, offsetintercept = getslopeandintercept(pt1, pt2, offset)
            # calculate for x with y coord
            xcoord = (ycoord - offsetintercept)/m
        # if second line is vertical
        elif (pt3[0] - pt2[0]) == 0.0:
            xcoord = pt2[0] + math.sin(math.atan2(pt3[1] - pt2[1], 0.0)) * offset
            m, offsetintercept = getslopeandintercept(pt1, pt2, offset)
            # solve for y with x coordinate
            ycoord = m * xcoord + offsetintercept
        # if both lines are sloped
        else:
            xcoord, ycoord = getpt(pt1, pt2, pt3, offset)
    return xcoord, ycoord

def offsetpolygon(polyx, offset):
    """
    Offsets a clockwise list of coordinates
    polyx distance offset to the inside of
    the polygon.
    Returns list of offset points.
    """
    polyy = []
    # need three points at a time
    for counter in range(0, len(polyx) - 3):
        # get first offset intercept

        pt = getoffsetcornerpoint(polyx[counter],
                   polyx[counter + 1],
                   polyx[counter + 2],
                   offset)
        # append new point to polyy
        polyy.append(pt)


    #try:
    # last three points
    pt = getoffsetcornerpoint(polyx[-3], polyx[-2], polyx[-1], offset)
    polyy.append(pt)
    pt = getoffsetcornerpoint(polyx[-2], polyx[-1], polyx[0], offset)
    polyy.append(pt)
    pt = getoffsetcornerpoint(polyx[-1], polyx[0], polyx[1], offset)
    polyy.append(pt)
    #except ZeroDivisionError:
    #    pass

    return polyy
