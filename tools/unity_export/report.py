"""Reads the Unity export (unity/DeadLetter/Assets/Art) and prints what is in it: per region the files and sizes, meshes,
primitives, triangles, materials, textures and their estimated resident memory per platform, and the markers per prefix.
Plain Python (no bpy), so it runs anywhere:

    python3 tools/unity_export/report.py [--art unity/DeadLetter/Assets/Art] [--json out.json]

Exits 1 if a region is over the texture budget (port_architecture §8.2; the same numbers as Core TextureBudget).
"""
import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
PREFIXES = ('COL_', 'LGT_', 'MECH_', 'CAM_', 'CHK_')

# Core/Art/TextureBudget.cs, transcribed.
PC_MAX, PC_MURAL_MAX, SWITCH_MAX = 2048, 4096, 1024
PC_RESIDENT, SWITCH_RESIDENT = 600 * 1024 * 1024, 160 * 1024 * 1024


def texture_bytes(w, h, platform):
    mural = max(w, h) > PC_MAX
    cap = (PC_MURAL_MAX if mural else PC_MAX) if platform == 'PC' else SWITCH_MAX
    while max(w, h) > cap:
        w, h = max(1, w // 2), max(1, h // 2)
    total = 0
    while True:
        total += 16 * ((w + 3) // 4) * ((h + 3) // 4) if platform == 'PC' else 16 * ((w + 5) // 6) * ((h + 5) // 6)
        if w == 1 and h == 1:
            return total
        w, h = max(1, w // 2), max(1, h // 2)


def png_size(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return 0, 0
    return struct.unpack('>II', data[16:24])


def load_gltf(path):
    """(json, list of binary buffers) for a .gltf (external .bin) or a .glb."""
    with open(path, 'rb') as fh:
        raw = fh.read()
    if path.endswith('.glb'):
        n = struct.unpack_from('<I', raw, 12)[0]
        j = json.loads(raw[20:20 + n])
        off = 20 + n
        blen = struct.unpack_from('<I', raw, off)[0] if off < len(raw) else 0
        return j, [raw[off + 8:off + 8 + blen]]
    j = json.loads(raw)
    bufs = []
    for b in j.get('buffers', []):
        with open(os.path.join(os.path.dirname(path), b['uri']), 'rb') as fh:
            bufs.append(fh.read())
    return j, bufs


def image_bytes(j, bufs, base, im):
    if 'uri' in im:
        p = os.path.normpath(os.path.join(base, im['uri']))
        with open(p, 'rb') as fh:
            return fh.read(), p
    bv = j['bufferViews'][im['bufferView']]
    o = bv.get('byteOffset', 0)
    return bufs[bv.get('buffer', 0)][o:o + bv['byteLength']], None


def stats(path):
    j, bufs = load_gltf(path)
    base = os.path.dirname(path)
    acc = j.get('accessors', [])
    prims = tris = 0
    for m in j.get('meshes', []):
        for p in m['primitives']:
            prims += 1
            if p.get('mode', 4) != 4:
                continue
            n = acc[p['indices']]['count'] if 'indices' in p else acc[p['attributes']['POSITION']]['count']
            tris += n // 3
    images = []
    for im in j.get('images', []):
        data, p = image_bytes(j, bufs, base, im)
        w, h = png_size(data)
        images.append({'name': im.get('name'), 'file': os.path.basename(p) if p else None, 'path': p,
                       'width': w, 'height': h, 'bytes': len(data)})
    markers = {k: 0 for k in PREFIXES}
    for nd in j.get('nodes', []):
        for k in PREFIXES:
            if nd.get('name', '').startswith(k):
                markers[k] += 1
    anims = []
    for a in j.get('animations', []):
        t = 0.0
        for s in a['samplers']:
            t = max(t, acc[s['input']].get('max', [0])[0])
        anims.append((a.get('name'), round(t * 24)))
    return {
        'nodes': len(j.get('nodes', [])), 'meshes': len(j.get('meshes', [])), 'primitives': prims, 'triangles': tris,
        'materials': len(j.get('materials', [])), 'images': images, 'markers': markers, 'animations': anims,
        'skins': len(j.get('skins', [])), 'json': j,
    }


def file_size(path):
    return os.path.getsize(path) if os.path.exists(path) else 0


def dir_size(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--art', default=os.path.join(REPO, 'unity', 'DeadLetter', 'Assets', 'Art'))
    ap.add_argument('--json', default=None)
    args = ap.parse_args()
    art = os.path.abspath(args.art)
    index_path = os.path.join(art, 'regions.json')
    index = json.load(open(index_path)) if os.path.exists(index_path) else {'regions': []}
    rows, over, all_tex = [], [], {}
    for r in index['regions']:
        p = os.path.join(art, r['folder'], r['file'])
        if not os.path.exists(p):
            print('missing', p)
            continue
        s = stats(p)
        size = file_size(p)
        if p.endswith('.gltf'):
            size += sum(file_size(os.path.join(os.path.dirname(p), b['uri'])) for b in s['json'].get('buffers', []))
        pc = sum(texture_bytes(i['width'], i['height'], 'PC') for i in s['images'])
        sw = sum(texture_bytes(i['width'], i['height'], 'Switch') for i in s['images'])
        for i in s['images']:
            all_tex[i['path'] or (r['name'] + ':' + str(i['name']))] = i
        row = {'region': r['name'], 'bytes': size, 'nodes': s['nodes'], 'meshes': s['meshes'], 'primitives': s['primitives'],
               'triangles': s['triangles'], 'materials': s['materials'], 'textures': len(s['images']),
               'tex_mpx': round(sum(i['width'] * i['height'] for i in s['images']) / 1e6, 2),
               'tex_pc_mb': round(pc / 2**20, 2), 'tex_switch_mb': round(sw / 2**20, 2),
               'max_tex': max([max(i['width'], i['height']) for i in s['images']] or [0]),
               'markers': s['markers'], 'animations': len(s['animations'])}
        if pc > PC_RESIDENT or sw > SWITCH_RESIDENT:
            over.append(r['name'])
        rows.append(row)

    hdr = f"{'region':14} {'MB':>6} {'meshes':>6} {'prims':>6} {'tris':>8} {'mats':>5} {'tex':>4} {'Mpx':>6} " \
          f"{'PC MB':>6} {'Sw MB':>6} {'max':>5} {'anim':>4}  markers COL/LGT/MECH/CAM/CHK"
    print(hdr)
    for w in rows:
        m = w['markers']
        print(f"{w['region']:14} {w['bytes'] / 2**20:6.2f} {w['meshes']:6d} {w['primitives']:6d} {w['triangles']:8d} "
              f"{w['materials']:5d} {w['textures']:4d} {w['tex_mpx']:6.2f} {w['tex_pc_mb']:6.2f} {w['tex_switch_mb']:6.2f} "
              f"{w['max_tex']:5d} {w['animations']:4d}  {m['COL_']}/{m['LGT_']}/{m['MECH_']}/{m['CAM_']}/{m['CHK_']}")
    uniq_pc = sum(texture_bytes(i['width'], i['height'], 'PC') for i in all_tex.values())
    uniq_sw = sum(texture_bytes(i['width'], i['height'], 'Switch') for i in all_tex.values())
    total = dir_size(art)
    print(f"\nunique textures {len(all_tex)}: PC (BC7) {uniq_pc / 2**20:.1f} MB of {PC_RESIDENT // 2**20}, "
          f"Switch (ASTC 6x6) {uniq_sw / 2**20:.1f} MB of {SWITCH_RESIDENT // 2**20} (whole export resident at once)")
    print(f"Assets/Art on disk: {total / 2**20:.1f} MB (incl. .meta and sidecars)")
    if args.json:
        with open(args.json, 'w') as fh:
            json.dump({'regions': rows, 'unique_textures': len(all_tex), 'tex_pc_bytes': uniq_pc,
                       'tex_switch_bytes': uniq_sw, 'art_bytes': total}, fh, indent=1)
    if over:
        print('OVER TEXTURE BUDGET:', ', '.join(over))
        sys.exit(1)


if __name__ == '__main__':
    main()
