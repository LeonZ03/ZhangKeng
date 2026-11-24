"""Exterior finishes and geometry for the measured Zhangkeng villa."""

import bpy

from exterior_garden import kitchen, kitchen_screen, planting, shrubs, stones, trees
from exterior_geometry import MeshBuilder, center_and_spans, descendants, long_axis
from exterior_roof import refine_roof
from exterior_surfaces import Surfaces, replace_surface, solid, uv_project


def source_name(obj):
    return obj.get("source_name", obj.name)


def under(obj, label):
    while obj.parent:
        obj = obj.parent
        if source_name(obj) == label:
            return True
    return False


def apply_surface(obj, finish, size, grain=None):
    replace_surface(obj, finish)
    uv_project(obj, size, grain)


def exterior_opening(wall, opening, builder, glass, fittings, frame):
    axis = wall["axis"]
    position = wall["position"]
    along_x = axis == "x"
    sign = 1 if position == 0 else -1
    start, width, sill, height = [opening[key] for key in ("start", "width", "sill", "height")]
    top = height + sill
    opening_type = opening["type"]
    frame_width = 0.059 if opening_type == "slide" else 0.047

    def locate(u, v, depth):
        return (u, -position + depth * sign, v) if along_x else (position - depth * sign, -u, v)

    def strip(target, center_u, elevation, w, h, d=0.020, depth=0.049):
        target.box(locate(center_u, elevation, depth),
                   (w, d, h) if along_x else (d, w, h), bevel=0.0025)

    if opening_type == "door":
        # The photographed north service doorway is a recess in the wall with a shallow lintel canopy.
        if along_x and position == 0:
            strip(builder, start + width / 2, top + 0.155, width + 0.28, 0.065, 0.34, 0.25)
        return

    left = start + frame_width
    right = start + width - frame_width
    low, high = sill + frame_width, top - frame_width
    mul = start + width * (0.67 if opening_type == "window" and position != 0 else 0.5)
    lanes = [(left, right)] if width <= 1.2 else [(left, mul - 0.017), (mul + 0.017, right)]
    for a, b in lanes:
        pane = [locate(a, low, 0.013), locate(b, low, 0.013), locate(b, high, 0.013),
                locate(a, high, 0.013)]
        glass.face(pane)
        for u in [a + 0.005, b - 0.005]:
            strip(frame, u, (low + high) / 2, 0.010, high - low - 0.020, depth=0.051)
        for v in [low + 0.005, high - 0.005]:
            strip(frame, (a + b) / 2, v, b - a, 0.010, depth=0.051)
    if opening_type != "window" or width > 1.2:
        u = mul + 0.075 if width > 1.2 else start + width - 0.07
        elevation = min(sill + height * 0.45, sill + 1.10)
        strip(fittings, u, elevation, 0.021, 0.082, 0.021, 0.066)
        strip(fittings, u + 0.025, elevation + 0.008, 0.066, 0.015, 0.017, 0.075)


def openings(scene, root, walls, trim, frame, glass_mat, fittings_mat, oak):
    trim_builder, gaskets, panes, fittings = [MeshBuilder() for _ in range(4)]

    def xwall_strip(builder, wall, center, elevation, width, height, thickness=.020, depth=.051):
        builder.box((center, -wall['position'] + depth * (-1 if wall['position'] else 1), elevation),
                    (width, thickness, height), bevel=.0025)

    for wall in walls:
        if wall["exterior"]:
            for opening in wall["openings"]:
                if opening['type'] == 'slide' and wall['axis'] == 'x' and wall['position'] == 7.8:
                    start, width = opening['start'], opening['width']
                    sill, top = opening['sill'], opening['sill'] + opening['height']
                    fw, half = .059, width / 2
                    left, middle, right = start + fw, start + half, start + width - fw
                    low, high = sill + fw, top - fw
                    # Two real panels occupy separate track depths: the left
                    # leaf slides behind the fixed right leaf to clear passage.
                    pane_points = [
                        (middle, -wall['position'] + .015, low), (right, -wall['position'] + .015, low),
                        (right, -wall['position'] + .015, high), (middle, -wall['position'] + .015, high),
                    ]
                    panes.face(pane_points)
                    for u in [middle + .005, right - .005]:
                        xwall_strip(gaskets, wall, u, (low + high) / 2, .010, high - low - .020)
                    for v in [low + .005, high - .005]:
                        xwall_strip(gaskets, wall, (middle + right) / 2, v, right - middle, .010)
                    pivot = bpy.data.objects.new('可操作二层南阳台推拉玻璃门', None)
                    root.users_collection[0].objects.link(pivot)
                    pivot.parent = root
                    pivot.location = (start, -wall['position'], 0)
                    pivot['exploreAction'] = 'slide'
                    pivot['exploreLabel'] = '二层南阳台推拉玻璃门'
                    pivot['exploreAmount'] = half - fw
                    frame_builder, glass_builder = MeshBuilder(), MeshBuilder()
                    x0, x1 = fw, half - .003
                    depth_frame = .046
                    depth_glass = .014
                    for u in [x0 + .027, x1 - .027]:
                        frame_builder.box((u, depth_frame, (low + high) / 2), (.054, .057, high - low - .108), bevel=.003)
                    for z in [low + .027, high - .027]:
                        frame_builder.box(((x0 + x1) / 2, depth_frame, z), (x1 - x0, .057, .054), bevel=.003)
                    glass_builder.face([(x0 + .054, depth_glass, low + .054),
                                        (x1 - .054, depth_glass, low + .054),
                                        (x1 - .054, depth_glass, high - .054),
                                        (x0 + .054, depth_glass, high - .054)])
                    frame_builder.box((x1 - .11, depth_frame * 1.65, 1.52), (.018, .018, .14), bevel=.003)
                    frame_builder.object(scene, pivot, 'Balcony sliding leaf frame and pull', frame)
                    glass_builder.object(scene, pivot, 'Balcony sliding leaf safety glass', glass_mat)
                    # Fixed surround remains fully static in its original measured opening.
                    xwall_strip(gaskets, wall, start + fw / 2, (low + high) / 2, fw, high - low - 2 * fw)
                    xwall_strip(gaskets, wall, start + width - fw / 2, (low + high) / 2, fw, high - low - 2 * fw)
                    xwall_strip(gaskets, wall, start + width / 2, low + fw / 2, width, fw)
                    xwall_strip(gaskets, wall, start + width / 2, high - fw / 2, width, fw)
                    continue
                if opening['type'] == 'entry' and wall['axis'] == 'x' and wall['position'] == 7.8:
                    # Keep the measured opening's surrounding shell and jambs,
                    # while giving its existing glazed leaf a true hinge pivot.
                    start, width = opening['start'], opening['width']
                    top = opening['sill'] + opening['height']
                    # Two glazed leaves meet at the opening center. Their outer
                    # jambs stay fixed; each pivot carries its own glass, rails,
                    # and pull so the front-left target selects the left leaf.
                    leaf_w = width / 2 - .047 - .003
                    for side, hinge_x, sign in [('左扇', start + .047, 1), ('右扇', start + width - .047, -1)]:
                        pivot = bpy.data.objects.new(f'可操作南侧入户玻璃门{side}', None)
                        root.users_collection[0].objects.link(pivot)
                        pivot.parent = root
                        pivot.location = (hinge_x, -wall['position'], 0)
                        pivot['exploreAction'] = 'swing'
                        pivot['exploreLabel'] = f'正门深橡木双开门{side}'
                        pivot['exploreAmount'] = 1.2 if sign > 0 else -1.2
                        door_frame, door_glass = MeshBuilder(), MeshBuilder()
                        handle = MeshBuilder()
                        x0, x1 = (0, leaf_w) if sign > 0 else (-leaf_w, 0)
                        y = .006
                        # Solid oak leaf with a recessed central panel and raised rails.
                        door_frame.box(((x0 + x1) / 2, y, top / 2), (leaf_w, .078, top - .03), bevel=.009)
                        door_frame.box(((x0 + x1) / 2, y - .043, top / 2), (leaf_w - .13, .012, top - .26), bevel=.012)
                        pull_x = x1 - .10 if sign > 0 else x0 + .10
                        handle.box((pull_x, -.052, 1.04), (.021, .019, .16), bevel=.004)
                        door_frame.object(scene, pivot, f'South oak entrance {side} leaf and hardware', oak)
                        handle.object(scene, pivot, f'South entrance {side} handle', fittings_mat)
                    continue
                if opening['type'] == 'entry' and wall['axis'] == 'z' and wall['position'] == 0:
                    # Upper west stair landing door keeps its glazed appearance and swings on its own hinge.
                    start, width = opening['start'], opening['width']
                    top = opening['sill'] + opening['height']
                    pivot = bpy.data.objects.new('可操作西侧楼梯二层玻璃门', None)
                    root.users_collection[0].objects.link(pivot)
                    pivot.parent = root
                    pivot.location = (0, -start, 0)
                    pivot['exploreAction'] = 'swing'
                    pivot['exploreLabel'] = '楼梯门二层西侧玻璃门'
                    pivot['exploreAmount'] = -1.15
                    leaf_frame, leaf_glass = MeshBuilder(), MeshBuilder()
                    # Local X follows the wall opening; the pivot sits on the north jamb.
                    stile_bottom, header_bottom = .019, top - .0485
                    leaf_frame.box((-.006, -width / 2, top / 2), (.057, width - .097, .043), bevel=.003)
                    leaf_frame.box((-.006, -width / 2, top - .027), (.057, width, .043), bevel=.003)
                    for u in [-.027, -width + .027]:
                        leaf_frame.box((-.006, u, (stile_bottom + header_bottom) / 2),
                                       (.057, .043, header_bottom - stile_bottom), bevel=.003)
                    leaf_glass.face([(.006, -.05, .052), (.006, -width + .05, .052),
                                     (.006, -width + .05, top - .05), (.006, -.05, top - .05)])
                    leaf_frame.box((-.038, -width + .10, 1.02), (.018, .018, .15), bevel=.003)
                    leaf_frame.object(scene, pivot, 'Upper west stair door frame and pull', frame)
                    leaf_glass.object(scene, pivot, 'Upper west stair door safety glass', glass_mat)
                    continue
                if opening['type'] == 'door' and wall['axis'] == 'x' and wall['position'] == 0 and abs(opening['start'] - 7.05) < .01:
                    # Measured north service doorway: independent oak leaf, fixed jambs and canopy stay put.
                    exterior_opening(wall, opening, trim_builder, panes, fittings, gaskets)
                    start, width = opening['start'], opening['width']
                    top = opening['sill'] + opening['height']
                    pivot = bpy.data.objects.new('可操作北侧后门橡木单扇', None)
                    root.users_collection[0].objects.link(pivot)
                    pivot.parent = root
                    pivot.location = (start + .047, 0, 0)
                    pivot['exploreAction'] = 'swing'
                    pivot['exploreLabel'] = '后门北侧深橡木单扇'
                    pivot['exploreAmount'] = -1.18
                    leaf_width = width - .094
                    leaf, hardware = MeshBuilder(), MeshBuilder()
                    leaf.box((leaf_width / 2, .01, top / 2), (leaf_width, .078, top - .025), bevel=.009)
                    leaf.box((leaf_width / 2, -.034, top / 2), (leaf_width - .12, .012, top - .24), bevel=.012)
                    hardware.box((leaf_width - .10, -.061, 1.02), (.021, .019, .16), bevel=.004)
                    leaf.object(scene, pivot, 'North oak rear door leaf', oak)
                    hardware.object(scene, pivot, 'North rear door handle', fittings_mat)
                    continue
                exterior_opening(wall, opening, trim_builder, panes, fittings, gaskets)
    trim_builder.object(scene, root, "North service entrance rain hood", trim)
    gaskets.object(scene, root, "Exterior insulated glazing seals", frame)
    panes.object(scene, root, "Recessed insulated glazing panes", glass_mat)
    fittings.object(scene, root, "Door and window hardware", fittings_mat)


def fit_wing_wall_to_roof(obj, heights):
    center, spans = center_and_spans(obj)
    if min(abs(center.y), abs(center.y + 9.0)) > 0.005 or spans.y > 0.205:
        return
    west, east = center.x - spans.x / 2, center.x + spans.x / 2
    if west < 8.299 and east > 3.501:
        return
    ridge, eave = heights["mainRidge"], heights["mainEave"]
    slope = (ridge - eave) / 4.5
    world = obj.matrix_world
    local = world.inverted_safe()
    for vertex in obj.data.vertices:
        point = world @ vertex.co
        point.z = min(point.z, ridge - abs(point.y + 4.5) * slope - 0.047)
        vertex.co = local @ point
    obj.data.update()


def fit_cross_closure(obj, heights, include_main_roof=True):
    world = obj.matrix_world
    local = world.inverted_safe()
    main_ridge, cross_ridge = heights["mainRidge"], heights["crossRidge"]
    main_slope = (main_ridge - heights["mainEave"]) / 4.5
    cross_slope = (cross_ridge - heights["crossEave"]) / 2.4
    for vertex in obj.data.vertices:
        point = world @ vertex.co
        main = main_ridge - abs(point.y + 4.5) * main_slope
        cross = cross_ridge - abs(point.x - 5.9) * cross_slope
        # A long rectangular partition has no intermediate top vertices at
        # the valley. Keep it below the cross eave along its entire length.
        ceiling = max(main, cross) - 0.044 if include_main_roof else cross - 0.035
        point.z = min(point.z, ceiling)
        vertex.co = local @ point
    obj.data.update()


def slab_returns(scene, parent, plaster):
    returns = MeshBuilder()
    side_depth = 0.011
    west, east = -0.102, 11.902
    north, south = 0.103, -9.102
    side_length = north - south - side_depth
    west_edge, east_edge = west - side_depth / 2, east + side_depth / 2
    for center, dimensions in [
        ((west, (north + south) / 2, -0.106), (side_depth, side_length, 0.225)),
        ((east, (north + south) / 2, -0.106), (side_depth, side_length, 0.225)),
        (((west_edge + east_edge) / 2, north, -0.106), (east_edge - west_edge, side_depth, 0.225)),
        (((west_edge + 3.4) / 2, south, -0.106), (3.4 - west_edge, side_depth, 0.225)),
        (((8.4 + east_edge) / 2, south, -0.106), (east_edge - 8.4, side_depth, 0.225)),
    ]:
        returns.box(center, dimensions, uv_span=0.82)
    returns.object(scene, parent, "Stucco returns at the upper slab perimeter", plaster)


def refine_shell(scene, parent, walls, heights, textures, glass_mat, frame, seal, hardware, level):
    plaster, trim, footer, stone = (textures[key] for key in ("plaster", "trim", "footer", "stone"))
    for obj in list(descendants(parent)):
        if obj.type != "MESH":
            continue
        material = obj.get("source_material", "")
        if material == "plaster":
            replace_surface(obj, plaster)
            if level:
                fit_wing_wall_to_roof(obj, heights)
            uv_project(obj, (0.82, 0.82))
        elif material == "trim":
            apply_surface(obj, trim, (0.82, 0.82))
        elif material == "footer":
            apply_surface(obj, footer, (0.86, 0.86))
        elif material == "sill":
            apply_surface(obj, stone, (1, 1))
        elif level and material == "wall":
            center, size = center_and_spans(obj)
            if size.x <= 0.21 and min(abs(center.x - edge) for edge in (3.5, 8.3)) < 0.01:
                # Keep both upper partitions below the intersecting roof surfaces.
                if obj.data.users > 1:
                    obj.data = obj.data.copy()
                fit_cross_closure(obj, heights, include_main_roof=False)
        elif material in {"frame", "window"}:
            center, size = center_and_spans(obj)
            if material == "frame":
                removed = False
                for wall in walls:
                    if not wall["exterior"]:
                        continue
                    axis_x = wall["axis"] == "x"
                    along = center.x if axis_x else -center.y
                    distance = -center.y if axis_x else center.x
                    if abs(distance - wall["position"]) >= .004:
                        continue
                    if any(opening["type"] in {"entry", "slide"} and opening["width"] > 1.2
                           and abs(along - opening["start"] - opening["width"] / 2) < .004
                           and size.z > 1.0 and size.x < .11 and size.y < .11
                           for opening in wall["openings"]):
                        bpy.data.objects.remove(obj, do_unlink=True)
                        removed = True
                        break
                if removed:
                    continue
            # All full-shell glazing is exterior here, including the balcony.
            railing = level and (center.y < -9.84 or (
                min(abs(center.x - x) for x in (3.5, 8.3)) < 0.03 and center.y < -7.85
            ))
            if material == "window" and not railing:
                bpy.data.objects.remove(obj, do_unlink=True)
                continue
            replace_surface(obj, glass_mat if material == "window" else frame)
    openings(scene, parent, walls, trim, seal, glass_mat, hardware, textures['oakDoor'])


def refine(ctx):
    """Build physical exterior detail under the viewer's existing layer nodes."""
    bpy.context.view_layer.update()
    surfaces = Surfaces(ctx.workspace)
    textures = {
        "plaster": surfaces.textured("Cream aggregate stucco", (222, 215, 201), "stucco", 0.89, 0.60),
        "trim": surfaces.textured("Pale molded facade bands", (231, 224, 210), "stucco", 0.86, 0.29),
        "footer": surfaces.textured("Slate-colored cement plinth", (108, 112, 107), "stone", 0.9, 0.42),
        "stone": surfaces.textured("Honed pale limestone", (185, 174, 152), "stone", 0.78, 0.42),
        "soffit": surfaces.textured("Honey fir exterior joinery", (167, 110, 61), "wood", 0.56, 0.37),
        "oakDoor": surfaces.textured("Dark stained oak entrance doors", (72, 43, 26), "wood", 0.48, 0.32),
        "treads": surfaces.textured("Light oiled timber stair nosing", (196, 142, 79), "wood", 0.57, 0.36),
        "deck": surfaces.textured("Warm composite decking", (133, 103, 75), "wood", 0.72, 0.35),
        "ceramic": surfaces.textured("Charcoal glazed ceramic roof tile", (49, 52, 58), "slate", 0.37, 0.30),
        "lawn": surfaces.textured("Courtyard lawn and moss", (112, 129, 65), "lawn", 0.95, 0.47),
        "earth": surfaces.textured("Construction stage silty soil", (132, 111, 81), "earth", 0.96, 0.47),
        "gravel": surfaces.textured("Dark mixed pea gravel", (94, 93, 83), "gravel", 0.93, 0.43),
        "brick": surfaces.textured("Construction phase red clay masonry", (142, 95, 72), "brick",
                                   0.87, 0.65, mortar=(118, 112, 98)),
        "ashlar": surfaces.textured("Proposed courtyard ashlar", (138, 132, 116), "ashlar",
                                    0.81, 0.65, mortar=(101, 96, 82)),
        "bark": surfaces.textured("Mature courtyard tree bark", (91, 72, 52), "wood", 0.92, 0.56),
    }
    ceramic, soffit, stone = [textures[key] for key in ("ceramic", "soffit", "stone")]
    frame = solid("Warm graphite window frames", (83, 85, 77), 0.43, 0.44)
    seal = solid("Weather seals for insulating glass", (55, 59, 54), 0.64)
    glass = solid("Clear slightly blue-green exterior glazing", (139, 168, 171), 0.13, 0.07, 0.36, True)
    fittings = solid("Graphite hardware and handrails", (61, 64, 60), 0.36, 0.57)
    stainless = solid("Brushed outdoor sink steel", (155, 159, 150), 0.39, 0.61)

    ground, upper = ctx.nodes["GroundFloor"], ctx.nodes["UpperFloor"]
    root = ctx.nodes["Roof"]
    for obj in list(descendants(root)):
        if obj.type != "MESH":
            continue
        material = obj.get("source_material")
        if material == "roof":
            bpy.data.objects.remove(obj, do_unlink=True)
        elif material in {"timber", "oak"}:
            apply_surface(obj, soffit, (2.6, 0.92), long_axis(obj))
        elif material == "roofEdge":
            apply_surface(obj, ceramic, (0.9, 0.9))
        elif material == "plaster":
            replace_surface(obj, textures["plaster"])
            fit_cross_closure(obj, ctx.plan["roof"])
            uv_project(obj, (0.82, 0.82))
    refine_roof(ctx.scene, root, ctx.plan["roof"], ceramic, soffit)

    floors = ctx.plan["floors"]
    for level, shell in [("ground", "GroundShell"), ("upper", "UpperShell")]:
        floor = floors[level]
        refine_shell(ctx.scene, ctx.nodes[shell], floor["walls"], ctx.plan["roof"], textures, glass,
                     frame, seal, fittings, floor["elevation"])
    slab_returns(ctx.scene, ctx.nodes["UpperShell"], textures["plaster"])
    for obj in descendants(ground):
        if obj.type != "MESH" or not under(obj, "西侧室外木梯"):
            continue
        source = obj.get("source_material")
        if source in {"wood", "timber", "oak"}:
            apply_surface(obj, textures["treads" if source != "oak" else "soffit"],
                          (2.6, 0.92), long_axis(obj))
        elif source == "cement":
            apply_surface(obj, stone, (0.9, 0.9))
    for floor in (ground, upper):
        for obj in floor.children:
            if obj.type == "MESH" and obj.get("source_material") in {"cement", "trim", "stone"}:
                center, dimensions = center_and_spans(obj)
                if center.y < -7.8 or center.y > 0:
                    apply_surface(obj, stone, (0.9, 0.9))

    yard = ctx.nodes["Yard"]
    proposal = ctx.nodes["YardDesign"]
    existing = ctx.nodes["YardExisting"]
    for obj in yard.children:
        if obj.type == "MESH" and obj.get("source_material") == "soil":
            apply_surface(obj, textures["earth"], (1.8, 1.8))
    ground_materials = {
        "lawn": ("lawn", (1.35, 1.35)), "darkStone": ("gravel", (0.67, 0.67)),
        "paving": ("stone", (0.86, 0.86)), "stone": ("stone", (0.86, 0.86)),
        "sill": ("stone", (0.86, 0.86)), "rock": ("ashlar", (1.23, 0.52)),
        "soil": ("earth", (0.86, 0.86)), "plaster": ("plaster", (0.82, 0.82)),
        "brick": ("brick", (1.17, 0.58)), "cement": ("footer", (0.86, 0.86)),
    }
    for parent in (proposal, existing):
        for obj in descendants(parent):
            if obj.type != "MESH":
                continue
            source = obj.get("source_material", "")
            if source in ground_materials:
                name, size = ground_materials[source]
                apply_surface(obj, textures[name], size)
            elif source in {"wood", "timber", "oak"}:
                texture = textures["deck"] if under(obj, "东北塑木平台") else soffit
                apply_surface(obj, texture, (2.6, 0.78), long_axis(obj))
            elif source.startswith("custom-") and under(obj, "石板园路"):
                uv_project(obj, (0.9, 0.9))
    stones(ctx.scene, proposal, stone, textures["footer"])
    planting(ctx.scene, proposal)
    shrubs(ctx.scene, proposal)
    trees(ctx.scene, proposal, textures["bark"])
    kitchen(ctx.scene, proposal, stainless, fittings, textures["footer"])
    kitchen_screen(ctx.scene, proposal, textures["ashlar"], textures["trim"])
