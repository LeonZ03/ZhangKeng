"""Kitchen joinery, sanitary fixtures, bedside pieces, and the living-room plant."""

from math import cos, pi, sin
from random import Random

from interior_geometry import rounded_outline


def sink(g, node, name, at, rx, ry, depth, finish, power=.25):
    profile = [(1, 0), (.94, -.005), (.88, -.037), (.76, -depth * .86),
               (.64, -depth), (.04, -depth)]
    count = 48
    vertices = [(x, y, z) for r, z in profile for x, y in rounded_outline(rx * r, ry * r, power, count)]
    faces = [
        (j * count + i, j * count + (i + 1) % count,
         (j + 1) * count + (i + 1) % count, (j + 1) * count + i)
        for j in range(len(profile) - 1) for i in range(count)
    ]
    faces.append(tuple(range(len(vertices) - count, len(vertices))))
    g.mesh(node, name, vertices, faces, finish, at, smooth=True)
    g.lathe(node, 'Recessed waste ring', 'graphite', (at[0], at[1], at[2] - depth), [
        (0, 0), (.024, 0), (.025, .003), (0, .003)], segments=20)


def faucet(g, node, x, y, z, height=.216, reach=.124):
    g.lathe(node, 'Tap deck escutcheon', 'sink', (x, y, z), [
        (0, 0), (.027, 0), (.027, .012), (.022, .016), (0, .016)], segments=24)
    points = [(x, y, z), (x, y, z + height * .58)]
    for i in range(13):
        angle = pi * i / 12
        points.append((x, y - reach / 2 * (1 - cos(angle)), z + height * .59 + height * .40 * sin(angle)))
    points.append((x, y - reach, z + height * .43))
    g.tube(node, 'Gooseneck mixer', 'sink', points, .013)
    g.tube(node, 'Mixer control', 'sink', [(x + .011, y, z + .063), (x + .041, y, z + .063),
                                           (x + .041, y, z + .106)], .007)


def bath(g, parent, plan):
    node = g.group(parent, 'Bath · sanitary assemblies', (plan['x'], -plan['z'], .014))
    node.scale.x = plan['direction']
    g.box(node, 'Recessed shower tray', 'bathfloor', (.005, -.379, .017), (.704, .704, .034), .012)
    for y in [-.161, -.152, -.143, -.134]:
        g.box(node, 'Linear shower waste slot', 'graphite', (.002, y, .035), (.189, .003, .003), 0)
    g.tube(node, 'Riser and overhead arm', 'sink', [
        (.017, -.023, .968), (.017, -.023, 1.922), (.017, -.047, 1.984), (.017, -.204, 1.984)], .012)
    g.lathe(node, 'Rain shower disk', 'sink', (.017, -.204, 1.942), [
        (0, 0), (.100, 0), (.103, .010), (.098, .020), (0, .020)])
    for x in [-.055, .0, .055]:
        g.tube(node, 'Thermostatic mixer', 'sink', [(x, -.022, 1.00), (x, -.080, 1.00)], .018)
    g.tube(node, 'Handset hose', 'sink', [
        (.054, -.068, .973), (.066, -.095, .783), (.109, -.105, .701),
        (.150, -.102, .722), (.183, -.076, .811), (.177, -.053, 1.112)], .005)
    g.tube(node, 'Shower handset', 'sink', [(.177, -.053, 1.095), (.177, -.063, 1.217), (.177, -.096, 1.264)], .014)
    x = .665
    g.box(node, 'Ceramic cistern', 'ceramic', (x, -.123, .568), (.355, .192, .407), .040)
    g.box(node, 'Flush buttons', 'sink', (x, -.13, .776), (.078, .039, .008), .003)
    g.lathe(node, 'Glazed toilet bowl and pedestal', 'ceramic', (x, -.400, 0), [
        (0, 0), (.132, 0), (.152, .026), (.147, .148), (.160, .238), (.186, .338), (.191, .376),
        (.178, .402), (.141, .395), (.135, .345), (.100, .275), (.053, .249), (0, .249)], aspect=1.40)
    g.lathe(node, 'Open soft-close seat ring', 'ceramic', (x, -.395, .391), [
        (.156, 0), (.189, 0), (.191, .016), (.178, .037), (.147, .034), (.144, .014), (.156, 0)],
        aspect=1.37)
    g.lathe(node, 'Bowl water', 'water', (x, -.418, .257), [(0, 0), (.063, 0), (.063, .002), (0, .002)], aspect=1.3)
    x = 1.44
    g.box(node, 'Floating vanity', 'oak', (x, -.300, .448), (.674, .492, .609), .012)
    for z in [.300, .527]:
        g.box(node, 'Vanity drawer front', 'oak', (x, -.557, z), (.653, .026, .219), .004, grain='x')
        g.box(node, 'Vanity bar pull', 'bronze', (x, -.583, z + .059), (.191, .027, .013), .004)
    for side in [-1, 1]:
        g.box(node, 'Basin countertop edge', 'quartz', (x + side * .295, -.303, .782), (.153, .566, .060), .009)
    for y in [-.541, -.066]:
        g.box(node, 'Basin countertop return', 'quartz', (x, y, .782), (.458, .090, .060), .006)
    g.lathe(node, 'Oval vitreous-china vessel', 'ceramic', (x, -.302, .795), [
        (0, 0), (.154, 0), (.189, .035), (.225, .099), (.227, .113), (.211, .122),
        (.199, .102), (.173, .059), (.104, .021), (0, .020)], aspect=.825)
    g.lathe(node, 'Vanity basin waste', 'sink', (x, -.302, .816), [
        (0, 0), (.022, 0), (.022, .003), (0, .003)], segments=20)
    faucet(g, node, x, -.071, .814, .160, .134)
    g.box(node, 'Bronze mirror surround', 'bronze', (x, -.018, 1.332), (.597, .027, .776), .012)
    g.box(node, 'Silvered bath mirror', 'mirror', (x, -.035, 1.332), (.574, .010, .753), .004)


def kitchen(g, parent):
    node = g.group(parent, 'L-shaped kitchen · joinery', (0, 0, .014))
    g.box(node, 'North cabinet recessed plinth', 'graphite', (10.202, -.392, .048), (2.857, .532, .096))
    for x, w in [(9.139, .706), (10.927, 1.514)]:
        g.box(node, 'North cabinet carcase', 'cabinet', (x, -.374, .497), (w, .545, .801))
    g.box(node, 'Lower sink cabinet', 'cabinet', (9.881, -.369, .434), (.781, .524, .686))
    for i in range(5):
        x = 9.021 + .528 * i
        for z, h in [(.402, .567), (.759, .136)]:
            g.box(node, 'Satin cabinet door or drawer', 'cabinet', (x, -.669, z), (.514, .026, h), .005)
            g.box(node, 'Dark recessed pull', 'graphite', (x, -.687, z + h / 2 - .037), (.163, .018, .012), .002)
    # Four slabs frame a real opening for the undermount pair beneath the window.
    for x, w in [(9.214, .726), (10.950, 1.493)]:
        g.box(node, 'North quartz counter', 'quartz', (x, -.412, .917), (w, .626, .062), .007, grain='x')
    for y, d in [(-.18, .163), (-.664, .123)]:
        g.box(node, 'Worktop sink surround', 'quartz', (9.879, y, .917), (.607, d, .062), .006)
    for x in [9.724, 10.033]:
        sink(g, node, 'Undermount stainless bowl', (x, -.442, .937), .157, .192, .144, 'sink')
    g.box(node, 'Center sink divider', 'sink', (9.878, -.441, .943), (.026, .377, .012), .006)
    faucet(g, node, 9.879, -.191, .951, .242, .149)
    g.box(node, 'East cabinet base', 'cabinet', (11.388, -1.388, .492), (.564, 1.331, .815))
    g.box(node, 'East quartz return', 'quartz', (11.389, -1.386, .917), (.611, 1.321, .062), .006, grain='y')
    g.box(node, 'Oven dark glass front', 'graphite', (11.087, -1.377, .530), (.023, .598, .529), .007)
    g.box(node, 'Oven handle', 'sink', (11.055, -1.378, .719), (.035, .463, .026), .008, grain='y')
    g.box(node, 'Gas hob insert', 'graphite', (11.387, -1.388, .953), (.509, .741, .022), .009)
    for y in [-1.180, -1.553]:
        x = 11.391
        g.lathe(node, 'Sealed burner ring', 'sink', (x, y, .957), [
            (0, 0), (.086, 0), (.087, .015), (.075, .020), (.047, .013), (0, .013)], segments=24)
        g.lathe(node, 'Burner cover', 'graphite', (x, y, .970), [
            (0, 0), (.054, 0), (.053, .014), (0, .014)], segments=22)
        for angle in [pi / 4, 3 * pi / 4, 5 * pi / 4, 7 * pi / 4]:
            g.box(node, 'Cast-iron grate finger', 'graphite',
                  (x + .097 * cos(angle), y + .097 * sin(angle), .987), (.067, .026, .019), .004, rotation=angle)
    for y in [-1.676, -1.735]:
        g.lathe(node, 'Hob knob', 'graphite', (11.206, y, .966), [
            (0, 0), (.023, 0), (.023, .017), (.020, .019), (0, .019)], segments=20)
    g.box(node, 'Fridge cabinet', 'sink', (8.721, -.414, .909), (.575, .605, 1.818), .025)
    for z, h in [(.288, .533), (1.186, 1.237)]:
        g.box(node, 'Fridge door', 'sink', (8.721, -.746, z), (.565, .078, h), .020)
        g.box(node, 'Vertical fridge pull', 'graphite', (8.916, -.796, z + h * .24), (.031, .031, .170), .006)


def bedside(g, parent, x, z, table_only=False):
    node = g.group(parent, 'Solid oak side table', (x, -z, .015))
    g.box(node, 'Timber top', 'oak', (0, 0, .453), (.448, .40, .038), .009, grain='x')
    g.box(node, 'Drawer housing', 'walnut', (0, 0, .355), (.391, .338, .149), .009, grain='x')
    g.box(node, 'Drawer face', 'oak', (0, -.183, .350), (.366, .028, .116), .005, grain='x')
    g.box(node, 'Drawer pull', 'bronze', (0, -.203, .357), (.113, .017, .014), .003)
    for a in [-.164, .164]:
        for b in [-.143, .143]:
            g.box(node, 'Solid oak foot', 'oak', (a, b, .151), (.034, .036, .303), .005)
    if not table_only:
        g.lathe(node, 'Stoneware lamp base', 'ceramic', (0, .026, .472), [
            (0, 0), (.064, 0), (.065, .026), (.040, .064), (.023, .117), (0, .117)], segments=24)
        g.lathe(node, 'Linen lamp shade', 'linen', (0, .026, .567), [
            (.113, 0), (.073, .153), (.069, .153), (.109, .004), (.113, 0)], segments=28)


def plant(g, parent):
    node = g.group(parent, 'Rubber plant in stoneware', (7.70, -3.96, .015))
    g.lathe(node, 'Tapered stoneware planter', 'ceramic', (0, 0, 0), [
        (0, 0), (.112, 0), (.138, .028), (.155, .240), (.161, .251), (.160, .275),
        (.143, .276), (.123, .184), (0, .184)])
    g.lathe(node, 'Potting surface', 'soil', (0, 0, .243), [(0, 0), (.144, 0), (.145, .003), (0, .003)])
    rng = Random(983)
    for branch in range(4):
        angle = branch * pi / 2 + .28
        dx, dy = cos(angle), sin(angle)
        tip = .792 + rng.uniform(-.06, .21)
        g.tube(node, 'Ficus stem', 'soil', [(0, 0, .245), (.075 * dx, .075 * dy, .614),
                                          (.114 * dx, .114 * dy, tip)], .007, sides=7)
        for index in range(4):
            bearing = angle + (1 if index % 2 else -1) * .48
            length = rng.uniform(.15, .221)
            x, y, z = .086 * dx, .086 * dy, tip - .126 * index
            c, s = cos(bearing), sin(bearing)
            verts = []
            for t in [0, .16, .36, .59, .81, 1]:
                width = sin(pi * t) * length * .27
                for u in [-1, 0, 1]:
                    verts.append((x + length * t * c - u * width * s,
                                  y + length * t * s + u * width * c,
                                  z + .070 * sin(pi * t) - u * u * width * .31 - .040 * t))
            faces = [(i, i + 3, i + 4, i + 1) for i in range(15) if i % 3 != 2]
            g.mesh(node, 'Curved ficus leaf', verts, faces, 'newleaf' if not index else 'green', smooth=True)


def fixtures(g):
    ground, upper = (g.ctx.nodes[key] for key in ('GroundFixtures', 'UpperFixtures'))
    for plan in g.ctx.plan['baths']:
        bath(g, ground if plan['floor'] == 'ground' else upper, plan)
    kitchen(g, ground)
    for z in [.39, 2.44, 6.35, 8.65]:
        bedside(g, ground, .4, z)
    for z in [6.35, 8.65]:
        bedside(g, ground, 11.39, z)
    bedside(g, ground, 7.72, 7.2, table_only=True)
    plant(g, ground)
    for z in [5.93, 8.29]:
        bedside(g, upper, .41, z)
