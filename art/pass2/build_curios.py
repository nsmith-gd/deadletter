"""Chapter 1, pass 2: the curiosity props and D-17's clips for them (docs/chapter1_pass2_plan.md, section 6).

Built in world coordinates, after every other scene (OFF2..OFF4 already applied). Other builders' objects are only
changed here, by name. Each curiosity: where D-17 stands (game x, his facing), the props the game drives, and
his clip. Every clip starts and ends on the Idle pose at the stand point; where he steps in to a prop, or climbs
onto it, the root bone carries him there and back inside the clip.

  DL-01  ParcelScale: the dial column moves to the platform's right end (x 1.62) so the dial reads past him, the
         platform drops to 0.028; ScaleTicketBox on the column, ScaleTicket in it (the game slides it out along -x).
         DispatchRack: a little card rack on a post under the dispatch board, RouteCardD17 standing in it.
  DL-02  FrankerCounter, HandFranker (+ HandFrankerHead, HandFrankerLever) left of the passage doorway.
         CourierShelf by the tea corner with MugD17 on it (and two other couriers' mugs).
         ClawStamp (in d17.glb, on his left claw) and MugD17Held (in d17.glb, in his right claw): hidden until used.
  DL-04  RackSeat: a low seat in the empty slot under the chalk flowers.
  DL-05  SorterChair (+ SorterCushion) in the scanner corridor, before the arch.
  DL-06  ClockWinderBox + ClockWinder (a wind-up key) by the stopped clock's post; ClockHandHour, ClockHandMin.
  DL-08  CoinViewer (+ CoinViewerHead) and CoinViewerStep on the balcony.
  Tags   CurioTag_scale, _dispatch, _franker, _mug: small red enamel tags on the early ones.

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y.
Game coordinates are (x, z, -y).
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

import build_d17 as d17
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, rounded_box, simple_material, worn_material,
                       smoothstep, ease_back, SIDES, CLAW_REST_OPEN, _key)

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_C = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'

# ---------------------------------------------------------------------------------------------------------
# Shared with the game. Stand points are game x; face is D-17's facing when the clip starts.
# ---------------------------------------------------------------------------------------------------------
OFF3, OFF4 = 21.0, 30.0
DECK = 1.6

# DL-01 parcel scale (art/dl01 SCALE = (1.45, 0.05)).
SCALE_STAND = (1.27, 1)                     # on the platform's left half, facing the dial
SCALE_COL_DX = 0.17                         # the column, dial and needle move right by this (to x 1.62)
SCALE_TOP = 0.028                           # the platform's top after it is lowered
TICKET_BOX = (1.545, 0.30, 0.34)            # the ticket box's centre on the column's left face
TICKET = (0.07, 0.045)                      # length (along x), height
TICKET_OUT = 0.05                           # how far the game slides it out (along game -x)

# DL-01 dispatch rack (under the dispatch board, x 0.69 to 1.41).
DISPATCH_STAND = (1.13, -1)
RACK = (0.93, 0.36)                         # the rack post's x, y
CARD = (0.075, 0.105, 0.86)                 # RouteCardD17: width, height, its top edge at rest
CARD_LIFT = 0.035                           # the game slides it up this much

# DL-02 hand franker, on a courier-height counter left of the passage doorway (Door2Frame 12.77 to 13.63).
FRANKER_STAND = (12.70, -1)
COUNTER = (12.22, 12.62, 0.27, 0.6, 0.34)   # x0, x1, y0, y1, top
PLATEN = (12.47, 0.335, 0.375)              # the platen's centre (top face)
HEAD_GAP = 0.055                            # the die face above the platen at rest
FRANK_DROP = 0.035                          # the game drops HandFrankerHead this much at the thunk
LEVER_PIVOT = (12.545, 0.43, 0.53)          # HandFrankerLever's pivot (axis along x)
LEVER_LEN = 0.15
LEVER_REST = 35.0                           # degrees up from pointing at the lane (toward -y)
LEVER_PULL = 50.0                           # degrees the pull swings it down

# DL-02 the couriers' low shelf by the tea corner, MugD17 on it.
MUG_STAND = (15.18, 1)
SHELF = (15.29, 15.65, 0.26, 0.5, 0.5)      # x0, x1, y0, y1, top
MUG = (15.40, 0.34, 0.035, 0.088)           # MugD17: x, y (its base centre on the shelf top), radius, height

# DL-04 the empty slot on the column (art/racks MEMORIAL_X 41.1; column face y 1.07; plinth top 0.06).
RACK_STAND = (41.08, 1)
RACK_SEAT = (41.1, 0.71, 0.98, 0.265)       # x, y0, y1, top
RACK_SIT_Y = 0.80                           # his root's y when seated (back to the contacts)

# DL-05 the sorter's chair in the scanner corridor (back wall face y 0.62; scanner arch from 49.47).
CHAIR_STAND = (48.80, 1)
CHAIR = (48.80, 0.40, 0.46, 0.4, 0.44)      # seat centre x, y, width, depth, seat top (the cushion sits on it)
CUSHION = 0.045

# DL-06 the stopped clock (art/dl03 CLOCK_X 41.7 + OFF3; face centre at the deck + 2.0, y 0.765).
CLOCK_X = OFF3 + 41.7
CLOCK_C = (CLOCK_X, 0.758, DECK + 2.0)
CLOCK_STAND = (OFF3 + 40.42, 1)
WINDER = (OFF3 + 40.66, 0.295, DECK + 0.40)  # the key's centre (its shaft along y, the wings face the lane)
STOP_HOUR, STOP_MIN = 4, 12                 # the flood's time

# DL-05 ring C / DL-08 the balcony coin viewer (art/dl04 BALCONY 70 to 74.6 + OFF4, deck 1.6).
VIEWER_STAND = (OFF4 + 72.6, 1)
VIEWER = (OFF4 + 72.6, 0.66)                # the post
VIEWER_EYE = (0.5, DECK + 0.96)             # the eyepieces' y, height
STEP = (0.17, 0.43, 0.27)                   # CoinViewerStep: y0, y1, height
COIN_BOX = (0.52, DECK + 0.72)              # the coin box's front face y (less 0.02), its centre height; the red plunger is 0.035 above

# Ring C generic: the prop straight behind him (Blender +y) at his x.
RADIO_KNOB = (0.25, 0.8)                    # y, height
SWITCH = (0.25, 0.62)

TAG = (0.042, 0.058)                        # CurioTag plate: width, height


# ---------------------------------------------------------------------------------------------------------
# Textures (small, drawn once into art/pass2/textures)
# ---------------------------------------------------------------------------------------------------------

def _font(size, mono=False):
    from PIL import ImageFont
    try:
        return ImageFont.truetype(FONT_C if mono else FONT, size)
    except OSError:
        return ImageFont.load_default()


def _age(img, seed, amount=0.5):
    """Grime and wear over a drawn texture."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(seed)
    w, h = img.size
    over = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(over)
    for _ in range(int(40 * amount) + 4):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(w * 0.03, w * 0.25)
        d.ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), fill=rnd.randint(10, 40))
    over = over.filter(ImageFilter.GaussianBlur(w * 0.03))
    dark = Image.new('RGB', (w, h), (40, 30, 18))
    return Image.composite(dark, img.convert('RGB'), over)


def _stamp(d, cx, cy, r, ink, text, size):
    """A round postmark: two rings and a word across the middle."""
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ink, width=max(2, r // 9))
    d.ellipse((cx - r * 0.78, cy - r * 0.78, cx + r * 0.78, cy + r * 0.78), outline=ink, width=max(1, r // 16))
    f = _font(size)
    tw = d.textlength(text, font=f)
    d.rectangle((cx - tw / 2 - 4, cy - size * 0.62, cx + tw / 2 + 4, cy + size * 0.62), fill=(0, 0, 0, 0))
    d.text((cx - tw / 2, cy - size * 0.6), text, font=f, fill=ink)


def make_ticket(path):
    """The scale's ticket: POSTAGE DUE in a box, a little stamp with a question mark, a weight line."""
    from PIL import Image, ImageDraw, ImageFilter
    w, h = 320, 206
    img = Image.new('RGB', (w, h), (214, 202, 170))
    d = ImageDraw.Draw(img)
    ink, red = (40, 36, 30), (158, 38, 30)
    for x in range(0, w, 16):                                   # perforated top edge
        d.ellipse((x + 4, -6, x + 12, 4), fill=(120, 110, 90))
    d.rectangle((12, 22, w - 12, h - 12), outline=ink, width=4)
    d.text((26, 34), 'POSTAGE', font=_font(44), fill=red)
    d.text((26, 82), 'DUE', font=_font(58), fill=red)
    d.text((26, 152), '0.71 m  41 kg', font=_font(22, True), fill=ink)
    sx, sy = 236, 104                                           # the stamp: a perforated square, a question mark
    for k in range(-34, 35, 9):
        for (a, b) in ((sx + k, sy - 40), (sx + k, sy + 40), (sx - 40, sy + k), (sx + 40, sy + k)):
            d.ellipse((a - 3, b - 3, a + 3, b + 3), fill=(214, 202, 170))
    d.rectangle((sx - 36, sy - 36, sx + 36, sy + 36), outline=red, width=4)
    d.text((sx - 15, sy - 32), '?', font=_font(56), fill=red)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    _age(img, 11, 0.3).save(path)


def make_route_card(path):
    """His route card: D-17, ROUTE C, C-114, a little house with a candle-lit window, three ticks."""
    from PIL import Image, ImageDraw, ImageFilter
    w, h = 240, 336
    img = Image.new('RGB', (w, h), (222, 214, 188))
    d = ImageDraw.Draw(img)
    ink, red, blue = (36, 34, 30), (160, 40, 32), (40, 62, 92)
    d.rectangle((0, 0, w, 52), fill=blue)                         # the depot's blue header band
    d.text((14, 6), 'D-17', font=_font(40), fill=(230, 224, 200))
    d.text((14, 62), 'ROUTE C', font=_font(34), fill=ink)
    d.line((14, 108, w - 14, 108), fill=ink, width=3)
    hx, hy = w // 2, 196                                          # the house pictogram
    d.polygon([(hx - 62, hy - 6), (hx, hy - 62), (hx + 62, hy - 6)], outline=ink, width=8)
    d.rectangle((hx - 46, hy - 6, hx + 46, hy + 56), outline=ink, width=8)
    d.rectangle((hx - 32, hy + 8, hx - 8, hy + 32), fill=(214, 160, 60))   # a lit window
    d.rectangle((hx + 10, hy + 14, hx + 32, hy + 56), fill=ink)            # the door
    d.text((22, 262), 'C-114', font=_font(52), fill=red)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    _age(img, 12, 0.35).save(path)


def make_claw_stamp(path):
    """RECEIVED, round, in red ink, with a smudge: the franker's mark on his claw (alpha)."""
    from PIL import Image, ImageDraw, ImageFilter
    s = 256
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ink = (190, 30, 24, 235)
    d.ellipse((10, 10, s - 10, s - 10), outline=ink, width=14)
    d.ellipse((34, 34, s - 34, s - 34), outline=ink, width=5)
    for k in range(5):                                            # the cancel lines
        y = 70 + k * 12
        d.line((40, y, s - 40, y), fill=ink, width=5)
        d.line((40, s - y, s - 40, s - y), fill=ink, width=5)
    d.rectangle((14, 104, s - 14, 152), fill=(0, 0, 0, 0))
    f = _font(34)
    tw = d.textlength('RECEIVED', font=f)
    d.text(((s - tw) / 2, 108), 'RECEIVED', font=f, fill=ink)
    rnd = random.Random(31)                                       # patchy ink
    a = img.split()[3]
    holes = Image.new('L', (s, s), 255)
    hd = ImageDraw.Draw(holes)
    for _ in range(26):
        x, y, r = rnd.uniform(0, s), rnd.uniform(0, s), rnd.uniform(4, 14)
        hd.ellipse((x - r, y - r, x + r, y + r), fill=rnd.randint(60, 160))
    from PIL import ImageChops
    a = ImageChops.multiply(a, holes.filter(ImageFilter.GaussianBlur(3)))
    img.putalpha(a)
    img.filter(ImageFilter.GaussianBlur(0.8)).save(path)


def make_mug_label(path):
    """D-17 in red enamel paint on his mug, a little lopsided (alpha)."""
    from PIL import Image, ImageDraw, ImageFilter
    w, h = 256, 128
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ink = (168, 34, 28, 255)
    d.text((18, 16), 'D-17', font=_font(84), fill=ink)
    img = img.rotate(-4, resample=3, center=(w / 2, h / 2))
    img.filter(ImageFilter.GaussianBlur(0.7)).save(path)


def make_clock_face(path):
    """The depot clock's face as art/dl03 draws it, without its hands (they are separate now)."""
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (400, 400), (24, 24, 22))
    d = ImageDraw.Draw(img)
    ink = (30, 28, 24)
    d.ellipse((20, 20, 380, 380), fill=(206, 198, 172), outline=(60, 56, 50), width=14)
    for k in range(12):
        a = k * math.pi / 6
        d.line((200 + 150 * math.sin(a), 200 - 150 * math.cos(a), 200 + 172 * math.sin(a), 200 - 172 * math.cos(a)),
               fill=ink, width=10 if k % 3 == 0 else 5)
    d.ellipse((188, 188, 212, 212), fill=ink)
    _age(img, 8, 0.4).save(path)


def make_viewer_plate(path):
    """The coin viewer's enamel plate: a pictogram of an eye over a city skyline, and a coin."""
    from PIL import Image, ImageDraw, ImageFilter
    w, h = 256, 160
    img = Image.new('RGB', (w, h), (26, 44, 40))
    d = ImageDraw.Draw(img)
    ink = (212, 204, 172)
    d.rounded_rectangle((6, 6, w - 6, h - 6), radius=14, outline=ink, width=6)
    for x0, top in ((24, 90), (52, 62), (80, 80), (104, 46), (132, 72), (158, 58), (186, 86)):
        d.rectangle((x0, top, x0 + 22, 132), fill=ink)
    d.ellipse((96, 20, 120, 34), outline=ink, width=4)            # a dome
    d.ellipse((196, 30, 236, 70), outline=(196, 140, 40), width=6)          # the coin
    d.text((209, 34), '1', font=_font(28), fill=(196, 140, 40))
    img = img.filter(ImageFilter.GaussianBlur(0.7))
    _age(img, 14, 0.3).save(path)


TEXTURES = {
    'ticket': ('scale_ticket.png', make_ticket),
    'route': ('route_card_d17.png', make_route_card),
    'stamp': ('claw_stamp.png', make_claw_stamp),
    'mug': ('mug_d17.png', make_mug_label),
    'clock': ('clock_face_nohands.png', make_clock_face),
    'viewer': ('coin_viewer_plate.png', make_viewer_plate),
}


def texture(key):
    name, fn = TEXTURES[key]
    path = os.path.join(TEX, name)
    if not os.path.exists(path):
        os.makedirs(TEX, exist_ok=True)
        fn(path)
    return path


# ---------------------------------------------------------------------------------------------------------
# Mesh helpers
# ---------------------------------------------------------------------------------------------------------

def _obj(name, bm, mats, coll, sharp=35):
    return d17.mesh_object(name, bm, mats, coll, sharp=sharp)


def _flat_obj(name, bm, mats, coll):
    """A mesh kept exactly as wound (decals: one-sided in the game, so their normals must face out)."""
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for mt in mats:
        me.materials.append(mt)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _mat(m, key, name):
    """An existing material: from the shared dict, else by name."""
    return m.get(key) or bpy.data.materials.get(name)


def _image_material(name, path, rough=0.7, alpha=False):
    mat, nt, bsdf = d17._new_material(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    if alpha:
        nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
        for attr, value in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
            if hasattr(mat, attr):
                try:
                    setattr(mat, attr, value)
                except (TypeError, ValueError):
                    pass
    return mat


def _quad(bm, uv, corners, mat=0, uvs=((0, 0), (1, 0), (1, 1), (0, 1))):
    """One UV-mapped quad: corners in order (u0 v0, u1 v0, u1 v1, u0 v1)."""
    f = bm.faces.new([bm.verts.new(c) for c in corners])
    f.material_index = mat
    for lp, t in zip(f.loops, uvs):
        lp[uv].uv = t
    return f


def _card(bm, uv, c, w, h, mat, back_mat, thick=0.0015, tilt=0.0):
    """A thin card in the x-z plane facing -y (the camera), its texture on the front, plain on the back."""
    r = Matrix.Rotation(tilt, 3, 'X')
    pts = lambda y: [c + r @ Vector(p) for p in ((-w / 2, y, -h / 2), (w / 2, y, -h / 2), (w / 2, y, h / 2), (-w / 2, y, h / 2))]  # noqa: E731
    _quad(bm, uv, pts(-thick / 2), mat)
    b = pts(thick / 2)
    _quad(bm, uv, [b[1], b[0], b[3], b[2]], back_mat, uvs=((0, 0), (0.02, 0), (0.02, 0.02), (0, 0.02)))
    for i in range(4):                                         # the edges
        a, bb = pts(-thick / 2), pts(thick / 2)
        f = bm.faces.new([bm.verts.new(a[i]), bm.verts.new(a[(i + 1) % 4]), bm.verts.new(bb[(i + 1) % 4]), bm.verts.new(bb[i])])
        f.material_index = back_mat
        for lp in f.loops:
            lp[uv].uv = (0.01, 0.01)


def _mug_mesh(bm, uv, base, r, h, handle_dir, body_mat, label_mat, dark_mat, label=True):
    """An enamel mug standing on `base` (its base centre), the handle toward `handle_dir` (unit xy), and a
    label wrapped round the front (the side facing -y when the handle points +x)."""
    hd = Vector((handle_dir[0], handle_dir[1], 0)).normalized()
    side = Vector((-hd.y, hd.x, 0))                           # 90 degrees anticlockwise of the handle
    add_cyl(bm, base, base + Vector((0, 0, h)), r, r * 0.97, seg=18, mat=body_mat)
    add_cyl(bm, base + Vector((0, 0, h - 0.004)), base + Vector((0, 0, h + 0.002)), r * 1.04, seg=18, mat=body_mat)
    add_cyl(bm, base + Vector((0, 0, h - 0.01)), base + Vector((0, 0, h + 0.0006)), r * 0.9, seg=18, mat=dark_mat)   # the dark inside
    hc = base + hd * (r + 0.012) + Vector((0, 0, h * 0.52))
    axis = side
    add_torus(bm, hc, axis, 0.022, 0.0055, seg=14, rseg=6, mat=body_mat)
    if label:
        front = -side                                         # the side facing -y when the handle points +x
        n = 6
        ang0 = math.atan2(front.y, front.x)
        z0, z1 = base.z + h * 0.28, base.z + h * 0.78
        rr = r * 1.004 + 0.0012
        for i in range(n):
            a0 = ang0 - math.radians(55) + math.radians(110) * i / n
            a1 = ang0 - math.radians(55) + math.radians(110) * (i + 1) / n
            p = lambda a, z: Vector((base.x + rr * math.cos(a), base.y + rr * math.sin(a), z))  # noqa: E731
            _quad(bm, uv, [p(a0, z0), p(a1, z0), p(a1, z1), p(a0, z1)], label_mat,
                  uvs=((i / n, 0), ((i + 1) / n, 0), ((i + 1) / n, 1), (i / n, 1)))


# ---------------------------------------------------------------------------------------------------------
# The set
# ---------------------------------------------------------------------------------------------------------

def curio_materials(m):
    c = {}
    c['red'] = _mat(m, 'red', 'LeverRed')
    c['steel'] = _mat(m, 'steel', 'DepotSteel')
    c['green'] = _mat(m, 'depot_green', 'DepotGreen')
    c['wood'] = _mat(m, 'wood', 'CrateWood')
    c['rubber'] = _mat(m, 'rubber', 'Rubber')
    c['brass'] = bpy.data.materials.get('Brass') or simple_material('Brass', (0.45, 0.32, 0.12), 0.45, metallic=0.8)
    c['enamel'] = bpy.data.materials.get('TeaEnamel') or simple_material('TeaEnamel', (0.58, 0.55, 0.47), 0.35)
    c['iron'] = bpy.data.materials.get('CastIron') or worn_material(
        'CastIron', base=(0.035, 0.034, 0.032), dirt=(0.05, 0.03, 0.018), chip=(0.13, 0.12, 0.1), rough=0.75,
        chip_rough=0.45, metallic=0.5)
    c['dark'] = bpy.data.materials.get('EyeDark') or simple_material('EyeDark', (0.003, 0.003, 0.003), 0.3)
    c['paper'] = bpy.data.materials.get('LetterPaper') or _mat(m, 'paper', 'ParcelBrown')
    c['pigeon'] = bpy.data.materials.get('PigeonWood') or c['wood']
    # New: the sorter's cushion, worn oxblood leather (index.html WORN.SorterCushion).
    c['cushion'] = bpy.data.materials.get('SorterCushion') or worn_material(
        'SorterCushion', base=(0.16, 0.045, 0.035), dirt=(0.07, 0.03, 0.022), chip=(0.24, 0.17, 0.12), rough=0.62,
        chip_rough=0.85, metallic=0.0)
    c['ticket'] = _image_material('ScaleTicketMat', texture('ticket'), rough=0.85)
    c['route'] = _image_material('RouteCardMat', texture('route'), rough=0.85)
    c['mug'] = _image_material('MugD17Label', texture('mug'), rough=0.35, alpha=True)
    c['viewer'] = _image_material('CoinViewerPlateMat', texture('viewer'), rough=0.5)
    return c


def curio_tag(name, top, c, coll, swing=0.0):
    """A small red enamel tag on a ring, hanging from `top` and facing the camera: the usable mark."""
    w, h = TAG
    bm = bmesh.new()
    rot = Matrix.Rotation(swing, 4, 'Y')
    ring = top + Vector((0, -0.002, -0.008))
    add_torus(bm, ring, (0, 1, 0), 0.007, 0.0016, seg=12, rseg=4, mat=1)
    add_cyl(bm, ring + Vector((0, 0, -0.006)), ring + Vector((0, 0, -0.016)), 0.0012, seg=4, mat=1)
    plate = top + Vector((0, -0.002, -0.016 - h / 2))
    rounded_box((w, 0.003, h), plate, p=4.0, cuts=4, mat=0, bm=bm, rot=rot)
    add_cyl(bm, plate + Vector((0, -0.0022, h / 2 - 0.009)), plate + Vector((0, 0.0022, h / 2 - 0.009)), 0.0035, seg=10, mat=1)
    return _obj(name, bm, [c['red'], c['brass']], coll)


def build_scale_curio(c, coll):
    """The parcel scale: its dial column moves to the platform's right end, so the dial and its needle read past
    him as he stands on the left half; the platform drops to just above the floor; a ticket box on the column's
    left face, a ticket peeking out of its slot."""
    sc = bpy.data.objects.get('ParcelScale')
    if sc is not None:
        for v in sc.data.vertices:
            co = sc.matrix_world @ v.co
            if co.y > 0.23:
                v.co.x += SCALE_COL_DX
            elif 0.025 < co.z < 0.06 and abs(co.y) < 0.2:
                v.co.z -= 0.05 - SCALE_TOP + 0.0
        sc.data.update()
    for n in ('ScaleDial', 'ScaleNeedle'):
        o = bpy.data.objects.get(n)
        if o is not None:
            o.location.x += SCALE_COL_DX
    bx, by, bz = TICKET_BOX
    bm = bmesh.new()
    add_box(bm, (bx, by, bz), (0.08, 0.07, 0.075), mat=0)
    add_box(bm, (bx, by, bz + 0.04), (0.088, 0.078, 0.008), mat=0)                  # a lip on top
    add_box(bm, (bx - 0.0405, by - 0.004, bz), (0.004, 0.012, 0.058), mat=1)           # the slot's brass bezel
    add_box(bm, (bx - 0.0425, by - 0.004, bz), (0.002, 0.004, 0.05), mat=2)            # the slot
    add_cyl(bm, (bx, by - 0.036, bz + 0.012), (bx, by - 0.04, bz + 0.012), 0.012, seg=14, mat=1)   # a coin-sized boss
    _obj('ScaleTicketBox', bm, [c['green'], c['brass'], c['dark']], coll)
    # The ticket, its origin at its centre: at rest 6 mm of it shows; the game slides it out along -x.
    tw, th = TICKET
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    _card(bm, uv, Vector((0, 0, 0)), tw, th, 0, 1)
    t = _obj('ScaleTicket', bm, [c['ticket'], c['paper']], coll, sharp=20)
    t.location = (bx - 0.04 + tw / 2 - 0.006, by - 0.004, bz)
    curio_tag('CurioTag_scale', Vector((bx - 0.022, by - 0.036, bz - 0.038)), c, coll, swing=0.08)


def build_dispatch_curio(c, coll):
    """A little card rack on a post, under the dispatch board: three route cards standing in it, his in front."""
    x, y = RACK
    bm = bmesh.new()
    add_box(bm, (x, y, 0.01), (0.16, 0.14, 0.02), mat=1)                               # the foot
    add_box(bm, (x, y + 0.01, 0.38), (0.032, 0.032, 0.72), mat=1)                      # the post
    rounded_box((0.21, 0.075, 0.07), (x, y - 0.005, 0.765), p=6, cuts=4, mat=0, bm=bm)   # the rack
    for k in range(3):                                                                 # its slots' dividers
        add_box(bm, (x, y - 0.035 + k * 0.025, 0.801), (0.2, 0.004, 0.004), mat=1)
    _obj('DispatchRack', bm, [c['wood'], c['green']], coll)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    cw, ch, ctop = CARD
    for dx, dy, top, tilt in ((-0.05, 0.02, ctop - 0.01, 0.05), (0.035, 0.0, ctop - 0.02, -0.04)):   # the others'
        _card(bm, uv, Vector((x + dx, y + dy, top - ch / 2)), cw, ch, 0, 0, tilt=tilt)
    _obj('DispatchRackCards', bm, [c['paper']], coll, sharp=20)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    _card(bm, uv, Vector((0, 0, 0)), cw, ch, 0, 1)
    card = _obj('RouteCardD17', bm, [c['route'], c['paper']], coll, sharp=20)
    card.location = (x + 0.045, y - 0.03, ctop - ch / 2)                                  # origin at its centre
    curio_tag('CurioTag_dispatch', Vector((x + 0.098, y - 0.044, 0.735)), c, coll, swing=-0.06)


def build_franker(c, coll):
    """A hand franker on a courier-height counter: a cast-iron C-frame, a die head over a rubber platen, and a
    red lever on its right cheek that drives the head down."""
    x0, x1, y0, y1, top = COUNTER
    bm = bmesh.new()
    add_box(bm, ((x0 + x1) / 2, (y0 + y1) / 2, top - 0.015), (x1 - x0, y1 - y0, 0.03), mat=0)
    for x in (x0 + 0.025, x1 - 0.025):
        for y in (y0 + 0.025, y1 - 0.025):
            add_box(bm, (x, y, (top - 0.03) / 2), (0.03, 0.03, top - 0.03), mat=1)
    add_box(bm, ((x0 + x1) / 2, y0 + 0.02, top - 0.07), (x1 - x0 - 0.04, 0.012, 0.06), mat=0)   # an apron
    add_box(bm, ((x0 + x1) / 2, (y0 + y1) / 2, 0.08), (x1 - x0 - 0.04, y1 - y0 - 0.04, 0.015), mat=0)   # a shelf
    for k in range(3):                                                                 # stacks of forms on it
        add_box(bm, (x0 + 0.08 + k * 0.12, (y0 + y1) / 2 + 0.03, 0.1 + 0.01 * k), (0.1, 0.14, 0.02 + 0.02 * k), mat=2)
    _obj('FrankerCounter', bm, [c['wood'], c['steel'], c['paper']], coll)
    px, py, pz = PLATEN
    bm = bmesh.new()
    add_box(bm, (px, py + 0.04, top + 0.01), (0.15, 0.2, 0.02), mat=0)                  # the base
    add_box(bm, (px, py, pz - 0.0075), (0.085, 0.085, 0.015), mat=1)                   # the platen
    add_box(bm, (px, py + 0.115, (top + 0.02 + 0.56) / 2), (0.06, 0.04, 0.56 - top - 0.02), mat=0)   # the C-frame
    add_box(bm, (px, py + 0.055, 0.535), (0.06, 0.16, 0.05), mat=0)                    # its arm over the platen
    add_cyl(bm, (px, py, 0.51), (px, py, 0.57), 0.02, seg=14, mat=0)                   # the guide boss
    add_cyl(bm, LEVER_PIVOT, Vector(LEVER_PIVOT) + Vector((-0.04, 0, 0)), 0.018, seg=14, mat=2)   # the lever's hub
    add_box(bm, (px - 0.0305, py + 0.13, 0.43), (0.002, 0.03, 0.05), mat=2)            # a maker's plate
    _obj('HandFranker', bm, [c['iron'], c['rubber'], c['brass']], coll)
    # The head: a guide rod and the die, its origin at the die face's centre; the game drops it FRANK_DROP.
    bm = bmesh.new()
    z = pz + HEAD_GAP
    add_box(bm, (0, 0, 0.018), (0.07, 0.07, 0.036), mat=0)
    add_box(bm, (0, 0, 0.002), (0.062, 0.062, 0.004), mat=1)                           # the die, inked
    add_cyl(bm, (0, 0, 0.036), (0, 0, 0.11), 0.009, seg=10, mat=0)
    head = _obj('HandFrankerHead', bm, [c['iron'], c['red']], coll)
    head.location = (px, py, z)
    # The lever, modelled about its pivot (its origin): the game rotates it about x by LEVER_PULL at the pull.
    bm = bmesh.new()
    a = math.radians(LEVER_REST)
    d = Vector((0, -math.cos(a), math.sin(a)))
    add_cyl(bm, (0.012, 0, 0), Vector((0.012, 0, 0)) + d * LEVER_LEN, 0.007, seg=10, mat=0)
    add_sphere(bm, Vector((0.012, 0, 0)) + d * (LEVER_LEN + 0.012), 0.016, seg=14, mat=0)
    add_cyl(bm, (0.0, 0, 0), (0.02, 0, 0), 0.012, seg=12, mat=1)
    lever = _obj('HandFrankerLever', bm, [c['red'], c['iron']], coll)
    lever.location = LEVER_PIVOT
    curio_tag('CurioTag_franker', Vector((px - 0.06, y0 + 0.012, top - 0.035)), c, coll, swing=0.05)


def build_mug_curio(c, coll):
    """The couriers' low shelf by the tea corner: three mugs at their height, D-17's in front."""
    x0, x1, y0, y1, top = SHELF
    bm = bmesh.new()
    for x in (x0 + 0.012, x1 - 0.012):
        add_box(bm, (x, (y0 + y1) / 2, top / 2), (0.024, y1 - y0, top), mat=0)
    for z in (top - 0.012, 0.24):
        add_box(bm, ((x0 + x1) / 2, (y0 + y1) / 2, z), (x1 - x0, y1 - y0, 0.024), mat=0)
    add_box(bm, ((x0 + x1) / 2, y1 - 0.01, top + 0.04), (x1 - x0, 0.02, 0.06), mat=0)  # a little back rail
    add_box(bm, ((x0 + x1) / 2, y0 + 0.012, 0.03), (x1 - x0, 0.02, 0.06), mat=0)       # the kick board
    for k, (x, sz) in enumerate(((x0 + 0.1, 0.1), (x0 + 0.24, 0.08))):                   # tins on the lower shelf
        add_cyl(bm, (x, (y0 + y1) / 2, 0.252), (x, (y0 + y1) / 2, 0.252 + sz), 0.04, seg=14, mat=1)
    _obj('CourierShelf', bm, [c['wood'], c['steel']], coll)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    _mug_mesh(bm, uv, Vector((x0 + 0.24, y0 + 0.13, top)), 0.034, 0.085, (1, 0.3), 0, 0, 1, label=False)
    _mug_mesh(bm, uv, Vector((x0 + 0.31, y0 + 0.17, top)), 0.033, 0.082, (1, -0.2), 0, 0, 1, label=False)
    _obj('CourierShelfMugs', bm, [c['enamel'], c['dark']], coll)
    mx, my, r, h = MUG
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    _mug_mesh(bm, uv, Vector((0, 0, 0)), r, h, (1, 0), 0, 1, 2)
    mug = _obj('MugD17', bm, [c['enamel'], c['mug'], c['dark']], coll)
    mug.location = (mx, my, top)
    curio_tag('CurioTag_mug', Vector((x0 + 0.05, y0 - 0.002, top - 0.02)), c, coll, swing=-0.05)


def build_rack_seat(c, coll):
    """The empty slot on the column: a low seat in it, where a courier would sit back on its folded legs."""
    x, y0, y1, top = RACK_SEAT
    bm = bmesh.new()
    rounded_box((0.36, y1 - y0, top - 0.06 - 0.012), (x, (y0 + y1) / 2, (0.06 + top - 0.012) / 2), p=6, cuts=6,
                mat=0, bm=bm, dents=((0.003, 8.0),), seed=61)
    rounded_box((0.33, y1 - y0 - 0.03, 0.014), (x, (y0 + y1) / 2 + 0.005, top - 0.007), p=5, cuts=4, mat=1, bm=bm)
    add_box(bm, (x, y0 + 0.004, top - 0.03), (0.34, 0.008, 0.03), mat=2)              # a worn copper edge
    _obj('RackSeat', bm, [c['green'], c['rubber'], _mat({}, '', 'Copper') or c['brass']], coll)


def _cushion(c, coll):
    """The sorter's cushion, worn into D-17's shape: a rounded dent the size of his pod, and two small dents in
    front where his claws push off."""
    cx, cy, w, dpt, top = CHAIR
    cw, cd = w - 0.04, dpt - 0.04
    nx, ny = 22, 18
    bm = bmesh.new()
    verts = {}

    def height(u, v):
        x, y = u * cw / 2, v * cd / 2
        edge = (1 - abs(u) ** 6) * (1 - abs(v) ** 6)
        z = CUSHION * (0.55 + 0.45 * edge ** 0.5)
        pod = (abs(x / 0.175) ** 3.5 + abs((y - 0.01) / 0.115) ** 3.5)
        z -= 0.024 * math.exp(-pod ** 2)
        for sx in (-1, 1):
            q = ((x - sx * 0.13) / 0.03) ** 2 + ((y + 0.13) / 0.025) ** 2
            z -= 0.008 * math.exp(-q)
        return z
    for i in range(nx + 1):
        for j in range(ny + 1):
            u, v = -1 + 2 * i / nx, -1 + 2 * j / ny
            verts[i, j] = bm.verts.new((cx + u * cw / 2, cy + v * cd / 2, top + height(u, v)))
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((verts[i, j], verts[i + 1, j], verts[i + 1, j + 1], verts[i, j + 1]))
    bot = [bm.verts.new((cx + u * cw / 2 * 0.98, cy + v * cd / 2 * 0.98, top + 0.002))
           for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(bot[::-1])
    ring = [verts[i, 0] for i in range(nx + 1)] + [verts[nx, j] for j in range(1, ny + 1)] + \
           [verts[i, ny] for i in range(nx - 1, -1, -1)] + [verts[0, j] for j in range(ny - 1, 0, -1)]
    corner = lambda vtx: min(range(4), key=lambda k: (bot[k].co - vtx.co).xy.length)  # noqa: E731
    for a, b in zip(ring, ring[1:] + ring[:1]):
        ka, kb = corner(a), corner(b)
        if ka == kb:
            bm.faces.new((a, b, bot[ka]))
        else:
            bm.faces.new((a, b, bot[kb], bot[ka]))
    return _obj('SorterCushion', bm, [c['cushion']], coll, sharp=60)


def build_chair(c, coll):
    """The sorter's chair by the scanner: a steel-framed chair with a wooden seat, its cushion worn to his shape."""
    cx, cy, w, dpt, top = CHAIR
    bm = bmesh.new()
    add_box(bm, (cx, cy, top - 0.012), (w, dpt, 0.024), mat=0)                         # the seat
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = cx + sx * (w / 2 - 0.02), cy + sy * (dpt / 2 - 0.02)
            add_box(bm, (x, y, (top - 0.024) / 2), (0.022, 0.022, top - 0.024), mat=1)
        add_box(bm, (cx + sx * (w / 2 - 0.02), cy, 0.12), (0.016, dpt - 0.04, 0.016), mat=1)   # the rungs
        add_box(bm, (cx + sx * (w / 2 - 0.02), cy + dpt / 2 - 0.02, top + 0.2), (0.022, 0.022, 0.4), mat=1)
    add_box(bm, (cx, cy + dpt / 2 - 0.02, top + 0.29), (w - 0.02, 0.018, 0.17), mat=0)   # the back rest
    add_box(bm, (cx, cy - dpt / 2 + 0.02, 0.12), (w - 0.04, 0.016, 0.016), mat=1)
    _obj('SorterChair', bm, [c['pigeon'], c['steel']], coll)
    _cushion(c, coll)


def build_clock_curio(c, coll):
    """The stopped clock: its hands made separate (stopped at the flood's time), and a winding box by the deck
    with a wind-up key, its rod climbing over the return line to the clock's post."""
    face = bpy.data.objects.get('ClockFace')
    if face is not None and face.active_material is not None:
        for nd in face.active_material.node_tree.nodes:
            if nd.type == 'TEX_IMAGE':
                nd.image = bpy.data.images.load(texture('clock'), check_existing=True)
    cx, cy, cz = CLOCK_C
    for name, length, width, deg in (('ClockHandHour', 0.085, 0.012, (STOP_HOUR % 12 + STOP_MIN / 60) * 30),
                                     ('ClockHandMin', 0.13, 0.008, STOP_MIN * 6)):
        bm = bmesh.new()
        add_box(bm, (0, -0.002 if name == 'ClockHandMin' else 0, length / 2 - 0.015), (width, 0.003, length + 0.03))
        add_box(bm, (0, -0.002 if name == 'ClockHandMin' else 0, length - 0.01), (width * 1.8, 0.003, 0.025),
                rot=Matrix.Rotation(math.radians(45), 4, 'Y'))
        add_cyl(bm, (0, -0.005, 0), (0, 0.002, 0), 0.012, seg=12)
        h = _obj(name, bm, [c['iron']], coll)
        h.location = (cx, cy - 0.002, cz)
        h.rotation_euler = (0, math.radians(deg), 0)                     # clockwise from twelve, seen from the lane
    wx, wy, wz = WINDER
    bm = bmesh.new()
    by = 0.3205                                                                       # kept clear of the carriers (y 0.34 on)
    add_box(bm, (wx, by, wz), (0.11, 0.031, 0.15), mat=0)                             # the winding box
    add_box(bm, (wx, by, wz + 0.08), (0.12, 0.034, 0.012), mat=0)
    add_cyl(bm, (wx, 0.305, wz), (wx, 0.301, wz), 0.022, seg=16, mat=1)                 # the key's brass boss
    add_box(bm, (wx, by, (DECK + wz - 0.075) / 2), (0.03, 0.03, wz - 0.075 - DECK), mat=0)   # its stand
    add_box(bm, (wx, by, DECK + 0.006), (0.09, 0.034, 0.012), mat=0)
    rod = [Vector((wx, by, wz + 0.086)), Vector((wx, by, DECK + 1.45)), Vector((CLOCK_X, by, DECK + 1.45)),
           Vector((CLOCK_X, 0.83, DECK + 1.45))]
    for a, b in zip(rod, rod[1:]):
        add_cyl(bm, a, b, 0.008, seg=8, mat=2)
    for p in rod[1:3]:
        add_sphere(bm, p, 0.018, seg=10, mat=0)                                        # bevel boxes at the bends
    add_box(bm, (CLOCK_X, 0.82, DECK + 1.45), (0.07, 0.05, 0.07), mat=0)
    add_box(bm, (wx - 0.035, 0.304, wz + 0.05), (0.03, 0.002, 0.02), mat=3)           # a little turn arrow plate
    _obj('ClockWinderBox', bm, [c['iron'], c['brass'], c['steel'], _mat({}, '', 'ReflectTag')], coll)
    # The wind-up key: shaft along y, the bow (two rounded wings) facing the lane. Origin on the shaft's axis.
    bm = bmesh.new()
    add_cyl(bm, (0, 0.008, 0), (0, -0.008, 0), 0.007, seg=10, mat=1)
    for s in (-1, 1):
        add_sphere(bm, (s * 0.034, -0.009, 0), 0.026, seg=14, scale=(1.0, 0.12, 0.85), mat=0)
    add_box(bm, (0, -0.009, 0), (0.05, 0.006, 0.02), mat=0)
    add_cyl(bm, (0, -0.006, 0), (0, -0.0125, 0), 0.009, seg=10, mat=1)
    key = _obj('ClockWinder', bm, [c['red'], c['brass']], coll)
    key.location = (wx, wy, wz)


def build_viewer(c, coll):
    """A coin-operated viewer on the balcony, child height, with a step: a post, a coin box with a red plunger,
    and the binocular head on a yoke (CoinViewerHead, its origin at the yoke's pivot)."""
    vx, vy = VIEWER
    bm = bmesh.new()
    add_cyl(bm, (vx, vy, DECK), (vx, vy, DECK + 0.03), 0.13, 0.11, seg=24, mat=0)
    add_cyl(bm, (vx, vy, DECK + 0.03), (vx, vy, DECK + 0.84), 0.045, 0.038, seg=18, mat=0)
    add_cyl(bm, (vx, vy, DECK + 0.84), (vx, vy, DECK + 0.87), 0.06, seg=18, mat=0)
    by, bz = COIN_BOX
    add_box(bm, (vx, by + 0.065, bz), (0.12, 0.09, 0.16), mat=0)                       # the coin box
    add_box(bm, (vx + 0.03, by + 0.019, bz + 0.05), (0.006, 0.003, 0.03), mat=2)        # the coin slot
    add_cyl(bm, (vx - 0.025, by + 0.022, bz + 0.035), (vx - 0.025, by, bz + 0.035), 0.012, seg=12, mat=1)   # the plunger
    add_sphere(bm, (vx - 0.025, by - 0.004, bz + 0.035), 0.016, seg=12, mat=1)
    _obj('CoinViewer', bm, [c['green'], c['red'], c['dark']], coll)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    _quad(bm, uv, [(vx - 0.05, by + 0.0185, bz - 0.075), (vx + 0.05, by + 0.0185, bz - 0.075),
                   (vx + 0.05, by + 0.0185, bz - 0.0125), (vx - 0.05, by + 0.0185, bz - 0.0125)])
    _flat_obj('CoinViewerPlate', bm, [c['viewer']], coll)
    # The head, about its pivot on the yoke.
    pz = DECK + 0.9
    ey, ez = VIEWER_EYE
    bm = bmesh.new()
    add_cyl(bm, (0, 0, -0.03), (0, 0, 0.01), 0.03, seg=14, mat=0)                       # the neck on the yoke
    rounded_box((0.26, 0.2, 0.12), (0, ey + 0.12 - vy, ez - pz), p=3.5, cuts=6, mat=0, bm=bm)
    for s in (-1, 1):
        add_cyl(bm, (s * 0.07, ey + 0.2 - vy, ez - pz), (s * 0.07, ey + 0.24 - vy, ez - pz), 0.045, 0.05, seg=18, mat=0)
        add_cyl(bm, (s * 0.07, ey + 0.238 - vy, ez - pz), (s * 0.07, ey + 0.242 - vy, ez - pz), 0.042, seg=18, mat=3)
        add_cyl(bm, (s * 0.045, ey + 0.02 - vy, ez - pz + 0.01), (s * 0.045, ey - vy, ez - pz + 0.01), 0.02, seg=14, mat=2)
    add_box(bm, (0, ey + 0.02 - vy, ez - pz + 0.05), (0.2, 0.05, 0.014), mat=0)          # a hood over the eyepieces
    add_cyl(bm, (0.13, 0, ez - pz - 0.01), (0.2, 0, ez - pz - 0.01), 0.01, seg=10, mat=1)
    head = _obj('CoinViewerHead', bm, [c['green'], c['red'], c['rubber'], _mat({}, '', 'Window') or c['brass']], coll)
    head.location = (vx, vy, pz)
    # The step: a little wooden box step, with a worn top.
    y0, y1, h = STEP
    bm = bmesh.new()
    rounded_box((0.34, y1 - y0, h - 0.02), (vx, (y0 + y1) / 2, (h - 0.02) / 2), p=8, cuts=4, mat=0, bm=bm,
                dents=((0.002, 9.0),), seed=88)
    add_box(bm, (vx, (y0 + y1) / 2, h - 0.01), (0.36, y1 - y0 + 0.02, 0.02), mat=0)
    add_box(bm, (vx, (y0 + y1) / 2, h + 0.001), (0.28, y1 - y0 - 0.06, 0.004), mat=1)
    step = _obj('CoinViewerStep', bm, [c['wood'], c['rubber']], coll)
    step.location.z = DECK


def build_set(dl01, m, coll):
    c = curio_materials(m)
    build_scale_curio(c, coll)
    build_dispatch_curio(c, coll)
    build_franker(c, coll)
    build_mug_curio(c, coll)
    build_rack_seat(c, coll)
    build_chair(c, coll)
    build_clock_curio(c, coll)
    build_viewer(c, coll)


# ---------------------------------------------------------------------------------------------------------
# Clip authoring. Everything is placed in stand space: the rig object's space as the game places it at a stand
# point, so -Y is where he faces and +X is his left. Props are given in world coordinates and mapped into it.
# The root bone may step and turn him (location and yaw); feet are planted in stand space and step between
# plants; claws are put on targets in stand space, clamped to what his short arms can reach.
# ---------------------------------------------------------------------------------------------------------

ANKLE = {s: Vector((s * 0.097, -0.005, 0.034)) for _, s in SIDES}
SHOULDER = {s: Vector((s * 0.255, -0.01, 0.385)) for _, s in SIDES}
ARM_LEN = 0.282                       # shoulder to wrist, nearly straight
GRIP = 0.072                          # wrist to the point between the claw's blades
HEAD_EYE = Vector((0.0, -0.12, 0.6))  # where he looks from (rig space)


def rz(deg):
    return Matrix.Rotation(math.radians(deg), 3, 'Z')


def to_stand(stand, p, floor=0.0):
    """World point -> stand space for a stand (x, face); `floor` is the surface he stands on."""
    x0, face = stand
    dx, dy, dz = p[0] - x0, p[1], p[2] - floor
    return Vector((dy, -dx, dz)) if face > 0 else Vector((-dy, dx, dz))


def body_matrix(body, body_rot):
    head = Vector((0, 0, 0.4))
    r = Euler([math.radians(v) for v in body_rot], 'XYZ').to_matrix().to_4x4()
    return Matrix.Translation(head + Vector(body)) @ r @ Matrix.Translation(-head)


def lerp(a, b, k):
    return a + (b - a) * k


def ktrack(keys, f, ease=smoothstep):
    """track() for vectors."""
    if f <= keys[0][0]:
        return Vector(keys[0][1])
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            return Vector(v0).lerp(Vector(v1), ease((f - f0) / (f1 - f0)) if f1 > f0 else 1.0)
    return Vector(keys[-1][1])


class Act:
    """One clip, authored frame by frame in stand space."""

    def __init__(self, dl01, arm, name, frames):
        self.dl01, self.frames = dl01, frames
        self.c = dl01.Clip(arm, name, frames)
        self.pb = arm.pose.bones
        self.root_keys = [(0, (0, 0, 0))]
        self.yaw_keys = [(0, 0.0)]
        self.steps = {'L': [], 'R': []}       # (lift, land, pos or None, yaw or None, height)

    # The root: where he is and which way he faces, by frame.
    def root(self, f):
        return ktrack(self.root_keys, f), self.dl01.track(self.yaw_keys, f)

    def step(self, side, lift, land, pos=None, yaw=None, height=0.035):
        self.steps[side].append((lift, land, pos, yaw, height))

    def home(self, side, f):
        """Where a foot rests under the root at frame f (stand space), and its yaw."""
        r, y = self.root(f)
        s = 1 if side == 'L' else -1
        return r + rz(y) @ ANKLE[s], y

    def foot(self, side, f):
        """A foot's position and yaw in stand space: planted, or stepping between plants."""
        pos, yaw = self.home(side, 0)
        for lift, land, p, y, h in self.steps[side]:
            tp, ty = self.home(side, land)
            tp = Vector(p) if p is not None else tp
            ty = y if y is not None else ty
            if f <= lift:
                break
            if f >= land:
                pos, yaw = tp, ty
                continue
            k = smoothstep((f - lift) / (land - lift))
            return pos.lerp(tp, k) + Vector((0, 0, h * math.sin(math.pi * k))), lerp(yaw, ty, k), k
        return pos, yaw, None

    def feet(self, f, pitch=None, extra=None):
        """IK foot offsets for Clip.pose, from the planted feet. `pitch` (deg per side) tips a foot (toes down
        positive); `extra` adds a stand-space offset per side."""
        r, ry = self.root(f)
        out = {}
        for side, s in SIDES:
            p, y, k = self.foot(side, f)
            if extra and side in extra:
                p = p + Vector(extra[side])
            loc = rz(-ry) @ (p - r) - ANKLE[s]
            dangle = 14 * math.sin(math.pi * k) if k is not None else 0.0
            out[side] = (tuple(loc), ((pitch or {}).get(side, 0.0) + dangle, 0, y - ry))
        return out

    # Converting stand-space targets for the hands and head.
    def to_root(self, f, p):
        r, y = self.root(f)
        return rz(-y) @ (Vector(p) - r)

    def dir_to_root(self, f, d):
        return rz(-self.root(f)[1]) @ Vector(d)

    def hand(self, f, s, wrist, body, body_rot, d=None, x_axis=None, twist=0.0):
        """IK offset and hand_rot for a wrist at a stand-space point, the claw pointing along stand-space `d`
        (default: down), its blades opening along `x_axis` where given. The wrist is held to his reach."""
        w = self.to_root(f, wrist)
        bm = body_matrix(body, body_rot)
        sh = bm @ SHOULDER[s]
        v = w - sh
        if v.length > ARM_LEN:
            w = sh + v.normalized() * ARM_LEN
        off = bm.inverted() @ w - self.dl01.REST_WRIST[s]
        rot = None
        if d is not None:
            rb = bm.to_3x3().inverted()
            dz = (rb @ self.dir_to_root(f, d)).normalized()
            xa = rb @ self.dir_to_root(f, x_axis) if x_axis is not None else Vector((1, 0, 0))
            zc = -dz
            xc = (xa - zc * xa.dot(zc))
            if xc.length < 1e-4:
                xc = Vector((0, 1, 0)) - zc * zc.y
            xc.normalize()
            yc = zc.cross(xc)
            m = Matrix((xc, yc, zc)).transposed()
            if twist:
                m = Matrix.Rotation(math.radians(twist), 3, dz) @ m
            rot = tuple(math.degrees(a) for a in m.to_euler('XYZ'))
        return off, rot

    def grip(self, f, s, point, body, body_rot, d, x_axis=None, twist=0.0, depth=GRIP):
        """The claw's grip point on a stand-space point, pointing along d."""
        d = Vector(d).normalized()
        return self.hand(f, s, Vector(point) - d * depth, body, body_rot, d, x_axis, twist)

    def look(self, f, target, body, body_rot, roll=0.0):
        """Head (pitch, roll, yaw) to look at a stand-space point."""
        bm = body_matrix(body, body_rot)
        eye = bm @ HEAD_EYE
        d = bm.to_3x3().inverted() @ (self.to_root(f, target) - eye)
        yaw = math.degrees(math.atan2(d.x, -d.y))
        pitch = math.degrees(math.atan2(-d.z, math.hypot(d.x, d.y)))
        return (pitch, roll, yaw)

    def pose(self, frame, **kw):
        f = frame - 1
        r, y = self.root(f)
        self.pb['root'].location = r
        self.c.pose(frame, yaw=y, **kw)

    def done(self):
        self.pb['root'].location = (0, 0, 0)
        self.c.done()


def mix_hand(a, b, k):
    """Blend two (offset, rot) hand poses."""
    (oa, ra), (ob, rb) = a, b
    ra = ra or (-24, 0, 0)
    rb = rb or (-24, 0, 0)
    return oa.lerp(ob, k), tuple(lerp(p, q, k) for p, q in zip(ra, rb))


def rest_hand(dl01, s):
    return dl01.CARRY[s].copy(), (-24, s * 6, s * 10)


def antenna_set(base, wobble=0.0, f=0, droop_k=(0.8, 1.0, 1.2)):
    return [(base * droop_k[i] + wobble * math.sin(f * 0.9 - i * 0.8) * (1 + 0.3 * i), 0) for i in range(3)]


T = None          # build_dl01's track/spring, bound in add_clips


def tr(keys, f, ease=smoothstep):
    return T.track(keys, f, ease)


def spr(f, f0, amp, decay=7.0, freq=0.9):
    return T.spring(f, f0, amp, decay, freq)


def pulse(f, f0, f1):
    """0 -> 1 -> 0 over [f0, f1], a sine bump."""
    return math.sin(math.pi * (f - f0) / (f1 - f0)) if f0 <= f <= f1 else 0.0


IDLE_BODY, IDLE_ROT, IDLE_HEAD = (0, 0, -0.005), (2.0, 0, 0), (2.0, 0, 0)


# DL-01 WeighSelf -----------------------------------------------------------------------------------------
# The game slides ScaleTicket out along game -x by ticket_out(f) metres (it pops at TICKET_POP).
TICKET_POP = 30


def ticket_out(f):
    return tr([(0, 0), (TICKET_POP, 0), (TICKET_POP + 3, 0.035), (40, 0.035), (45, TICKET_OUT), (58, TICKET_OUT),
               (64, 0.0)], f)


def clip_weigh_self(dl01, arm):
    """He steps up onto the scale and settles; looks down at the dial as the needle swings; a little test
    bounce, two; the ticket pops out and he startles; he leans, pinches it out, reads it with his head on one
    side (POSTAGE DUE), pushes it back in neatly, a nod, and steps down."""
    N = 82
    a = Act(dl01, arm, 'WeighSelf', N)
    stand = SCALE_STAND
    top = SCALE_TOP
    a.root_keys = [(0, (0, 0, 0)), (2, (0, 0, 0)), (10, (0, 0, top)), (N - 12, (0, 0, top)), (N - 3, (0, 0, 0))]
    a.step('L', 1, 6, ANKLE[1] + Vector((0, -0.01, top)))
    a.step('R', 5, 10, ANKLE[-1] + Vector((0, -0.01, top)))
    a.step('R', N - 12, N - 7, ANKLE[-1])
    a.step('L', N - 8, N - 3, ANKLE[1])
    dial = to_stand(stand, (1.45 + SCALE_COL_DX, 0.24, 0.52))
    bx, by, bz = TICKET_BOX
    edge = bx - 0.04 - 0.006                       # the ticket's near end at rest (world x)
    for frame in range(1, N + 1):
        f = frame - 1
        out = ticket_out(f)
        tick = to_stand(stand, (edge - out + 0.011, by - 0.004, bz))
        bounce = tr([(18, 0), (21, -0.028), (24, 0.01), (27, -0.024), (30, 0.006), (34, 0)], f)
        startle = spr(f, TICKET_POP + 1, 1.0, decay=4, freq=1.3)
        lean = tr([(32, 0), (40, 1), (64, 1), (70, 0.2), (76, 0)], f)
        step_bob = -0.012 * (pulse(f, 2, 8) + pulse(f, 6, 12) + pulse(f, N - 12, N - 6) + pulse(f, N - 8, N - 2))
        body = (0.01 * lean, -0.02 * lean, -0.005 + bounce + 0.006 * startle + step_bob - 0.008 * lean)
        body_rot = (2 + 9 * lean - 6 * max(0, startle), -6 * lean, 4 * lean)
        # The head: the dial, the ticket, a tilt while he reads it.
        look_dial = a.look(f, dial, body, body_rot)
        look_tick = a.look(f, tick, body, body_rot)
        w_dial = tr([(6, 0), (12, 1), (TICKET_POP, 1), (TICKET_POP + 3, 0)], f)
        w_tick = tr([(TICKET_POP + 1, 0), (TICKET_POP + 5, 1), (64, 1), (70, 0)], f, ease=lambda x: ease_back(x, 0.8))
        read_tilt = tr([(46, 0), (50, 16), (56, 14), (59, -10), (63, -8), (66, 0)], f)
        nod = 10 * pulse(f, 66, 72)
        head = [IDLE_HEAD[i] * (1 - w_dial - w_tick) + look_dial[i] * w_dial + look_tick[i] * w_tick for i in range(3)]
        head[0] += -12 * max(0, startle) + nod + 3 * math.sin(f * 1.1) * pulse(f, 18, 34)
        head[1] += read_tilt
        # Claws: arms out a little for balance on the bounces; the left one pinches the ticket.
        bal = tr([(16, 0), (20, 1), (32, 1), (36, 0)], f)
        hands = {s: dl01.CARRY[s] + Vector((s * 0.035 * bal, 0, 0.03 * bal + 0.02 * max(0, startle))) for _, s in SIDES}
        rot = {'L': (-24 - 10 * bal, 6, 10), 'R': (-24 - 10 * bal, -6, -10)}
        reach = tr([(36, 0), (42, 1), (62, 1), (68, 0)], f)
        if reach > 0:
            g = a.grip(f, 1, tick, body, body_rot, d=(0.25, -1.0, -0.4), x_axis=(1, 0, 0))
            off, hr = mix_hand((hands[1], rot['L']), g, reach)
            hands[1], rot['L'] = off, hr
        claw_l = tr([(36, 20), (40, 34), (42, 30), (44, 3), (60, 3), (63, 30), (70, CLAW_REST_OPEN['L'])], f)
        claw_r = CLAW_REST_OPEN['R'] + 14 * bal + 20 * max(0, startle)
        # The antenna: bobbing on the bounces, up at the pop, a puzzled droop as he reads, a perk at the nod.
        ant = tr([(0, 0), (10, -4), (18, -6), (TICKET_POP, -6), (TICKET_POP + 2, -22), (40, -8), (50, 10), (60, 14),
                  (66, -6), (74, -2), (N - 1, 0)], f)
        antenna = [(ant * (0.8 + 0.2 * i) + spr(f, 21, 9 * (1 + 0.3 * i), 4, 1.3) + spr(f, 27, 9 * (1 + 0.3 * i), 4, 1.3)
                    - spr(f, 66, 8 * (1 + 0.3 * i), 5, 1.2), 0) for i in range(3)]
        feet = a.feet(f, pitch={side: 14 * max(0.0, bounce) / 0.01 for side in 'LR'})
        a.pose(frame, body=body, body_rot=body_rot, head=tuple(head), antenna=antenna, feet=feet, hands=hands,
               hand_rot=rot, claws={'L': claw_l, 'R': claw_r}, elbows={'L': reach})
    a.done()


# ---------------------------------------------------------------------------------------------------------
# Things he holds (in d17.glb, parented to his bones; the game shows them only while used)
# ---------------------------------------------------------------------------------------------------------

def attach_claw_stamp(arm, coll):
    """ClawStamp: the RECEIVED mark on the outer blade of his left claw (finger_b.L). Hidden until he franks it."""
    mat = bpy.data.materials.get('ClawStampMat') or _image_material('ClawStampMat', texture('stamp'), rough=0.6, alpha=True)
    b = arm.data.bones['finger_b.L']
    h, t = b.head_local, b.tail_local
    c = h.lerp(t, 0.42) + Vector((0.0098, 0, 0))
    up = (t - h).normalized()
    side = Vector((0, 1, 0))
    r = 0.0105
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    # Seen from his left (+x, where its normal faces), it reads with its top toward his wrist.
    corners = [c - side * r - up * r, c - side * r + up * r, c + side * r + up * r, c + side * r - up * r]
    _quad(bm, uv, corners, uvs=((0, 1), (0, 0), (1, 0), (1, 1)))
    ob = _flat_obj('ClawStamp', bm, [mat], coll)
    d17.parent_to_bone(ob, arm, 'finger_b.L')
    return ob


def attach_held(arm, coll, name, build, bone, at_frame, clip, prop_matrix):
    """A copy of a prop parented to a hand bone, placed so that at `at_frame` of `clip` it sits exactly where the
    prop does (prop_matrix, stand space): the game swaps the two at that frame."""
    ad = arm.animation_data
    act = bpy.data.actions[clip]
    ad.action = act
    bpy.context.scene.frame_set(at_frame)
    bpy.context.view_layer.update()
    pose_m = arm.pose.bones[bone].matrix.copy()
    rest_m = arm.data.bones[bone].matrix_local.copy()
    ad.action = None
    bm = bmesh.new()
    mats = build(bm)
    bmesh.ops.transform(bm, matrix=rest_m @ pose_m.inverted() @ prop_matrix, verts=bm.verts)
    ob = _obj(name, bm, mats, coll)
    d17.parent_to_bone(ob, arm, bone)
    return ob


# ---------------------------------------------------------------------------------------------------------
# What the game drives with each clip, by clip frame (f from 0): {object: (Blender offset, Blender rotation in
# degrees added to its rest, visible)}. Used for the previews; the report gives the same schedules.
# ---------------------------------------------------------------------------------------------------------

def game_moves(name, f):
    if name == 'WeighSelf':
        wob = 6 * math.sin(f * 1.4) * tr([(18, 0), (21, 1), (34, 1), (40, 0)], f)
        return {'ScaleTicket': ((-ticket_out(f), 0, 0), (0, 0, 0), True),
                'ScaleNeedle': ((0, 0, 0), (0, 95 + wob, 0), True)}
    return {}


PREVIEW = {
    'WeighSelf': dict(stand=SCALE_STAND, key=50, cx=0.15, look_z=0.45, frames=[1, 9, 15, 22, 28, 32, 37, 43, 51, 57, 64, 79]),
}


def add_clips(dl01, arm):
    global T
    T = dl01
    clip_weigh_self(dl01, arm)
    coll = bpy.data.collections.get('D17')
    attach_claw_stamp(arm, coll)
