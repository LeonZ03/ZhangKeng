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
    x, y, z = -2.36 + 0.77, 4.61 + 1.16, DATUM + 1.006
    # Raised rim and modeled bowl above the appliance location on the designed cabinet.
    sink.box((x, y, z + 0.025), (0.56, 0.38, 0.025), bevel=0.007)
    for dx in [-0.269, 0.269]:
        sink.box((x + dx, y, z + 0.048), (0.031, 0.38, 0.031), bevel=0.004)
    for dy in [-0.178, 0.178]:
        sink.box((x, y + dy, z + 0.048), (0.55, 0.025, 0.031), bevel=0.004)
    for a, b in zip([(x + 0.08, y + 0.15, z), (x + 0.08, y + 0.15, z + 0.205),
                     (x + 0.08, y + 0.10, z + 0.252)],
                    [(x + 0.08, y + 0.15, z + 0.205), (x + 0.08, y + 0.10, z + 0.252),
                     (x + 0.08, y - 0.045, z + 0.251)]):
        tap.branch(a, b, 0.012, 0.012, sides=9)
    for i in range(5):
        xx = -3.49 + i * 0.565
        cabinet.box((xx, 5.477, DATUM + 0.51), (0.546, 0.028, 0.67), bevel=0.005)
        tap.box((xx, 5.454, DATUM + 0.733), (0.141, 0.022, 0.019), bevel=0.004)
    sink.object(scene, parent, "Outdoor stainless sink and rim", stainless)
    tap.object(scene, parent, "Outdoor faucet and cabinet hardware", bronze)
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
