"""Unity export of the Blender sets (U-12, issue #9): one glTF per region into unity/DeadLetter/Assets/Art/, alongside
the web build's GLBs, which this never writes.

    python3 tools/unity_export/export_regions.py                       # prologue regions + the White + couriers
    python3 tools/unity_export/export_regions.py --regions DL-01,DL-02 # a subset (shared textures are kept)
    python3 tools/unity_export/export_regions.py --check-web /tmp/web  # also write the web GLBs to /tmp/web and
                                                                       # compare them with game/undelivered/assets
    python3 tools/unity_export/export_regions.py --chapter1 --out /tmp/att   # chapter 1 (attendance) as well

Runs under bpy-as-module (pip install bpy==5.2.x, Python 3.13), the same as the generators. It does not change the
generators: it runs art/dl01/build_dl01.py's main() (and art/ch1/build_attendance.py's) with their export functions
swapped for one that records which objects each web GLB would hold, then, in that throwaway Blender session:

1. splits the set into regions (conventions.py: by bounding-box centre x; >30 m wide meshes go to the backdrop),
2. renames the mechanism objects to MECH_<Type>_<scene>_<name>[__<part>] (their source name kept as the custom
   property dl_name, exported as glTF extras) and adds the CHK_ checkpoint empties and the anchors of part-only
   mechanisms,
3. exports each region as <region>/<region>.gltf + .bin with its PNGs in the shared Art/Textures/ folder (one copy of
   each texture, and a TextureImporter Unity can set per-platform sizes on; an embedded GLB texture has none),
4. writes <region>/<region>.art.json (bounds, lane x-range, markers, materials, textures, names the web build looks
   up), Art/regions.json and Art/Textures/textures.json, and stable-GUID .meta files for new outputs,
5. exports the White and the couriers as GLBs with the web build's exporter settings, and rebuilds D-17 to check its
   clips against the committed Assets/Art/D17/d17.glb (written only with --write-d17).

docs/unity/asset_conventions.md describes the outputs; tools/unity_export/report.py prints their numbers.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import conventions as C  # noqa: E402
import report  # noqa: E402

WEB_ASSETS = os.path.join(REPO, 'game', 'undelivered', 'assets')
INDEX_HTML = os.path.join(REPO, 'game', 'undelivered', 'index.html')
UNITY_PROJECT = os.path.join(REPO, 'unity', 'DeadLetter')
DEFAULT_OUT = os.path.join(UNITY_PROJECT, 'Assets', 'Art')
TEXTURES = 'Textures'


def log(*a):
    print('[unity_export]', *a, flush=True)


# ---- Running the generators with their exports captured ------------------------------------------------------------

def run_captured(dl01, entry, argv, check_dir=None):
    """Runs a generator's main() with dl01.export recording {glb name: objects} instead of writing (or, with check_dir,
    writing there with the unchanged web settings). pack_for_web (the base64 JSON parts) never runs."""
    captured = {}
    real_export, real_pack = dl01.export, dl01.pack_for_web

    def export(path, objects):
        name = os.path.splitext(os.path.basename(path))[0]
        captured[name] = list(objects)
        if check_dir:
            real_export(os.path.join(check_dir, name + '.glb'), list(objects))

    dl01.export = export
    dl01.pack_for_web = lambda out, names: None
    old = sys.argv
    sys.argv = argv
    try:
        entry()
    finally:
        sys.argv = old
        dl01.export, dl01.pack_for_web = real_export, real_pack
    return captured


def export_gltf(bpy, path, objects, separate):
    """The web build's exporter settings (build_dl01.export), plus extras and, for sets, external textures."""
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    kw = dict(filepath=path, export_format='GLTF_SEPARATE' if separate else 'GLB', use_selection=True,
              export_apply=True, export_yup=True, export_lights=False, export_cameras=False,
              export_animations=True, export_animation_mode='NLA_TRACKS', export_force_sampling=True,
              export_optimize_animation_size=True, export_def_bones=False, export_skins=True,
              export_materials='EXPORT', export_extras=True)
    if separate:
        kw['export_texture_dir'] = '../' + TEXTURES
    bpy.ops.export_scene.gltf(**kw)


# ---- Region split -------------------------------------------------------------------------------------------------

def hierarchy_groups(objs):
    """Top-level object (within objs) -> [it and its descendants within objs], in a stable order."""
    inside = set(objs)
    groups = {}
    for o in objs:
        top = o
        while top.parent is not None and top.parent in inside:
            top = top.parent
        groups.setdefault(top, []).append(o)
    return groups


def world_bounds(objs):
    from mathutils import Vector
    lo, hi = [1e9] * 3, [-1e9] * 3
    for o in objs:
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box] if o.type in ('MESH', 'CURVE') else [o.matrix_world.translation]
        for p in pts:
            for k in range(3):
                lo[k] = min(lo[k], p[k])
                hi[k] = max(hi[k], p[k])
    return lo, hi


def split(objs, table, backdrop, forced):
    """region name -> objects. forced: top-level object -> region (mechanisms export with their scene)."""
    out = {}
    for top, members in hierarchy_groups(objs).items():
        lo, hi = world_bounds(members)
        if top in forced:
            region = forced[top]
        elif backdrop and hi[0] - lo[0] > C.BACKDROP_WIDTH:
            region = backdrop[0]
        else:
            region = C.region_for_x(table, (lo[0] + hi[0]) / 2) or table[-1][0]
        out.setdefault(region, []).extend(members)
    return out


# ---- Conventions applied to the export copy -----------------------------------------------------------------------

def driven_names():
    """Quoted identifiers in index.html: the names the web build looks objects up by (plus some noise; only names that
    match an object are used)."""
    with open(INDEX_HTML, encoding='utf-8') as fh:
        text = fh.read()
    return set(re.findall(r"""['"]([A-Za-z][A-Za-z0-9_.]{2,})['"]""", text))


def apply_mechanisms(bpy, objs, marker_coll):
    """Renames the mapped mechanism objects; returns (records, forced top-level regions, anchors, problems)."""
    by_name = {o.name: o for o in objs}
    inside = set(objs)
    records, forced, anchors, problems = [], {}, [], []
    for type_, mid, root, parts in C.MECHANISMS:
        region = C.SCENE_REGION[mid.split('.')[0]]
        srcs = ([(root, None)] if root else []) + [(p, p) for p in parts]
        found = [(by_name[s], part) for s, part in srcs if s in by_name]
        for s, _ in srcs:
            if s not in by_name:
                problems.append(f'{mid}: object {s} not in the set')
        if not found:
            continue
        for o, part in found:
            src = o.name
            new = C.mech_name(type_, mid, part)
            o.name = new
            if o.name != new:
                problems.append(f'{mid}: {src} could not take the name {new} (got {o.name})')
            o['dl_name'], o['dl_mech'], o['dl_type'] = src, mid, type_
            if part:
                o['dl_part'] = part
            top = o
            while top.parent is not None and top.parent in inside:
                top = top.parent
            forced[top] = region
            records.append({'source': src, 'name': o.name, 'type': type_, 'id': mid, 'part': part or '', 'region': region})
        if root is None:
            # A mechanism made only of parts gets an empty anchor at their centre (the parts are not re-parented).
            lo, hi = world_bounds([o for o, _ in found])
            e = bpy.data.objects.new(C.mech_name(type_, mid), None)
            e.location = [(a + b) / 2 for a, b in zip(lo, hi)]
            e.empty_display_type = 'PLAIN_AXES'
            e['dl_mech'], e['dl_type'] = mid, type_
            marker_coll.objects.link(e)
            anchors.append((e, region))
            records.append({'source': '', 'name': e.name, 'type': type_, 'id': mid, 'part': '', 'region': region})
    return records, forced, anchors, problems


def add_checkpoints(bpy, table, marker_coll):
    out = []
    order = 0
    for name, x, y, game_region in C.CHECKPOINTS:
        order += 1
        region = C.region_for_x(table, x)
        if region is None:
            continue
        e = bpy.data.objects.new('CHK_' + name, None)
        e.location = (x, 0.0, y)
        e.empty_display_type = 'SINGLE_ARROW'
        e['dl_order'], e['dl_game_region'], e['dl_height'] = order, game_region, y
        marker_coll.objects.link(e)
        out.append((e, region))
    return out


# ---- Sidecars -----------------------------------------------------------------------------------------------------

def material_records(j):
    imgs = j.get('images', [])
    texs = j.get('textures', [])

    def tex(info):
        if not info:
            return ''
        im = imgs[texs[info['index']]['source']]
        return os.path.basename(im.get('uri', im.get('name', '')))

    out = []
    for m in j.get('materials', []):
        pbr = m.get('pbrMetallicRoughness', {})
        ext = m.get('extensions', {})
        out.append({
            'name': m.get('name', ''),
            'baseColor': pbr.get('baseColorFactor', [1, 1, 1, 1]),
            'metallic': pbr.get('metallicFactor', 1.0),
            'roughness': pbr.get('roughnessFactor', 1.0),
            'emissive': m.get('emissiveFactor', [0, 0, 0]),
            'emissiveStrength': ext.get('KHR_materials_emissive_strength', {}).get('emissiveStrength', 1.0),
            'transmission': ext.get('KHR_materials_transmission', {}).get('transmissionFactor', 0.0),
            'alphaMode': m.get('alphaMode', 'OPAQUE'),
            'alphaCutoff': m.get('alphaCutoff', 0.5),
            'doubleSided': bool(m.get('doubleSided', False)),
            'baseColorTexture': tex(pbr.get('baseColorTexture')),
            'emissiveTexture': tex(m.get('emissiveTexture')),
            'normalTexture': tex(m.get('normalTexture')),
            'normalScale': m.get('normalTexture', {}).get('scale', 1.0),
            'metallicRoughnessTexture': tex(pbr.get('metallicRoughnessTexture')),
            'occlusionTexture': tex(m.get('occlusionTexture')),
        })
    return out


def texture_uses(materials):
    use = {}
    for m in materials:
        for k, u in (('baseColorTexture', 'color'), ('emissiveTexture', 'color'), ('normalTexture', 'normal'),
                     ('metallicRoughnessTexture', 'linear'), ('occlusionTexture', 'linear')):
            if m[k]:
                use.setdefault(m[k], u)
    return use


def marker_record(o):
    from conventions import blender_to_unity
    name = o.name
    prefix = next((p for p in report.PREFIXES if name.startswith(p)), '')
    props = [{'key': k[3:], 'value': str(o[k])} for k in sorted(o.keys()) if k.startswith('dl_')]
    lo, hi = world_bounds([o])
    # Most generators build meshes in world space with the origin at 0, so 'position' (the node's origin, what the
    # Unity transform holds) is often 0 and 'center' (the bounding-box centre) is where the thing is.
    rec = {'name': name, 'prefix': prefix.rstrip('_'), 'source': str(o.get('dl_name', '')),
           'position': blender_to_unity(o.matrix_world.translation),
           'center': blender_to_unity([(a + b) / 2 for a, b in zip(lo, hi)]), 'hasMesh': o.type in ('MESH', 'CURVE'),
           'props': props}
    return rec


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def ensure_meta(project_root, abs_path, folder=False):
    """A stable-GUID .meta (Core StableGuid's scheme) for a new output; an existing .meta is left alone."""
    rel = os.path.relpath(abs_path, project_root).replace(os.sep, '/')
    meta = abs_path + '.meta'
    if not os.path.exists(meta):
        write_text(meta, C.folder_meta(rel) if folder else C.file_meta(rel))


def sha(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ---- One build (prologue or chapter 1) --------------------------------------------------------------------------

def export_set(bpy, set_objs, table, backdrop, out, wanted, mech, written_textures, index, driven):
    marker_coll = bpy.data.collections.new('UnityMarkers')
    bpy.context.scene.collection.children.link(marker_coll)
    records, forced, anchors, problems = apply_mechanisms(bpy, set_objs, marker_coll) if mech else ([], {}, [], [])
    for p in problems:
        log('mechanism map:', p)
    checkpoints = add_checkpoints(bpy, table, marker_coll)
    regions = split(set_objs, table, backdrop, forced)
    for e, region in anchors + checkpoints:
        regions.setdefault(region, []).append(e)
    meta = {r[0]: r for r in table + ([backdrop] if backdrop else [])}
    project_root = UNITY_PROJECT
    for name in [r[0] for r in table] + ([backdrop[0]] if backdrop else []):
        objs = regions.get(name, [])
        if wanted and name not in wanted:
            continue
        if not objs:
            log(name, 'has no objects; skipped')
            continue
        folder = os.path.join(out, name)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, name + '.gltf')
        log('export', name, len(objs), 'objects')
        export_gltf(bpy, path, objs, separate=True)
        s = report.stats(path)
        j = s['json']
        mats = material_records(j)
        uses = texture_uses(mats)
        textures = []
        for im in s['images']:
            textures.append({'file': im['file'], 'width': im['width'], 'height': im['height'],
                             'use': uses.get(im['file'], 'color')})
            entry = written_textures.setdefault(im['file'], dict(textures[-1], regions=[]))
            entry['regions'].append(name)
        lo, hi = world_bounds(objs)
        _, scenes, game_region, x0, x1 = meta[name]
        node_names = {n.get('name') for n in j.get('nodes', [])}
        markers = [marker_record(o) for o in objs
                   if any(o.name.startswith(p) for p in report.PREFIXES) and o.name in node_names]
        src_names = {str(o.get('dl_name', o.name)) for o in objs}
        sidecar = {
            'format': 1,
            'region': name,
            'scenes': scenes,
            'gameRegion': game_region,
            'laneRange': [x0, x1] if x0 is not None else [round(lo[0], 3), round(hi[0], 3)],
            'boundsMin': C.blender_to_unity(lo),
            'boundsMax': C.blender_to_unity(hi),
            'axes': 'unity = (blender.x, blender.z, blender.y), port_architecture 0.2',
            'gltf': name + '.gltf',
            'counts': {'nodes': s['nodes'], 'meshes': s['meshes'], 'primitives': s['primitives'],
                       'triangles': s['triangles'], 'materials': s['materials'], 'textures': len(s['images'])},
            'markers': markers,
            'materials': mats,
            'textures': textures,
            'driven': sorted(n for n in src_names if n in driven),
            'todo': [f'{k}_: {v}' for k, v in C.TODO.items()],
        }
        sidecar_path = os.path.join(folder, name + '.art.json')
        write_text(sidecar_path, json.dumps(sidecar, indent=1) + '\n')
        for p in (folder,):
            ensure_meta(project_root, p, folder=True)
        for f in os.listdir(folder):
            if not f.endswith('.meta'):
                ensure_meta(project_root, os.path.join(folder, f))
        index.append({'name': name, 'kind': 'set', 'folder': name, 'file': name + '.gltf', 'scenes': scenes,
                      'gameRegion': game_region, 'laneRange': sidecar['laneRange'], 'boundsMin': sidecar['boundsMin'],
                      'boundsMax': sidecar['boundsMax'], 'sidecar': name + '.art.json'})
    return records


def write_name_map(path, records, driven_by_region):
    lines = ['region,source_name,unity_name,kind,mechanism_id,type,part']
    for r in sorted(records, key=lambda r: (r['region'], r['id'], r['part'])):
        lines.append(','.join([r['region'], r['source'], r['name'], 'mechanism', r['id'], r['type'], r['part']]))
    for region in sorted(driven_by_region):
        for n in sorted(driven_by_region[region]):
            lines.append(','.join([region, n, n, 'driven', '', '', '']))
    write_text(path, '\n'.join(lines) + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', default=DEFAULT_OUT, help='the Unity Art folder (default: unity/DeadLetter/Assets/Art)')
    ap.add_argument('--regions', default=None, help='comma-separated region names (default: all)')
    ap.add_argument('--chapter1', action='store_true', help='also build and export chapter 1 (attendance)')
    ap.add_argument('--no-prologue', action='store_true', help='skip the prologue (with --chapter1)')
    ap.add_argument('--no-characters', action='store_true', help='skip the White, the couriers and the D-17 check')
    ap.add_argument('--write-d17', action='store_true', help='replace Assets/Art/D17/d17.glb with the rebuilt one')
    ap.add_argument('--check-web', default=None, metavar='DIR',
                    help='also write the web GLBs into DIR (never game/) and compare them with game/undelivered/assets')
    ap.add_argument('--name-map', default=os.path.join(REPO, 'docs', 'unity', 'name_map.csv'))
    args = ap.parse_args()

    out = os.path.abspath(args.out)
    if os.path.commonpath([out, os.path.abspath(WEB_ASSETS)]) == os.path.abspath(WEB_ASSETS):
        sys.exit('refusing to write into the web build assets')
    wanted = set(args.regions.split(',')) if args.regions else None
    os.makedirs(os.path.join(out, TEXTURES), exist_ok=True)
    check_dir = os.path.abspath(args.check_web) if args.check_web else None
    if check_dir:
        os.makedirs(check_dir, exist_ok=True)

    sys.path.insert(0, os.path.join(REPO, 'art', 'dl01'))
    import bpy
    import build_dl01 as dl01
    log('bpy', bpy.app.version_string)
    driven = driven_names()

    written_textures, index, records, driven_by_region = {}, [], [], {}
    scratch = tempfile.mkdtemp(prefix='dl_unity_export_')
    index_path = os.path.join(out, 'regions.json')
    old_index = json.load(open(index_path))['regions'] if os.path.exists(index_path) else []

    if not args.no_prologue:
        cap = run_captured(dl01, dl01.main, ['build_dl01.py', '--out', scratch], check_dir)
        log('prologue built:', {k: len(v) for k, v in cap.items()})
        records += export_set(bpy, cap['set'], C.PROLOGUE, C.PROLOGUE_BACKDROP, out, wanted, True,
                              written_textures, index, driven)
        if not args.no_characters:
            for key, folder, fname in (('white', 'White', 'white.glb'), ('couriers', 'Couriers', 'couriers.glb')):
                dst = os.path.join(out, folder, fname)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                dl01.export(dst, cap[key])          # the web settings: same content as the web GLB
                ensure_meta(UNITY_PROJECT, os.path.dirname(dst), folder=True)
                ensure_meta(UNITY_PROJECT, dst)
                index.append({'name': folder, 'kind': 'character', 'folder': folder, 'file': fname, 'scenes': [],
                              'gameRegion': 0, 'laneRange': [0, 0], 'boundsMin': [0, 0, 0], 'boundsMax': [0, 0, 0],
                              'sidecar': ''})
            d17_tmp = os.path.join(scratch, 'd17.glb')
            dl01.export(d17_tmp, cap['d17'])
            committed = os.path.join(out, 'D17', 'd17.glb')
            if os.path.exists(committed) and sha(committed) == sha(d17_tmp):
                log('D17: the rebuild is byte-identical to Assets/Art/D17/d17.glb')
            else:
                new, old = report.stats(d17_tmp)['animations'], (report.stats(committed)['animations'] if os.path.exists(committed) else [])
                log('D17: rebuild differs in bytes; clips', 'identical' if new == old else f'DIFFER: {set(new) ^ set(old)}')
            if args.write_d17:
                shutil.copyfile(d17_tmp, committed)
                log('D17: wrote', committed)
            index.append({'name': 'D17', 'kind': 'character', 'folder': 'D17', 'file': 'd17.glb', 'scenes': [],
                          'gameRegion': 0, 'laneRange': [0, 0], 'boundsMin': [0, 0, 0], 'boundsMax': [0, 0, 0],
                          'sidecar': ''})

    if args.chapter1:
        sys.path.insert(0, os.path.join(REPO, 'art', 'ch1'))
        sys.path.insert(0, os.path.join(REPO, 'art', 'common'))
        import build_attendance
        cap = run_captured(dl01, build_attendance.main, ['build_attendance.py', '--out', scratch], check_dir)
        log('chapter 1 built:', {k: len(v) for k, v in cap.items()})
        records += export_set(bpy, cap['attendance'], C.CHAPTER1, None, out, wanted, False,
                              written_textures, index, driven)

    # Driven names per region, from the sidecars just written.
    for r in index:
        if r['kind'] == 'set':
            with open(os.path.join(out, r['folder'], r['sidecar'])) as fh:
                driven_by_region[r['name']] = [n for n in json.load(fh)['driven'] if not n.startswith('MECH_')]
    mapped_sources = {r['source'] for r in records}
    driven_by_region = {k: [n for n in v if n not in mapped_sources] for k, v in driven_by_region.items()}

    # The shared textures: manifest, metas, and (after a full export) no stale files.
    tex_dir = os.path.join(out, TEXTURES)
    full = wanted is None and not args.no_prologue
    if full:
        for f in os.listdir(tex_dir):
            stem = f[:-5] if f.endswith('.meta') else f
            if stem.endswith('.png') and stem not in written_textures:
                os.remove(os.path.join(tex_dir, f))
    manifest_path = os.path.join(tex_dir, 'textures.json')
    manifest = {} if full or not os.path.exists(manifest_path) else {t['file']: t for t in json.load(open(manifest_path))['textures']}
    manifest.update(written_textures)
    write_text(manifest_path, json.dumps({'format': 1, 'textures': [manifest[k] for k in sorted(manifest)]}, indent=1) + '\n')
    ensure_meta(UNITY_PROJECT, tex_dir, folder=True)
    for f in os.listdir(tex_dir):
        if not f.endswith('.meta'):
            ensure_meta(UNITY_PROJECT, os.path.join(tex_dir, f))

    # The index keeps regions this run did not touch.
    names = {r['name'] for r in index}
    index = [r for r in old_index if r['name'] not in names] + index
    write_text(index_path, json.dumps({'format': 1, 'regions': index}, indent=1) + '\n')
    ensure_meta(UNITY_PROJECT, index_path)
    if records or full:
        write_name_map(args.name_map, records, driven_by_region)

    if check_dir:
        for f in sorted(os.listdir(check_dir)):
            if f.endswith('.glb') and os.path.exists(os.path.join(WEB_ASSETS, f)):
                same = sha(os.path.join(check_dir, f)) == sha(os.path.join(WEB_ASSETS, f))
                log('web check', f, 'byte-identical to game/undelivered/assets' if same else 'DIFFERS from game/undelivered/assets')
    shutil.rmtree(scratch, ignore_errors=True)
    log('done:', ', '.join(r['name'] for r in index))


if __name__ == '__main__':
    main()
