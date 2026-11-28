"""Surface detail and measured hardscape for the proposed courtyard."""

from math import cos, pi, sin
from random import Random

import bpy
from mathutils import Vector

from exterior_geometry import MeshBuilder, descendants
from exterior_surfaces import RGB, replace_surface, solid, use_vertex_color


DATUM = -0.29


def is_inside(x, y, polygon):
    inside = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > y) != (b[1] > y):
            at = a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])
            if x < at:
                inside = not inside
    return inside


def planting(scene, parent):
    beds = [
        [(0.68, 6.16), (8.58, 6.16), (8.22, 5.22), (7.38, 4.08), (5.45, 3.94),
         (4.06, 3.23), (2.3, 3.6), (0.68, 3.6)],
        [(-3.68, 2.72), (-2.0, 2.82), (-1.43, 1.88), (-2.13, 0.20), (-3.68, 0.20)],
        [(-0.05, 1.42), (3.13, 2.16), (6.32, 1.86), (6.52, 0.29), (0.02, 0.22)],
        [(12.15, 6.17), (13.48, 6.17), (13.48, 2.6), (12.18, 2.6)],
        [(-2.92, -10.43), (-1.92, -10.43), (-1.92, -11.43), (-2.92, -11.43)],
        [(10.89, -10.43), (11.89, -10.43), (11.89, -11.43), (10.89, -11.43)],
    ]
    rng = Random(2719)
    grass = MeshBuilder()
    grass_color = [RGB(c) for c in [(89, 110, 53), (109, 128, 62), (126, 141, 75), (70, 89, 42)]]
    for i, polygon in enumerate(beds):
        z = DATUM + (0.22 if i > 3 else 0.10) - 0.004
        left, right = min(p[0] for p in polygon), max(p[0] for p in polygon)
        near, far = min(p[1] for p in polygon), max(p[1] for p in polygon)
        for _ in range(int((right - left) * (far - near) * 176)):
            x, y = rng.uniform(left, right), rng.uniform(near, far)
            if not is_inside(x, y, polygon):
                continue
            angle = rng.uniform(0, 2 * pi)
            dx, dy = cos(angle), sin(angle)
            width = rng.uniform(0.006, 0.013)
            height = rng.uniform(0.026, 0.071)
            grass.face([(x - dx * width, y - dy * width, z),
                        (x + dx * width, y + dy * width, z),
                        (x + dy * height * 0.24, y - dx * height * 0.24, z + height)],
                       color=rng.choice(grass_color))
    mat = solid("Lawn blade greens", (119, 139, 74), 0.94, two_sided=True)
    use_vertex_color(mat)
    grass.object(scene, parent, "Fine courtyard turf blades", mat, tint=True)


SHRUB_LEAF_OUTLINE = (
    (-1, 0), (-.78, -.50), (-.43, -.87), (0, -1),
    (.44, -.83), (.78, -.44), (1, 0), (.78, .44),
    (.44, .83), (0, 1), (-.43, .87), (-.78, .50),
)
SHRUB_LEAF_FACES = tuple((i, (i + 1) % len(SHRUB_LEAF_OUTLINE), len(SHRUB_LEAF_OUTLINE))
                         for i in range(len(SHRUB_LEAF_OUTLINE)))


def leaf_mesh(builder, rng, center, length, tint):
    half = length * rng.uniform(0.38, 0.59)
    theta = rng.uniform(0, 2 * pi)
    along = Vector((cos(theta), sin(theta), rng.uniform(-0.58, 0.66))).normalized() * half
    across = Vector((-sin(theta), cos(theta), rng.uniform(-0.28, 0.28))).normalized() * half * 0.50
    normal = along.cross(across).normalized()
    outline = [center + u * along + v * across for u, v in SHRUB_LEAF_OUTLINE]
    builder.patch([*outline, center + normal * half * 0.18], SHRUB_LEAF_FACES, color=tint, smooth=True)


def shrubs(scene, parent):
    """Replace the six broad-leaf placeholders with low, branched garden shrubs."""
    plants = [
        (0.99, 5.80, 1.70), (6.70, 5.75, 1.80), (7.84, 5.60, 1.90),
        (12.85, 3.23, 1.60), (2.47, 0.90, 1.40), (4.85, 1.24, 1.50),
    ]
    # The source garden has a cylindrical soil-colored stem and six oval leaves
    # directly under YardDesign. Remove only those meshes around the known sites.
    for obj in list(parent.children):
        if obj.type != "MESH" or obj.get("source_material") not in {"soil", "plant"}:
            continue
        center = obj.matrix_world.translation
        if any((center.x - x) ** 2 + (center.y - y) ** 2 < (0.48 * scale) ** 2 and
               DATUM - 0.08 < center.z < DATUM + 1.18 * scale
               for x, y, scale in plants):
            bpy.data.objects.remove(obj, do_unlink=True)

    branches, leaves = MeshBuilder(), MeshBuilder()
    leafmat = solid("Courtyard shrub foliage", (82, 109, 54), 0.88, two_sided=True)
    use_vertex_color(leafmat)
    rng = Random(61583)
    palette = [RGB(color) for color in (
        (63, 83, 42), (78, 103, 48), (93, 119, 55),
        (110, 132, 62), (128, 143, 72), (75, 96, 48),
    )]
    for index, (x, y, scale) in enumerate(plants):
        base = Vector((x, y, DATUM + 0.10))
        canopy_height = rng.uniform(0.45, 0.53) * scale
        canopy_radius = rng.uniform(0.23, 0.26) * scale
        # Several woody stems rise from the base and fork into an irregular,
        # leafy crown. The silhouette stays within the old planting footprint.
        for arm in range(8):
            angle = arm * (2.39996 + index * 0.017) + rng.uniform(-0.18, 0.18)
            radial = canopy_radius * rng.uniform(0.67, 1.0)
            start = base + Vector((rng.uniform(-0.045, 0.045) * scale,
                                   rng.uniform(-0.045, 0.045) * scale,
                                   rng.uniform(0.04, 0.12) * scale))
            joint = base + Vector((cos(angle) * radial * 0.43,
                                   sin(angle) * radial * 0.43,
                                   canopy_height * rng.uniform(0.43, 0.58)))
            tip = base + Vector((cos(angle) * radial, sin(angle) * radial,
                                 canopy_height * rng.uniform(0.78, 1.0)))
            branches.branch(start, joint, 0.024 * scale, 0.014 * scale, sides=6)
            branches.branch(joint, tip, 0.014 * scale, 0.004 * scale, sides=5)
            for side in (-1, 1):
                twig_angle = angle + side * rng.uniform(0.48, 0.78)
                twig = joint.lerp(tip, rng.uniform(0.49, 0.72))
                twig_tip = twig + Vector((cos(twig_angle) * radial * 0.31,
                                          sin(twig_angle) * radial * 0.31,
                                          canopy_height * rng.uniform(0.08, 0.20)))
                branches.branch(twig, twig_tip, 0.008 * scale, 0.002 * scale, sides=5)
                for _ in range(10):
                    t = rng.uniform(0.42, 1.0)
                    point = twig.lerp(twig_tip, t)
                    point += Vector((rng.gauss(0, 0.035), rng.gauss(0, 0.035),
                                     rng.gauss(0, 0.035))) * scale
                    leaf_mesh(leaves, rng, point, rng.uniform(0.075, 0.10) * scale,
                              rng.choice(palette))
            for _ in range(9):
                t = rng.uniform(0.62, 1.0)
                point = joint.lerp(tip, t)
                point += Vector((rng.gauss(0, 0.035), rng.gauss(0, 0.035),
                                 rng.gauss(0, 0.035))) * scale
                leaf_mesh(leaves, rng, point, rng.uniform(0.08, 0.10) * scale,
                          rng.choice(palette))
    bark = solid("Young shrub branch bark", (91, 76, 54), 0.94, 0.60)
    branches.object(scene, parent, "Forked low courtyard shrub branches", bark)
    leaves.object(scene, parent, "Layered low courtyard shrub leaves", leafmat, tint=True)


def trees(scene, parent, bark):
    leafmat = solid("Courtyard broadleaf canopies", (96, 121, 57), 0.84, two_sided=True)
    use_vertex_color(leafmat)
    branches, leaves = MeshBuilder(), MeshBuilder()
    rng = Random(25779)
    tree_groups = [obj for obj in descendants(parent) if obj.get("source_name", obj.name) == "庭院乔木"]
    for index, node in enumerate(tree_groups):
        sx, sy, z = node.matrix_world.translation
        scale = node.matrix_world.to_scale().x
        warm = index == 0
        leaf_colors = [RGB(color) for color in (
            [(135, 70, 42), (157, 89, 43), (184, 112, 55), (162, 126, 59), (116, 92, 46)]
            if warm else [(67, 89, 37), (85, 108, 42), (113, 131, 49), (125, 141, 66), (79, 112, 49)])]
        base = Vector((sx, sy, z - 0.012))
        fork = base + Vector((0.09, 0.03, 1.10)) * scale
        middle = base + Vector((0.06, 0.02, 0.46)) * scale
        branches.branch(base, middle, 0.100 * scale, 0.074 * scale)
        branches.branch(middle, fork, 0.074 * scale, 0.052 * scale)
        for arm in range(10):
            angle = arm * 2.39996
            radial = (0.82 if arm < 7 else 0.30) * rng.uniform(0.75, 1.18)
            tip = base + Vector((cos(angle) * radial, sin(angle) * radial,
                                 rng.uniform(1.70, 2.12) if arm < 7 else rng.uniform(2.32, 2.59))) * scale
            start = fork + Vector((0, 0, (arm % 3 - 1) * 0.16 * scale))
            joint = start.lerp(tip, 0.64) - Vector((0, 0, 0.07 * scale))
            branches.branch(start, joint, 0.034 * scale, 0.018 * scale)
            branches.branch(joint, tip, 0.018 * scale, 0.006 * scale, sides=5)
            for sprig in range(3):
                phi = angle + sprig * 2.1
                offset = Vector((cos(phi), sin(phi), rng.uniform(-0.2, 0.65))) * (0.23 * scale)
                stem = joint.lerp(tip, 0.62 + sprig * 0.12)
                branches.branch(stem, tip + offset, 0.010 * scale, 0.002 * scale, sides=5)
                for _ in range(44):
                    offset = Vector((rng.gauss(0, 0.17), rng.gauss(0, 0.17), rng.gauss(0, 0.115))) * scale
                    if offset.length > 0.48 * scale:
                        continue
                    position = tip + offset + Vector((cos(phi), sin(phi), 0.15)) * 0.30 * scale
                    leaf_mesh(leaves, rng, position, 0.073 * scale, rng.choice(leaf_colors))
        for old in list(node.children):
            if old.type == "MESH":
                bpy.data.objects.remove(old, do_unlink=True)
    branches.object(scene, parent, "Bifurcating garden tree trunks", bark)
    leaves.object(scene, parent, "Individually modeled garden broadleaves", leafmat, tint=True)


def stones(scene, parent, mat, dark):
    # Rectangles digitized from the north courtyard layout on sheets 14–15.
    # The common plan origin is the northwest house corner on sheet 14.
    course = [
        (366, 125, 393, 255), (395, 154, 417, 250), (388, 255, 451, 285),
        (335, 284, 393, 313), (393, 287, 451, 315), (405, 316, 450, 342),
        (287, 321, 332, 353), (247, 350, 285, 375), (211, 374, 286, 398),
        (176, 403, 286, 425), (456, 264, 576, 326), (584, 234, 776, 312),
        (585, 211, 640, 232), (642, 212, 669, 230), (781, 237, 862, 316),
        (782, 199, 862, 234), (820, 164, 869, 196), (853, 133, 901, 163),
        (860, 98, 902, 131), (903, 73, 919, 104),
        (781, 321, 934, 379), (939, 321, 1055, 379), (1060, 321, 1165, 379),
        (1168, 357, 1225, 381), (794, 384, 933, 408), (940, 384, 1017, 412),
        (1021, 384, 1146, 411), (1148, 385, 1224, 407), (928, 273, 976, 295),
        (981, 273, 1039, 295), (1043, 272, 1115, 295), (950, 298, 1055, 317),
        (1060, 298, 1144, 317), (1000, 321, 1033, 349),
    ]
    detail, grids = MeshBuilder(), MeshBuilder()
    existing_cards = [obj for obj in descendants(parent) if obj.get("source_name", obj.name) == "石板园路"]
    for node in existing_cards:
        for obj in descendants(node):
            if obj.type != "MESH":
                continue
            src = obj.get("source_material", "")
            if src.startswith("custom-"):
                replace_surface(obj, dark if obj.matrix_world.translation.x > 11.93 and
                                obj.matrix_world.translation.y < 0 else mat)

    for index, (left, top, right, bottom) in enumerate(course):
        # The existing ±0.00 path base is below the slabs. Drains and bed edges
        # are above that base so they remain distinct in the orthogonal view.
        x = (left + right - 630) / 132.6
        y = (890 - top - bottom) / 132.6
        w = (right - left) / 66.3
        d = (bottom - top) / 66.3
        if index == len(course) - 1:
            grids.box((x, y, DATUM + 0.030), (0.21, 0.21, 0.013), bevel=0.003)
            for offset in [-0.075, -0.045, -0.015, 0.015, 0.045, 0.075]:
                grids.box((x + offset, y, DATUM + 0.039), (0.013, 0.184, 0.013), bevel=0.002)
        else:
            detail.box((x, y, DATUM + 0.004), (w - 0.011, d - 0.011, 0.047), bevel=0.006)
    detail.object(scene, parent, "North garden cut limestone flagstones", mat)
    grids.object(scene, parent, "Courtyard drain grate", solid("Dark cast courtyard drain", (66, 68, 60), 0.53, 0.45))


def kitchen(scene, parent, stainless, bronze, rock):
    sink, tap, cabinet = MeshBuilder(), MeshBuilder(), MeshBuilder()
    hob, burner = MeshBuilder(), MeshBuilder()
    x, y = -1.59, 5.77
    top = DATUM + 0.9925
    hob_x = -3.21

    def kitchen_ancestor(obj):
        while obj:
            if obj.get("source_name", obj.name) == "西北户外厨房":
                return True
            obj = obj.parent
        return False

    def world_box(obj):
        corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        low = Vector(tuple(min(point[i] for point in corners) for i in range(3)))
        high = Vector(tuple(max(point[i] for point in corners) for i in range(3)))
        return (low + high) * 0.5, high - low

    # Remove the three simple source boxes at their measured positions. Split
    # the original 2.89 m top into four pieces around the sink cutout, keeping
    # its finish and thickness while making the bowl a real through-opening.
    counter_material = rock
    counter_found = False
    core_material = rock
    core_found = False
    for obj in list(descendants(parent)):
        if obj.type != "MESH" or not kitchen_ancestor(obj):
            continue
        center, size = world_box(obj)
        if (abs(center.x + 2.36) < 0.04 and abs(center.y - y) < 0.04 and
                abs(center.z - (top - 0.0375)) < 0.04 and
                abs(size.x - 2.89) < 0.06 and abs(size.y - 0.62) < 0.06 and
                abs(size.z - 0.075) < 0.02):
            if obj.data.materials:
                counter_material = obj.data.materials[0]
            bpy.data.objects.remove(obj, do_unlink=True)
            counter_found = True
        elif (abs(center.x + 2.36) < 0.04 and abs(center.y - y) < 0.04 and
              abs(size.x - 2.83) < 0.06 and abs(size.y - 0.56) < 0.06 and
              abs(size.z - 0.88) < 0.06):
            if obj.data.materials:
                core_material = obj.data.materials[0]
            bpy.data.objects.remove(obj, do_unlink=True)
            core_found = True
        elif (abs(center.y - y) < 0.05 and abs(center.z - (top + 0.0075)) < 0.05 and
              ((abs(center.x - hob_x) < 0.05 and abs(size.x - 0.54) < 0.06 and
                abs(size.y - 0.39) < 0.06) or
               (abs(center.x - x) < 0.05 and abs(size.x - 0.60) < 0.06 and
                abs(size.y - 0.38) < 0.06))):
            bpy.data.objects.remove(obj, do_unlink=True)
    if counter_found:
        counter = MeshBuilder()
        counter_bottom = top - 0.075
        counter_center_z = (top + counter_bottom) / 2
        x0, x1 = -2.36 - 2.89 / 2, -2.36 + 2.89 / 2
        y0, y1 = y - 0.62 / 2, y + 0.62 / 2
        hole_x0, hole_x1 = x - 0.514 / 2, x + 0.514 / 2
        hole_y0, hole_y1 = y - 0.328 / 2, y + 0.328 / 2
        for left, right in ((x0, hole_x0), (hole_x1, x1)):
            counter.box(((left + right) / 2, y, counter_center_z),
                        (right - left, y1 - y0, 0.075), bevel=0.002)
        for near, far in ((y0, hole_y0), (hole_y1, y1)):
            counter.box(((hole_x0 + hole_x1) / 2, (near + far) / 2, counter_center_z),
                        (hole_x1 - hole_x0, far - near, 0.075), bevel=0.002)
        counter.object(scene, parent, "Outdoor kitchen counter with sink cutout", counter_material)
    if core_found:
        core = MeshBuilder()
        core_x0, core_x1 = -2.36 - 2.83 / 2, -2.36 + 2.83 / 2
        core_y0, core_y1 = y - 0.56 / 2, y + 0.56 / 2
        core_bottom, core_top = DATUM + 0.04, DATUM + 0.92
        # Leave clearance below the steel basin floor to avoid overlapping faces.
        recess_bottom = top - 0.111
        lower_height = recess_bottom - core_bottom
        core.box((-2.36, y, core_bottom + lower_height / 2),
                 (2.83, 0.56, lower_height), bevel=0.002)
        opening_x0, opening_x1 = x - 0.514 / 2, x + 0.514 / 2
        opening_y0, opening_y1 = y - 0.328 / 2, y + 0.328 / 2
        upper_height = core_top - recess_bottom
        upper_center_z = (core_top + recess_bottom) / 2
        for left, right in ((core_x0, opening_x0), (opening_x1, core_x1)):
            core.box(((left + right) / 2, y, upper_center_z),
                     (right - left, 0.56, upper_height), bevel=0.002)
        for near, far in ((core_y0, opening_y0), (opening_y1, core_y1)):
            core.box(((opening_x0 + opening_x1) / 2, (near + far) / 2, upper_center_z),
                     (opening_x1 - opening_x0, far - near, upper_height), bevel=0.002)
        core.object(scene, parent, "Outdoor kitchen sink clearance through cabinet core", core_material)

    # The fixture is modeled as a twin hob with one control per burner.
    hob_center = (hob_x, y, top + 0.009)
    dark_glass = solid("Outdoor twin hob dark ceramic glass", (31, 33, 34), 0.24, 0.16)
    hob.box(hob_center, (0.61, 0.43, 0.018), bevel=0.014)
    knob_distance = 0.172
    for burner_x, side, label in ((hob_x - 0.145, "Left", "后院左灶旋钮"),
                                  (hob_x + 0.145, "Right", "后院右灶旋钮")):
        # Two fine annular rings make the burner geometry legible without
        # creating dense appliance meshes.
        for radius, tube_radius, z in ((0.101, 0.010, top + 0.023),
                                       (0.070, 0.006, top + 0.026)):
            segments = 24
            for index in range(segments):
                a, b = 2 * pi * index / segments, 2 * pi * (index + 1) / segments
                outer = radius + tube_radius
                inner = radius - tube_radius
                burner.face([
                    (burner_x + outer * cos(a), y + outer * sin(a), z),
                    (burner_x + outer * cos(b), y + outer * sin(b), z),
                    (burner_x + inner * cos(b), y + inner * sin(b), z),
                    (burner_x + inner * cos(a), y + inner * sin(a), z),
                ])
        burner.box((burner_x, y, top + 0.027), (0.086, 0.086, 0.012), bevel=0.006)
        for angle in (pi / 4, 3 * pi / 4, 5 * pi / 4, 7 * pi / 4):
            start = (burner_x + 0.047 * cos(angle), y + 0.047 * sin(angle), top + 0.034)
            end = (burner_x + 0.101 * cos(angle), y + 0.101 * sin(angle), top + 0.034)
            burner.branch(start, end, 0.004, 0.004, sides=5)
        control = bpy.data.objects.new("ExploreOutdoorBurner" + side, None)
        parent.users_collection[0].objects.link(control)
        control.parent = parent
        control.location = (burner_x, y - knob_distance, top + 0.019)
        control["exploreAction"] = "burner"
        control["exploreLabel"] = label
        control["exploreAmount"] = 1.0
        # The flame offset uses glTF's Y-up coordinates, with north along -Z.
        control["exploreFlameOffset"] = [0.0, 0.011, -knob_distance]
        control["exploreFlameRadius"] = 0.064
        knob = MeshBuilder()
        sides = 16
        knob.branch((0, 0, 0), (0, 0, 0.024), 0.024, 0.021, sides=sides)
        knob.face([(0.021 * cos(2 * pi * i / sides), 0.021 * sin(2 * pi * i / sides), 0.024)
                   for i in range(sides)])
        knob.box((0, 0, 0.025), (0.014, 0.032, 0.008), bevel=0.003)
        knob.object(scene, control, "Outdoor hob knob", bronze)
        mark = MeshBuilder()
        mark.box((0, -0.010, 0.030), (0.004, 0.009, 0.002), bevel=0.0005)
        mark.object(scene, control, "Outdoor hob position mark", stainless)

    # Thin steel flange plus sloped walls and a low basin floor read as a
    # genuine open inset. The floor closes the opening, so the counter cannot
    # visually continue through the bowl; the drain is a separate small ring.
    cut_w, cut_d = 0.514, 0.328
    rim_w, rim_d, rim_t = 0.56, 0.38, 0.008
    rim_z = top + 0.006
    sink.box((x, y - (rim_d - 0.026) / 2, rim_z), (rim_w, 0.026, rim_t), bevel=0.005)
    sink.box((x, y + (rim_d - 0.026) / 2, rim_z), (rim_w, 0.026, rim_t), bevel=0.005)
    for side in (-1, 1):
        sink.box((x + side * (rim_w - 0.026) / 2, y, rim_z),
                 (0.026, rim_d - 0.052, rim_t), bevel=0.005)
    lip_z, floor_z = top + 0.010, top - 0.105
    outer = [(x - cut_w / 2, y - cut_d / 2, lip_z),
             (x + cut_w / 2, y - cut_d / 2, lip_z),
             (x + cut_w / 2, y + cut_d / 2, lip_z),
             (x - cut_w / 2, y + cut_d / 2, lip_z)]
    inner = [(x - 0.207, y - 0.116, floor_z), (x + 0.207, y - 0.116, floor_z),
             (x + 0.207, y + 0.116, floor_z), (x - 0.207, y + 0.116, floor_z)]
    for i in range(4):
        j = (i + 1) % 4
        sink.face([outer[i], outer[j], inner[j], inner[i]])
    sink.face(inner)
    # Recessed waste flange and perforated drain are kept low-poly.
    drain_x, drain_y = x + 0.105, y + 0.025
    for index in range(20):
        a, b = 2 * pi * index / 20, 2 * pi * (index + 1) / 20
        sink.face([(drain_x + 0.029 * cos(a), drain_y + 0.029 * sin(a), floor_z + 0.003),
                   (drain_x + 0.029 * cos(b), drain_y + 0.029 * sin(b), floor_z + 0.003),
                   (drain_x + 0.022 * cos(b), drain_y + 0.022 * sin(b), floor_z + 0.003),
                   (drain_x + 0.022 * cos(a), drain_y + 0.022 * sin(a), floor_z + 0.003)])

    # Center the mounting foot on the stone deck behind the steel rim. The
    # spout turns downward over the center of the bowl.
    tap_y = y + rim_d / 2 + 0.040
    sides = 16
    tap.branch((x, tap_y, top), (x, tap_y, top + 0.018), 0.027, 0.025, sides=sides)
    tap.face([(x + 0.025 * cos(2 * pi * i / sides), tap_y + 0.025 * sin(2 * pi * i / sides), top + 0.018)
              for i in range(sides)])
    radius = (tap_y - y) / 2
    arch = [(tap_y, top + 0.016, 0)]
    for i in range(17):
        angle = pi * i / 16
        arch.append((tap_y - radius * (1 - cos(angle)), top + 0.172 + 0.094 * sin(angle), angle))
    arch.append((y, top + 0.149, pi))
    points = []
    for cy, cz, angle in arch:
        for i in range(sides):
            phase = 2 * pi * i / sides
            points.append((x + 0.012 * cos(phase), cy + 0.012 * sin(phase) * cos(angle),
                           cz + 0.012 * sin(phase) * sin(angle)))
    tap.patch(points, [(row * sides + i, row * sides + (i + 1) % sides,
                        (row + 1) * sides + (i + 1) % sides, (row + 1) * sides + i)
                       for row in range(len(arch) - 1) for i in range(sides)], smooth=True)
    tap.branch((x, y, top + 0.155), (x, y, top + 0.138), 0.0135, 0.0135, sides=sides)
    tap.branch((x + 0.010, tap_y, top + 0.059),
               (x + 0.046, tap_y, top + 0.078), 0.008, 0.006, sides=10)
    pulls = MeshBuilder()
    for i in range(5):
        xx = -3.49 + i * 0.565
        cabinet.box((xx, 5.477, DATUM + 0.51), (0.546, 0.028, 0.67), bevel=0.005)
        pulls.box((xx, 5.454, DATUM + 0.733), (0.141, 0.022, 0.019), bevel=0.004)
    hob.object(scene, parent, "Outdoor twin burner hob glass", dark_glass)
    burner.object(scene, parent, "Outdoor twin burner rings and pan supports", bronze)
    sink.object(scene, parent, "Outdoor recessed open stainless sink and drain", stainless)
    tap.object(scene, parent, "Outdoor deck-mounted gooseneck mixer", bronze)
    pulls.object(scene, parent, "Outdoor kitchen cabinet pulls", bronze)
    cabinet.object(scene, parent, "Outdoor kitchen base fronts", rock)


def kitchen_screen(scene, parent, stone, block_material):
    # Sheet 15 places this 3 m screen along the south edge of the outdoor kitchen.
    # The height and 2.018 m ventilation band come from the sheet 19 elevation.
    masonry, open_blocks = MeshBuilder(), MeshBuilder()
    left, right, y = -3.86, -0.86, 2.75
    masonry.box(((left + right) / 2, y, DATUM + 0.5), (3.0, 0.24, 1.0), bevel=0.008)
    masonry.box(((left + right) / 2, y, DATUM + 1.35), (3.0, 0.24, 0.3), bevel=0.008)
    masonry.box((left + 0.491, y, DATUM + 1.10), (0.982, 0.24, 0.20), bevel=0.005)
    pitch = 2.018 / 10
    for i in range(10):
        x = right - (i + 0.5) * pitch
        for shift in [-0.073, 0.073]:
            open_blocks.box((x + shift, y, DATUM + 1.10), (0.051, 0.20, 0.20), bevel=0.004)
            open_blocks.box((x, y, DATUM + 1.10 + shift), (0.095, 0.20, 0.051), bevel=0.004)
    masonry.object(scene, parent, "Outdoor kitchen 3 m irregular stone screen", stone)
    open_blocks.object(scene, parent, "Outdoor kitchen open 200 mm block band", block_material)
