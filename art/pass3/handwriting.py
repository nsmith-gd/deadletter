"""Handwriting for the painted textures (PIL only, no fonts needed): a small single-stroke alphabet drawn as pen,
pencil or crayon lines, with a 'parent' hand (neat, slanted, even) and a 'child' hand (big, wobbly, letters of
different sizes, the odd one backwards). Used by art/d17 (the parcel label), art/sorting_hall (Mara's letter),
art/pass2 (the route card) and art/pass3 (the lore notices).

    write(draw, text, x, y, size, hand='parent', ink=(30, 30, 60), width=4, seed=1) -> x after the last letter

`y` is the top of the capitals; `size` is the capital height in pixels.
"""
import math
import random

# Glyphs on a grid 4 wide and 6 tall (y down; capitals from 0 to 6). Each is a list of strokes; a stroke whose
# first item is 'dot' is a dot at that point. Curved glyphs are smoothed when drawn (SMOOTH).
_O = [[(2, 0), (3.4, 0.5), (4, 2), (4, 4), (3.4, 5.5), (2, 6), (0.6, 5.5), (0, 4), (0, 2), (0.6, 0.5), (2, 0)]]
G = {
    'A': [[(0, 6), (2, 0), (4, 6)], [(0.8, 3.9), (3.2, 3.9)]],
    'B': [[(0, 6), (0, 0), (2.6, 0), (3.6, 0.7), (3.6, 2.2), (2.6, 2.9), (0, 2.9)],
          [(2.6, 2.9), (3.9, 3.7), (3.9, 5.2), (2.9, 6), (0, 6)]],
    'C': [[(4, 1), (3, 0), (1.2, 0), (0, 1.6), (0, 4.4), (1.2, 6), (3, 6), (4, 5)]],
    'D': [[(0, 0), (0, 6), (2.2, 6), (3.6, 5), (4, 3), (3.6, 1), (2.2, 0), (0, 0)]],
    'E': [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 2.9), (3, 2.9)]],
    'F': [[(4, 0), (0, 0), (0, 6)], [(0, 2.9), (3, 2.9)]],
    'G': [[(4, 1), (3, 0), (1.2, 0), (0, 1.6), (0, 4.4), (1.2, 6), (3, 6), (4, 4.8), (4, 3.4), (2.3, 3.4)]],
    'H': [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    'I': [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    'J': [[(4, 0), (4, 4.6), (3, 6), (1, 6), (0, 4.8)]],
    'K': [[(0, 0), (0, 6)], [(4, 0), (0, 3.7)], [(1.4, 2.5), (4, 6)]],
    'L': [[(0, 0), (0, 6), (4, 6)]],
    'M': [[(0, 6), (0, 0), (2, 3.6), (4, 0), (4, 6)]],
    'N': [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    'O': _O,
    'P': [[(0, 6), (0, 0), (2.8, 0), (4, 0.9), (4, 2.3), (2.8, 3.2), (0, 3.2)]],
    'Q': _O + [[(2.5, 4.4), (4.3, 6.4)]],
    'R': [[(0, 6), (0, 0), (2.8, 0), (4, 0.9), (4, 2.3), (2.8, 3.2), (0, 3.2)], [(1.8, 3.2), (4, 6)]],
    'S': [[(4, 0.9), (3, 0), (1, 0), (0, 0.9), (0, 2.1), (1, 2.9), (3, 3.1), (4, 3.9), (4, 5.1), (3, 6), (1, 6), (0, 5.1)]],
    'T': [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    'U': [[(0, 0), (0, 4.6), (1, 6), (3, 6), (4, 4.6), (4, 0)]],
    'V': [[(0, 0), (2, 6), (4, 0)]],
    'W': [[(0, 0), (1, 6), (2, 2.4), (3, 6), (4, 0)]],
    'X': [[(0, 0), (4, 6)], [(4, 0), (0, 6)]],
    'Y': [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    'Z': [[(0, 0), (4, 0), (0, 6), (4, 6)]],
    '0': [[(2, 0), (3.3, 0.6), (3.8, 3), (3.3, 5.4), (2, 6), (0.7, 5.4), (0.2, 3), (0.7, 0.6), (2, 0)]],
    '1': [[(0.9, 1.2), (2.2, 0), (2.2, 6)]],
    '2': [[(0, 1.1), (1, 0), (3, 0), (4, 1), (4, 2.2), (0, 6), (4, 6)]],
    '3': [[(0, 0.7), (1, 0), (3, 0), (4, 0.9), (4, 2.1), (3, 2.9), (1.6, 2.9)],
          [(3, 2.9), (4, 3.8), (4, 5.1), (3, 6), (1, 6), (0, 5.3)]],
    '4': [[(3, 6), (3, 0), (0, 4.2), (4, 4.2)]],
    '5': [[(4, 0), (0.3, 0), (0, 2.8), (2.8, 2.5), (4, 3.5), (4, 5), (3, 6), (0, 5.8)]],
    '6': [[(3.6, 0), (1.6, 0.3), (0.2, 2.4), (0, 4.6), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (1, 3), (0.1, 4)]],
    '7': [[(0, 0), (4, 0), (1.4, 6)]],
    '8': [[(2, 2.9), (0.6, 2.2), (0.4, 0.9), (1.4, 0), (2.6, 0), (3.6, 0.9), (3.4, 2.2), (2, 2.9), (0.4, 3.8),
           (0.2, 5.2), (1.2, 6), (2.8, 6), (3.8, 5.2), (3.6, 3.8), (2, 2.9)]],
    '9': [[(4, 2), (3, 3), (1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 4), (2.6, 6), (0.6, 6)]],
    '-': [[(0.6, 3), (3.4, 3)]],
    '.': [['dot', (1.2, 5.7)]],
    ',': [[(1.6, 5.4), (1.0, 7.0)]],
    '?': [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2.1), (2, 3.4), (2, 4.4)], ['dot', (2, 5.9)]],
    '!': [[(1.5, 0), (1.5, 4.2)], ['dot', (1.5, 5.9)]],
    "'": [[(1.4, 0), (1.1, 1.6)]],
    '·': [['dot', (1.2, 3.2)]],
    '/': [[(4, 0), (0, 6)]],
    ':': [['dot', (1.2, 2.2)], ['dot', (1.2, 5.6)]],
    '&': [[(4, 6), (0.6, 2), (1, 0.3), (2.2, 0), (3, 0.8), (2.6, 2), (0.2, 4), (0.4, 5.4), (1.6, 6), (3, 5.2), (4, 3.6)]],
    '+': [[(0.4, 3), (3.6, 3)], [(2, 1.4), (2, 4.6)]],
    # Lower case (x-height from 2.8 to 6; ascenders from 0).
    'a': [[(3.4, 3.4), (2, 2.8), (0.6, 3.4), (0, 4.6), (0.6, 5.8), (2, 6), (3.4, 5.2)], [(3.4, 2.8), (3.4, 6)]],
    'd': [[(3.4, 3.4), (2, 2.8), (0.6, 3.4), (0, 4.6), (0.6, 5.8), (2, 6), (3.4, 5.2)], [(3.4, 0), (3.4, 6)]],
    'e': [[(0.2, 4.4), (3.4, 4.4), (3, 3.2), (1.8, 2.8), (0.6, 3.3), (0, 4.6), (0.6, 5.7), (1.8, 6), (3.2, 5.5)]],
    'f': [[(3, 0.4), (2.2, 0), (1.4, 0.5), (1.3, 6)], [(0.2, 2.9), (2.6, 2.9)]],
    'i': [[(1, 2.9), (1, 6)], ['dot', (1, 1.5)]],
    'l': [[(1, 0), (1, 6)]],
    'm': [[(0, 2.9), (0, 6)], [(0, 3.8), (0.8, 2.9), (1.6, 3), (2, 3.8), (2, 6)],
          [(2, 3.8), (2.8, 2.9), (3.6, 3), (4, 3.8), (4, 6)]],
    'n': [[(0, 2.9), (0, 6)], [(0, 3.8), (1, 2.9), (2.4, 2.9), (3, 3.8), (3, 6)]],
    'o': [[(1.7, 2.8), (3, 3.3), (3.4, 4.4), (3, 5.6), (1.7, 6), (0.4, 5.6), (0, 4.4), (0.4, 3.3), (1.7, 2.8)]],
    'r': [[(0.4, 2.9), (0.4, 6)], [(0.4, 4.1), (1.4, 3.0), (2.8, 2.9)]],
    's': [[(2.9, 3.2), (1.6, 2.8), (0.4, 3.2), (0.4, 4.1), (2.6, 4.6), (2.9, 5.5), (1.6, 6), (0.2, 5.6)]],
    't': [[(1.2, 0.8), (1.2, 5.4), (1.8, 6), (2.6, 5.8)], [(0.2, 2.9), (2.4, 2.9)]],
    'v': [[(0, 2.9), (1.6, 6), (3.2, 2.9)]],
    'y': [[(0, 2.9), (1.6, 6)], [(3.2, 2.9), (1.4, 7.4), (0.4, 7.8)]],
    'b': [[(0, 0), (0, 6)], [(0, 3.6), (1.4, 2.8), (2.8, 3.2), (3.4, 4.4), (2.8, 5.6), (1.4, 6), (0, 5.4)]],
    'c': [[(3.2, 3.3), (1.8, 2.8), (0.5, 3.3), (0, 4.4), (0.5, 5.6), (1.8, 6), (3.2, 5.5)]],
    'g': [[(3.4, 3.4), (2, 2.8), (0.6, 3.4), (0, 4.4), (0.6, 5.4), (2, 5.7), (3.4, 5.0)], [(3.4, 2.8), (3.4, 6.8), (2.6, 7.8), (0.8, 7.8), (0.2, 7.2)]],
    'h': [[(0, 0), (0, 6)], [(0, 3.8), (1, 2.9), (2.4, 2.9), (3, 3.8), (3, 6)]],
    'k': [[(0, 0), (0, 6)], [(2.8, 2.9), (0, 4.6)], [(1.0, 4.0), (3, 6)]],
    'p': [[(0, 2.9), (0, 7.8)], [(0, 3.6), (1.4, 2.8), (2.8, 3.2), (3.4, 4.4), (2.8, 5.6), (1.4, 6), (0, 5.4)]],
    'u': [[(0, 2.9), (0, 5.2), (0.8, 6), (2.2, 6), (3, 5.2)], [(3, 2.9), (3, 6)]],
    'w': [[(0, 2.9), (0.9, 6), (1.8, 3.6), (2.7, 6), (3.6, 2.9)]],
    'x': [[(0, 2.9), (3, 6)], [(3, 2.9), (0, 6)]],
}
SMOOTH = set('CGJOQSU0235689?&abcdegopsu')
NARROW = {'I': 3.0, '1': 3.0, '.': 2.2, ',': 2.2, '!': 2.6, "'": 2.2, '·': 2.4, ':': 2.4,
          'i': 2.0, 'l': 2.0, 'f': 3.2, 'r': 3.0, 't': 2.8, 's': 3.2, 'o': 3.6, 'a': 3.8, 'd': 3.8, 'e': 3.6, 'n': 3.4,
          'v': 3.4, 'y': 3.4, 'b': 3.6, 'c': 3.4, 'g': 3.6, 'h': 3.2, 'k': 3.0, 'p': 3.6, 'u': 3.2, 'x': 3.2}
WIDE = {'M': 4.6, 'W': 4.8, 'm': 4.4}

HANDS = {
    # jitter (grid units), size wobble, rotation (deg), baseline wobble (fraction of size), slant, spacing, mirror odds
    'parent': dict(jit=0.07, size=0.04, rot=2.0, base=0.03, slant=0.16, gap=1.12, mirror=0.0, passes=1),
    'clerk': dict(jit=0.04, size=0.02, rot=1.0, base=0.015, slant=0.05, gap=1.3, mirror=0.0, passes=1),
    'child': dict(jit=0.22, size=0.16, rot=9.0, base=0.12, slant=0.0, gap=1.4, mirror=0.0, passes=2),
    'chalk': dict(jit=0.12, size=0.08, rot=4.0, base=0.06, slant=0.08, gap=1.35, mirror=0.0, passes=2),
    'paint': dict(jit=0.1, size=0.06, rot=3.0, base=0.04, slant=0.0, gap=1.25, mirror=0.0, passes=1),
}


def _chaikin(pts, n=2):
    for _ in range(n):
        if len(pts) < 3:
            return pts
        q = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            q.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            q.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        q.append(pts[-1])
        pts = q
    return pts


def _line(draw, pts, ink, width):
    if len(pts) < 2:
        return
    draw.line(pts, fill=ink, width=width, joint='curve')
    r = width / 2.0
    for x, y in (pts[0], pts[-1]):                     # round caps
        draw.ellipse((x - r, y - r, x + r, y + r), fill=ink)


def glyph_width(ch, size):
    return (WIDE.get(ch, NARROW.get(ch, 4.0))) * size / 6.0


def write(draw, text, x, y, size, hand='parent', ink=(30, 30, 60), width=4, seed=1, mirror=(), spacing=1.0):
    """Draw `text` from (x, y) (top of capitals) at capital height `size`. `mirror`: indices of letters drawn
    backwards (a child's hand). Returns the x after the last letter."""
    h = HANDS[hand]
    rnd = random.Random(seed)
    u = size / 6.0
    for i, ch in enumerate(text):
        if ch == ' ':
            x += size * 0.55 * spacing
            continue
        strokes = G.get(ch) or G.get(ch.upper())
        if strokes is None:
            x += size * 0.5
            continue
        k = 1.0 + rnd.uniform(-h['size'], h['size'])
        rot = math.radians(rnd.uniform(-h['rot'], h['rot']))
        by = y + rnd.uniform(-h['base'], h['base']) * size
        gw = glyph_width(ch, size) * k
        cx, cy = 2.0, 3.0
        flip = i in mirror
        sx = (WIDE.get(ch, NARROW.get(ch, 4.0))) / 4.0

        def at(px, py, prnd):
            px = (4 - px) if flip else px
            px += prnd.uniform(-h['jit'], h['jit'])
            py += prnd.uniform(-h['jit'], h['jit'])
            dx, dy = (px - cx) * k, (py - cy) * k
            dx, dy = dx * math.cos(rot) - dy * math.sin(rot), dx * math.sin(rot) + dy * math.cos(rot)
            dx += (cy - py) * h['slant'] * k
            return (x + (cx * k + dx) * sx * u, by + (cy + dy) * u)
        for passn in range(h['passes']):
            prnd = random.Random(seed * 131 + i * 17 + passn)
            for st in strokes:
                if st[0] == 'dot':
                    X, Y = at(st[1][0], st[1][1], prnd)
                    r = width * 0.75
                    draw.ellipse((X - r, Y - r, X + r, Y + r), fill=ink)
                    continue
                pts = [at(px, py, prnd) for px, py in st]
                if ch in SMOOTH:
                    pts = _chaikin(pts, 2)
                _line(draw, pts, ink, width)
        x += gw + (size * (h['gap'] - 1.0) * 0.9 * spacing + size * 0.12) * (0.55 if ch.islower() else 1.0)
    return x


def text_width(text, size, hand='parent', spacing=1.0):
    h = HANDS[hand]
    w = 0.0
    for ch in text:
        if ch == ' ':
            w += size * 0.55 * spacing
        else:
            w += glyph_width(ch, size) + (size * (h['gap'] - 1.0) * 0.9 * spacing + size * 0.12) * (0.55 if ch.islower() else 1.0)
    return w


def crayon(draw, pts, colour, width=6, passes=3, jitter=1.8, rnd=None):
    """A wax-crayon line: several jittered passes."""
    rnd = rnd or random.Random(7)
    for _ in range(passes):
        q = [(x + rnd.uniform(-jitter, jitter), y + rnd.uniform(-jitter, jitter)) for x, y in pts]
        draw.line(q, fill=colour, width=width, joint='curve')


def crayon_circle(draw, cx, cy, r, colour, width=6, n=28, rnd=None, ry=None):
    ry = r if ry is None else ry
    crayon(draw, [(cx + r * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n + 1)],
           colour, width, rnd=rnd)


def crooked_tree(draw, x, y, s, colour, rnd=None, width=6, leaves=None):
    """The family's crooked tree: a trunk that leans and kinks, two branches, a lopsided crown. (x, y) = its foot."""
    rnd = rnd or random.Random(3)
    trunk = [(x, y), (x + 0.1 * s, y - 0.22 * s), (x - 0.16 * s, y - 0.46 * s), (x - 0.04 * s, y - 0.6 * s),
             (x + 0.12 * s, y - 0.82 * s)]
    crayon(draw, trunk, colour, width, rnd=rnd)
    crayon(draw, [(x - 0.12 * s, y - 0.52 * s), (x - 0.42 * s, y - 0.66 * s), (x - 0.5 * s, y - 0.8 * s)], colour, max(2, width - 2), rnd=rnd)
    crayon(draw, [(x + 0.06 * s, y - 0.3 * s), (x + 0.32 * s, y - 0.42 * s), (x + 0.4 * s, y - 0.58 * s)], colour, max(2, width - 2), rnd=rnd)
    if leaves:
        for cx, cy, r in ((x - 0.5 * s, y - 0.9 * s, 0.17 * s), (x + 0.1 * s, y - 1.02 * s, 0.24 * s),
                          (x + 0.42 * s, y - 0.72 * s, 0.15 * s)):
            crayon_circle(draw, cx, cy, r, leaves, max(2, width - 2), rnd=rnd)
