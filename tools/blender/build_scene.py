"""Build the editable villa and the website GLB from the metric floor plan."""

import argparse
from collections import defaultdict
from contextlib import contextmanager
import json
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

import bpy
from mathutils import Matrix, Quaternion, Vector
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[2]
ARTIFACTS = WORKSPACE / ".work" / "blender"
BASIS = Matrix.Rotation(math.pi / 2, 4, "X")
BASIS_INVERSE = BASIS.inverted()
LAYER_GROUPS = {
    "GroundFloor": "01 一层",
    "UpperFloor": "02 二层",
    "Roof": "03 屋顶",
    "Yard": "04 庭院",
}
HIDDEN_IN_EXTERIOR = ("GroundSlice", "UpperSlice", "YardExisting")
GLB_LIMIT = 24 * 1024 * 1024


def make_material(key, source):
    material = bpy.data.materials.new(key)
    color = (*source["color"], source["opacity"])
    material.diffuse_color = color
    material.use_nodes = True
    material.use_backface_culling = not source["doubleSided"]
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Alpha"].default_value = source["opacity"]
    shader.inputs["Roughness"].default_value = source["roughness"]
    shader.inputs["Metallic"].default_value = source["metalness"]
    if source["opacity"] < 1:
        material.surface_render_method = "BLENDED"
    if source["vertexColors"]:
        vertex_color = material.node_tree.nodes.new("ShaderNodeVertexColor")
        vertex_color.layer_name = "Surface color"
        material.node_tree.links.new(vertex_color.outputs["Color"], shader.inputs["Base Color"])
    return material


def blender_vectors(flat):
    vectors = np.asarray(flat, dtype=np.float32).reshape(-1, 3)
    return np.column_stack((vectors[:, 0], -vectors[:, 2], vectors[:, 1]))


def make_mesh(key, geometry, material, flat):
    positions = blender_vectors(geometry["position"])
    indices = geometry["indices"]
    if indices is None:
        indices = np.arange(len(positions), dtype=np.int32)
    triangles = np.asarray(indices, dtype=np.int32).reshape(-1, 3)
    mesh = bpy.data.meshes.new(key)
    mesh.from_pydata(positions.tolist(), [], triangles.tolist())
    mesh.materials.append(material)
    mesh.update()
    if "normal" in geometry and not flat:
        normals = blender_vectors(geometry["normal"])
        mesh.polygons.foreach_set("use_smooth", np.full(len(mesh.polygons), True, dtype=bool))
        mesh.normals_split_custom_set_from_vertices(normals.tolist())
    if "uv" in geometry:
        loop_vertices = np.empty(len(mesh.loops), dtype=np.int32)
        mesh.loops.foreach_get("vertex_index", loop_vertices)
        uv_by_vertex = np.asarray(geometry["uv"], dtype=np.float32).reshape(-1, 2)
        mesh.uv_layers.new(name="UVMap").data.foreach_set("uv", uv_by_vertex[loop_vertices].ravel())
    if "color" in geometry:
        color = np.asarray(geometry["color"], dtype=np.float32).reshape(-1, 3)
        rgba = np.column_stack((color, np.ones(len(color), dtype=np.float32)))
        layer = mesh.color_attributes.new(name="Surface color", type="FLOAT_COLOR", domain="POINT")
        layer.data.foreach_set("color", rgba.ravel())
    return mesh


def import_plan(data):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "樟坑别墅"
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.unit_settings.scale_length = 1.0
    model_collection = bpy.data.collections.new("樟坑别墅")
    scene.collection.children.link(model_collection)
    ctx = SimpleNamespace(
        workspace=WORKSPACE, artifacts=ARTIFACTS, scene=scene, plan=data["plan"], nodes={},
        materials={key: make_material(key, source) for key, source in data["materials"].items()},
    )
    meshes = {}

    def import_node(node, parent, collection):
        identifier = node.get("id")
        if identifier in LAYER_GROUPS:
            layer = bpy.data.collections.new(LAYER_GROUPS[identifier])
            collection.children.link(layer)
            collection = layer
        material = node.get("material")
        mesh = None
        if material is not None:
            mesh_id = (node["mesh"], material)
            if mesh_id not in meshes:
                meshes[mesh_id] = make_mesh(
                    f"{material} {node['mesh']:03d}", data["geometries"][node["mesh"]],
                    ctx.materials[material], data["materials"][material]["flat"],
                )
            mesh = meshes[mesh_id]
        obj = bpy.data.objects.new(identifier or node["label"] or material or "构件", mesh)
        collection.objects.link(obj)
        obj.parent = parent
        x, y, z, w = node["rotation"]
        transform = Matrix.LocRotScale(Vector(node["position"]), Quaternion((w, x, y, z)), Vector(node["scale"]))
        obj.matrix_basis = BASIS @ transform @ BASIS_INVERSE
        obj["source_name"] = node["label"]
        if mesh is None:
            obj.empty_display_size = 0.15
        else:
            obj["source_material"] = material
            obj["castShadow"] = node["castShadow"]
            obj["receiveShadow"] = node["receiveShadow"]
        if identifier:
            ctx.nodes[identifier] = obj
        for child in node["children"]:
            import_node(child, obj, collection)

    import_node(data["scene"], None, model_collection)
    bpy.context.view_layer.update()
    return ctx


def set_hidden(root, hidden):
    for obj in (root, *root.children_recursive):
        obj.hide_set(hidden)
        obj.hide_render = hidden


def camera(collection, name, position, target, focal, roll=0):
    data = bpy.data.cameras.new(name)
    data.lens = focal
    data.sensor_width = 36
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = position
    obj.rotation_mode = "QUATERNION"
    direction = (Vector(target) - obj.location).to_track_quat("-Z", "Y")
    obj.rotation_quaternion = direction @ Quaternion((0, 0, 1), roll)
    return obj


def add_presentation(ctx):
    scene = ctx.scene
    collection = bpy.data.collections.new("05 观察相机与灯光")
    scene.collection.children.link(collection)
    # Photo viewpoints were aligned approximately from facade corners and openings.
    scene.camera = camera(collection, "西南", (-10.138, -17.864, 1.884), (-1.001, -10.127, 2.696), 30.442, -0.03145)
    camera(collection, "东南", (27.1, -16.8, 0.85), (16.8, -10.8, 2.22), 33.1, -0.074)
    camera(collection, "东北", (19.762, 12.541, 0.931), (11.697, 3.695, 1.768), 27.107, -0.01517)
    camera(collection, "庭院总览", (-18.0, -23.5, 18.0), (4.8, -2.35, 2.4), 40)
    camera(collection, "一层剖切", (-11.2, -19.4, 17.7), (5.5, -4.4, 0.25), 44)
    camera(collection, "二层剖切", (22.6, -17.6, 21.1), (5.5, -4.4, 3.52), 45)

    world = bpy.data.worlds.new("日间环境")
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.57, 0.68, 0.86, 1)
    background.inputs["Strength"].default_value = 0.56
    scene.world = world
    sun_data = bpy.data.lights.new("午后日光", "SUN")
    sun_data.energy = 2.4
    sun_data.color = (1.0, 0.91, 0.79)
    sun_data.angle = math.radians(4.5)
    sun = bpy.data.objects.new("午后日光", sun_data)
    collection.objects.link(sun)
    sun.rotation_euler = Vector((-0.52, 0.53, -0.77)).to_track_quat("-Z", "Y").to_euler()

    ground_material = bpy.data.materials.new("场地外灰石台")
    ground_material.diffuse_color = (0.19, 0.185, 0.17, 1)
    ground_mesh = bpy.data.meshes.new("场地外灰石台")
    ground_mesh.from_pydata([(-120, -120, -.66), (120, -120, -.66), (120, 120, -.66), (-120, 120, -.66)], [], [[0, 1, 2, 3]])
    ground_mesh.materials.append(ground_material)
    ground = bpy.data.objects.new("场地外灰石台", ground_mesh)
    collection.objects.link(ground)

    ctx.nodes["Villa"]["尺寸来源"] = "建筑设计平面图、庭院施工图、现场照片"
    ctx.nodes["Villa"]["估算尺寸"] = "檐口、屋脊、部分窗台、未标注的家具规格与饰面"
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.view_settings.view_transform = "AgX"
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                view = area.spaces.active
                view.shading.color_type = "MATERIAL"
                view.overlay.show_extras = False
                view.region_3d.view_perspective = "CAMERA"


@contextmanager
def web_model(ctx):
    """Combine opaque meshes within each switchable layer or furniture anchor."""
    originals = {obj: name for name, obj in ctx.nodes.items()}
    for obj in ctx.nodes["Villa"].children_recursive:
        if obj.get("exploreAction"):
            originals.setdefault(obj, obj.name)
    collection = bpy.data.collections.new("临时网页导出")
    ctx.scene.collection.children.link(collection)
    clones = {}
    batches = defaultdict(list)

    def layer_parent(obj):
        parent = obj.parent
        while parent and parent not in originals:
            parent = parent.parent
        return parent

    def combine(group, members):
        if len(members) < 2:
            return
        root, shadow, receives, materials = group
        label = materials[0].name if materials and materials[0] else "构件"
        tile = bpy.data.meshes.new(label)
        batch = bpy.data.objects.new(f"{root.name} {label}", tile)
        collection.objects.link(batch)
        batch.parent = root
        batch["castShadow"] = shadow
        batch["receiveShadow"] = receives
        bpy.context.view_layer.update()
        with bpy.context.temp_override(active_object=batch, selected_objects=[batch, *members],
                                       selected_editable_objects=[batch, *members]):
            bpy.ops.object.join()

    try:
        for source, name in originals.items():
            source.name = f"可编辑 {name}"
        for source, name in originals.items():
            clone = bpy.data.objects.new(name, None)
            collection.objects.link(clone)
            clones[source] = clone
            for key, value in source.items():
                clone[key] = value
        for source, clone in clones.items():
            parent = layer_parent(source)
            clone.parent = clones.get(parent)
            clone.matrix_basis = (parent.matrix_world.inverted_safe() @ source.matrix_world) if parent else source.matrix_world.copy()

        depsgraph = bpy.context.evaluated_depsgraph_get()
        source_root = ctx.nodes["Villa"]
        for source in source_root.children_recursive:
            if source.type != "MESH":
                continue
            mesh = bpy.data.meshes.new_from_object(source.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph)
            clone = bpy.data.objects.new(source.name, mesh)
            collection.objects.link(clone)
            scope = layer_parent(source)
            clone.parent = clones[scope]
            clone.matrix_basis = scope.matrix_world.inverted_safe() @ source.matrix_world
            materials = tuple(mesh.materials)
            opaque = all(material.diffuse_color[3] >= .99 for material in materials if material)
            shadow = bool(source.get("castShadow", opaque))
            receives = bool(source.get("receiveShadow", opaque))
            clone["castShadow"] = shadow
            clone["receiveShadow"] = receives
            if opaque:
                batches[clones[scope], shadow, receives, materials].append(clone)

        bpy.context.view_layer.update()
        for group, members in batches.items():
            combine(group, members)
        yield clones[source_root]
    finally:
        for obj in list(collection.objects):
            mesh = obj.data if obj.type == "MESH" else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        bpy.data.collections.remove(collection)
        for source, name in originals.items():
            source.name = name


def export_glb(ctx, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="page-export-", suffix=".glb", dir=ARTIFACTS, delete=False) as handle:
        staging = Path(handle.name)
    try:
        with web_model(ctx) as root:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in (root, *root.children_recursive):
                obj.select_set(True)
            bpy.context.view_layer.objects.active = root
            bpy.ops.export_scene.gltf(
                filepath=str(staging), export_format="GLB", use_selection=True,
                export_yup=True, export_cameras=False, export_lights=False,
                export_extras=True, export_animations=False, export_apply=False,
                export_image_format="WEBP", export_image_quality=94,
            )
        size = staging.stat().st_size
        if size > GLB_LIMIT:
            raise RuntimeError(f"GLB exceeds the Pages asset budget: {size / 1024 ** 2:.1f} MiB")
        staging.replace(destination)
    finally:
        staging.unlink(missing_ok=True)
    print(f"Website GLB: {size / 1024 ** 2:.2f} MiB ({destination})", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ARTIFACTS / "geometry.json")
    parser.add_argument("--blend", type=Path, default=ARTIFACTS / "樟坑别墅.blend")
    parser.add_argument("--asset", type=Path, default=WORKSPACE / "site" / "assets" / "zhangkeng.glb")
    parser.add_argument("--base-only", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    data = json.loads(args.source.read_text(encoding="utf-8"))
    if data["schema"] != 1:
        raise ValueError("Unknown Blender input schema")
    ctx = import_plan(data)
    if not args.base_only:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import exterior
        import interior

        exterior.refine(ctx)
        bpy.context.view_layer.update()
        interior.refine(ctx)
        bpy.context.view_layer.update()

    export_glb(ctx, args.asset.resolve())
    add_presentation(ctx)
    for name in HIDDEN_IN_EXTERIOR:
        set_hidden(ctx.nodes[name], True)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.file.pack_all()
    args.blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.blend.resolve()), compress=True)


if __name__ == "__main__":
    main()
