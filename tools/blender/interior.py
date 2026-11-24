"""Resolve the villa's plan furniture into editable, glTF-compatible assemblies."""

from math import cos, pi, sin, tau
from pathlib import Path
from random import Random

import bpy
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

from interior_fixtures import fixtures
from interior_geometry import Geometry, rounded_outline


def clear_contents(parent):
    for child in list(parent.children):
        clear_contents(child)
        bpy.data.objects.remove(child, do_unlink=True)


def bed_library():
    path = Path(__file__).with_name('furniture_assets') / 'courtyard43-bed.blend'
    with bpy.data.libraries.load(str(path), link=False) as (source, loaded):
        loaded.collections = [name for name in source.collections if name == 'Courtyard43 bed geometry']
    return loaded.collections[0]


def bed(g, parent, item, library):
    w, d = item['w'], item['d']
    accent = {'bed-nw': 'sage', 'bed-sw': 'umber', 'bed-se': 'linen', 'bed-up': 'sage'}[item['id']]
    # The source bed runs along X with its head at negative X. The villa's bed
    # anchors expect the head at positive Y. Keep the adaptation below the anchor.
    across, along = w / 1.585, d / 2.508
    fit = Matrix(((0, across, 0, 2.018 * across),
                  (-along, 0, 0, -.748 * along),
                  (0, 0, 1, 0), (0, 0, 0, 1)))
    parent['furniture_provenance'] = 'BeiPiao / Courtyard43-furniture.blend / C43_Bed'
    parent['adaptation'] = 'Rotated, footprint-resized, recolored, and fitted with matching twin pillows'
    for source in library.objects:
        original = source['source_object'].removeprefix('C43_')
        mesh = source.data.copy()
        mesh.transform(fit)
        material = 'linen'
        if original.startswith(('BedPlatform', 'BedHeadboard')):
            material = 'oak'
        elif original.startswith(('BedLong', 'BedCross', 'BedRound', 'BedFoot')):
            material = 'graphite'
        elif original == 'FloralDuvet':
            material = accent
            duvet = mesh
        if original.startswith(('CottonPillow', 'PillowPipedSeam')):
            min_x = min(v.co.x for v in mesh.vertices)
            max_x = max(v.co.x for v in mesh.vertices)
            center = (min_x + max_x) / 2
        if not mesh.uv_layers:
            mesh.uv_layers.new()
        uv = mesh.uv_layers.active.data
        for poly in mesh.polygons:
            for j in poly.loop_indices:
                co = mesh.vertices[mesh.loops[j].vertex_index].co
                if material == 'oak':
                    uv[j].uv = (co.z * 2.8, co.x * .72)
                else:
                    uv[j].uv = (co.x * 8, co.y * 8)
        mesh.materials.append(g.m[material])
        name = original.replace('FloralDuvet', 'Duvet')
        if original.startswith(('CottonPillow', 'PillowPipedSeam')):
            for side in (-1, 1):
                obj = g.attach(parent, name, mesh, (side * w * .233 - center, 0, 0))
                obj['source_object'] = source['source_object']
        else:
            obj = g.attach(parent, name, mesh)
            obj['source_object'] = source['source_object']
    # A tailored textile at the foot gives the beds the strip drawn in the plans.
    if item['id'] in {'bed-sw', 'bed-se', 'bed-up'}:
        runner(g, parent, duvet, w, d, 'sage' if accent == 'umber' else 'umber')


def runner(g, parent, duvet, w, d, color):
    surface = BVHTree.FromPolygons([vertex.co for vertex in duvet.vertices],
                                   [poly.vertices for poly in duvet.polygons])
    vertices, coords, faces = [], [], []
    cols, rows = 44, 14
    for row in range(rows + 1):
        t = row / rows
        for col in range(cols + 1):
            u = col / cols
            edge = abs(u * 2 - 1)
            x = ((u - .5) * (w - .042)) + (.006 * sin(tau * t) * edge ** 6)
            y = d * (-.197 - .253 * t) + .009 * sin(tau * u + 2 * t)
            location, _, _, _ = surface.ray_cast((x, y, 1.0), (0, 0, -1))
            z = (location.z if location is not None else .551) + .009
            z += .003 * sin(tau * u * 1.4 + t * 1.5) + .002 * sin(tau * (t * .7 + u))
            vertices.append((x, y, z))
            coords.append((x * 8, y * 8))
    for row in range(rows):
        for col in range(cols):
            i = (cols + 1) * row + col
            faces.append((i, i + cols + 1, i + cols + 2, i + 1))
    uv = [[coords[j] for j in face] for face in faces]
    g.mesh(parent, 'Draped bed runner', vertices, faces, color, uv=uv, smooth=True)


def wardrobe(g, parent, item):
    w, d = item['w'], item['d']
    h = 2.16
    g.box(parent, 'Wardrobe plinth', 'walnut', (0, 0, .045), (w - .06, d - .06, .09))
    g.box(parent, 'Wardrobe carcass', 'oak', (0, .024, (h + .085) / 2), (w, d - .048, h - .085))
    for i in range(4):
        x = (i - 1.5) * w / 4
        g.box(parent, f'Veneered leaf {i + 1}', 'oak', (x, -d / 2 + .01, 1.105), (w / 4 - .009, .027, 2.048), .004)
        g.box(parent, 'Pull backplate', 'bronze', (x + (.17 if i % 2 == 0 else -.17), -d / 2 - .016, 1.124), (.015, .026, .156))


def sofa(g, parent, item):
    w, d = item['w'], item['d']
    for x in [-w * .398, w * .398]:
        for y in [-d * .343, d * .343]:
            g.box(parent, 'Splayed walnut foot', 'walnut', (x, y, .063), (.055, .055, .126), .008)
    g.box(parent, 'Upholstered lower frame', 'sofa', (0, 0, .224), (w, d, .244), .055)
    g.box(parent, 'Sofa rear shell', 'sofa', (0, d / 2 - .093, .535), (w - .03, .186, .599), .051)
    for sign in [-1, 1]:
        g.box(parent, 'Rolled rectangular arm', 'sofa', (sign * (w / 2 - .073), -.033, .474), (.146, d - .068, .335), .051)
    seats = max(1, round(w / .75))
    span = (w - .302) / seats
    for i in range(seats):
        x = span * (i - (seats - 1) / 2)
        center_y = -.077
        seat_d = d - .235
        g.box(parent, 'Loose seat cushion', 'linen', (x, center_y, .386), (span - .013, seat_d, .134), .059)
        seam = [(x + a, center_y + b, .402)
                for a, b in rounded_outline(span / 2 - .008, seat_d * .491, .18)]
        g.tube(parent, 'Seat cushion welt', 'sofa', seam, .0027, sides=6, closed=True)
        back = g.box(parent, 'Loose back cushion', 'sofa', (x, d / 2 - .173, .636), (span - .015, .165, .361), .071)
        back.rotation_euler.x = -.14
    for index, x in enumerate(([-w * .29, w * .28] if seats > 1 else [0])):
        pillow = g.box(parent, 'Textured throw cushion', 'sage' if index % 2 == 0 else 'umber',
                       (x, d / 2 - .287, .602), (.32, .139, .315), .063)
        pillow.rotation_euler.x = -.29
        pillow.rotation_euler.y = .16 * (-1 if index == 0 else 1)


def chair(g, parent, x, y, angle, tea=False):
    seat = g.group(parent, 'Tea armchair' if tea else 'Dining chair', (x, y, 0), angle)
    color = 'walnut' if tea else 'oak'
    g.box(seat, 'Seat frame', color, (0, 0, .427), (.412, .408, .054), .013, grain='x')
    g.box(seat, 'Loose seat pad', 'sage' if tea else 'sofa', (0, -.011, .471), (.398, .393, .065), .027)
    for sign in [-1, 1]:
        x = sign * .159
        leg = g.box(seat, 'Tapered front support', color, (x, -.157, .223), (.033, .039, .435), .006)
        leg.rotation_euler.y = -.059 * sign
        leg = g.box(seat, 'Angled back support', color, (x, .173, .426), (.041, .037, .847), .008)
        leg.rotation_euler.x = -.11
        g.box(seat, 'Side stretcher', color, (x, .001, .324), (.025, .322, .028), .004, grain='y')
        if tea:
            g.box(seat, 'Arm support', color, (sign * .205, -.103, .53), (.026, .029, .234), .005)
            g.box(seat, 'Rounded armrest', color, (sign * .207, .004, .653), (.054, .353, .040), .017, grain='y')
    back = g.box(seat, 'Backrest ' + ('cushion' if tea else 'rail'), 'sage' if tea else color,
                 (0, .190, .742), (.37, .059, .173), .027, grain='x')
    back.rotation_euler.x = -.13


def dining(g, parent, item, tea=False):
    w, d = item['tabletop']
    top = .759
    finish = 'walnut' if tea else 'oak'
    g.box(parent, 'Solid timber slab', finish, (0, 0, top - .027), (w, d, .054), .017, grain='y')
    for sign in [-1, 1]:
        y = sign * (d / 2 - .157)
        g.box(parent, 'Breadboard end apron', finish, (0, y, .669), (w - .17, .046, .084), .009, grain='x')
        x = sign * (w / 2 - .112)
        g.box(parent, 'Long apron', finish, (x, 0, .671), (.040, d - .307, .082), .007, grain='y')
        for leg_y in (-abs(y), abs(y)):
            g.box(parent, 'Recessed solid wood leg', finish, (x, leg_y, .364), (.077, .077, .719), .011)
    chair(g, parent, 0, d / 2 + .171, 0, tea)
    for y in [-d * .319, 0, d * .319]:
        chair(g, parent, -w / 2 - .201, y, pi / 2, tea)
        if not tea:
            chair(g, parent, w / 2 + .201, y, -pi / 2)
    if tea:
        chair(g, parent, w / 2 + .270, 0, -pi / 2, True)
        tea_set(g, parent, top)
    else:
        chair(g, parent, 0, -d / 2 - .171, pi)
        for x in [-.297, .297]:
            for y in [-.632, 0, .632]:
                g.plate(parent, 'Stoneware dining plate', 'ceramic', (x, y, top), .106)
        for y in [-.770, .770]:
            g.plate(parent, 'Stoneware end plate', 'ceramic', (0, y, top), .106)
        g.lathe(parent, 'Earthenware centerpiece', 'sage', (0, 0, top), [
            (0, 0), (.068, 0), (.090, .037), (.063, .101), (.038, .118), (.033, .115), (.050, .032), (0, .012)])


def tea_set(g, parent, top):
    g.box(parent, 'Carved tea tray', 'walnut', (0, .237, top + .012), (.384, .662, .024), .012, grain='y')
    for x in [-.172, -.157, -.142, -.127, -.112]:
        g.box(parent, 'Tea tray fluting', 'oak', (x, .235, top + .027), (.003, .615, .003), 0, grain='y')
    teapot = (0, .278, top + .026)
    g.lathe(parent, 'Brown clay teapot', 'walnut', teapot, [
        (0, 0), (.067, 0), (.086, .022), (.097, .054), (.083, .094), (.059, .11), (0, .111)])
    g.lathe(parent, 'Teapot lid and knob', 'walnut', teapot, [
        (0, .107), (.064, .107), (.063, .119), (.020, .134), (.018, .145), (0, .148)])
    z = teapot[2]
    g.tube(parent, 'Arched pot handle', 'walnut', [
        (-.07, .278, z + .09), (-.121, .278, z + .109), (-.143, .278, z + .067),
        (-.127, .278, z + .024), (-.081, .278, z + .037)], .011)
    g.tube(parent, 'Curved clay spout', 'walnut', [
        (.081, .278, z + .041), (.121, .278, z + .058), (.140, .278, z + .100),
        (.151, .278, z + .118)], .014)
    for x, y in [(-.101, .013), (.095, .011), (-.099, .451), (.106, .452), (.004, .501)]:
        g.lathe(parent, 'Porcelain tasting cup', 'ceramic', (x, y, z), [
            (0, 0), (.024, 0), (.038, .037), (.036, .040), (.032, .038), (.020, .009), (0, .009)],
            segments=24)


def coffee(g, parent, item):
    w, d = item['w'], item['d']
    g.box(parent, 'Coffee table edge', 'oak', (0, 0, .328), (w, d, .058), .024, grain='y')
    g.box(parent, 'Honed stone inlay', 'quartz', (0, 0, .359), (w - .025, d - .025, .015), .007)
    for y in [-d * .31, d * .31]:
        for x in [-w * .34, w * .34]:
            g.box(parent, 'Solid walnut leg', 'walnut', (x, y, .15), (.073, .073, .302), .009)
        g.box(parent, 'Recessed table stretcher', 'walnut', (0, y, .093), (w * .70, .045, .046), .006, grain='x')
    g.box(parent, 'Cloth-bound volume', 'sage', (.07, .243, .381), (.20, .255, .027), .006, rotation=-.12)
    g.box(parent, 'Inset page block', 'linen', (.072, .243, .383), (.194, .244, .016), .002, rotation=-.12)
    g.plate(parent, 'Low stoneware bowl', 'ceramic', (-.025, -.219, .366), .105, .035)


def floor_finishes(g):
    for story, node in [('ground', 'GroundFloor'), ('upper', 'UpperFloor')]:
        parent = g.ctx.nodes[node]
        rooms = g.ctx.plan['floors'][story]['rooms']
        for room in rooms:
            x1, z1, x2, z2 = room['bounds']
            wood = room['finish'] == 'wood'
            bath = room['finish'] == 'bath'
            # An unbroken 600 mm joint grid continues between the dining and living areas.
            zstep = .182 if wood else .30 if bath else .60
            xstep = 1.52 if wood else zstep
            gap = .0025 if wood else .0035
            tile = 'floorwood' if wood else 'bathfloor' if bath else 'limestone'
            verts, faces, uv = [], [], []
            rng = Random(842331)
            r = int(z1 / zstep)
            while r * zstep < z2 - .001:
                top = max(z1, r * zstep) + gap / 2
                bottom = min(z2, (r + 1) * zstep) - gap / 2
                offset = (r % 3) * xstep / 3 if wood else 0
                col = int((x1 - offset) // xstep)
                while col * xstep + offset < x2 - .001:
                    left = max(x1, col * xstep + offset) + gap / 2
                    right = min(x2, (col + 1) * xstep + offset) - gap / 2
                    if right > left and bottom > top:
                        i = len(verts)
                        corners = [(left, -bottom), (right, -bottom), (right, -top), (left, -top)]
                        verts.extend((x, y, .0155) for x, y in corners)
                        faces.append(tuple(range(i, i + 4)))
                        u, v = rng.random(), rng.random()
                        uv.append([(u + y * 3.9, v + x * .50) if wood else
                                   (u + x * 1.5, v + y * 1.5) for x, y in corners])
                    col += 1
                r += 1
            g.mesh(parent, room['name'] + ' · recessed joints', [
                (x1, -z2, .013), (x2, -z2, .013), (x2, -z1, .013), (x1, -z1, .013)],
                [(0, 1, 2, 3)], 'woodbase' if wood else 'tilebase')
            g.mesh(parent, room['name'] + ' · finish', verts, faces, tile, uv=uv)


def refine(ctx):
    g = Geometry(ctx)
    library = bed_library()
    models = {'wardrobe': wardrobe, 'sofa': sofa, 'coffee': coffee, 'dining': dining}
    for item in ctx.plan['furnishings']:
        node = ctx.nodes[item['id']]
        clear_contents(node)
        if item['type'] == 'bed':
            bed(g, node, item, library)
        elif item['type'] == 'tea':
            dining(g, node, item, tea=True)
        else:
            models[item['type']](g, node, item)
    for source in list(library.objects):
        bpy.data.objects.remove(source, do_unlink=True)
    bpy.data.collections.remove(library)
    for name in ('GroundFixtures', 'UpperFixtures'):
        clear_contents(ctx.nodes[name])
    fixtures(g)
    floor_finishes(g)
