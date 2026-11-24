"""Extract the reusable, texture-free bed meshes from the BeiPiao source.

Run Blender with the original furniture blend open and this script as --python.
The source is read-only. The output library contains individual editable meshes.
"""

from pathlib import Path

import bpy


def extract():
    source = bpy.data.objects['C43_Bed']
    depsgraph = bpy.context.evaluated_depsgraph_get()
    library = bpy.data.collections.new('Courtyard43 bed geometry')
    bpy.context.scene.collection.children.link(library)
    for obj in source.children:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph, preserve_all_data_layers=True)
        mesh.transform(obj.matrix_world)
        mesh.materials.clear()
        for uv in list(mesh.uv_layers)[1:]:
            mesh.uv_layers.remove(uv)
        copy = bpy.data.objects.new(obj.name.removeprefix('C43_'), mesh)
        library.objects.link(copy)
        copy['source_object'] = obj.name
        if len(mesh.vertices) > 5000:
            reduction = copy.modifiers.new('Simplify woven silhouette', 'DECIMATE')
            reduction.ratio = 0.28 if len(mesh.vertices) > 10000 else 0.55
            bpy.context.view_layer.objects.active = copy
            bpy.ops.object.modifier_apply(modifier=reduction.name)

    output = Path(__file__).resolve().parent / 'furniture_assets' / 'courtyard43-bed.blend'
    bpy.data.libraries.write(str(output), {library}, compress=True)


if __name__ == '__main__':
    extract()
