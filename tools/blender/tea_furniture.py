"""Solid-wood tea chairs with low guest backs and a larger host's armchair."""

from math import cos, pi, radians, sin

from mathutils import Vector

from interior_geometry import rounded_outline


WOOD = 'teaWood'
PANEL = 'teaPanel'


def curved_member(g, parent, name, points, radius, closed=False):
    """Round a wooden member along a smooth curve through its joints."""
    knots = [Vector(point) for point in points]
    path = []
    for i in range(len(knots) if closed else len(knots) - 1):
        a = knots[i - 1] if i or closed else knots[0]
        b, c = knots[i], knots[(i + 1) % len(knots)]
        d = knots[(i + 2) % len(knots)] if closed else knots[min(i + 2, len(knots) - 1)]
        for t in (0, .25, .5, .75):
            path.append((2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                         + (3 * b - a - 3 * c + d) * t * t * t) * .5)
    if not closed:
        path.append(knots[-1])
    return g.tube(parent, name, WOOD, path, radius, sides=12, closed=closed)


def back_splat(g, parent, w, seat, crest, host):
    start = seat - .011
    height = crest[2] - start
    depth = .012 if host else .0095

    def center(t):
        return crest[1] - .040 * (1 - t) - .040 * sin(pi * t) + .014 * sin(2 * pi * t)

    sides = 16
    verts = []
    for row in range(13):
        t = row / 12
        half_width = w * (.16 if host else .116) * (.77 + .23 * cos(pi * (t - .74)))
        verts.extend((x, center(t) + y, start + t * height)
                     for x, y in rounded_outline(half_width, depth, .28, sides))
    faces = [tuple(reversed(range(sides)))]
    for low in range(0, len(verts) - sides, sides):
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((low + i, low + j, low + j + sides, low + i + sides))
    faces.append(tuple(range(len(verts) - sides, len(verts))))
    uv = [[(verts[i][0] * 3.5 + verts[i][1] * .4, verts[i][2] * .9) for i in face] for face in faces]
    g.mesh(parent, 'S-curved solid back splat', verts, faces, PANEL, uv=uv, smooth=True)

    if host:
        z = start + height * .78
        outline = [(-.058, .008), (-.043, .027), (-.024, .027), (0, .046), (.024, .027),
                   (.043, .027), (.058, .008), (.040, -.014), (.019, -.013), (0, -.029),
                   (-.019, -.013), (-.040, -.014)]
        curved_member(g, parent, 'Small ruyi relief on host back',
                      [(x, center((z + dz - start) / height) - depth - .001, z + dz)
                       for x, dz in outline], .0031, closed=True)


def wooden_chair(g, parent, size, host):
    w, d, h = size
    seat = .466 if host else .448
    seat_w = w * (.85 if host else .925)
    seat_d = d * (.82 if host else .91)
    leg = .020 if host else .0165
    corner = seat_w / 2 - .028
    front = -seat_d / 2 + .032
    rear = seat_d / 2 - .036

    g.box(parent, 'Rounded solid-wood seat frame', WOOD, (0, 0, seat - .022), (seat_w, seat_d, .044), .015, grain='y')
    g.box(parent, 'Framed solid seat panel', PANEL, (0, 0, seat + .004), (seat_w - .048, seat_d - .052, .014), .006, grain='y')
    g.box(parent, 'Recessed front apron', WOOD, (0, front, seat - .063), (2 * corner, .026, .045), .008, grain='x')

    def hoop(t):
        drop = (1 - cos(t)) / (1 - cos(1.67))
        return ((w / 2 - .017) * sin(t), d * (.439 - .827 * drop), h - .016 - (h - .686) * drop)

    def crown(t):
        return (t * (w / 2 - .019), d * .441 - .017 * t * t,
                h - .019 - .029 * sin(pi * abs(t)) + .002 * abs(t))

    crest = crown if host else hoop
    span = 1 if host else 1.67
    g.tube(parent, 'Swept crest rail' if host else 'Continuous horseshoe rail', WOOD,
           [crest(span * (i / 12 - 1)) for i in range(25)], .0175 if host else .016, sides=12)
    back_splat(g, parent, w, seat, crest(0), host)

    for side in (-1, 1):
        x = side * corner
        g.lathe(parent, 'Tapered front leg', WOOD, (x, front, 0), [
            (0, 0), (leg * .73, 0), (leg * .80, .024), (leg * .87, .15),
            (leg, seat - .04), (leg, seat - .018), (0, seat - .018),
        ], segments=12)
        back = crest(side * (.82 if host else .68))
        if host:
            arm = [(side * w * (.38 + .089 * t), d * (.350 - .788 * t), .781 - .086 * t + .013 * sin(pi * t))
                   for t in (0, .20, .40, .60, .80, 1)]
            curved_member(g, parent, 'Outswept host armrest', arm, .018)
            arm_joint = arm[0]
            tip = arm[-2]
        else:
            arm_joint = ((x + back[0]) / 2, rear - .012, .655)
            tip = hoop(side * 1.43)
        curved_member(g, parent, 'Continuous rear leg and back stile',
                      [(x * 1.045, rear + .012, .003), (x, rear, seat - .018), arm_joint, back], leg)
        curved_member(g, parent, 'Curved front arm support',
                      [(x, front + .012, seat - .015), (x * 1.07, front + .016, seat + .092), tip],
                      .013 if host else .011)
        g.tube(parent, 'Side stretcher', WOOD, [(x, front, .176), (x, rear, .195)], .0105, sides=10)

    g.tube(parent, 'Front foot stretcher', WOOD, [(-corner, front, .145), (corner, front, .145)], .012, sides=10)
    g.tube(parent, 'Rear stretcher', WOOD, [(-corner, rear, .216), (corner, rear, .216)], .010, sides=10)


def tea_chairs(g, parent, seating):
    for pose in seating['positions']:
        host = pose.get('host', False)
        node = g.group(parent, 'Host high-back chair' if host else 'Guest horseshoe chair',
                       (pose['x'], -pose['z'], 0), radians(pose['angle']))
        wooden_chair(g, node, seating['host' if host else 'guest'], host)
