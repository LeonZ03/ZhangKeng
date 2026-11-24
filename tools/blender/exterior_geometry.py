"""Compact mesh construction for tile courses, masonry, planting and fittings."""

from math import cos, pi, sin

import bpy
from mathutils import Vector

from exterior_surfaces import vertex_color


class MeshBuilder:
    def __init__(self):
        self.points = []
        self.faces = []
        self.uvs = []
        self.colors = []
        self.smooth = []

    def face(self, points, uv=None, color=None, smooth=False):
        self.patch(points, [tuple(range(len(points)))], uv, color, smooth)

    def patch(self, points, faces, uv=None, color=None, smooth=False):
        start = len(self.points)
        self.points.extend(points)
        self.faces.extend(tuple(start + index for index in face) for face in faces)
        self.uvs.extend(uv or [(p[0], p[1]) for p in points])
        self.colors.extend([color or (1, 1, 1)] * len(points))
        self.smooth.extend([smooth] * len(faces))

    def object(self, scene, parent, name, mat, tint=False):
        if not self.faces:
            return None
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.points, [], self.faces)
        mesh.update()
        layer = mesh.uv_layers.new(name="Surface")
        for face, smooth in zip(mesh.polygons, self.smooth):
            face.use_smooth = smooth
            for index in face.loop_indices:
                layer.data[index].uv = self.uvs[mesh.loops[index].vertex_index]
        if tint:
            vertex_color(mesh, self.colors)
        obj = bpy.data.objects.new(name, mesh)
        collection = parent.users_collection[0] if parent.users_collection else scene.collection
        collection.objects.link(obj)
        obj.parent = parent
        mesh.materials.append(mat)
        return obj

    def box(self, center, dimensions, angle=0, color=None, uv_span=0.9, bevel=0):
        cx, cy, cz = center
        a, b, c = (length / 2 for length in dimensions)
        # Two inboard rings and two full-width rings give the horizontal tile edges a light bevel.
        inset = min(bevel, a * 0.33, b * 0.33, c * 0.8)
        corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        levels = [(-c, inset), (c, inset)] if not inset else [
            (-c, inset), (-c + inset, 0), (c - inset, 0), (c, inset),
        ]
        points = []
        for z, offset in levels:
            for sign_x, sign_y in corners:
                x, y = sign_x * (a - offset), sign_y * (b - offset)
                points.append((cx + x * cos(angle) - y * sin(angle),
                               cy + x * sin(angle) + y * cos(angle), cz + z))
        top = (len(levels) - 1) * 4
        for face in [(3, 2, 1, 0), (top, top + 1, top + 2, top + 3)]:
            coords = [points[index] for index in face]
            self.face(coords, [(p[0] / uv_span, p[1] / uv_span) for p in coords], color)
        for level in range(len(levels) - 1):
            for side in range(4):
                i = level * 4 + side
                j = level * 4 + (side + 1) % 4
                coords = [points[index] for index in (i, j, j + 4, i + 4)]
                use_x = abs(coords[1][0] - coords[0][0]) > abs(coords[1][1] - coords[0][1])
                self.face(coords, [(p[0 if use_x else 1] / uv_span, p[2] / uv_span)
                                   for p in coords], color)

    def branch(self, start, end, radius_a, radius_b, sides=7, color=None):
        start, end = Vector(start), Vector(end)
        direction = (end - start).normalized()
        u = direction.cross(Vector((0, 0, 1)))
        if u.length_squared < 0.01:
            u = direction.cross(Vector((0, 1, 0)))
        u.normalize()
        v = direction.cross(u)
        points, uv = [], []
        length = (end - start).length
        for center, radius, x in ((start, radius_a, 0.0), (end, radius_b, length)):
            for i in range(sides + 1):
                theta = i * 2 * pi / sides
                points.append(center + (u * cos(theta) + v * sin(theta)) * radius)
                uv.append((x / 2.6, theta * radius_a / 0.8))
        faces = [(i, i + 1, i + sides + 2, i + sides + 1) for i in range(sides)]
        self.patch(points, faces, uv, color, smooth=True)


def descendants(parent):
    for child in list(parent.children):
        yield child
        yield from descendants(child)


def center_and_spans(obj):
    bounds = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lower = Vector(tuple(min(p[axis] for p in bounds) for axis in range(3)))
    upper = Vector(tuple(max(p[axis] for p in bounds) for axis in range(3)))
    return (lower + upper) * 0.5, upper - lower


def long_axis(obj):
    world = obj.matrix_world.to_3x3()
    bounds = [Vector(corner) for corner in obj.bound_box]
    spans = [(max(p[axis] for p in bounds) - min(p[axis] for p in bounds)
              ) * world.col[axis].length for axis in range(3)]
    return world.col[max(range(3), key=spans.__getitem__)].normalized()
