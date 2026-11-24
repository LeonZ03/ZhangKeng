"""Render exterior reference angles, courtyard and floor cutaways from the packed blend."""

import argparse
from pathlib import Path
import sys

import bpy
from mathutils import Vector


SHOTS = {
    "southwest": ("西南", "existing"),
    "southeast": ("东南", "existing"),
    "northeast": ("东北", "existing"),
    "courtyard": ("庭院总览", "design"),
    "ground": ("一层剖切", "ground"),
    "upper": ("二层剖切", "upper"),
    "living": ("客餐厅", "living"),
    "tea": ("茶室", "tea"),
}
ROOMS = {
    "living": ((4.12, -7.02, 1.63), (6.10, -3.65, 1.38), (5.58, -5.10, 2.92)),
    "tea": ((3.85, -2.64, 4.92), (6.62, -6.66, 4.56), (6.30, -5.25, 5.83)),
}


def show_group(name, visible):
    root = bpy.data.objects[name]
    for obj in (root, *root.children_recursive):
        obj.hide_render = not visible
        obj.hide_set(not visible)


def render_shot(name, camera, mode, folder):
    scene = bpy.context.scene
    whole = mode in ("existing", "design") or mode in ROOMS
    show_group("Roof", whole)
    show_group("Yard", whole)
    if whole:
        show_group("YardDesign", mode != "existing")
        show_group("YardExisting", mode == "existing")
    for floor, root in [("ground", "Ground"), ("upper", "Upper")]:
        show_group(root + "Floor", whole or mode == floor)
        show_group(root + "Shell", whole)
        show_group(root + "Slice", mode == floor)
    fill = None
    if mode in ROOMS:
        position, target, light = ROOMS[mode]
        lens = bpy.data.cameras.new(camera)
        lens.lens = 25
        room_camera = bpy.data.objects.new(camera, lens)
        scene.collection.objects.link(room_camera)
        room_camera.location = position
        room_camera.rotation_euler = (Vector(target) - Vector(position)).to_track_quat("-Z", "Y").to_euler()
        scene.camera = room_camera
        source = bpy.data.lights.new("室内漫反射补光", "AREA")
        source.energy = 95
        source.size = 2.8
        fill = bpy.data.objects.new(source.name, source)
        fill.location = light
        scene.collection.objects.link(fill)
    else:
        scene.camera = bpy.data.objects[camera]
    scene.render.filepath = str(folder / (name + ".jpg"))
    bpy.ops.render.render(write_still=True)
    if fill:
        bpy.data.objects.remove(fill, do_unlink=True)
    print(f"Review image saved: {name}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(".work/blender/review"))
    parser.add_argument("--shots", nargs="+", choices=tuple(SHOTS), default=list(SHOTS))
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--samples", type=int, default=20)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    folder = args.output.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.width * 3 // 4
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 93
    scene.cycles.samples = args.samples
    for name in args.shots:
        render_shot(name, *SHOTS[name], folder)


if __name__ == "__main__":
    main()
