"""Chapter 1 Attendance (DL-12 to DL-14): its own set, built and exported apart from the prologue.

Design: docs/chapter1_attendance_plan.md. Game x from OFF6 = 200, floor at height 0, the lane at Blender y = 0.
Each scene's module (dl12.py, dl13.py, dl14.py, here) has build_set(dl01, m, coll), called in final world coordinates
with the prologue's builder (art/dl01/build_dl01.py) as `dl01` for its helpers and `m` its shared materials. A module
that doesn't exist yet is skipped.

Run from art/dl01 (shares the Blender lock with the prologue's build):
    flock <lock> /opt/bpyenv/bin/python ../ch1/build_attendance.py --out <dir> [--blend <dir>/attendance.blend]
Writes attendance.glb and attendance.json (+ parts) for the game's assets/.
"""
import argparse
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'dl01'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'common'))

import bpy  # noqa: E402
import build_dl01 as dl01  # noqa: E402

OFF6 = 200.0
SCENES = ('dl12', 'dl13', 'dl14')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--blend', default=None)
    ap.add_argument('--only', default=None, help='comma-separated scene modules to build (default: all)')
    args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 24
    m = dl01.set_materials()
    coll = bpy.data.collections.new('ATT_Set')
    bpy.context.scene.collection.children.link(coll)
    wanted = args.only.split(',') if args.only else SCENES
    for name in wanted:
        if not os.path.exists(os.path.join(HERE, name + '.py')):
            print('skip', name, '(not written yet)')
            continue
        mod = importlib.import_module(name)
        bpy.context.view_layer.update()
        mod.build_set(dl01, m, coll)
        print('built', name)
    objs = [o for o in coll.all_objects if o.type in ('MESH', 'CURVE', 'EMPTY')]
    if not objs:
        print('nothing to export')
        return
    dl01.export(os.path.join(out, 'attendance.glb'), objs)
    dl01.pack_for_web(out, ['attendance'])
    if args.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))
    print('exported', out)


if __name__ == '__main__':
    main()
