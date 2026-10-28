"""Pairs Unity's and the prototype's captures by shot name: one image per shot, prototype on top, Unity below.

    python side_by_side.py <prototypeDir> <unityDir> <outDir> [scale=0.5]

Each shot is labelled with its name and both positions from the two capture.json files, so a frame that drifted (a
different x) is told apart from one that looks different. Needs Pillow.
"""
import json
import os
import sys

from PIL import Image, ImageDraw


def shots(d):
    path = os.path.join(d, "capture.json")
    if not os.path.exists(path):
        return {}
    return {s["name"]: s for s in json.load(open(path, encoding="utf-8"))["shots"]}


def main():
    proto, unity, out = sys.argv[1:4]
    scale = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
    os.makedirs(out, exist_ok=True)
    ps, us = shots(proto), shots(unity)
    names = sorted(n[:-4] for n in os.listdir(unity) if n.endswith(".png") and os.path.exists(os.path.join(proto, n)))
    for name in names:
        a = Image.open(os.path.join(proto, name + ".png")).convert("RGB")
        b = Image.open(os.path.join(unity, name + ".png")).convert("RGB")
        w, h = int(a.width * scale), int(a.height * scale)
        a, b = a.resize((w, h)), b.resize((w, h))
        bar = 18
        img = Image.new("RGB", (w, 2 * h + 2 * bar), (40, 40, 40))
        img.paste(a, (0, bar))
        img.paste(b, (0, 2 * bar + h))
        draw = ImageDraw.Draw(img)
        p, u = ps.get(name, {}), us.get(name, {})
        draw.text((4, 3), f"PROTOTYPE {name}  x={p.get('x')} rel={p.get('rel')}", fill=(255, 220, 120))
        draw.text((4, bar + h + 3), f"UNITY {name}  x={u.get('x')} rel={u.get('rel')}", fill=(140, 220, 255))
        img.save(os.path.join(out, name + ".png"))
    print(len(names), "pairs in", out)


if __name__ == "__main__":
    main()
