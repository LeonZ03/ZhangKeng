"""Geometry and packed material maps for the villa interior."""

from math import cos, pi, sin, tau
from pathlib import Path
from tempfile import TemporaryDirectory

import bmesh
import bpy
import numpy as np
from mathutils import Vector


def linear(srgb):
    return srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4


def material(name, color, roughness, metal=0.0, image=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    rgb = tuple(linear(c / 255) for c in color)
    mat.diffuse_color = (*rgb, 1)
    mat.roughness = roughness
    mat.metallic = metal
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metal
    if image:
        texture = nodes.new('ShaderNodeTexImage')
        texture.image = image
        mat.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
    return mat


def maps(artifacts):
    side = 512
    rng = np.random.default_rng(58633)
    y, x = np.mgrid[0:side, 0:side] / side

    def fiber(bands, warp, contrast):
        # Irregular bands and a repeating domain yield seamless longitudinal
        # fibers without imposing a stripe period or visible tile boundary.
        samples = rng.normal(0, 1, bands)
        steps = (warp % 1) * bands
        whole = steps.astype(int)
        fraction = steps - whole
        blend = fraction * fraction * (3 - 2 * fraction)
        return contrast * (samples[whole % bands] * (1 - blend) + samples[(whole + 1) % bands] * blend)

    wave = x + .017 * np.sin(tau * y + 2.2 * np.sin(tau * x)) + .009 * np.sin(tau * (2 * y + x))
    grain = fiber(17, wave, 3.9) + fiber(65, wave + .0017 * np.sin(tau * 3 * y), 2.6)
    grain += fiber(173, wave, 1.7) - 2.8 * np.maximum(0, fiber(91, wave, 1)) ** 1.6
    grain += rng.normal(0, .9, (side, side))
    weave = 3.3 * np.sin(tau * 64 * x) * (1 + .41 * np.cos(tau * 32 * y))
    weave += 2.3 * np.sin(tau * 64 * y) * (1 - .42 * np.cos(tau * 32 * x))
    weave += rng.normal(0, 1.25, (side, side))
    cloud = np.sin(tau * (x + y)) * 1.25 + np.cos(tau * (2 * x - y)) * 1.5
    cloud += np.sin(tau * (4 * x + 3 * y)) * .65 + rng.normal(0, .9, (side, side))
    cloud += -6 * (rng.random((side, side)) < .006)

    def textured(temporary, key, name, color, roughness, pattern):
        # Opaque sRGB maps travel in the blend and GLB as packed JPEGs.
        data = np.ones((side, side, 4), dtype=np.float32)
        data[:, :, :3] = np.clip((np.array(color) + pattern[:, :, None]) / 255, 0, 1)
        path = str(Path(temporary) / (key + '.jpg'))
        generated = bpy.data.images.new(key, width=side, height=side, alpha=False)
        generated.colorspace_settings.name = 'sRGB'
        generated.pixels.foreach_set(data.reshape(-1))
        generated.file_format = 'JPEG'
        generated.save(filepath=path, quality=91)
        bpy.data.images.remove(generated)
        img = bpy.data.images.load(path)
        img.name = name + ' • sRGB'
        img.pack()
        img.filepath = '//' + key + '.jpg'
        result[key] = material(name, color, roughness, image=img)

    result = {}
    finishes = [
        ('oak', 'European oak · rift sawn', (170, 128, 89), .49, grain),
        ('walnut', 'Black walnut · oiled', (110, 75, 47), .44, grain),
        ('floorwood', 'White oak · matte floorboards', (178, 143, 105), .61, grain * 1.28),
        ('limestone', 'Limestone · honed', (203, 186, 162), .63, cloud * 1.22),
        ('bathfloor', 'Sage porcelain · satin', (170, 178, 172), .53, cloud),
        ('quartz', 'Ivory quartz · composite', (226, 220, 204), .40, cloud * .65),
        ('sofa', 'Natural flax upholstery', (199, 181, 155), .84, weave),
        ('linen', 'Ivory washed linen', (230, 223, 209), .82, weave * .82),
        ('sage', 'Olive plain weave', (145, 150, 117), .88, weave),
        ('umber', 'Caramel cotton weave', (169, 125, 89), .83, weave),
        ('massage_leather', 'Black grained upholstery', (32, 31, 30), .54, cloud * .5),
    ]
    with TemporaryDirectory(prefix='finish-maps-', dir=artifacts) as temporary:
        for key, name, color, rough, pattern in finishes:
            textured(temporary, key, name, color, rough, pattern)
    for key, name, color, rough, metal in [
        ('ceramic', 'Warm white glazed porcelain', (247, 242, 230), .24, 0),
        ('sink', 'Brushed stainless steel', (173, 181, 179), .31, .92),
        ('graphite', 'Graphite powder coat', (50, 46, 39), .35, .3),
        ('bronze', 'Satin bronze fittings', (161, 129, 86), .34, .74),
        ('cabinet', 'Kitchen fronts · muted olive', (148, 153, 129), .48, 0),
        ('tilebase', 'Warm grey grout', (168, 158, 143), .92, 0),
        ('woodbase', 'Recessed plank joints', (120, 95, 68), .85, 0),
        ('mirror', 'Silvered mirror', (218, 227, 224), .08, 1),
        ('water', 'Basin interior shadow', (159, 171, 160), .34, .17),
        ('green', 'Rubber plant · deep green', (68, 92, 52), .51, 0),
        ('newleaf', 'Rubber plant · new growth', (108, 128, 67), .57, 0),
        ('soil', 'Dry potting soil', (96, 77, 58), .94, 0),
        ('massage_shell', 'Satin black molded shell', (31, 33, 36), .40, .16),
        ('massage_trim', 'Anodized smoke trim', (82, 86, 91), .38, .61),
        ('massage_inset', 'Charcoal padded inserts', (51, 49, 47), .63, 0),
        ('book_pages', 'Ivory book paper', (213, 199, 173), .91, 0),
        ('book_navy', 'Indigo cloth binding', (55, 70, 91), .86, 0),
        ('book_green', 'Eucalyptus cloth binding', (84, 103, 83), .84, 0),
        ('book_red', 'Oxblood binding', (120, 64, 58), .77, 0),
        ('book_gray', 'Slate dust jacket', (108, 117, 121), .75, 0),
        ('book_cream', 'Oat paper cover', (196, 181, 150), .88, 0),
        ('book_brown', 'Umber leather binding', (100, 74, 51), .72, 0),
    ]:
        result[key] = material(name, color, rough, metal)
    return result


class Geometry:
    def __init__(self, ctx):
        self.ctx = ctx
        self.m = maps(ctx.artifacts)

    def group(self, parent, name, at=(0, 0, 0), rotation=0):
        obj = bpy.data.objects.new(name, None)
        parent.users_collection[0].objects.link(obj)
        obj.parent = parent
        obj.location = at
        obj.rotation_euler.z = rotation
        return obj

    def attach(self, parent, name, mesh, at=(0, 0, 0)):
        obj = bpy.data.objects.new(name, mesh)
        parent.users_collection[0].objects.link(obj)
        obj.parent = parent
        obj.location = at
        return obj

    def mesh(self, parent, name, vertices, faces, mat, at=(0, 0, 0), uv=None, smooth=False):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        mesh.materials.append(self.m[mat])
        for polygon in mesh.polygons:
            polygon.use_smooth = smooth
        if uv:
            layer = mesh.uv_layers.new()
            for polygon, coords in zip(mesh.polygons, uv):
                for loop, value in zip(polygon.loop_indices, coords):
                    layer.data[loop].uv = value
        return self.attach(parent, name, mesh, at)

    def box(self, parent, name, mat, at, dims, radius=.005, *, grain='z', rotation=0):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        for v in bm.verts:
            v.co = tuple(c * d for c, d in zip(v.co, dims))
        radius = min(radius, min(dims) * .46)
        if radius > 0:
            bmesh.ops.bevel(
                bm, geom=list(bm.edges), offset=radius, segments=3,
                affect='EDGES', clamp_overlap=True,
            )
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        finish = self.m[mat]
        mesh.materials.append(finish)
        if any(node.type == 'TEX_IMAGE' for node in finish.node_tree.nodes):
            layer = mesh.uv_layers.new()
            grain_axis = 'xyz'.index(grain)
            woven = mat in {'sofa', 'linen', 'sage', 'umber', 'massage_leather'}
            wood = mat in {'oak', 'walnut', 'floorwood'}
            scale = (8, 8) if woven else (2.8, .72) if wood else (1.8, 1.8)
            shift = (.5 + .245 * at[0] + .461 * at[1] + .307 * at[2], .5) if wood else (.5, .5)
            for poly in mesh.polygons:
                normal_axis = max(range(3), key=lambda k: abs(poly.normal[k]))
                axes = sorted({0, 1, 2} - {normal_axis})
                if wood and grain_axis in axes:
                    axes = [next(k for k in axes if k != grain_axis), grain_axis]
                for loop_index in poly.loop_indices:
                    co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
                    layer.data[loop_index].uv = tuple(co[k] * s + offset for k, s, offset in zip(axes, scale, shift))
        if radius > 0:
            # A rounded box has flat field normals and round edges. Use the
            # analytic fillet normal at each corner of each polygon.
            inner = tuple(d / 2 - radius for d in dims)
            normals = []
            for poly in mesh.polygons:
                poly.use_smooth = True
                for loop_index in poly.loop_indices:
                    co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
                    normal = Vector([c - max(-h, min(c, h)) for c, h in zip(co, inner)])
                    normals.append(normal.normalized() if normal.length > 1e-6 else poly.normal)
            mesh.normals_split_custom_set(normals)
        obj = self.attach(parent, name, mesh, at)
        obj.rotation_euler.z = rotation
        return obj

    def tube(self, parent, name, mat, path, radius, sides=10, closed=False):
        path = [Vector(p) for p in path]
        vertices, faces, uv = [], [], []
        for row, point in enumerate(path):
            a = path[row - 1] if row or closed else point
            b = path[(row + 1) % len(path)] if row + 1 < len(path) or closed else point
            direction = (b - a).normalized()
            ref = Vector((0, 0, 1)) if abs(direction.z) < .84 else Vector((1, 0, 0))
            u = direction.cross(ref).normalized() * radius
            v = direction.cross(u)
            for side in range(sides):
                phase = side * tau / sides
                vertices.append(point + cos(phase) * u + sin(phase) * v)
        for row in range(len(path) if closed else len(path) - 1):
            start = row * sides
            nxt = (row + 1) % len(path) * sides
            for side in range(sides):
                j = (side + 1) % sides
                faces.append((start + side, start + j, nxt + j, nxt + side))
                a, b = side / sides, (side + 1) / sides
                u, v = row / len(path), (row + 1) / len(path)
                uv.append([(a, u), (b, u), (b, v), (a, v)])
        if not closed:
            faces += [tuple(range(sides - 1, -1, -1)), tuple(range(len(vertices) - sides, len(vertices)))]
            uv += [[(.5, .5)] * sides] * 2
        return self.mesh(parent, name, vertices, faces, mat, uv=uv, smooth=True)

    def lathe(self, parent, name, mat, at, profile, *, aspect=1, segments=32):
        """Revolve a bottom-to-top profile, continuing inward for open vessels."""
        vertices, rows = [], []
        for r, z in profile:
            rows.append(len(vertices))
            if r == 0:
                vertices.append((0, 0, z))
                continue
            vertices.extend((r * cos(i * tau / segments), r * aspect * sin(i * tau / segments), z) for i in range(segments))
        faces, uv = [], []
        for idx, ((r0, z0), (r1, z1)) in enumerate(zip(profile, profile[1:])):
            a, b = rows[idx:idx + 2]
            for i in range(segments):
                j = (i + 1) % segments
                u, v = i / segments, (i + 1) / segments
                if r0 == 0:
                    face = (a, b + j, b + i)
                    coords = ((.5, z0 * 6), (v, z1 * 6), (u, z1 * 6))
                elif r1 == 0:
                    face = (a + i, a + j, b)
                    coords = ((u, z0 * 6), (v, z0 * 6), (.5, z1 * 6))
                else:
                    face = (a + i, a + j, b + j, b + i)
                    coords = ((u, z0 * 6), (v, z0 * 6), (v, z1 * 6), (u, z1 * 6))
                faces.append(face)
                uv.append(coords)
        return self.mesh(parent, name, vertices, faces, mat, at, uv=uv, smooth=True)

    def plate(self, parent, name, mat, at, radius, lip=.018):
        return self.lathe(parent, name, mat, at, [
            (0, 0), (radius * .68, 0), (radius * .95, lip * .40), (radius, lip * .80),
            (radius * .98, lip), (radius * .82, lip * .64), (radius * .61, lip * .28), (0, lip * .28),
        ])


def rounded_outline(rx, ry, power=.22, count=48):
    def signpow(value):
        return abs(value) ** power * (1 if value >= 0 else -1)
    return [
        (rx * signpow(cos(i * 2 * pi / count)), ry * signpow(sin(i * 2 * pi / count)))
        for i in range(count)
    ]
