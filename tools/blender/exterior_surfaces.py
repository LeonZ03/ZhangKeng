"""Tileable maps authored in metres for the villa exterior and courtyard."""

from pathlib import Path
import struct
import zlib

import bpy
import numpy as np
from mathutils import Vector


SIZE = 320


def png(path, rgb):
    def chunk(name, contents):
        return (struct.pack("!I", len(contents)) + name + contents
                + struct.pack("!I", zlib.crc32(name + contents)))

    height, width, _ = rgb.shape
    scanlines = b"".join(b"\x00" + row.tobytes() for row in rgb)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(scanlines, 7))
        + chunk(b"IEND", b"")
    )


def noise(rng, u, v, columns, rows):
    lattice = rng.standard_normal((rows, columns))
    x, y = (u % 1) * columns, (v % 1) * rows
    xi, yi = np.floor(x).astype(int), np.floor(y).astype(int)
    a, b = x - xi, y - yi
    a, b = a * a * (3 - 2 * a), b * b * (3 - 2 * b)
    ix, iy = xi % columns, yi % rows
    jx, jy = (ix + 1) % columns, (iy + 1) % rows
    return ((1 - a) * lattice[iy, ix] + a * lattice[iy, jx]) * (1 - b) + (
        (1 - a) * lattice[jy, ix] + a * lattice[jy, jx]) * b


def RGB(rgb):
    """sRGB to scene-linear color, for Blender and glTF material factors."""
    channels = [channel / 255 for channel in rgb]
    return tuple(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
                 for channel in channels)


def solid(name, rgb, roughness, metallic=0, alpha=1, two_sided=False):
    mat = bpy.data.materials.new(name)
    color = (*RGB(rgb), alpha)
    mat.diffuse_color = color
    mat.use_nodes = True
    mat.use_backface_culling = not two_sided
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Alpha"].default_value = alpha
    if alpha < 1 and hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    return mat


class Surfaces:
    def __init__(self, workspace):
        self.directory = Path(workspace) / ".work" / "exterior"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.materials = {}
        axis = (np.arange(SIZE, dtype=np.float32) + 0.5) / SIZE
        self.u, self.v = np.meshgrid(axis, axis)

    def pattern(self, kind):
        u, v = self.u, self.v
        rng = np.random.default_rng(4217 + sum(ord(ch) for ch in kind))
        coarse = noise(rng, u, v, 8, 8)
        mid = noise(rng, u, v, 30, 30)
        fine = noise(rng, u, v, 140, 140)
        grain = rng.standard_normal(u.shape)
        if kind == "wood":
            warp = noise(rng, u, v, 5, 9) * 0.011
            stripe = noise(rng, u, v + warp, 6, 112)
            fibers = noise(rng, u, v + warp, 21, 148)
            latewood = np.sin(2 * np.pi * (v * 39 + warp * 36)) ** 14
            variation = stripe * 8 + fibers * 6 - latewood * 9 + coarse * 3 + grain * 2
            relief = stripe * 0.008 + fibers * 0.009 - latewood * 0.012 + grain * 0.003
        elif kind == "stucco":
            stones = np.maximum(0, fine + grain * 0.33)
            variation = coarse * 2 + mid * 2 + fine * 8 + grain * 7
            relief = stones * 0.035 + grain * 0.010
        elif kind == "slate":
            variation = coarse * 3 + mid * 3 + fine * 3 + grain
            relief = mid * 0.012 + fine * 0.01 + grain * 0.004
        elif kind in {"stone", "gravel", "earth"}:
            multiplier = 1.9 if kind == "gravel" else 1
            variation = coarse * 8 + mid * 6 + (fine * 6 + grain * 4) * multiplier
            relief = (mid * 0.033 + fine * 0.026 + grain * 0.009) * multiplier
        elif kind == "ashlar":
            rows, columns = 3, 5
            x = u * columns + mid * 0.041
            y = v * rows - mid * 0.043
            col, row = np.floor(x).astype(int), np.floor(y).astype(int)
            seeds = rng.uniform(0.14, 0.86, (rows, columns, 2))
            shades = rng.uniform(-18, 18, (rows, columns))
            first, second = np.full_like(u, 100), np.full_like(u, 100)
            shade = np.zeros_like(u)
            for yy in (-1, 0, 1):
                for xx in (-1, 0, 1):
                    ix, iy = (col + xx) % columns, (row + yy) % rows
                    dx = x - col - xx - seeds[iy, ix, 0]
                    dy = y - row - yy - seeds[iy, ix, 1]
                    distance = np.sqrt(dx * dx + dy * dy)
                    nearer = distance < first
                    second = np.where(nearer, first, np.minimum(second, distance))
                    first = np.where(nearer, distance, first)
                    shade = np.where(nearer, shades[iy, ix], shade)
            raised = np.clip(((second - first) - 0.019) * 13, 0, 1)
            variation = raised * (shade + coarse * 6 + mid * 5 + fine * 4 + grain * 4)
            relief = (raised - 1) * 0.22 + (coarse * 0.026 + mid * 0.033 + fine * 0.021) * raised
            return variation, relief, raised
        elif kind == "brick":
            rows, columns = 8, 5
            row = np.floor(v * rows).astype(int)
            spread = u * columns + row % 2 * 0.5
            column = np.floor(spread).astype(int) % columns
            joint = np.minimum(np.minimum(spread % 1, 1 - spread % 1),
                               np.minimum((v * rows) % 1, 1 - (v * rows) % 1))
            raised = np.clip((joint + mid * 0.012 - 0.033) * 25, 0, 1)
            tone = rng.standard_normal((rows, columns))[row, column]
            variation = raised * (tone * 10 + coarse * 4 + mid * 5 + fine * 6 + grain * 4)
            relief = ((raised - 1) * 0.24 + (mid * 0.026 + fine * 0.036 + grain * 0.01) * raised)
            return variation, relief, raised
        else:
            tufts = noise(rng, u, v, 65, 85)
            variation = coarse * 9 + mid * 5 + tufts * 7 + fine * 5 + grain * 5
            relief = tufts * 0.04 + fine * 0.04 + grain * 0.01
        return variation, relief, None

    def textured(self, name, rgb, kind, roughness, strength, mortar=None, metallic=0):
        mat = solid(name, rgb, roughness, metallic)
        variation, relief, raised = self.pattern(kind)
        color = np.asarray(rgb)[None, None, :] + variation[:, :, None]
        if mortar is not None:
            color = color * raised[:, :, None] + (np.asarray(mortar)[None, None, :]
                     + variation[:, :, None] * 0.3) * (1 - raised[:, :, None])
        color = np.clip(color, 0, 255).astype(np.uint8)

        dx = (np.roll(relief, -1, axis=1) - np.roll(relief, 1, axis=1)) * 3.5
        dy = (np.roll(relief, -1, axis=0) - np.roll(relief, 1, axis=0)) * 3.5
        vectors = np.stack((-dx, dy, np.ones_like(relief)), axis=-1)
        vectors /= np.linalg.norm(vectors, axis=-1, keepdims=True)
        normals = np.clip((vectors * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        for suffix, pixels in (("color", color), ("normal", normals)):
            key = name if suffix == "color" else kind
            path = self.directory / f"{key}-{suffix}.png"
            img = bpy.data.images.get(path.name)
            if img is None:
                png(path, pixels)
                img = bpy.data.images.load(str(path), check_existing=True)
                if suffix == "normal":
                    img.colorspace_settings.name = "Non-Color"
                img.pack()
            texture = nodes.new("ShaderNodeTexImage")
            texture.image = img
            texture.location = (-660, 130 if suffix == "color" else -130)
            if suffix == "color":
                links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])
            else:
                normal = nodes.new("ShaderNodeNormalMap")
                normal.location = (-280, -110)
                normal.inputs["Strength"].default_value = strength
                links.new(texture.outputs["Color"], normal.inputs["Color"])
                links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
        self.materials[name] = mat
        return mat


def uv_project(obj, metresize, grain=None, layer_name=None):
    """World-aligned UV islands, or use explicit world grain direction on timber."""
    mesh = obj.data
    if mesh.users > 1:
        mesh = mesh.copy()
        obj.data = mesh
    layer = mesh.uv_layers.active
    if not layer:
        layer = mesh.uv_layers.new(name=layer_name or "Surface")
    coords = [obj.matrix_world @ v.co for v in mesh.vertices]
    normal_matrix = obj.matrix_world.to_3x3().inverted_safe().transposed()
    span_u, span_v = metresize
    for face in mesh.polygons:
        normal = (normal_matrix @ face.normal).normalized()
        if grain is not None and abs(grain.dot(normal)) < 0.94:
            u = (grain - grain.dot(normal) * normal).normalized()
            v = normal.cross(u)
        elif abs(normal.z) > 0.65:
            u = Vector((1, 0, 0))
            v = normal.cross(u).normalized()
        elif abs(normal.x) > abs(normal.y):
            u = Vector((0, 1, 0))
            v = normal.cross(u).normalized()
        else:
            u = Vector((1, 0, 0))
            v = normal.cross(u).normalized()
        for index in face.loop_indices:
            co = coords[mesh.loops[index].vertex_index]
            layer.data[index].uv = (u.dot(co) / span_u, v.dot(co) / span_v)


def vertex_color(mesh, colors):
    attribute = mesh.color_attributes.new(name="Surface tint", type="BYTE_COLOR", domain="POINT")
    for item, color in zip(attribute.data, colors):
        item.color = (*color, 1)
    mesh.color_attributes.active_color = attribute
    return attribute


def use_vertex_color(mat):
    nodes = mat.node_tree.nodes
    color = nodes.new("ShaderNodeVertexColor")
    color.layer_name = "Surface tint"
    mat.node_tree.links.new(color.outputs["Color"], nodes.get("Principled BSDF").inputs["Base Color"])


def replace_surface(obj, mat):
    if obj.data.users > 1:
        obj.data = obj.data.copy()
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
