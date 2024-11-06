import cairo
import sys
import pathlib
import math

WIDTH = 256
HEIGHT = 256

RADIUS = 0.45
NODE_RADIUS = 0.02

SKELETON_WIDTH = 0.015
CHORD_WIDTH = 0.01

RIGIDITY = 6


class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        else:
            return NotImplemented

    def __sub__(self, other):
        return self + (-1 * other)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Point(other * self.x, other * self.y)
        else:
            return NotImplemented

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return (1 / other) * self

    def as_tuple(self):
        return self.x, self.y

    def __abs__(self):
        return math.dist(self.as_tuple(), (0, 0))

    def __getitem__(self, index):
        if isinstance(index, int):
            if index == 0:
                return self.x
            if index == 1:
                return self.y
            else:
                raise IndexError("Point index out of range")
        else:
            return NotImplemented


def parse(args):
    if len(args) < 2:
        raise ValueError("Not enough arguments.")

    candidate = args[1:]
    appearances = {}
    for word in candidate:
        if word not in appearances:
            appearances[word] = 1
        else:
            appearances[word] += 1
    input_valid = all(count == 2 for count in appearances.values())

    if input_valid:
        return candidate, len(candidate) / 2
    else:
        raise ValueError("Arguments don't form valid chord diagram")


def clock_dict(chordword):
    clock_dict = {}
    for i, w in enumerate(chordword):
        if w not in clock_dict:
            clock_dict[w] = [i]
        else:
            clock_dict[w].append(i)
    return clock_dict


def main():

    chordword, n = parse(sys.argv)
    clock = clock_dict(chordword)

    parent = pathlib.Path(__file__).resolve().parent
    outpath = parent / "out.svg"

    surface = cairo.SVGSurface(outpath, WIDTH, HEIGHT)
    surface.set_document_unit(7)
    context = cairo.Context(surface)

    # Make a right-handed coordinate system with the origin at the centre.
    context.scale(WIDTH, -HEIGHT)
    context.translate(0.5, -0.5)

    # Draw the skeleton.
    context.set_line_width(SKELETON_WIDTH)
    context.arc(0, 0, RADIUS, 0, 2 * math.pi)
    context.stroke()

    # Figure out how to draw chords...
    def place_chord(s, t):
        s = math.pi * s / n
        t = math.pi * t / n

        p = Point(RADIUS * math.cos(s), RADIUS * math.sin(s))
        q = Point(RADIUS * math.cos(t), RADIUS * math.sin(t))
        o = Point(0, 0)

        weight = RIGIDITY * (1 + math.cos(2 * (t - s))) / 2

        def weighted_midpoint(a, b, w):
            return w * a + (1 - w) * b

        p_mid_ctrl = weighted_midpoint(o, p, weight)
        q_mid_ctrl = weighted_midpoint(o, q, weight)

        p_q_ctrl = p + (q - p) * (abs(p - p_mid_ctrl) / abs(p - q))
        q_p_ctrl = q + (p - q) * (abs(q - q_mid_ctrl) / abs(q - p))

        p_ctrl = (p_mid_ctrl + p_q_ctrl) / 2
        q_ctrl = (q_mid_ctrl + q_p_ctrl) / 2

        context.set_line_width(CHORD_WIDTH)
        context.move_to(*p)
        context.curve_to(*p_ctrl, *q_ctrl, *q)
        context.stroke()

        # ...and nodes.
        context.arc(*p, NODE_RADIUS, 0, 2 * math.pi)
        context.fill()
        context.arc(*q, NODE_RADIUS, 0, 2 * math.pi)
        context.fill()

    # Draw all of the chords and nodes.
    for chord in clock.values():
        place_chord(*chord)

    surface.finish()


if __name__ == "__main__":
    main()
