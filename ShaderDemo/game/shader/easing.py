
import math

def linear(pos):
    return pos

def inQuad(pos):
    return pow(pos, 2)

def outQuad(pos):
    return -(pow((pos - 1), 2) -1)

def inOutQuad(pos):
    pos /= 0.5
    if pos < 1:
        return 0.5 * pow(pos, 2);
    pos -= 2
    return -0.5 * (pos * pos - 2);

def inSine(pos):
    return -math.cos(pos * (math.pi / 2)) + 1

def outSine(pos):
    return math.sin(pos * (math.pi / 2))

def inOutSine(pos):
    return (-0.5 * (math.cos(math.pi * pos) - 1))

def inCirc(pos):
    return -(math.sqrt(1 - (pos * pos)) - 1)

def outCirc(pos):
    return math.sqrt(1 - pow(pos - 1, 2))

def inOutCirc(pos):
    pos /= 0.5
    if pos < 1:
        return -0.5 * (math.sqrt(1 - pos * pos) - 1)
    pos -= 2
    return 0.5 * (math.sqrt(1 - pos*pos) + 1)

def inBack(pos):
    s = 1.70158
    return pos * pos * ((s + 1) * pos - s)

def outBack(pos):
    s = 1.70158
    pos = pos - 1
    return pos * pos * ((s + 1) * pos + s) + 1

def inOutBack(pos):
    s = 1.70158 * 1.525
    pos /= 0.5
    if pos < 1:
        return 0.5 * (pos * pos * ((s + 1) * pos - s))
    pos -= 2
    return 0.5 * (pos * pos * ((s + 1) * pos +s) + 2)

def swingFrom(pos):
    s = 1.70158
    return pos * pos * ((s + 1) * pos - s)

def swingTo(pos):
    s = 1.70158
    pos -= 1
    return pos * pos * ((s + 1) * pos + s) + 1

def swingFromTo(pos):
    s = 1.70158 * 1.525
    pos /= 0.5
    if pos < 1:
        return 0.5 * (pos * pos * ((s + 1) * pos - s))
    pos -= 2
    return 0.5 * (pos * pos * ((s + 1) * pos + s) + 2)

def elastic(pos):
    return -1 * pow(4, -8 * pos) * math.sin((pos * 6 - 1) * (2 * math.pi) / 2) + 1

def bounce(pos):
    if pos < (1 / 2.75):
        return 7.5625 * pos * pos
    elif pos < (2 / 2.75):
        pos -= (1.5/2.75)
        return 7.5625 * pos * pos + 0.75
    elif (pos < (2.5 / 2.75)):
        pos -= 2.25 / 2.75
        return 7.5625 * pos * pos + 0.9375
    else:
        pos -= 2.625 / 2.75
        return 7.5625 * (pos) * pos + 0.984375

EASINGS = {
    "linear": linear,

    "inQuad": inQuad,
    "outQuad": outQuad,
    "inOutQuad": inOutQuad,

    "inSine": inSine,
    "outSine": outSine,
    "inOutSine": inOutSine,

    "inCirc": inCirc,
    "outCirc": outCirc,
    "inOutCirc": inOutCirc,

    "inBack": inBack,
    "outBack": outBack,
    "inOutBack": inOutBack,

    "swingFrom": swingFrom,
    "swingTo": swingTo,
    "swingFromTo": swingFromTo,

    "elastic": elastic,
    "bounce": bounce,
}

