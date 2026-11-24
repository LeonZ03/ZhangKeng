"""Exterior finishes and geometry for the measured Zhangkeng villa."""

import bpy
from mathutils import Vector

from exterior_garden import kitchen, kitchen_screen, planting, stones, trees
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
        for u in [a + 0.003, b - 0.003]:
            strip(frame, u, (low + high) / 2, 0.010, high - low, depth=0.051)
        for v in [low + 0.004, high - 0.004]:
            strip(frame, (a + b) / 2, v, b - a, 0.010, depth=0.051)
    if opening_type != "window" or width > 1.2:
        u = mul + 0.075 if width > 1.2 else start + width - 0.07
        elevation = min(sill + height * 0.45, sill + 1.10)
        strip(fittings, u, elevation, 0.021, 0.082, 0.021, 0.066)
        strip(fittings, u + 0.025, elevation + 0.008, 0.066, 0.015, 0.017, 0.075)


def openings(scene, root, walls, trim, frame, glass_mat, fittings_mat):
    trim_builder, gaskets, panes, fittings = [MeshBuilder() for _ in range(4)]
    for wall in walls:
        if wall["exterior"]:
            for opening in wall["openings"]:
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
    for center, dimensions in [
        ((-0.102, -4.50, -0.106), (0.011, 9.20, 0.225)),
        ((11.902, -4.50, -0.106), (0.011, 9.20, 0.225)),
        ((5.90, 0.103, -0.106), (12.00, 0.011, 0.225)),
        ((1.65, -9.102, -0.106), (3.50, 0.011, 0.225)),
        ((10.15, -9.102, -0.106), (3.50, 0.011, 0.225)),
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
            # All full-shell glazing is exterior here, including the balcony.
            railing = level and (center.y < -9.84 or (
                min(abs(center.x - x) for x in (3.5, 8.3)) < 0.03 and center.y < -7.85
            ))
            if material == "window" and not railing:
                bpy.data.objects.remove(obj, do_unlink=True)
                continue
            replace_surface(obj, glass_mat if material == "window" else frame)
            if material != "frame" or railing:
                continue
            # Existing outer framing remains on the drawing's opening.
            # Tall narrow members at the center are shifted to match the photographed jamb division.
            for wall in walls:
                if not wall["exterior"]:
                    continue
                axis_x = wall["axis"] == "x"
                u = center.x if axis_x else -center.y
                distance = -center.y if axis_x else center.x
                if abs(distance - wall["position"]) >= 0.004:
                    continue
                for opening in wall["openings"]:
                    start, width = opening["start"], opening["width"]
                    if (opening["type"] != "window" or width <= 1.2 or
                            abs(u - start - width / 2) >= 0.004):
                        continue
                    if (wall["position"] != 0 and size.z > 0.45 and size.x < 0.11 and size.y < 0.11
                            and abs(center.z - level - opening["sill"] - opening["height"] / 2) < 0.03):
                        offset = width * 0.17
                        move = Vector((offset, 0, 0) if axis_x else (0, -offset, 0))
                        obj.location += obj.parent.matrix_world.to_3x3().inverted_safe() @ move
                    if (axis_x and wall["position"] > 0 and size.z < 0.05
                            and abs(center.z - level - opening["sill"] - 1.048) < 0.007):
                        factor = 0.33
                        world_width_axis = Vector((1, 0, 0))
                        basis = obj.matrix_world.to_3x3()
                        local = max(range(3), key=lambda index: abs(basis.col[index].normalized().dot(world_width_axis)))
                        obj.scale[local] *= factor
                        obj.location += obj.parent.matrix_world.to_3x3().inverted_safe() @ (
                            world_width_axis * width * (1 - factor) / 2)
    openings(scene, parent, walls, trim, seal, glass_mat, hardware)


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
    trees(ctx.scene, proposal, textures["bark"])
    kitchen(ctx.scene, proposal, stainless, fittings, textures["footer"])
    kitchen_screen(ctx.scene, proposal, textures["ashlar"], textures["trim"])
