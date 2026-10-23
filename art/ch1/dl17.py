"""Chapter 1 Attendance, DL-17 A Different Lesson (game x 280.0 to 296.0, and the stair beyond to 303.15).
Design: docs/chapter1_part2_plan.md; rev 0.3 (docs/chapter1_rev03_plan.md, docs/full_game_plan.md DL-17).

The school's workshop: a volunteer maintenance bench, warm light, the most lived-in room in the school. Children's
growing experiments everywhere, all of them long dead and dry (nobody has tended them for decades): a tall slatted
shelf of seed trays and pots, each with a child's name tag, the soil shrunk and cracked, the seedlings shrivelled
brown; beans in jars gone dry, each bean shrivelled against the glass; a mended pot; a grow-lamp over the window shelf
(the game switches it off) and under it a pot with a dry stalk and the tag M. D. Nothing green, nothing living. Under
the bench, a plan chest; its lowest drawer, PLACEMENTS, holds Mara's irrigation drawing and her placement card.
The drawing is all hers, in her own pencil: her crooked tree with the knot made a garden bed, the trunk the main
channel, the branches laterals with sluices, the knot a settling loop. Beside her lines, never over them, the
volunteer's blue pencil in his own hand: "fall 1 in 100", "levels!" at the tank, a shallower channel section drawn
next to hers, a tick at the knot. The card: she applied for the placement herself (APPLICATION: BY THE PUPIL, her
signature beside his); Works Dept., ring A, water and irrigation, sponsor E. Vance, P.A. 316; REPORT VIA residential
access, ring A (Works gate sealed). The way on is the stair door in the right end wall: it opens on a lit stair up
and out of frame, RESIDENTIAL ACCESS . RING A on a blade sign over it.

Called by build_attendance.py as build_set(dl01, m, coll), in final world coordinates.
Blender (x, y, z) is the game's (x, z, -y): +y is away from the camera, z is up. The lane is y = 0, the floor z = 0.

What the game moves (origin = pivot, world coordinates; numbers in REPORT at the bottom):
    Att17Drawer    the plan chest's lowest drawer, built SHUT; origin on the middle of its front face; slides -y 0.45.
                   Its contents (papers, the drawing, the card, a pencil) are part of its mesh.
    Att17Tray      the fallen seed tray (carried); mesh built level about its bottom centre; the tilt it lies at is
                   the object's rotation (zero rotation = level, as carried).
    Att17GrowLamp  the grow-lamp's two tubes (EMIT Att17GrowLamp); origin at their centre.
    Att17Door      the stair door's leaf, built SHUT; origin on its hinge axis at the floor (HINGE); opens +90 deg
                   about +z, away from the room, toward the stair.
The expansion (docs/chapter1_expansion_build.md, DL-17 changes): Vance's apprentice test rig between the sink and the
stair door (build_rig), and its moving parts:
    Att17Valve     the valve's wheel and spindle, on the tank's down-pipe; origin the wheel's centre; spins about y.
    Att17ValveKey  the T-key on the valve's spindle (hidden until he has it); a child of Att17Valve.
    Att17Key       the T-key in the drawer, on the papers; a child of Att17Drawer (it slides out with it).
    Att17SluiceA/B/C  the levers, built OPEN (handle up); origin the pivot; +80 deg about x shuts (the grip comes forward).
    Att17TankWater the water in the tank's sight glass, full; origin the glass's bottom; scales in z.
    Att17Water1/2/3  each bed's water, full (0.13); origin the middle of the tray's floor; scales in z.
    Att17Stream1/2/3 the water falling from the spout over each bed; origin the spout's mouth.
    Att17Float     the copper float in bed 1, low; origin its bottom; rises 0.12.
    Att17Latch     the stair door's drop latch, down (locked), on the frame; origin its pivot; up = 70 deg about -y.
Her drawing gains her working for the rig along its bottom (her plan shrunk to 0.78 to make room) and his red-pencil
margin note; the atlas gains the rig's cells (rigcard, bed1-3, plA-C, sightscale). The drawing and card cells are
where they were.
Static: Att17Set (the room and the stairwell), Att17Bulbs (EMIT Att17Bulb: the pendant, the bench lamp, the bulkhead
by the door), Att17StairLamp (EMIT Att17StairLamp: the lamp over the flight), and the card player from
art/common/voice_props.py.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
from build_d17 import add_box, add_cyl, add_sphere, add_torus, worn_material, simple_material, emission_material

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
COMMON = os.path.join(HERE, '..', 'common')

# =====================================================================================================================
# Layout (Blender world; game x = x)
# =====================================================================================================================
X0, X1 = 280.0, 296.0
LWALL = (280.0, 280.15)              # the left wall (DL-16's doorway is 279.6 to 280.0)
DOORWAY = (-0.45, 0.55, 2.1)         # its opening: y0, y1, head
END_X = 295.8                        # the right end wall's face
WALL_Y, WALL_Y2 = 1.3, 1.45          # the back wall's face and back
FRONT_Y = -1.6                       # the floor's front edge
CEIL = 3.0
SHELF = (281.0, 282.4, 0.82, 1.28)   # the tall slatted shelf: x0, x1, y0, y1
SHELF_LEVELS = (0.10, 0.52, 0.94, 1.36, 1.78)
SHELF_TOP = 2.1
BENCH = (282.8, 288.6, 0.65, 1.3, 0.9)          # x0, x1, y0, y1, top
CHEST = (285.18, 286.82)                        # the plan chest's carcass, x
CHEST_FRONT = 0.645                             # its carcass front; drawer fronts stand 0.025 proud, at 0.62
DRAWER = (285.3, 286.7, 0.62, 0.12, 0.48)       # x0, x1, front face y, z0, z1
DRAWER_ORIGIN = (286.0, 0.62, 0.30)
DRAWER_TRAVEL = 0.45
CONTENT_Z = 0.392                               # the top of the paper stack in the drawer
POT = (286.9, 0.35)                             # the mended pot, on the floor
TRAY = (285.7, 0.05)                            # Att17Tray's bottom centre (x, y)
TRAY_SIZE = (0.42, 0.30, 0.09)
TRAY_TILT = (10.0, 0.0, -9.0)                   # degrees, XYZ euler: back edge up on a heap of spilled soil
STOOL = (287.6, 288.4, 0.30, 0.70, 0.45)        # x0, x1, y0, y1, top
PLAYER = (288.0, 0.48, 0.45)                    # the voice-card player on the stool (front to the camera)
BOARD = (282.95, 285.75, 1.05, 2.05, 1.276)     # the tool board: x0, x1, z0, z1, face y
WINDOW = (289.3, 291.7, 1.05, 2.0)              # x0, x1, sill, head (a dead light well behind)
WSHELF = (289.0, 292.0, 0.82, 1.3, 0.92)        # the window shelf: x0, x1, y0, y1, top
GROW = (289.42, 291.58, 1.05, 1.60)             # the grow-lamp tubes: x0, x1, y centre, z
MD_POT = (290.5, 1.06)                          # M. D.'s pot, under the middle of the grow-lamp (dry, dead)
SINK = (292.1, 292.9)
DOOR17 = (-0.5, 0.5, 2.15)                      # the way on: the stair door in the right end wall, y0, y1, head
HINGE = (296.0, 0.5, 0.0)                       # Att17Door's hinge (its origin): the stair-side face, the back jamb
LEAF_T = 0.045                                  # the leaf's thickness (hung flush with the wall's stair-side face)
STAIR_X0, RISE, GOING, TREADS = 297.1, 0.18, 0.26, 18   # first riser; tread i (1..18) top RISE*i; then the upper landing
STAIR_Y = (-0.6, 0.9)                           # the flight's width (front edge, back wall face)
WELL = (296.0, 303.0, -0.75, 0.9, 1.05, 5.2)    # the stairwell: x0, x1, front y, back wall face, back, top
WELL_FASCIA = 298.2                             # the room's ceiling carries on over the landing to here; beyond, open up
STAIR_LAMP = (299.3, 0.84, 3.62)                # the warm lamp over the flight (Att17StairLamp)
SIGN17 = (294.62, 295.72, 2.42, 2.718)          # the blade sign over the door: x0, x1, z0, z1 (in the plane y = 0)
PENDANT = (285.95, 0.80, 2.215)                 # the lit pendant's bulb over the bench and the drawer
LAMP_HEAD = Vector((285.0, 0.92, 1.40))         # the bench lamp's head
LAMP_AIM = Vector((285.5, 0.70, 0.90))
DOOR_LAMP = (295.25, 1.20, 2.25)
BROOM = (295.52, 1.12)                          # the broom's head, in the corner by the stair door (it leant by the sink)

# Vance's apprentice test rig (docs/chapter1_expansion_build.md, DL-17 changes), between the sink and the stair door.
# The tank on the wall feeds a down-pipe; the valve on it (turned with his T-key) lets the tank through to a manifold
# under the bench; three sluices A, B, C on the bench front open three brass pipes that rise behind the bench and cross:
# A feeds bed 3, B bed 1, C bed 2. A float in bed 1 hangs on a chain that runs up to a pulley, along under the ceiling
# and down to the latch on the stair door.
VALVE = (292.55, 0.50, 0.70)                    # Att17Valve: the wheel's centre (the wheel faces the camera, -y)
VALVE_R = 0.085                                 # the wheel's radius
DOWN_Y = 0.60                                   # the down-pipe's axis y (the valve's body on it; its spindle comes forward)
SPINDLE_TIP = 0.47                              # the spindle's square end (y): Att17ValveKey's socket goes on it here
TANK = (293.0, 294.2, 0.76, 1.24, 1.7, 2.3)     # x0, x1, y0, y1, z0, z1: on two wall brackets, centre y 1.0
SIGHT = (293.95, 0.735, 1.78, 2.22)             # the sight glass on the tank's front: x, axis y, z0 (its bottom), z1
RIG = (293.05, 295.3, 0.35, 0.95, 0.55)         # the test bench: x0, x1, y0, y1, top
BEDS = ((293.1, 293.75), (293.8, 294.45), (294.5, 295.15))   # beds 1, 2, 3: x0, x1
BED_Y = (0.45, 0.85)
BED_T = 0.015                                   # the trays' walls and floors
BED_TOP = RIG[4] + 0.15                         # their rims (trays 0.15 deep)
WATER_Z = RIG[4] + BED_T                        # the water's bottom, the trays' floor: Att17Water1/2/3's origins
WATER_D = 0.13                                  # full
SOIL_T = 0.015                                  # a skin of dry soil on each tray's floor
BED_NAMES = ('M. D.', 'R. A.', 'T. O.')
SLUICES = (('A', 293.45, 3), ('B', 294.1, 1), ('C', 294.8, 2))   # lever, pivot x, the bed its pipe feeds
SLUICE_PIVOT = (0.33, 0.45)                     # the levers' pivots: y (on the bench's front panel), z
LEVER_L = 0.15                                  # pivot to the top of the grip
MANIFOLD = (0.60, 0.30)                         # the feed under the bench: y, z (from the down-pipe to the last cock)
COCK_Z = 0.42                                   # the sluices' cocks on the manifold, behind the front panel
RISE_Y = {'A': 1.02, 'C': 1.10, 'B': 1.18}      # the pipes' depth behind the bench (A in front, B at the back)
RUN_Z = {'A': 0.95, 'C': 1.10, 'B': 1.25}       # the height each runs across at
SPOUT_X = (293.25, 293.95, 294.98)              # each bed's spout (beds 1, 2, 3)
MOUTH = (0.66, 0.86)                            # the spouts' mouths: y, z (Att17Stream1/2/3's origins)
PIPE_R = 0.013                                  # the three sluice pipes, all the same brass
BACKBOARD = (293.0, 295.35, 1.255, 1.27, 0.56, 1.40)   # a painted board behind the pipes: x0, x1, y0, y1, z0, z1
FLOAT = (293.60, 0.64, WATER_Z + SOIL_T)        # Att17Float: its bottom, low (on bed 1's soil)
FLOAT_R = 0.045
FLOAT_RISE = 0.12
CHAIN_Y = 0.64                                  # the chain's plane, from the float to the end wall
PULLEY1 = (293.64, CHAIN_Y, 2.76, 0.04)         # x, y, z, r: hung from the beam at 293.6 (axle along y)
PULLEY2 = (295.705, CHAIN_Y, 2.76, 0.04)        # on a bracket off the end wall (axle along y)
PULLEY3 = (295.745, 0.62, 2.15, 0.02)           # beside the door's architrave (axle along x): the chain turns toward -y
PULLEY4 = (295.925, -0.45, 2.11, 0.02)          # under the door's head, over the latch's eye (axle along x)
LATCH = (295.82, -0.47, 1.90)                   # Att17Latch's pivot: on a bracket on the free jamb, at the wall's face;
LATCH_L = 0.127                                 # the bar runs +x from it across the reveal, its nib dropping into a
LATCH_EYE = 295.925                             # keeper on the leaf. The chain's eye on the bar (x).
LATCH_UP = 70.0                                 # degrees, lifted: about Blender -y (game +z), the bar's end rising
KEY_AT = (285.60, 1.04, CONTENT_Z + 0.0025 + 0.012, 0.5)   # Att17Key in the drawer, shut: its socket's centre, its turn
RIGCARD = (293.10, 293.40, 1.92, 2.098)         # Vance's card on the tank's front: x0, x1, z0, z1
# The present-day service thread (the director's addition; the prologue's new cable, art/pass6/build_ending_secrets.py):
# a new cable comes in through the left wall, runs along the top of the back wall to a small new pump-and-relay box by
# the tank (which refills the tank through a recently repaired pipe), and carries on through the end wall by the stair
# door and up the stairwell toward ring A. The way on follows it.
PUMP = (294.38, 294.76, 1.10, 1.92, 2.32)       # the box: x0, x1, front face y (its back on the wall), z0, z1
RELAY_LAMP = (294.70, 1.094, 2.27)              # Att17RelayLamp: the tiny green pilot lamp on its front (centre)
CABLE_Y, CABLE_Z = WALL_Y - 0.03, 2.80          # the cable along the top of the back wall
WELL_CABLE_Y = 0.87                             # and along the stairwell's back wall (face y 0.9), 1.5 over the nosings

# =====================================================================================================================
# Materials
# =====================================================================================================================
NEW_WORN = {     # the game's WORN table format is in REPORT
    'WorkPlaster': dict(base=(.33, .27, .18), dirt=(.17, .13, .08), chip=(.23, .19, .14), rough=.9, chip_rough=.85,
                        metallic=0, grime_scale=3, chip_scale=18, chip_amount=.7, streaks=.5, dust=(.26, .22, .16), dust_amount=.4),
    'PotClay': dict(base=(.34, .15, .075), dirt=(.16, .1, .06), chip=(.42, .36, .28), rough=.9, chip_rough=.95,
                    metallic=0, grime_scale=10, chip_scale=40, chip_amount=.72, streaks=.3, dust=(.36, .32, .26), dust_amount=.5),
}
REUSE_WORN = {   # names already in index.html's WORN table (fallbacks for a lone build)
    'WinDado': dict(base=(.12, .16, .135), dirt=(.065, .075, .06), chip=(.30, .27, .21), rough=.55, chip_rough=.85,
                    metallic=0, grime_scale=4, chip_scale=22, chip_amount=.68, streaks=.5, dust=(.16, .17, .15), dust_amount=.4),
    'PigeonWood': dict(base=(.12, .085, .055), dirt=(.06, .045, .03), chip=(.2, .15, .1), rough=.85, chip_rough=.8, metallic=0,
                       grime_scale=6, chip_scale=30, chip_amount=.75, dust=(.1, .09, .08), dust_amount=.6),
    'CrateWood': dict(base=(.18, .12, .07), dirt=(.08, .055, .035), chip=(.25, .19, .12), rough=.85, chip_rough=.8, metallic=0,
                      grime_scale=6, chip_scale=30, chip_amount=.75, streaks=.6),
    'PupilWood': dict(base=(.36, .27, .17), dirt=(.17, .12, .08), chip=(.46, .38, .27), rough=.7, chip_rough=.6, metallic=0,
                      grime_scale=12, chip_scale=40, chip_amount=.74, dust=(.3, .28, .24), dust_amount=.5),
    'WornIron': dict(base=(.045, .043, .04), dirt=(.06, .035, .02), chip=(.3, .29, .27), rough=.7, chip_rough=.35, metallic=.6,
                     grime_scale=9, chip_scale=40, chip_amount=.6, dust=(.09, .085, .075), dust_amount=.4),
    'HandledBrass': dict(base=(.2, .14, .06), dirt=(.08, .06, .03), chip=(.62, .46, .2), rough=.5, chip_rough=.2, metallic=.85,
                         grime_scale=8, chip_scale=26, chip_amount=.5, dust=(.12, .1, .07), dust_amount=.2),
    'DarkMetal': dict(base=(.017, .016, .014), dirt=(.03, .024, .016), chip=(.075, .068, .055), rough=.72, chip_rough=.45,
                      metallic=.25, dust=(.075, .072, .062), grime_scale=5, chip_scale=34, chip_amount=.78, dust_amount=.7),
    'LuggageCanvas': dict(base=(.13, .135, .105), dirt=(.07, .065, .05), chip=(.21, .2, .16), rough=.9, chip_rough=.9, metallic=0,
                          grime_scale=10, chip_scale=30, chip_amount=.72, dust_amount=.6),
    'DepotGreen': dict(base=(.06, .09, .07), dirt=(.04, .035, .025), chip=(.12, .11, .1), rough=.65, chip_rough=.5, metallic=.2,
                       grime_scale=8, chip_scale=40, chip_amount=.7, dust_amount=.5),
    'WornStrap': dict(base=(.2, .17, .11), dirt=(.1, .08, .05), chip=(.32, .28, .2), rough=.95, chip_rough=.9, metallic=0,
                      grime_scale=14, chip_scale=50, chip_amount=.7, dust=(.2, .18, .14), dust_amount=.3),
    'ParcelBrown': dict(base=(.3, .22, .13), dirt=(.15, .11, .07), chip=(.4, .33, .24), rough=.9, chip_rough=.85, metallic=0,
                        dust=(.2, .18, .15), grime_scale=10, chip_scale=40, chip_amount=.75, dust_amount=.7),
}
REUSE_PLAIN = {'DirtyGlass': ((.03, .035, .035), .25, .2), 'TeaEnamel': ((.58, .55, .47), .35, 0.0),
               'Cable': ((.014, .013, .012), .55, 0.0), 'Copper': ((.55, .3, .18), .35, 1.0),
               'Water': ((.01, .012, .012), .04, .3),     # the rig's water (the game's Water: dark, a little see-through)
               'NewCable': ((.016, .016, .018), .28, 0.0),   # the prologue's new cable: glossy black (and the fresh tape)
               'NewSteel': ((.26, .27, .28), .4, .8)}        # galvanised: its clips, the new box, the new coupling
NEW_EMIT = {'Att17GrowLamp': ((0.78, 0.84, 1.0), 3.0), 'Att17Bulb': ((1.0, 0.78, 0.5), 5.0), 'Att17StairLamp': ((1.0, 0.8, 0.55), 6.0),
            'Att17RelayLamp': ((0.35, 1.0, 0.45), 4.0)}
REUSE_EMIT = {}
IMAGES = {'Att17Atlas': ('dl17_atlas.png', 0.85)}


def mat(name):
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    if name in NEW_WORN:
        return worn_material(name, **NEW_WORN[name])
    if name in REUSE_WORN:
        return worn_material(name, **REUSE_WORN[name])
    if name in REUSE_PLAIN:
        c, r, mtl = REUSE_PLAIN[name]
        return simple_material(name, c, r, metallic=mtl)
    if name == 'Window':                       # the game's GLASSY Window (see-through): the jars, the door's light
        return simple_material('Window', (0.8, 0.82, 0.8), 0.12, transmission=0.95)
    if name in NEW_EMIT or name in REUSE_EMIT:
        c, s = NEW_EMIT.get(name) or REUSE_EMIT[name]
        return emission_material(name, c, s)
    if name in IMAGES:
        fn, rough = IMAGES[name]
        mt, nt, bsdf = d17._new_material(name)
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(os.path.join(TEX, fn), check_existing=True)
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = rough
        return mt
    vp = _voice_props()
    if vp is not None:
        return vp.material(name)
    raise KeyError(name)


def _voice_props():
    import sys
    if not os.path.exists(os.path.join(COMMON, 'VOICE_PROPS_READY')):
        return None
    if COMMON not in sys.path:
        sys.path.insert(0, COMMON)
    import voice_props
    return voice_props


# =====================================================================================================================
# The atlas (PIL, at build time, into art/ch1/textures/dl17_atlas.png). 2048 square; pixel (0, 0) is the top left.
# =====================================================================================================================
ATLAS = 2048
CELLS = {
    'drawing': (0, 0, 1280, 896),            # Mara's irrigation drawing, 0.50 x 0.35 m (2.56 px/mm)
    'card': (1280, 0, 2048, 480),            # her placement card, 0.20 x 0.125 m (3.84 px/mm)
    'cardB': (1280, 480, 1664, 720), 'cardC': (1664, 480, 2048, 720),
    'placements': (1280, 720, 1792, 816),    # the drawer's label
    'radio': (1792, 720, 2048, 848),
    'sign_shop': (0, 896, 768, 1088), 'sign_works': (768, 896, 1536, 1104),
    'rota': (1536, 896, 1792, 1072),
    'toolboard': (0, 1104, 1024, 1488), 'chart': (1024, 1104, 1536, 1488),
    'paper1': (1536, 1104, 1792, 1360), 'paper2': (1792, 1104, 2048, 1360),
    'seedlist': (1536, 1360, 2048, 1488),
    'soilcrack': (1040, 1704, 1328, 1992),    # dry soil, cracked (the trays' surface)
    # The test rig (expansion): Vance's card on the tank, the beds' name cards, the levers' letters, the sight glass's scale.
    'rigcard': (1336, 1696, 1848, 2000),      # 0.30 x 0.178 m
    'bed1': (0, 1816, 192, 1876), 'bed2': (192, 1816, 384, 1876), 'bed3': (384, 1816, 576, 1876),
    'plA': (576, 1816, 640, 1880), 'plB': (640, 1816, 704, 1880), 'plC': (704, 1816, 768, 1880),
    'sightscale': (776, 1816, 808, 2008),
}
NAMES = ['M. D.', 'T. ORME', 'R. ABEL', 'Ada', 'Ben K.', 'Lotte', 'Pim', 'Joss', 'Nell', 'Ivo', 'Tam', 'Kit', 'Rosa',
         'Dov', 'Hana', 'Sami', 'Ewa', 'Oskar', 'Lin', 'Bea', 'Tobi', 'Mira', 'Fen', 'Cass', 'Aldo', 'Yusuf', 'Wren',
         'Ines', 'Matti', 'Ola', 'Pia', 'Rufus', 'Saul', 'Teo', 'Una', 'Vik', 'Zia', 'Leni', 'Hugo', 'Elsie', 'Cato',
         'Dara', 'Gus', 'Ilse', 'Jory', 'Kara', 'Luka', 'Noor', 'Otto', 'Perry', 'Quin', 'Abe', 'Bo', 'Cleo', 'Dan R.',
         'Edie', 'Femi', 'Greta', 'Hal', 'Iris', 'Jem', 'Kofi', 'Lola', 'Max']
for _i in range(64):                         # name tags, 128 x 40 each (8 x 8 under the tool board)
    _x, _y = (_i % 8) * 128, 1488 + (_i // 8) * 40
    CELLS['tag%d' % _i] = (_x, _y, _x + 128, _y + 40)
SWATCH = {'sw_soil_dry': (72, 56, 42), 'sw_soil_dark': (30, 23, 17), 'sw_straw': (150, 126, 82), 'sw_deadleaf': (84, 66, 40),
          'sw_rot': (40, 34, 24), 'sw_glass': (74, 90, 84), 'sw_paper': (214, 206, 182), 'sw_white': (220, 216, 204),
          'sw_bakelite': (60, 36, 22), 'sw_red': (130, 40, 30), 'sw_black': (12, 11, 10), 'sw_bean': (112, 70, 50),
          'sw_wire': (128, 126, 118), 'sw_putty': (176, 166, 140), 'sw_string': (184, 172, 140), 'sw_cloth': (70, 60, 46),
          'sw_wool': (96, 70, 52), 'sw_pencil': (206, 160, 52), 'sw_graphite': (40, 40, 44), 'sw_tea': (34, 18, 8),
          'sw_steel': (140, 142, 140), 'sw_grille': (52, 44, 34), 'sw_tagwhite': (226, 222, 208), 'sw_lolly': (196, 168, 120),
          'sw_tray': (96, 68, 42), 'sw_green': (52, 78, 58), 'sw_seam': (22, 15, 9), 'sw_rubber': (20, 20, 19),
          'sw_cream': (200, 190, 160), 'sw_blue': (60, 80, 120), 'sw_tin': (110, 112, 104), 'sw_label': (200, 186, 150),
          'sw_crust': (112, 92, 70), 'sw_shrivel': (96, 72, 44), 'sw_beandead': (64, 44, 32)}
for _i, _k in enumerate(SWATCH):
    _x, _y = 1152 + (_i % 14) * 64, 1488 + (_i // 14) * 64
    CELLS[_k] = (_x, _y, _x + 64, _y + 64)


def cell_uv(name):
    x0, y0, x1, y1 = CELLS[name]
    return x0 / ATLAS, 1 - y1 / ATLAS, x1 / ATLAS, 1 - y0 / ATLAS


def cell_mid(name):
    u0, v0, u1, v1 = cell_uv(name)
    return (u0 + u1) / 2, (v0 + v1) / 2


FONTS = {'sans-bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
         'sans': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
         'carlito': '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf',
         'carlito-reg': '/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf',
         'letter': '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
         'letter-bold': '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
         'mono': '/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf',
         'mono-reg': '/usr/share/fonts/truetype/freefont/FreeMono.ttf',
         'ink': '/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf',
         'hand': '/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf'}


def _font(size, kind='sans-bold'):
    from PIL import ImageFont
    try:
        return ImageFont.truetype(FONTS[kind], int(size))
    except OSError:
        return ImageFont.load_default()


def _noise(w, h, cells, seed):
    """Smooth value noise in [0, 1] (bicubic-upsampled lattice)."""
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for o in range(3):
        c = cells * (2 ** o)
        g = (rng.random((max(2, int(c * h / w)) + 1, c + 1)) * 255).astype('uint8')
        out += amp * np.asarray(Image.fromarray(g).resize((w, h), Image.BICUBIC)).astype(float) / 255.0
        tot += amp
        amp *= 0.5
    return out / tot


def _paper(w, h, base, seed, amp=0.06, edge=0.1, edge_px=30):
    """A sheet: base colour, a little tooth, edges yellowed."""
    import numpy as np
    from PIL import Image
    n = _noise(w, h, 5, seed)
    a = np.ones((h, w, 3)) * np.array(base, float) * (1 - amp / 2 + amp * n)[..., None]
    yy, xx = np.mgrid[0:h, 0:w]
    e = np.clip(np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / float(edge_px), 0, 1)
    a *= (1 - edge * (1 - e))[..., None] * np.array([1.0, 0.98, 0.92])[None, None, :] ** (1 - e)[..., None]
    rng = np.random.default_rng(seed + 1)
    a *= (1 - 0.05 * (rng.random((h, w)) > 0.985))[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGB').convert('RGBA')


def _fade(img, seed, grey=(132, 130, 122), k=0.2, dust=0.12):
    import numpy as np
    from PIL import Image
    a = np.asarray(img.convert('RGB')).astype(float)
    a = a * (1 - k) + np.array(grey) * k
    a *= np.array([1.0, 0.97, 0.9])
    n = _noise(a.shape[1], a.shape[0], 6, seed)
    a = a * (1 - dust * (n[..., None] - 0.5) * 2)
    return Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGB')


def _hand(layer, xy, text, font, fill, rnd, jit=0.8, rot=3.0, anchor='l', track=1.0):
    """Lettering by hand: each glyph a little turned and off its line. xy: the line's left (or middle) at mid height."""
    from PIL import Image, ImageDraw
    x, y = xy
    widths = [font.getlength(c) * track for c in text]
    if anchor == 'm':
        x -= sum(widths) / 2
    elif anchor == 'r':
        x -= sum(widths)
    s = int(font.size * 2.2)
    for c, w in zip(text, widths):
        if c != ' ':
            g = Image.new('RGBA', (s, s), (0, 0, 0, 0))
            col = fill if len(fill) == 4 else fill + (255,)
            col = col[:3] + (int(col[3] * rnd.uniform(0.82, 1.0)),)
            ImageDraw.Draw(g).text((s / 2, s / 2), c, font=font, fill=col, anchor='mm')
            g = g.rotate(rnd.uniform(-rot, rot), resample=Image.BICUBIC)
            px, py = int(x + w / 2 - s / 2 + rnd.uniform(-jit, jit)), int(y - s / 2 + rnd.uniform(-jit, jit))
            sx0, sy0 = max(0, -px), max(0, -py)                 # clipped to the layer
            sx1, sy1 = min(s, layer.width - px), min(s, layer.height - py)
            if sx1 > sx0 and sy1 > sy0:
                layer.alpha_composite(g, (px + sx0, py + sy0), (sx0, sy0, sx1, sy1))
        x += w * rnd.uniform(0.97, 1.03)


def _typed(layer, xy, text, font, rnd, ink=(28, 26, 34)):
    """Typewriter: each strike a little high or low, a little heavy or light."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(layer)
    x, y = xy
    for c in text:
        if c != ' ':
            d.text((x, y + rnd.uniform(-1.4, 1.4)), c, font=font, fill=ink + (rnd.randint(170, 250),), anchor='lm')
        x += font.getlength(c)


def _grain(layer, seed, lo=0.6):
    """Pencil on paper: break up a drawn layer's alpha with the paper's tooth."""
    import numpy as np
    from PIL import Image
    a = np.asarray(layer).astype(float)
    rng = np.random.default_rng(seed)
    n = _noise(layer.width, layer.height, 40, seed) * 0.5 + rng.random((layer.height, layer.width)) * 0.5
    a[..., 3] *= lo + (1 - lo) * n
    return Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGBA')


# Mara's tree (art/dl05/build_dl05.py _crooked_tree): unit coordinates, the trunk's foot at (0, 0), y down.
_KNOT = [(0.2 + 0.055 * math.cos(a), -0.655 + 0.05 * math.sin(a)) for a in [math.pi * 0.5 + k * math.pi / 7 for k in range(15)]]
TREE = [
    ([(0.0, 0.0), (-0.03, -0.14), (0.04, -0.27), (-0.04, -0.42), (0.03, -0.56), (-0.05, -0.72)], 1.0),
    ([(-0.12, 0.02), (0.0, 0.0), (0.13, 0.03)], 0.6),
    ([(-0.02, -0.40), (-0.16, -0.48), (-0.24, -0.62), (-0.33, -0.66)], 0.7),
    ([(-0.17, -0.50), (-0.13, -0.62)], 0.45),
    ([(0.02, -0.52), (0.14, -0.58), (0.2, -0.62)], 0.7),
    (_KNOT, 0.55),
    ([(0.2, -0.61), (0.27, -0.66), (0.36, -0.7), (0.43, -0.78)], 0.6),
    ([(-0.05, -0.72), (-0.03, -0.84), (0.03, -0.93)], 0.6),
    ([(-0.04, -0.8), (0.1, -0.86)], 0.4),
    ([(0.02, -0.25), (0.15, -0.3), (0.22, -0.28)], 0.5),
]


GRAPHITE = (50, 50, 60)          # Mara's pencil
BLUE = (26, 58, 150)              # Vance's blue pencil
RED = (176, 40, 34)               # and his red one (the margin note on her working for his test rig)


def _wob(pts, rnd, amp=1.0, step=8.0, over=0.0):
    """A line by hand through pts (final px): resampled, swaying a little side to side, overshooting its ends."""
    pts = [tuple(p) for p in pts]
    if over and len(pts) > 1:
        for i0, i1 in ((0, 1), (-1, -2)):
            (ax, ay), (bx, by) = pts[i0], pts[i1]
            L = math.hypot(ax - bx, ay - by) or 1
            pts[i0] = (ax + (ax - bx) / L * over, ay + (ay - by) / L * over)
    ph1, ph2 = rnd.uniform(0, 6.3), rnd.uniform(0, 6.3)
    f1, f2 = rnd.uniform(0.015, 0.03), rnd.uniform(0.07, 0.11)
    out, s = [], 0.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        if L == 0:
            continue
        nx, ny = -(by - ay) / L, (bx - ax) / L
        n = max(1, int(L / step))
        for i in range(n):
            t = i / n
            o = amp * (0.7 * math.sin((s + t * L) * f1 + ph1) + 0.3 * math.sin((s + t * L) * f2 + ph2))
            out.append((ax + (bx - ax) * t + nx * o, ay + (by - ay) * t + ny * o))
        s += L
    out.append(pts[-1])
    return out


def _chaikin(pts, n=2):
    for _ in range(n):
        q = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            q += [(0.75 * ax + 0.25 * bx, 0.75 * ay + 0.25 * by), (0.25 * ax + 0.75 * bx, 0.25 * ay + 0.75 * by)]
        q.append(pts[-1])
        pts = q
    return pts


def _offset(pts, dist):
    """A polyline moved sideways by dist (its normals averaged at the joints)."""
    out = []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        out.append((x - (b[1] - a[1]) / L * dist, y + (b[0] - a[0]) / L * dist))
    return out


def _clip_circle(pts, c, r, keep='out'):
    """The part of a polyline outside (or inside) a circle, cut where it crosses."""
    def inside(p):
        return math.hypot(p[0] - c[0], p[1] - c[1]) < r
    out = []
    for a, b in zip(pts, pts[1:]):
        ia, ib = inside(a), inside(b)
        want_a, want_b = (not ia, not ib) if keep == 'out' else (ia, ib)
        if want_a and (not out or out[-1] != a):
            out.append(a)
        if want_a != want_b:
            lo, hi = 0.0, 1.0
            for _ in range(30):
                mid = (lo + hi) / 2
                p = (a[0] + (b[0] - a[0]) * mid, a[1] + (b[1] - a[1]) * mid)
                if inside(p) == ia:
                    lo = mid
                else:
                    hi = mid
            out.append((a[0] + (b[0] - a[0]) * lo, a[1] + (b[1] - a[1]) * lo))
    if pts and ((not inside(pts[-1])) if keep == 'out' else inside(pts[-1])):
        out.append(pts[-1])
    return out


def make_drawing():
    """Mara's irrigation drawing (1280 x 896, drawn at 2x), all of it in her own pencil: her crooked tree, sketched
    soft, made a garden bed: the trunk the main channel from the tank, the branches laterals with sluices, the knot a
    settling loop; plants along the laterals; her section, her notes, her title block. Beside her lines, never over
    them, the volunteer's blue pencil, in his own hand: 'fall 1 in 100', 'levels!' at the tank, a shallower channel
    section drawn next to hers, a tick at the knot, his initials where it says CHECKED. Final pixels; K scales to the
    working canvas."""
    from PIL import Image, ImageDraw, ImageFilter
    K = 2
    W, H = 1280, 896
    rnd = random.Random(1701)
    paper = _paper(W * K, H * K, (230, 222, 200), 1702, amp=0.07, edge=0.12, edge_px=60)
    BED = (150, 70, 800, 660)

    def P(u, v):                                               # the tree's unit coordinates -> final px
        return (470 + u * 700, 800 + v * 740)

    # Layout: her plan (the bed, the tank, and his notes on them) is drawn in its own coordinates and shrunk onto the
    # sheet's upper left, to make room along the bottom for her working for the test rig; the right-hand column (her
    # section, notes, title block; his section) is drawn as it was. Lettering in the plan shrinks less than its lines.
    PLAN, SHEET = (0.78, -8.0, 10.0), (1.0, 0.0, 0.0)
    XF = list(SHEET)                                           # the current layout: px = (ox + s x, oy + s y)

    def T(x, y):
        s_, ox, oy = XF
        return ox + s_ * x, oy + s_ * y

    def fs(size):
        return size * (0.5 + 0.5 * XF[0])

    def k(pts):
        return [(T(x, y)[0] * K, T(x, y)[1] * K) for x, y in pts]

    # 1. Her tree, sketched first: soft pencil, light, gone over; a hand's smudges.
    XF[:] = PLAN
    child = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0))
    dc = ImageDraw.Draw(child)
    for pts, wgt in TREE:
        q = [P(u, v) for u, v in pts]
        for _ in range(2):
            j = [(x + rnd.uniform(-2.0, 2.0), y + rnd.uniform(-2.0, 2.0)) for x, y in q]
            dc.line(k(j), fill=GRAPHITE + (rnd.randint(70, 100),), width=int(K * (3 + 4 * wgt)), joint='curve')
    for _ in range(4):
        cx, cy, r = rnd.uniform(380, 640), rnd.uniform(300, 760), rnd.uniform(30, 70)
        dc.ellipse(k([(cx - r, cy - r * 0.6), (cx + r, cy + r * 0.6)]), fill=(90, 90, 100, 8))
    child = _grain(child.filter(ImageFilter.GaussianBlur(1.0 * K)), 1703, lo=0.5)

    # 2. A first try, rubbed out: the right lateral drawn straight through where the knot is.
    ghost = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0))
    dg = ImageDraw.Draw(ghost)
    dg.line(k([(445, 415), (771, 223)]), fill=(80, 80, 92, 34), width=3 * K)
    dg.line(k([(445, 431), (771, 239)]), fill=(80, 80, 92, 26), width=3 * K)
    for _ in range(40):
        x, y = rnd.uniform(480, 760), rnd.uniform(220, 420)
        dg.ellipse(k([(x, y), (x + rnd.uniform(2, 6), y + rnd.uniform(1, 3))]), fill=(150, 140, 120, 60))
    ghost = ghost.filter(ImageFilter.GaussianBlur(1.2 * K))

    # 3. Her drawing over it: the same pencil, sharpened, pressed firmly; drawn freehand, the long lines against a
    #    ruler (straight, but overshooting their corners); her careful capitals.
    rl = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(rl)
    INK = GRAPHITE + (215,)
    LW = 2.2

    def pen(pts, w=LW, amp=0.9, over=0.0, fill=INK, step=8.0):
        d.line(k(_wob(pts, rnd, amp, step, over)), fill=fill, width=max(1, int(round(w * K))), joint='curve')

    def ruled(a, b, w=LW, over=5.0):
        pen([a, b], w, amp=0.35, over=over + rnd.uniform(-2, 3), step=20)

    def arrow(a, b, size=9, fill=INK, w=LW, amp=0.5):
        ax, ay = a
        bx, by = b
        L = math.hypot(bx - ax, by - ay) or 1
        ux, uy = (bx - ax) / L, (by - ay) / L
        pen([a, b], w, amp=amp, fill=fill)
        for s in (1, -1):                                       # a hand's arrowhead: two strokes
            pen([(bx, by), (bx - ux * size + s * uy * size * 0.5, by - uy * size - s * ux * size * 0.5)], w, amp=0.2, fill=fill)

    def circ(c, r, w=LW, fill=INK, wob=0.8):
        a0 = rnd.uniform(0, 6.3)
        n = max(10, int(r * 0.9))
        pts = [(c[0] + (r + wob * math.sin(i * 0.7 + a0)) * math.cos(a0 + 2 * math.pi * i / n * 1.06),
                c[1] + (r + wob * math.sin(i * 0.7 + a0)) * math.sin(a0 + 2 * math.pi * i / n * 1.06)) for i in range(n + 1)]
        d.line(k(pts), fill=fill, width=max(1, int(round(w * K))), joint='curve')

    lab = []                                                   # her lettering, put on after the lines

    def lbl(xy, text, size, anc='l', kind='letter'):
        lab.append((T(*xy), text, fs(size), anc, kind))
    # The sheet's border and the bed, against a ruler.
    XF[:] = SHEET
    for a, b in (((22, 24), (1257, 22)), ((1257, 22), (1258, 873)), ((1258, 873), (23, 874)), ((23, 874), (22, 24))):
        ruled(a, b, w=2.4, over=4)
    XF[:] = PLAN
    for a, b in (((BED[0], BED[1]), (BED[2], BED[1])), ((BED[2], BED[1]), (BED[2], BED[3])),
                 ((BED[2], BED[3]), (BED[0], BED[3])), ((BED[0], BED[3]), (BED[0], BED[1]))):
        ruled(a, b, w=2.6, over=8)
    lbl((164, 92), 'BED 1', 21, 'l')
    arrow((475, 46), (BED[0] + 2, 46), 9)
    arrow((475, 46), (BED[2] - 2, 46), 9)
    ruled((BED[0], 36), (BED[0], 58), 1.6, 2)
    ruled((BED[2], 36), (BED[2], 58), 1.6, 2)
    lbl((475, 36), '2400', 16, 'm')
    arrow((128, 365), (128, BED[1] + 2), 9)
    arrow((128, 365), (128, BED[3] - 2), 9)
    lbl((106, 365), '2200', 16, 'm')

    # The channels: banks either side of each branch of the tree, the knot made a ring.
    kc, kr0, kr1 = P(0.2, -0.655), 30, 46
    trunk = _chaikin([P(u, v) for u, v in TREE[0][0]])
    trunk[0] = (trunk[0][0], 818)                               # down to the tank's top
    branches = {}
    for i in (2, 4, 6, 7, 9):
        pts = _chaikin([P(u, v) for u, v in TREE[i][0]])
        if i in (4, 6):
            pts = _clip_circle(pts, kc, kr1 + 1)
        branches[i] = pts
    for s in (-9, 9):
        pen(_offset(trunk, s), 2.4, amp=1.5, step=6.0)
    for i, pts in branches.items():
        for s in (-6, 6):
            pen(_offset(pts, s), 2.2, amp=1.4, step=6.0)
    for i in (3, 8):                                            # twigs: furrows, a single line
        pen(_chaikin([P(u, v) for u, v in TREE[i][0]]), 1.8, amp=0.8)
    for r in (kr0, kr1):
        circ(kc, r, 2.4, wob=1.1)
    for a0 in (40, 160, 280):                                   # flow round the loop
        a = math.radians(a0)
        px, py = kc[0] + 38 * math.cos(a), kc[1] + 38 * math.sin(a)
        tx, ty = -math.sin(a), math.cos(a)
        d.polygon(k([(px + tx * 7, py + ty * 7), (px - tx * 5 + math.cos(a) * 4, py - ty * 5 + math.sin(a) * 4),
                     (px - tx * 5 - math.cos(a) * 4, py - ty * 5 - math.sin(a) * 4)]), fill=INK)
    pen([(kc[0] + 30, kc[1] + 38), (690, 392)], 1.6, amp=0.4)
    lbl((694, 394), 'SETTLING LOOP', 16, 'l')

    def flow(pts, at=0.5):
        n = len(pts) - 1
        i = max(0, min(n - 1, int(n * at)))
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        L = math.hypot(bx - ax, by - ay) or 1
        ux, uy, mx, my = (bx - ax) / L, (by - ay) / L, (ax + bx) / 2, (ay + by) / 2
        d.polygon(k([(mx + ux * 8, my + uy * 8), (mx - ux * 6 - uy * 4.5, my - uy * 6 + ux * 4.5),
                     (mx - ux * 6 + uy * 4.5, my - uy * 6 - ux * 4.5)]), fill=INK)
    flow(list(reversed(trunk)), 0.6)
    flow(list(reversed(trunk)), 0.25)
    for i, pts in branches.items():
        flow(pts, 0.45)

    # Plants along the laterals, both sides: her little circles with a dot.
    def near_trunk(p):
        return min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in trunk) < 24
    for i, pts in branches.items():
        acc, nxt = 0.0, 26.0
        for a, b in zip(pts, pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            while acc + L >= nxt:
                t = (nxt - acc) / L
                x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
                for s in (-1, 1):
                    px, py = x + nx * 22 * s, y + ny * 22 * s
                    if (BED[0] + 12 < px < BED[2] - 12 and BED[1] + 12 < py < BED[3] - 12 and not near_trunk((px, py))
                            and math.hypot(px - kc[0], py - kc[1]) > kr1 + 14):
                        circ((px + rnd.uniform(-1, 1), py + rnd.uniform(-1, 1)), 6.5, 1.6, wob=0.6)
                        d.ellipse(k([(px - 1.6, py - 1.6), (px + 1.6, py + 1.6)]), fill=INK)
                nxt += 38
            acc += L

    # Sluices at the head of each lateral: a gate across it, lettered in a ring.
    def sluice(pts, at, label, lx, ly):
        (ax, ay), (bx, by) = pts[at], pts[at + 1]
        L = math.hypot(bx - ax, by - ay) or 1
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        cx, cy = ax, ay
        for s in (-1, 1):
            d.polygon(k([(cx, cy), (cx + nx * 11 * s - ux * 6, cy + ny * 11 * s - uy * 6),
                         (cx + nx * 11 * s + ux * 6, cy + ny * 11 * s + uy * 6)]), outline=INK, fill=GRAPHITE + (110,))
        circ((lx, ly), 12, 1.8)
        lbl((lx, ly + 1), label, 17, 'm')
    sluice(branches[2], 2, 'A', 410, 532)
    sluice(branches[4], 2, 'B', 470, 372)
    sluice(branches[9], 2, 'C', 500, 650)
    lbl((176, 470), 'BEANS', 17, 'l')
    lbl((300, 136), 'PEAS', 17, 'l')
    lbl((688, 204), 'KALE', 17, 'l')
    lbl((640, 630), 'POTATOES', 17, 'l')
    # The tank and its feed.
    for a, b in (((425, 818), (515, 818)), ((515, 818), (515, 860)), ((515, 860), (425, 860)), ((425, 860), (425, 818))):
        ruled(a, b, 2.4, 4)
    lbl((470, 840), 'TANK', 15, 'm')
    arrow((236, 846), (421, 846), 9)
    lbl((238, 828), 'FROM RING A MAIN', 14, 'l')
    lbl((198, 712), 'FALL 1 IN 40', 15, 'l')
    arrow((184, 730), (184, 694), 8)
    # The section mark across the main.
    for sx in (412, 500):
        pen([(sx, 764), (sx + 24 * (1 if sx < 450 else -1), 764)], 3.4, amp=0.2)
        arrow((sx, 764), (sx, 748), 7)
    lbl((402, 748), 'A', 15, 'm')
    lbl((510, 748), 'A', 15, 'm')

    # Her section A-A: deep and narrow, clay-lined.
    XF[:] = SHEET
    lbl((880, 62), 'SECTION A-A', 19, 'l')
    pen([(880, 74), (1032, 74)], 1.6, amp=0.3)
    gy, by_ = 140, 214
    pen([(905, gy), (1000, gy)], 2.2, amp=0.5)
    pen([(1100, gy), (1190, gy)], 2.2, amp=0.5)
    for off in (0, 11):
        pen([(1000 - off, gy), (1026 - off * 0.5, by_ + off), (1074 + off * 0.5, by_ + off), (1100 + off, gy)], 2.2, amp=0.5)
    for t in range(0, 290, 16):                                 # the soil, hatched
        x = 905 + t
        if 984 < x < 1112:
            continue
        pen([(x, gy + 10), (x + 20, gy + 30)], 1.2, amp=0.2, fill=GRAPHITE + (130,))
    pen([(1012, gy + 40), (1088, gy + 40)], 1.4, amp=0.3)       # the water line
    d.polygon(k([(1042, gy + 26), (1058, gy + 26), (1050, gy + 38)]), outline=INK, width=K)
    arrow((1050, 104), (1000, 104), 6, w=1.4)
    arrow((1050, 104), (1100, 104), 6, w=1.4)
    lbl((1050, 92), '300', 15, 'm')
    pen([(1094, by_ - 6), (1150, by_ + 12)], 1.4, amp=0.3)
    lbl((1154, by_ + 14), 'CLAY 50', 14, 'l')
    pen([(1076, gy + 40), (1150, gy + 40)], 1.4, amp=0.3)
    lbl((1154, gy + 40), 'WATER', 14, 'l')

    # Her notes.
    notes = ['NOTES', '1. MAIN FEED FROM TANK.', '2. SLUICES A B C: SHUT TWO,', '    WATER THE THIRD.', '3. THE KNOT IS A SETTLING',
             '    LOOP. SILT DROPS OUT', '    BEFORE THE KALE.', '4. WATER LITTLE, OFTEN.']
    for i, s in enumerate(notes):
        lbl((884, 400 + i * 30), s, 18 if i else 21, 'l')
    pen([(884, 414), (946, 414)], 1.6, amp=0.3)
    # Her title block.
    tb = (880, 690, 1250, 866)
    for a, b in (((tb[0], tb[1]), (tb[2], tb[1])), ((tb[2], tb[1]), (tb[2], tb[3])), ((tb[2], tb[3]), (tb[0], tb[3])),
                 ((tb[0], tb[3]), (tb[0], tb[1]))):
        ruled(a, b, 2.4, 4)
    for y in (734, 778, 822):
        ruled((tb[0], y), (tb[2], y), 1.6, 3)
    ruled((1094, 734), (1094, 778), 1.6, 2)
    ruled((1094, 822), (1094, 866), 1.6, 2)
    lbl((894, 712), 'IRRIGATION · BED 1', 21, 'l')
    lbl((894, 756), 'DRAWN   M. D.', 19, 'l')
    lbl((1106, 756), 'AGE 14', 19, 'l')
    lbl((894, 800), 'CHECKED', 19, 'l')
    lbl((894, 844), 'SCALE 1:20', 19, 'l')
    lbl((1106, 844), 'SHEET 1/1', 19, 'l')
    rig_working(pen, ruled, arrow, circ, lbl, XF, SHEET)
    for (x, y), s, size, anc, kind in lab:                      # her lettering: careful capitals, not quite level
        if kind == 'hand':                                      # (her running hand, for quick notes)
            _hand(rl, (x * K, y * K), s, _font(size * K, 'hand'), INK, rnd, jit=0.7 * K, rot=3.0, anchor=anc, track=0.98)
        else:
            _hand(rl, (x * K, y * K), s, _font(size * K, 'letter'), INK, rnd, jit=0.8 * K, rot=4.0, anchor=anc, track=1.07)
    rl = _grain(rl.filter(ImageFilter.GaussianBlur(0.5 * K)), 1704, lo=0.6)

    # 4. Beside her lines, the volunteer's blue pencil: a looser hand, the practical things.
    bl = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0))
    db = ImageDraw.Draw(bl)
    BL = BLUE + (230,)

    def bpen(pts, w=3.0, amp=0.7):
        db.line(k(_wob(pts, rnd, amp, 7.0)), fill=BL, width=max(1, int(round(w * K))), joint='curve')

    def barrow(pts, size=11):
        bpen(pts)
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        L = math.hypot(bx - ax, by - ay) or 1
        ux, uy = (bx - ax) / L, (by - ay) / L
        for s in (1, -1):
            bpen([(bx, by), (bx - ux * size + s * uy * size * 0.55, by - uy * size - s * ux * size * 0.55)], amp=0.2)

    def bnote(xy, s, size=26, rot=3.0):
        x, y = T(*xy)
        _hand(bl, (x * K, y * K), s, _font(fs(size) * K, 'ink'), BL, rnd, jit=0.7 * K, rot=rot)

    def tick(x, y, s=1.0):
        bpen([(x, y), (x + 8 * s, y + 11 * s), (x + 26 * s, y - 14 * s)], 3.2, amp=0.3)

    # The fall, under hers.
    XF[:] = PLAN
    bnote((196, 756), 'fall 1 in 100', 27)
    bnote((210, 786), 'or it scours', 22)
    barrow([(298, 742), (306, 734), (314, 726)], 9)
    # Levels, at the tank: a datum mark and the word.
    bnote((548, 806), 'levels!', 28)
    bpen([(548, 822), (628, 820)], 2.0)
    bpen([(552, 829), (622, 828)], 1.6)
    barrow([(542, 812), (530, 818), (520, 824)], 9)
    db.polygon(k([(640, 784), (660, 784), (650, 798)]), outline=BL, width=K * 2)
    bpen([(632, 799), (668, 799)], 2.0)
    # His section, drawn next to hers: shallower, wider, gentler sides.
    XF[:] = SHEET
    sy, sb = 286, 310
    bpen([(930, sy), (978, sy)], 2.2)
    bpen([(1124, sy), (1172, sy)], 2.2)
    bpen([(978, sy), (1008, sb), (1094, sb), (1124, sy)], 2.4)
    bpen([(994, sy + 12), (1108, sy + 12)], 1.6)
    barrow([(1138, sy - 8), (1126, sy - 36), (1102, sy - 52)], 10)
    bnote((934, 336), 'wider, shallower', 23)
    bnote((934, 362), 'sides 1 in 2', 21)
    # The knot: a tick, and what he thought of it.
    XF[:] = PLAN
    bnote((592, 112), 'The knot works!', 28)
    tick(780, 112)
    barrow([(640, 132), (628, 186), (616, 236)], 10)
    bnote((660, 146), '- E.V.', 23)
    # Checked.
    XF[:] = SHEET
    bnote((1004, 802), 'E. V.', 25)
    tick(1062, 796, 0.9)
    bl = _grain(bl.filter(ImageFilter.GaussianBlur(0.55 * K)), 1705, lo=0.55)

    # 5. Beside her working for the rig, the volunteer again, in red pencil this time: a margin note.
    rd = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0))
    RD = RED + (235,)
    for (x, y), t_, size in (((476, 714), 'Good eye.', 28), ((476, 750), 'Most of them never', 24),
                             ((476, 778), 'look behind the', 24), ((476, 806), 'bench.', 24), ((560, 838), '- E.V.', 22)):
        _hand(rd, (x * K, y * K), t_, _font(size * K, 'ink'), RD, rnd, jit=0.7 * K, rot=3.0)
    dr = ImageDraw.Draw(rd)
    dr.line(k(_wob([(468, 722), (432, 736), (396, 752)], rnd, 0.6, 7.0)), fill=RD, width=int(2.6 * K), joint='curve')
    for s_ in (1, -1):                                          # his arrow, to her pipes behind the bench
        dr.line(k([(396, 752), (396 + 10 + s_ * 2, 752 - 2 + s_ * 6)]), fill=RD, width=int(2.4 * K))
    rd = _grain(rd.filter(ImageFilter.GaussianBlur(0.55 * K)), 1706, lo=0.55)

    for lay in (child, ghost, rl, bl, rd):
        paper.alpha_composite(lay)
    return paper.convert('RGB').resize((W, H), Image.LANCZOS)


def rig_working(pen, ruled, arrow, circ, lbl, XF, SHEET):
    """Her working for Vance's test rig, along the bottom of her irrigation sheet (the expansion): the rig drawn from
    the front, as it stands, to scale: the bench, the three beds with their names, the levers A B C under them, and the
    three pipes traced from each lever up behind the bench to the bed it really feeds, each broken where it passes
    behind another, gone over twice; an arrow down from each spout. It depicts the rig; it doesn't spell out the
    answer (no notes: the crossing is only drawn)."""
    XF[:] = SHEET
    X = lambda x: 50 + (x - RIG[0]) * 165
    Z = lambda z: 834 - (z - RIG[4]) * 165
    top = Z(RIG[4])
    # The bench and its legs; the beds on it, their names.
    ruled((X(RIG[0]), top), (X(RIG[1]), top), 2.4, 5)
    ruled((X(RIG[0]), top + 5), (X(RIG[1]), top + 5), 1.6, 3)
    for x in (RIG[0] + 0.03, RIG[1] - 0.03):
        pen([(X(x), top + 5), (X(x), 866)], 1.8, amp=0.4)
    for i, (b0, b1) in enumerate(BEDS):
        for a, b in (((X(b0), Z(BED_TOP)), (X(b1), Z(BED_TOP))), ((X(b0), Z(BED_TOP)), (X(b0), top)),
                     ((X(b1), Z(BED_TOP)), (X(b1), top))):
            ruled(a, b, 2.0, 2)
        lbl(((X(b0) + X(b1)) / 2, (Z(BED_TOP) + top) / 2 + 1), '%d  %s' % (i + 1, BED_NAMES[i].replace(' ', '')), 14, 'm')
    lv = Z(SLUICE_PIVOT[1]) + 3
    for name, x, bed in SLUICES:
        circ((X(x), lv), 11, 1.8)
        lbl((X(x), lv + 1), name, 15, 'm')
    # The pipes: up behind the bench (riser; hidden by the beds below their rims), across (run), forward and down over
    # the bed (drop: in front of them all).
    paths, depth = {}, {}
    for name, x, bed in SLUICES:
        sx = SPOUT_X[bed - 1]
        paths[name] = [(X(x), Z(BED_TOP) - 1), (X(x), Z(RUN_Z[name])), (X(sx), Z(RUN_Z[name])), (X(sx), Z(MOUTH[1]))]
        depth[name] = (RISE_Y[name], RISE_Y[name], MOUTH[0])

    def cross(a, b, c, d):
        """Where segment ab crosses cd (both axis-aligned): the parameter along ab, or None."""
        (ax, ay), (bx, by), (cx, cy), (dx, dy) = a, b, c, d
        if ax == bx and cy == dy:                                     # ab vertical, cd horizontal
            if min(cx, dx) < ax < max(cx, dx) and min(ay, by) < cy < max(ay, by):
                return (cy - ay) / (by - ay)
        if ay == by and cx == dx:                                     # ab horizontal, cd vertical
            if min(cy, dy) < ay < max(cy, dy) and min(ax, bx) < cx < max(ax, bx):
                return (cx - ax) / (bx - ax)
        return None
    for n_, pts in paths.items():
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            L_ = math.hypot(b[0] - a[0], b[1] - a[1])
            cuts = []
            for m_, q in paths.items():
                if m_ == n_:
                    continue
                for j, (c, d_) in enumerate(zip(q, q[1:])):
                    t = cross(a, b, c, d_)
                    if t is not None and depth[m_][j] < depth[n_][i]:     # the other one is in front: a break in this
                        cuts.append(t)
            g = 8.0 / L_
            pieces, t0 = [], 0.0
            for t in sorted(cuts):
                pieces.append((t0, t - g))
                t0 = t + g
            pieces.append((t0, 1.0))
            for p0, p1 in pieces:
                if p1 <= p0:
                    continue
                pa = (a[0] + (b[0] - a[0]) * p0, a[1] + (b[1] - a[1]) * p0)
                pb = (a[0] + (b[0] - a[0]) * p1, a[1] + (b[1] - a[1]) * p1)
                for k_ in range(2):                                       # traced: gone over
                    if i == 2 and p1 == 1.0 and k_ == 0:
                        arrow(pa, (pb[0], pb[1] + 6), 8, w=2.4)
                    else:
                        pen([pa, pb], 2.4 if k_ == 0 else 1.6, amp=0.6)
        mx, my = pts[-1]
        for dz in (16, 24):                                           # drops, falling
            pen([(mx, my + dz), (mx, my + dz + 4)], 1.6, amp=0.2)
    lbl((246, 704), 'TEST RIG (FROM THE FRONT)', 14)


CARD_A = (('M. D.', '14', 'WORKS DEPT., RING A', 'WATER AND IRRIGATION', 'E. VANCE', 'BY THE PUPIL',
           'RESIDENTIAL ACCESS, RING A', '(WORKS GATE SEALED)'), '0417', 1730)
CARD_B = (('R. ABEL', '13', 'KITCHENS, RING A', 'COOK (JUNIOR)', 'M. PRICE', 'BY THE PUPIL', 'KITCHEN DOOR, RING A', ''),
          '0409', 1731)
CARD_C = (('T. ORME', '13', 'STORES, RING A', 'STOREKEEPING', 'E. VANCE', 'BY THE PUPIL', 'STORES YARD, RING A', ''),
          '0412', 1732)


def make_card(w, h, entries, number, seed, stamp=True, sign=True, pupil='Mara D.'):
    """A placement card: printed in green, filled in on a typewriter, signed by the pupil who applied and by her
    sponsor, stamped. entries: name, age, placed with, trade, sponsor, application, report via (two lines).
    Drawn at 768 x 480."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(seed)
    W, H = 768, 480
    card = _paper(W, H, (224, 210, 172), seed, amp=0.08, edge=0.16, edge_px=24)
    pr = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(pr)
    GREEN = (34, 72, 54, 235)
    d.rectangle((22, 14, 746, 18), fill=GREEN)
    d.text((48, 34), 'REFUGE WORKS DEPARTMENT · APPRENTICE PLACEMENTS', font=_font(18, 'carlito'), fill=GREEN, anchor='lm')
    d.text((48, 78), 'PLACEMENT', font=_font(58, 'carlito'), fill=GREEN, anchor='lm')
    d.text((628, 76), 'No.', font=_font(22, 'carlito'), fill=GREEN, anchor='rm')
    d.rectangle((22, 108, 746, 110), fill=GREEN)
    rows = [('NAME', 134), ('PLACED WITH', 172), ('TRADE', 210), ('SPONSOR', 248), ('APPLICATION', 286), ('REPORT VIA', 324)]
    for s, y in rows:
        d.text((30, y), s, font=_font(19, 'carlito'), fill=GREEN, anchor='lm')
        for x in range(178, 742 if s != 'NAME' else 500, 7):
            d.point((x, y + 15), fill=GREEN)
            d.point((x + 1, y + 15), fill=GREEN)
    d.text((520, 134), 'AGE', font=_font(19, 'carlito'), fill=GREEN, anchor='lm')
    for x in range(566, 742, 7):
        d.point((x, 149), fill=GREEN)
        d.point((x + 1, 149), fill=GREEN)
    for x in range(178, 742, 7):
        d.point((x, 373), fill=GREEN)
    d.text((30, 448), "Pupil", font=_font(17, 'carlito-reg'), fill=GREEN, anchor='lm')
    d.text((300, 448), "Sponsor", font=_font(17, 'carlito-reg'), fill=GREEN, anchor='lm')
    for x0, x1 in ((74, 284), (360, 560)):
        for x in range(x0, x1, 7):
            d.point((x, 458), fill=GREEN)
    card.alpha_composite(pr)
    ty = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    _typed(ty, (640, 76), number, _font(30, 'mono'), rnd, ink=(150, 40, 32))
    name, age, placed, trade, sponsor, appl, via, via2 = entries
    f = _font(28, 'mono')
    for s, (x, y) in ((name, (186, 132)), (age, (572, 132)), (placed, (186, 170)), (trade, (186, 208)), (sponsor, (186, 246)),
                      (appl, (186, 284)), (via, (186, 322)), (via2, (186, 358))):
        if s:
            _typed(ty, (x + rnd.uniform(-2, 2), y), s, f, rnd)
    card.alpha_composite(ty.filter(ImageFilter.GaussianBlur(0.5)))
    ink = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if pupil:                                                  # hers in pencil, careful and joined
        _hand(ink, (84, 438), pupil, _font(36, 'hand'), (54, 54, 64, 225), rnd, jit=0.6, rot=3, track=0.96)
    if sign:
        _hand(ink, (370, 436), 'E. Vance', _font(38, 'ink'), (28, 34, 70, 230), rnd, jit=0.8, rot=5)
    card.alpha_composite(ink.filter(ImageFilter.GaussianBlur(0.45)))
    if stamp:
        st = Image.new('RGBA', (204, 94), (0, 0, 0, 0))
        ds = ImageDraw.Draw(st)
        V = (104, 52, 130, 215)
        ds.rounded_rectangle((4, 4, 200, 90), radius=11, outline=V, width=5)
        ds.rounded_rectangle((11, 11, 193, 83), radius=7, outline=V, width=2)
        ds.text((102, 34), 'ACCEPTED', font=_font(34, 'carlito'), fill=V, anchor='mm')
        ds.text((102, 60), 'WORKS DEPT · RING A', font=_font(16, 'carlito'), fill=V, anchor='mm')
        ds.text((102, 76), 'P.A. 316', font=_font(16, 'carlito'), fill=V, anchor='mm')
        st = _grain(st, seed + 7, lo=0.3).rotate(7, resample=Image.BICUBIC, expand=True)
        card.alpha_composite(st, (W - st.width - 14, H - st.height - 6))
    dd = ImageDraw.Draw(card)
    dd.ellipse((14, 58, 34, 78), fill=(36, 30, 24))                       # a punched hole
    dd.rectangle((686, 0, 712, 6), fill=(120, 76, 40, 255))                # a paper clip's rust
    out = card.convert('RGB')
    return out if (w, h) == (W, H) else out.resize((w, h), Image.LANCZOS)


def make_soilcrack(w, h, seed):
    """Dry soil, shrunk and cracked into plates (Voronoi cells): pale crusted tops, dark gaps, plate edges lifted."""
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(seed)
    pts = rng.random((46, 2)) * [w, h]
    pts = np.concatenate([pts + [dx * w, dy * h] for dx in (-1, 0, 1) for dy in (-1, 0, 1)])     # tiles
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx[..., None] - pts[:, 0]) ** 2 + (yy[..., None] - pts[:, 1]) ** 2)
    dist.sort(axis=2)
    gap = dist[..., 1] - dist[..., 0]
    n = _noise(w, h, 6, seed)
    base = np.array([112, 92, 70], float) * (0.82 + 0.3 * n)[..., None]
    lift = np.clip(1 - gap / 9.0, 0, 1)[..., None]                   # edges curl up, catch the light
    a = base * (1 + 0.16 * lift)
    crack = np.clip((3.2 + 1.5 * n - gap) / 1.6, 0, 1)[..., None]
    a = a * (1 - crack) + np.array([30, 22, 16]) * crack
    a *= (1 - 0.1 * (rng.random((h, w)) > 0.9))[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGB')


def make_atlas(path):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(1720)
    img = Image.new('RGB', (ATLAS, ATLAS), (60, 56, 50))
    img.paste(make_drawing(), CELLS['drawing'][:2])
    img.paste(make_card(768, 480, *CARD_A), CELLS['card'][:2])
    img.paste(make_card(384, 240, *CARD_B, sign=False, pupil='R. Abel'), CELLS['cardB'][:2])
    img.paste(make_card(384, 240, *CARD_C, pupil='T. Orme'), CELLS['cardC'][:2])
    ink = (30, 28, 24)

    # The drawer's label: a buff card in a brass holder, stencilled.
    x0, y0, x1, y1 = CELLS['placements']
    lb = _paper(x1 - x0, y1 - y0, (206, 192, 152), 1733, amp=0.1, edge=0.2, edge_px=10)
    ImageDraw.Draw(lb).text(((x1 - x0) / 2, (y1 - y0) / 2 + 3), 'PLACEMENTS', font=_font(70, 'carlito'), fill=ink + (240,), anchor='mm')
    img.paste(lb.convert('RGB'), (x0, y0))

    # Signs (legible at 9 m).
    x0, y0, x1, y1 = CELLS['sign_shop']
    s = Image.new('RGB', (x1 - x0, y1 - y0), (42, 68, 52))
    ds = ImageDraw.Draw(s)
    ds.rectangle((6, 6, x1 - x0 - 7, y1 - y0 - 7), outline=(214, 204, 172), width=6)
    ds.text(((x1 - x0) / 2, 82), 'WORKSHOP', font=_font(112, 'carlito'), fill=(222, 210, 176), anchor='mm')
    ds.text(((x1 - x0) / 2, 158), 'MAINTENANCE \u00b7 VOLUNTEERS', font=_font(32, 'carlito'), fill=(214, 204, 172), anchor='mm')
    img.paste(_fade(s, 1734, k=0.12, dust=0.18), (x0, y0))
    # The stair door's sign: the way on, through the homes (the Works' own gate is sealed); the Works' small cog mark.
    x0, y0, x1, y1 = CELLS['sign_works']
    sw, sh = x1 - x0, y1 - y0
    s = Image.new('RGB', (sw, sh), (26, 40, 66))
    ds = ImageDraw.Draw(s)
    cream = (226, 218, 194)
    ds.rounded_rectangle((8, 8, sw - 9, sh - 9), radius=18, outline=cream, width=7)
    size = 74
    while _font(size, 'carlito').getlength('RESIDENTIAL ACCESS') > 590:
        size -= 2
    ds.text((34, 66), 'RESIDENTIAL ACCESS', font=_font(size, 'carlito'), fill=cream, anchor='lm')
    ds.text((34, 148), 'RING A', font=_font(84, 'carlito'), fill=cream, anchor='lm')
    ra = _font(84, 'carlito').getlength('RING A')
    mx, my = 34 + ra + 64, 150                                  # the Works mark: a cog in a ring, WORKS beside it
    for t in range(10):
        a = t * math.pi / 5
        ds.polygon([(mx + 25 * math.cos(a + o), my + 25 * math.sin(a + o)) for o in (-0.16, 0.16)] +
                   [(mx + 33 * math.cos(a + o), my + 33 * math.sin(a + o)) for o in (0.11, -0.11)], fill=cream)
    ds.ellipse((mx - 27, my - 27, mx + 27, my + 27), fill=cream)
    ds.ellipse((mx - 11, my - 11, mx + 11, my + 11), fill=(26, 40, 66))
    ds.text((mx + 44, my + 2), 'WORKS', font=_font(28, 'carlito'), fill=cream, anchor='lm')
    ax, ay = 700, 104                                           # the arrow, up
    ds.polygon([(ax, ay - 76), (ax + 46, ay - 18), (ax + 16, ay - 18), (ax + 16, ay + 74), (ax - 16, ay + 74), (ax - 16, ay - 18),
                (ax - 46, ay - 18)], fill=cream)
    for xx in (26, sw - 26):
        ds.ellipse((xx - 7, sh // 2 - 7, xx + 7, sh // 2 + 7), fill=(150, 150, 140))
    s = _fade(s, 1735, k=0.1, dust=0.15)
    ds = ImageDraw.Draw(s)
    for _ in range(26):                                        # enamel chipped to black iron
        cx, cy, r = rnd.uniform(0, sw), rnd.choice((rnd.uniform(0, 18), rnd.uniform(sh - 18, sh))), rnd.uniform(2, 7)
        ds.ellipse((cx - r, cy - r, cx + r, cy + r * 0.7), fill=(16, 16, 18))
    img.paste(s, (x0, y0))

    # Dry soil, cracked into plates: the trays' surface.
    x0, y0, x1, y1 = CELLS['soilcrack']
    img.paste(make_soilcrack(x1 - x0, y1 - y0, 1745), (x0, y0))

    # The volunteer's notice, in ink.
    x0, y0, x1, y1 = CELLS['rota']
    r_ = _paper(x1 - x0, y1 - y0, (214, 206, 182), 1736, amp=0.08, edge=0.2, edge_px=12)
    for i, (t, sz) in enumerate((('Workshop', 30), ('Tues & Thurs', 22), ('E. Vance', 22), ("Kettle's always on.", 20),
                                 ('Ask before the iron.', 20))):
        _hand(r_, (14, 24 + i * 32), t, _font(sz, 'ink'), (26, 34, 72, 235), rnd, jit=0.6, rot=3)
    ImageDraw.Draw(r_).ellipse((120, 2, 134, 14), fill=(150, 40, 30))  # a drawing pin
    img.paste(r_.convert('RGB'), (x0, y0))

    # The radio's dial.
    x0, y0, x1, y1 = CELLS['radio']
    rd = Image.new('RGB', (x1 - x0, y1 - y0), (60, 36, 22))
    dd = ImageDraw.Draw(rd)
    dd.rounded_rectangle((10, 8, 246, 70), radius=8, fill=(206, 186, 140))
    for i in range(31):
        x = 24 + i * 7
        dd.line((x, 16, x, 22 if i % 5 else 28), fill=ink, width=1)
    for i, st_ in enumerate(('HOME', 'RING A', 'RING B', 'WORKS')):
        dd.text((34 + i * 58, 48), st_, font=_font(13, 'carlito'), fill=ink, anchor='mm')
    dd.line((150, 12, 146, 66), fill=(150, 30, 20), width=2)
    for i in range(9):                                         # the grille
        dd.line((14, 80 + i * 5, 242, 80 + i * 5), fill=(40, 24, 14), width=2)
    img.paste(rd, (x0, y0))

    # The tool board: brown pegboard; tool shapes painted in pale paint; the missing tools' shapes show bare.
    x0, y0, x1, y1 = CELLS['toolboard']
    tb = Image.new('RGB', (x1 - x0, y1 - y0), (92, 66, 42))
    a = np.asarray(tb).astype(float) * (0.88 + 0.22 * _noise(x1 - x0, y1 - y0, 8, 1737))[..., None]
    tb = Image.fromarray(np.clip(a, 0, 255).astype('uint8'))
    dt = ImageDraw.Draw(tb)
    for yy in range(8, y1 - y0, 14):
        for xx in range(8, x1 - x0, 14):
            dt.ellipse((xx - 2, yy - 2, xx + 2, yy + 2), fill=(30, 20, 12))
    su, sv = (x1 - x0) / (BOARD[1] - BOARD[0]), (y1 - y0) / (BOARD[3] - BOARD[2])
    for kind, present, parts in tool_parts():
        for poly, _m, _t in parts:
            pts = [(u * su, (y1 - y0) - v * sv) for u, v in poly]
            dt.polygon(pts, fill=(200, 190, 156), outline=(214, 206, 176))
            dt.line(pts + [pts[0]], fill=(222, 214, 186), width=3)
    img.paste(_fade(tb, 1738, k=0.1, dust=0.18), (x0, y0))

    # The bean chart: crayon, on sugar paper.
    x0, y0, x1, y1 = CELLS['chart']
    ch = _paper(x1 - x0, y1 - y0, (176, 186, 196), 1739, amp=0.1, edge=0.2, edge_px=16)
    dc = ImageDraw.Draw(ch)
    _hand(ch, (256, 34), 'OUR BEANS: HOW TALL?', _font(34, 'letter-bold'), (150, 40, 40, 230), rnd, jit=1.2, rot=5, anchor='m')
    dc.line((48, 70, 48, 330, 496, 330), fill=(40, 40, 50), width=3)
    for i in range(6):
        y = 330 - i * 50
        dc.line((40, y, 48, y), fill=(40, 40, 50), width=2)
        dc.text((36, y), str(i * 5), font=_font(14, 'letter'), fill=(40, 40, 50), anchor='rm')
    cols = [(150, 60, 50), (60, 110, 60), (50, 70, 140), (190, 140, 40), (120, 60, 120), (60, 120, 130)]
    heights = (210, 150, 240, 95, 180, 60, 30, 130, 0, 205, 20, 0)
    for i, hgt in enumerate(heights):
        x = 64 + i * 36
        if hgt:
            c = cols[i % len(cols)]
            for _ in range(22):
                xx = x + rnd.uniform(0, 22)
                dc.line((xx, 328, xx + rnd.uniform(-2, 2), 328 - hgt + rnd.uniform(-4, 4)), fill=c, width=3)
        _hand(ch, (x + 12, 350), NAMES[3 + i][:4], _font(14, 'letter-bold'), (40, 40, 50, 230), rnd, jit=0.6, rot=8, anchor='m')
    img.paste(ch.convert('RGB'), (x0, y0))

    # Papers in the drawer: a bean diary in pencil, a typed seed list, a long typed list.
    x0, y0, x1, y1 = CELLS['paper1']
    p1 = _paper(x1 - x0, y1 - y0, (222, 218, 204), 1740, amp=0.06)
    dp = ImageDraw.Draw(p1)
    for yy in range(34, 256, 12):
        dp.line((8, yy, 248, yy), fill=(150, 170, 200), width=1)
    dp.line((30, 0, 30, 256), fill=(200, 120, 120), width=1)
    _hand(p1, (40, 22), 'My bean', _font(20, 'letter-bold'), (60, 60, 70, 220), rnd, rot=6)
    for i in range(14):
        yy = 44 + i * 12
        pts = [(36 + j * 7, yy - 3 + 2 * math.sin(j * 1.7 + i)) for j in range(rnd.randint(12, 30))]
        dp.line(pts, fill=(70, 70, 80), width=1)
    dp.ellipse((180, 200, 214, 222), outline=(70, 70, 80), width=2)
    dp.line((197, 200, 200, 172, 214, 160), fill=(70, 70, 80), width=2)
    img.paste(p1.convert('RGB'), (x0, y0))
    x0, y0, x1, y1 = CELLS['paper2']
    p2 = _paper(x1 - x0, y1 - y0, (214, 208, 190), 1741, amp=0.06)
    dp = ImageDraw.Draw(p2)
    dp.text((128, 20), 'SEED STOCK', font=_font(18, 'mono'), fill=ink, anchor='mm')
    for i, s_ in enumerate(('RUNNER BEAN  2', 'KALE         1', 'PEA          3', 'POTATO (SET) 12', 'CRESS        4',
                            'TOMATO       0', 'ONION        1', 'BEET         2', 'LETTUCE      0', 'SQUASH       1',
                            'CHARD        2', 'BROAD BEAN   0', 'LEEK         1', 'RADISH       5')):
        dp.text((16, 44 + i * 14), s_, font=_font(12, 'mono-reg'), fill=ink, anchor='lm')
    img.paste(p2.convert('RGB'), (x0, y0))
    x0, y0, x1, y1 = CELLS['seedlist']
    p3 = _paper(x1 - x0, y1 - y0, (206, 196, 170), 1742, amp=0.08, edge=0.2, edge_px=10)
    dp = ImageDraw.Draw(p3)
    dp.text((20, 20), 'SEED TRAYS: WATERING ROTA (CLASS 4 - 6)', font=_font(16, 'mono'), fill=ink, anchor='lm')
    for i in range(6):
        y = 44 + i * 14
        dp.line((20, y + 6, 490, y + 6), fill=(140, 130, 110), width=1)
        dp.text((20, y), ', '.join(NAMES[3 + i * 6:9 + i * 6]), font=_font(11, 'mono-reg'), fill=ink, anchor='lm')
    img.paste(p3.convert('RGB'), (x0, y0))

    # Name tags: white plastic or lolly sticks, in pencil and marker; hers in neat capitals.
    for i, nm in enumerate(NAMES):
        x0, y0, x1, y1 = CELLS['tag%d' % i]
        wood = i % 3 == 1
        t = _paper(128, 40, (196, 168, 120) if wood else (228, 224, 210), 1750 + i, amp=0.12, edge=0.25, edge_px=6)
        if nm == 'M. D.':
            _hand(t, (64, 21), nm, _font(24, 'letter'), (40, 42, 54, 240), rnd, jit=0.4, rot=1.5, anchor='m', track=1.1)
            ImageDraw.Draw(t).line((34, 33, 94, 33), fill=(40, 42, 54), width=1)
        else:
            col = rnd.choice(((60, 60, 70, 230), (24, 24, 30, 245), (40, 60, 120, 235), (130, 40, 40, 230)))
            _hand(t, (64, 21), nm, _font(rnd.choice((22, 24, 26)), rnd.choice(('letter-bold', 'hand', 'letter'))), col, rnd,
                  jit=1.2, rot=8, anchor='m')
        ImageDraw.Draw(t).rectangle((0, 0, 127, 39), outline=(120, 110, 90), width=1)
        img.paste(t.convert('RGB'), (x0, y0))

    make_rig_cells(img, rnd)
    for name, rgb in SWATCH.items():
        x0, y0, x1, y1 = CELLS[name]
        ImageDraw.Draw(img).rectangle((x0, y0, x1 - 1, y1 - 1), fill=rgb)
    img.save(path, optimize=True)


def make_rig_cells(img, rnd):
    """The test rig's pictures (the expansion): Vance's card in his ink, the beds' name cards, the levers' enamel
    letters, the sight glass's scale."""
    from PIL import ImageDraw
    INKV = (26, 34, 72, 238)
    x0, y0, x1, y1 = CELLS['rigcard']
    c = _paper(x1 - x0, y1 - y0, (222, 212, 178), 1770, amp=0.08, edge=0.18, edge_px=18)
    for (x, y), t, size in (((26, 58), 'APPRENTICE TEST:', 46), ((26, 128), 'WATER BED 1 ONLY.', 50), ((26, 198), 'ONE TANK.', 50)):
        _hand(c, (x, y), t, _font(size, 'ink'), INKV, rnd, jit=0.8, rot=3.5)
    _hand(c, (486, 262), '- E.V.', _font(34, 'ink'), INKV, rnd, jit=0.6, rot=3, anchor='r')
    ImageDraw.Draw(c).line((30, 156, 440, 152), fill=INKV, width=3)               # WATER BED 1 ONLY, underlined
    img.paste(c.convert('RGB'), (x0, y0))
    for i, nm in enumerate(BED_NAMES):
        x0, y0, x1, y1 = CELLS['bed%d' % (i + 1)]
        c = _paper(x1 - x0, y1 - y0, (214, 204, 172), 1771 + i, amp=0.1, edge=0.2, edge_px=8)
        _hand(c, ((x1 - x0) / 2, 31), nm, _font(42, 'ink'), INKV, rnd, jit=0.6, rot=3, anchor='m')
        ImageDraw.Draw(c).rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), outline=(120, 108, 84), width=2)
        img.paste(c.convert('RGB'), (x0, y0))
    for i, ch in enumerate('ABC'):
        x0, y0, x1, y1 = CELLS['pl' + ch]
        from PIL import Image
        e = Image.new('RGB', (x1 - x0, y1 - y0), (60, 56, 50))
        de = ImageDraw.Draw(e)
        de.rounded_rectangle((1, 1, 62, 62), radius=12, fill=(26, 40, 66), outline=(214, 206, 180), width=4)
        de.text((32, 34), ch, font=_font(44, 'carlito'), fill=(226, 218, 194), anchor='mm')
        img.paste(_fade(e, 1774 + i, k=0.08, dust=0.12), (x0, y0))
    x0, y0, x1, y1 = CELLS['sightscale']
    d = ImageDraw.Draw(img)
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(206, 200, 180))
    for k in range(13):
        y = y0 + 6 + k * (y1 - y0 - 12) / 12
        d.line((x0 + 2, y, x0 + (26 if k % 4 == 0 else 14), y), fill=(24, 22, 20), width=3 if k % 4 == 0 else 2)


def make_textures():
    os.makedirs(TEX, exist_ok=True)
    make_atlas(os.path.join(TEX, 'dl17_atlas.png'))


# =====================================================================================================================
# The tool board's tools: shared by the painted shapes (texture) and the hung tools (mesh). Board coordinates in metres:
# u from the board's left edge, v up from its bottom edge.
# =====================================================================================================================
def _rect(u0, v0, u1, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def _rrect(cx, cy, w, h, ang):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def tool_parts():
    """[(kind, present, [(polygon, 'metal'|'wood', thickness)])]."""
    T = []
    T.append(('saw', True, [([(0.10, 0.70), (0.58, 0.655), (0.58, 0.80), (0.10, 0.775)], 'metal', 0.003),
                            (_rect(0.58, 0.64, 0.71, 0.82), 'wood', 0.024)]))
    T.append(('hammer', True, [(_rect(0.80, 0.38, 0.83, 0.74), 'wood', 0.024), (_rect(0.75, 0.74, 0.88, 0.79), 'metal', 0.03)]))
    T.append(('hammer2', False, [(_rect(0.955, 0.45, 0.978, 0.70), 'wood', 0.02), (_rect(0.915, 0.70, 1.02, 0.74), 'metal', 0.025)]))
    for i, L in enumerate((0.14, 0.17, 0.20, 0.23, 0.26)):
        u = 1.12 + i * 0.07
        T.append(('spanner%d' % i, i in (0, 2, 4), [(_rect(u - 0.011, 0.88 - L, u + 0.011, 0.88), 'metal', 0.006),
                                                       (_rect(u - 0.024, 0.88, u + 0.024, 0.92), 'metal', 0.006),
                                                       (_rect(u - 0.02, 0.88 - L - 0.035, u + 0.02, 0.88 - L), 'metal', 0.006)]))
    for i in range(6):
        u = 1.52 + i * 0.056
        T.append(('driver%d' % i, i != 3, [(_rect(u - 0.016, 0.72, u + 0.016, 0.84), 'wood', 0.03),
                                           (_rect(u - 0.0045, 0.58 - 0.012 * i, u + 0.0045, 0.72), 'metal', 0.009)]))
    T.append(('pliers', True, [(_rrect(1.92, 0.62, 0.022, 0.24, 0.12), 'metal', 0.012), (_rrect(1.96, 0.62, 0.022, 0.24, -0.12), 'metal', 0.012)]))
    T.append(('snips', False, [(_rrect(2.06, 0.62, 0.026, 0.26, 0.15), 'metal', 0.012), (_rrect(2.11, 0.62, 0.026, 0.26, -0.15), 'metal', 0.012)]))
    T.append(('square', True, [(_rect(2.27, 0.45, 2.295, 0.86), 'metal', 0.004), (_rect(2.265, 0.82, 2.46, 0.87), 'wood', 0.022)]))
    T.append(('mallet', True, [(_rect(2.56, 0.70, 2.70, 0.80), 'wood', 0.07), (_rect(2.615, 0.38, 2.645, 0.70), 'wood', 0.025)]))
    T.append(('brace', False, [(_rect(0.16, 0.30, 0.56, 0.33), 'metal', 0.015), (_rect(0.16, 0.16, 0.19, 0.33), 'metal', 0.015),
                               (_rect(0.53, 0.30, 0.56, 0.44), 'metal', 0.015), (_rect(0.10, 0.12, 0.25, 0.16), 'wood', 0.04)]))
    for i in range(4):
        u = 0.98 + i * 0.1
        T.append(('chisel%d' % i, i in (0, 1), [(_rect(u - 0.018, 0.24, u + 0.018, 0.36), 'wood', 0.03),
                                                 (_rect(u - 0.006 - 0.003 * i, 0.10, u + 0.006 + 0.003 * i, 0.24), 'metal', 0.006)]))
    for i in range(3):
        u = 1.58 + i * 0.09
        T.append(('file%d' % i, i != 1, [(_rect(u - 0.012, 0.10, u + 0.012, 0.30), 'metal', 0.006),
                                          (_rect(u - 0.016, 0.30, u + 0.016, 0.40), 'wood', 0.028)]))
    T.append(('clamp', True, [(_rect(2.24, 0.10, 2.27, 0.36), 'metal', 0.02), (_rect(2.24, 0.33, 2.42, 0.36), 'metal', 0.02),
                              (_rect(2.24, 0.10, 2.36, 0.13), 'metal', 0.02), (_rect(2.38, 0.14, 2.40, 0.33), 'metal', 0.012)]))
    T.append(('clamp2', False, [(_rect(2.52, 0.10, 2.55, 0.36), 'metal', 0.02), (_rect(2.52, 0.33, 2.70, 0.36), 'metal', 0.02),
                                (_rect(2.52, 0.10, 2.64, 0.13), 'metal', 0.02)]))
    return T


# =====================================================================================================================
# Mesh building (as dl14's MB)
# =====================================================================================================================
class MB:
    """One object being built: faces tagged by material name. Faces flagged 'flat' keep the winding they were built
    with (decals, which are one-sided in the game); the rest have their normals recalculated outward."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.flat = self.bm.faces.layers.int.new('flat')
        self.names = []
        self.log = []                         # every vertex a primitive made, in order (bmesh reuses freed slots,
                                              # so vertex indices are not creation order)

    def __call__(self, name):                 # voice_props' target protocol: name -> slot index, and .bm
        return self.m(name)

    def m(self, name):
        if name not in self.names:
            self.names.append(name)
        return self.names.index(name)

    def mark(self):
        return len(self.log)

    def since(self, n0):
        return self.log[n0:]

    def _log(self, vs):
        self.log.extend(vs)
        return vs

    def xform(self, n0, M):
        for v in self.since(n0):
            v.co = M @ v.co

    def paint(self, verts, cell):
        uv = cell_mid(cell)
        faces = set()
        for v in verts:
            faces.update(v.link_faces)
        for f in faces:
            for lp in f.loops:
                lp[self.uv].uv = uv

    def box(self, mt, x0, x1, y0, y1, z0, z1, rot=None, cell=None):
        vs = self._log(add_box(self.bm, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), mat=self.m(mt), rot=rot))
        if cell:
            self.paint(vs, cell)
        return vs

    def sbox(self, cell, x0, x1, y0, y1, z0, z1):
        return self.box('Att17Atlas', x0, x1, y0, y1, z0, z1, cell=cell)

    def cyl(self, mt, a, b, r, r2=None, seg=10, cell=None):
        vs = self._log(add_cyl(self.bm, a, b, r, r2, mat=self.m(mt), seg=seg))
        if cell:
            self.paint(vs, cell)
        return vs

    def scyl(self, cell, a, b, r, r2=None, seg=10):
        return self.cyl('Att17Atlas', a, b, r, r2, seg=seg, cell=cell)

    def sphere(self, mt, c, r, seg=10, scale=(1, 1, 1), cell=None):
        vs = self._log(add_sphere(self.bm, c, r, mat=self.m(mt), seg=seg, scale=scale))
        if cell:
            self.paint(vs, cell)
        return vs

    def torus(self, mt, c, axis, R, r, seg=20, rseg=6, cell=None):
        vs = self._log(add_torus(self.bm, c, axis, R, r, mat=self.m(mt), seg=seg, rseg=rseg))
        if cell:
            self.paint(vs, cell)
        return vs

    def face(self, mt, corners, uvs=None, flat=True):
        f = self.bm.faces.new(self._log([self.bm.verts.new(c) for c in corners]))
        f.material_index = self.m(mt)
        f[self.flat] = 1 if flat else 0
        if uvs:
            for lp, t in zip(f.loops, uvs):
                lp[self.uv].uv = t
        return f

    def decal(self, x0, x1, z0, z1, y, cell):
        """A picture on a wall, facing the camera (-y)."""
        u0, v0, u1, v1 = cell_uv(cell)
        return self.face('Att17Atlas', [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def sheet(self, cell, cx, cy, z, w, d, ang=0.0, edge=0.0):
        """A sheet lying flat, facing up, its picture upright as seen from the camera side (its top toward +y)."""
        u0, v0, u1, v1 = cell_uv(cell)
        c, s = math.cos(ang), math.sin(ang)
        P = lambda x, y: (cx + x * c - y * s, cy + x * s + y * c, z)
        self.face('Att17Atlas', [P(-w / 2, -d / 2), P(w / 2, -d / 2), P(w / 2, d / 2), P(-w / 2, d / 2)],
                  [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
        if edge:                                                 # the sheet's (or card's) thickness, in paper
            n0 = self.mark()
            self.sbox('sw_paper', -w / 2, w / 2, -d / 2, d / 2, -edge, -0.0002)
            self.xform(n0, Matrix.Translation((cx, cy, z)) @ Matrix.Rotation(ang, 4, 'Z'))

    def tbox(self, mt, x0, x1, y0, y1, z0, z1, cells):
        """A box with an atlas cell per face: cells = {'-y','+y','-x','+x','+z','-z', 'all'}."""
        P = {
            '-y': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            '+y': [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
            '-x': [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
            '+x': [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
            '+z': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
            '-z': [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
        }
        n0 = self.mark()
        for k, pts in P.items():
            c = cells.get(k, cells.get('all'))
            u0, v0, u1, v1 = cell_uv(c)
            if c.startswith('sw_'):
                u0 = u1 = (u0 + u1) / 2
                v0 = v1 = (v0 + v1) / 2
            self.face(mt, pts, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
        return n0

    def prism_xz(self, mt, pts, y0, y1, cell=None):
        """A polygon in (x, z), extruded from y0 to y1 (closed; normals recalculated)."""
        bm = self.bm
        f = [bm.verts.new((x, y0, z)) for x, z in pts]
        b = [bm.verts.new((x, y1, z)) for x, z in pts]
        fs = [bm.faces.new(f), bm.faces.new(list(reversed(b)))]
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            fs.append(bm.faces.new((f[j], f[i], b[i], b[j])))
        for fc in fs:
            fc.material_index = self.m(mt)
        if cell:
            self.paint(f + b, cell)
        return self._log(f + b)

    def prism_yz(self, mt, pts, x0, x1, cell=None):
        bm = self.bm
        f = [bm.verts.new((x0, y, z)) for y, z in pts]
        b = [bm.verts.new((x1, y, z)) for y, z in pts]
        fs = [bm.faces.new(f), bm.faces.new(list(reversed(b)))]
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            fs.append(bm.faces.new((f[j], f[i], b[i], b[j])))
        for fc in fs:
            fc.material_index = self.m(mt)
        if cell:
            self.paint(f + b, cell)
        return self._log(f + b)

    def obj(self, name, coll, origin=(0.0, 0.0, 0.0), sharp=35):
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if not f[self.flat]])
        o = Vector(origin)
        if o.length:
            bmesh.ops.translate(bm, verts=bm.verts, vec=-o)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for n in self.names:
            me.materials.append(mat(n))
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.set_sharp_from_angle(angle=math.radians(sharp))
        ob = bpy.data.objects.new(name, me)
        ob.location = o
        coll.objects.link(ob)
        return ob


def TR(x, y, z, yaw=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(yaw, 4, 'Z')


# =====================================================================================================================
# The room's shell
# =====================================================================================================================
def holed_wall(B, x0, x1, y0, y1, z0, z1, holes, split=1.0, lower='WinDado', upper='WorkPlaster'):
    """A wall slab with rectangular holes (hx0, hx1, hz0, hz1), as boxes over the grid the holes make."""
    xs = sorted({x0, x1} | {h[0] for h in holes if x0 < h[0] < x1} | {h[1] for h in holes if x0 < h[1] < x1})
    zs = sorted({z0, z1, split} | {h[2] for h in holes if z0 < h[2] < z1} | {h[3] for h in holes if z0 < h[3] < z1})
    zs = [z for z in zs if z0 <= z <= z1]
    for za, zb in zip(zs, zs[1:]):
        run = None
        for xa, xb in zip(xs, xs[1:]):
            cx, cz = (xa + xb) / 2, (za + zb) / 2
            solid = not any(h[0] < cx < h[1] and h[2] < cz < h[3] for h in holes)
            if solid:
                run = (run[0], xb) if run else (xa, xb)
            if (not solid or xb == xs[-1]) and run:
                B.box(lower if cz < split else upper, run[0], run[1], y0, y1, za, zb)
                run = None


def wall_runs(holes, z0, z1, xa, xb):
    cuts = sorted((h[0], h[1]) for h in holes if h[2] < z1 and h[3] > z0)
    runs, x = [], xa
    for a, b in cuts:
        if a > x:
            runs.append((x, min(a, xb)))
        x = max(x, b)
    if x < xb:
        runs.append((x, xb))
    return [(a, b) for a, b in runs if b - a > 0.02]


def build_shell(B):
    holes = [(WINDOW[0], WINDOW[1], WINDOW[2], WINDOW[3])]
    wx0 = LWALL[1]
    holed_wall(B, wx0, END_X, WALL_Y, WALL_Y2, 0.0, CEIL, holes)
    # Floor: timber boards along x (their joints as dark lines), ceiling, beams.
    B.box('CrateWood', X0, X1, FRONT_Y, WALL_Y2, -0.2, 0.0)
    u0, v0, u1, v1 = cell_uv('sw_seam')
    su = ((u0 + u1) / 2, (v0 + v1) / 2)
    y = FRONT_Y + 0.07
    k = 0
    while y < WALL_Y:
        xa = wx0 if y > DOORWAY[0] and y < DOORWAY[1] else wx0
        B.face('Att17Atlas', [(xa, y - 0.0025, 0.0006), (END_X, y - 0.0025, 0.0006), (END_X, y + 0.0025, 0.0006),
                              (xa, y + 0.0025, 0.0006)], [su] * 4)
        x = wx0 + 0.4 + (k % 3) * 0.9                            # butt joints, staggered
        while x < END_X - 0.2:
            B.face('Att17Atlas', [(x - 0.002, y + 0.003, 0.0006), (x + 0.002, y + 0.003, 0.0006), (x + 0.002, y + 0.137, 0.0006),
                                  (x - 0.002, y + 0.137, 0.0006)], [su] * 4)
            x += 2.7
        y += 0.14
        k += 1
    B.box('WorkPlaster', X0, X1, -1.0, WALL_Y2, CEIL, CEIL + 0.15)
    for x in (281.6, 284.0, 286.4, 288.8, 291.2, 293.6):
        B.box('PigeonWood', x - 0.07, x + 0.07, -1.0, WALL_Y, CEIL - 0.16, CEIL)
    B.box('PigeonWood', wx0, END_X, WALL_Y - 0.1, WALL_Y, CEIL - 0.12, CEIL)                   # wall plate
    # The left wall, with the doorway in from DL-16; its lining and architrave.
    ya, yb, hd = DOORWAY
    for (y0_, y1_, z0_, z1_) in ((-1.0, ya, 0.0, CEIL), (yb, WALL_Y2, 0.0, CEIL), (ya, yb, hd, CEIL)):
        for za, zb, mt in ((z0_, min(z1_, 1.0), 'WinDado'), (max(z0_, 1.0), z1_, 'WorkPlaster')):
            if zb > za:
                B.box(mt, LWALL[0], LWALL[1], y0_, y1_, za, zb)
    B.box('PigeonWood', LWALL[0], LWALL[1] + 0.02, ya - 0.01, ya + 0.02, 0.0, hd)
    B.box('PigeonWood', LWALL[0], LWALL[1] + 0.02, yb - 0.02, yb + 0.01, 0.0, hd)
    B.box('PigeonWood', LWALL[0], LWALL[1] + 0.02, ya - 0.01, yb + 0.01, hd - 0.03, hd)
    for (y0_, y1_, z0_, z1_) in ((ya - 0.08, ya - 0.01, 0.0, hd + 0.08), (yb + 0.01, yb + 0.08, 0.0, hd + 0.08), (ya - 0.08, yb + 0.08, hd, hd + 0.08)):
        B.box('PigeonWood', LWALL[1], LWALL[1] + 0.025, y0_, y1_, z0_, z1_)
    B.box('WornIron', LWALL[0] - 0.01, LWALL[1] + 0.01, ya, yb, 0.0, 0.012)                    # threshold strip
    # The right end wall, the stair door's opening in it (DOOR17), and above the ceiling the stairwell's side.
    dy0, dy1, dhd = DOOR17
    for (y0_, y1_, z0_, z1_) in ((-1.0, dy0, 0.0, CEIL), (dy1, WALL_Y2, 0.0, CEIL), (dy0, dy1, dhd, CEIL)):
        for za, zb, mt in ((z0_, min(z1_, 1.0), 'WinDado'), (max(z0_, 1.0), z1_, 'WorkPlaster')):
            if zb > za:
                B.box(mt, END_X, X1, y0_, y1_, za, zb)
    B.box('WorkPlaster', END_X, X1, WELL[2], WELL[4], CEIL + 0.15, WELL[5])
    # Skirting, dado rail, conduit along the back wall.
    for a, b in wall_runs(holes, 0.0, 0.12, wx0, END_X):
        B.box('PigeonWood', a, b, WALL_Y - 0.02, WALL_Y, 0.0, 0.12)
    for a, b in wall_runs(holes, 0.98, 1.03, wx0, END_X):
        B.box('PigeonWood', a, b, WALL_Y - 0.03, WALL_Y, 0.98, 1.03)
    for y0_, y1_ in ((-1.0, DOOR17[0] - 0.08), (DOOR17[1] + 0.08, WALL_Y)):
        B.box('PigeonWood', END_X - 0.02, END_X, y0_, y1_, 0.0, 0.12)
    B.box('PigeonWood', LWALL[1], LWALL[1] + 0.02, yb + 0.08, WALL_Y, 0.0, 0.12)
    B.cyl('WornIron', (wx0, WALL_Y - 0.04, 2.72), (END_X, WALL_Y - 0.04, 2.72), 0.016, seg=8)
    for x in (281.2, 284.2, 289.0, 292.4):
        B.box('WornIron', x - 0.05, x + 0.05, WALL_Y - 0.07, WALL_Y, 2.67, 2.77)
    B.cyl('WornIron', (284.2, WALL_Y - 0.04, 2.67), (284.2, WALL_Y - 0.04, 1.06), 0.014, seg=8)   # down to the bench's sockets
    B.box('WornIron', 284.13, 284.35, WALL_Y - 0.06, WALL_Y, 0.96, 1.06)
    B.sbox('sw_white', 284.16, 284.21, WALL_Y - 0.065, WALL_Y - 0.06, 0.99, 1.03)
    B.sbox('sw_white', 284.26, 284.31, WALL_Y - 0.065, WALL_Y - 0.06, 0.99, 1.03)
    B.cyl('WornIron', (292.4, WALL_Y - 0.04, 2.67), (292.4, WALL_Y - 0.04, 1.45), 0.014, seg=8)   # to the grow-lamp's timer
    B.box('WornIron', 292.32, 292.48, WALL_Y - 0.08, WALL_Y, 1.30, 1.46)
    B.cyl('Att17Atlas', (292.4, WALL_Y - 0.08, 1.38), (292.4, WALL_Y - 0.09, 1.38), 0.045, seg=14, cell='sw_cream')
    B.box('WornIron', 280.35, 280.42, WALL_Y - 0.03, WALL_Y, 1.3, 1.42)                    # the light switch by the door


def build_entry(B):
    """By the door: the volunteer's dust coat and cap on hooks, the WORKSHOP sign over them."""
    B.box('PigeonWood', 280.25, 281.0, WALL_Y - 0.03, WALL_Y, 1.66, 1.75)
    for x in (280.4, 280.62, 280.84):
        B.cyl('WornIron', (x, WALL_Y - 0.03, 1.71), (x, WALL_Y - 0.09, 1.73), 0.006, seg=6)
        B.cyl('WornIron', (x, WALL_Y - 0.09, 1.73), (x, WALL_Y - 0.1, 1.77), 0.006, seg=6)
    # The coat: shoulders on the hook, hanging to the knee; sleeves at its sides; its pockets.
    cx = 280.62
    B.prism_xz('WornStrap', [(cx - 0.2, 1.68), (cx - 0.24, 1.64), (cx - 0.26, 0.86), (cx + 0.26, 0.86), (cx + 0.24, 1.64),
                                 (cx + 0.2, 1.68), (cx + 0.04, 1.73), (cx - 0.04, 1.73)], WALL_Y - 0.14, WALL_Y - 0.035)
    for s in (-1, 1):
        B.prism_xz('WornStrap', [(cx + s * 0.22, 1.62), (cx + s * 0.27, 1.6), (cx + s * 0.29, 1.08), (cx + s * 0.22, 1.08)],
                   WALL_Y - 0.15, WALL_Y - 0.05)
    for s in (-1, 1):
        B.box('WornStrap', cx + s * 0.13 - 0.07, cx + s * 0.13 + 0.07, WALL_Y - 0.147, WALL_Y - 0.14, 1.06, 1.2)
        B.prism_xz('WornStrap', [(cx, 1.70), (cx + s * 0.13, 1.69), (cx + s * 0.04, 1.42)], WALL_Y - 0.15, WALL_Y - 0.14)   # lapels
    for z_ in (1.36, 1.22, 1.08, 0.94):
        B.sphere('Att17Atlas', (cx + 0.035, WALL_Y - 0.143, z_), 0.011, seg=6, scale=(1, 0.5, 1), cell='sw_bakelite')
    B.box('Att17Atlas', cx - 0.004, cx + 0.004, WALL_Y - 0.146, WALL_Y - 0.14, 0.86, 1.42, cell='sw_seam')
    B.cyl('Att17Atlas', (cx + 0.11, WALL_Y - 0.15, 1.42), (cx + 0.11, WALL_Y - 0.15, 1.56), 0.005, seg=5, cell='sw_pencil')
    # the cap on the next hook
    B.sphere('Att17Atlas', (280.4, WALL_Y - 0.09, 1.7), 0.09, seg=10, scale=(1, 1, 0.45), cell='sw_cloth')
    B.box('Att17Atlas', 280.33, 280.47, WALL_Y - 0.2, WALL_Y - 0.12, 1.66, 1.675, cell='sw_cloth')
    # The sign.
    B.box('PigeonWood', 280.27, 281.33, WALL_Y - 0.025, WALL_Y, 2.26, 2.565)
    B.decal(280.30, 281.30, 2.28, 2.53, WALL_Y - 0.026, 'sign_shop')


def name_tag(B, x, y, zs, idx, yaw=0.0, tall=0.07):
    """A plant label stuck in the soil: a stake and a flag with a child's name, facing the camera (turned by yaw)."""
    n0 = B.mark()
    wood = idx % 3 == 1
    B.sbox('sw_lolly' if wood else 'sw_tagwhite', -0.006, 0.006, -0.0015, 0.0015, -0.03, tall - 0.02)
    B.tbox('Att17Atlas', -0.034, 0.034, -0.0016, 0.0016, tall - 0.0213, tall, {'-y': 'tag%d' % idx, 'all': 'sw_lolly' if wood else 'sw_tagwhite'})
    B.xform(n0, TR(x, y, zs, yaw))


def dead_plant(B, x, y, zs, rnd, n=2, h=0.12, cell='sw_straw', droop=1.0):
    """Dead stalks: each leans, bends over and down; its withered leaves hang from it, shrivelled narrow."""
    for _ in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        hh = h * rnd.uniform(0.6, 1.1)
        p0 = Vector((x + rnd.uniform(-0.012, 0.012), y + rnd.uniform(-0.012, 0.012), zs))
        p1 = p0 + Vector((0.15 * hh * math.cos(a), 0.15 * hh * math.sin(a), hh))
        p2 = p1 + Vector((hh * 0.6 * droop * math.cos(a), hh * 0.6 * droop * math.sin(a), -hh * 0.55 * droop))
        B.scyl(cell, p0, p1, 0.0035, 0.0025, seg=4)
        B.scyl(cell, p1, p2, 0.0025, 0.0015, seg=3)
        for p, s, side in ((p2, 1.0, 0.0), (p0.lerp(p1, 0.7), 0.75, rnd.choice((-1.0, 1.0)))):
            n0 = B.mark()
            B.sbox(cell, 0.0, 0.026 * s, -0.004 * s, 0.004 * s, -0.0015, 0.0)
            B.xform(n0, Matrix.Translation(p) @ Matrix.Rotation(a + side * rnd.uniform(1.2, 1.9), 4, 'Z') @
                    Matrix.Rotation(rnd.uniform(0.9, 1.4), 4, 'Y') @ Matrix.Rotation(rnd.uniform(-0.6, 0.6), 4, 'X'))


def pot(B, x, y, z, r, h, rnd, tag=None, plant='dead', seg=12, soil='sw_crust', tag_yaw=None):
    """A clay pot: tapered body, rolled rim, soil dried pale; a dead plant (or none) and a name tag."""
    B.cyl('PotClay', (x, y, z), (x, y, z + h * 0.86), r * 0.74, r * 0.97, seg=seg)
    B.torus('PotClay', (x, y, z + h * 0.92), (0, 0, 1), r * 0.99, h * 0.075, seg=seg, rseg=4)
    zs = z + h * 0.9
    B.scyl(soil, (x, y, z + h * 0.8), (x, y, zs), r * 0.93, r * 0.97, seg=seg)
    if plant == 'dead':
        dead_plant(B, x, y, zs, rnd, n=rnd.randint(1, 3), h=rnd.uniform(0.08, 0.14) * min(1.3, r / 0.06))
    if tag is not None:
        a = -math.pi / 2 + rnd.uniform(-0.5, 0.5)
        name_tag(B, x + r * 0.62 * math.cos(a), y + r * 0.62 * math.sin(a), zs,
                 tag, rnd.uniform(-0.3, 0.3) if tag_yaw is None else tag_yaw)
    return zs


def seed_tray(B, cx, cy, z, rnd, tag, w=0.36, d=0.24, h=0.06, yaw=0.0, wood='CrateWood', soil='sw_soil_dark', dead=None):
    """A wooden seed tray, its soil dried and cracked, rows of shrivelled seedlings, a name tag and the name on its front."""
    n0 = B.mark()
    t = 0.012
    B.box(wood, -w / 2, w / 2, -d / 2, -d / 2 + t, 0.0, h)
    B.box(wood, -w / 2, w / 2, d / 2 - t, d / 2, 0.0, h)
    B.box(wood, -w / 2, -w / 2 + t, -d / 2 + t, d / 2 - t, 0.0, h)
    B.box(wood, w / 2 - t, w / 2, -d / 2 + t, d / 2 - t, 0.0, h)
    B.box(wood, -w / 2 + t, w / 2 - t, -d / 2 + t, d / 2 - t, 0.0, 0.01)
    zs = h * 0.8
    B.sbox(soil, -w / 2 + t, w / 2 - t, -d / 2 + t, d / 2 - t, 0.01, zs - 0.004)
    B.tbox('Att17Atlas', -w / 2 + t + 0.005, w / 2 - t - 0.005, -d / 2 + t + 0.005, d / 2 - t - 0.005, zs - 0.012, zs,
           {'+z': 'soilcrack', 'all': 'sw_crust'})
    B.decal(-0.055, 0.055, h * 0.25, h * 0.25 + 0.11 * 40 / 128, -d / 2 - 0.0008, 'tag%d' % tag)
    B.xform(n0, TR(cx, cy, z, yaw))
    rows, cols = 3, 6
    for i in range(rows):
        for j in range(cols):
            if rnd.random() < 0.18:
                continue
            lx, ly = -w / 2 + 0.04 + j * (w - 0.08) / (cols - 1), -d / 2 + 0.05 + i * (d - 0.1) / (rows - 1)
            px, py = cx + lx * math.cos(yaw) - ly * math.sin(yaw), cy + lx * math.sin(yaw) + ly * math.cos(yaw)
            dead_plant(B, px, py, z + zs, rnd, n=1, h=rnd.uniform(0.04, 0.08), cell=dead or rnd.choice(('sw_straw', 'sw_shrivel', 'sw_deadleaf')),
                       droop=rnd.uniform(0.8, 1.5))
    lx, ly = w / 2 - 0.04, -d / 2 + 0.03
    name_tag(B, cx + lx * math.cos(yaw) - ly * math.sin(yaw), cy + lx * math.sin(yaw) + ly * math.cos(yaw), z + zs, tag,
             yaw + rnd.uniform(-0.2, 0.2), tall=0.06)


class Names:
    """Hands out the children's names, one per tray, pot or jar (Mara's is kept for the living shoot)."""

    def __init__(self):
        self.i = 3

    def __call__(self):
        k = self.i
        self.i = 3 + (self.i - 3 + 1) % (len(NAMES) - 3)
        return k


def build_shelf(B, rnd, names):
    """The tall slatted shelf of seedling trays and pots, a name on each; nearly all of them dead and dry."""
    x0, x1, y0, y1 = SHELF
    for x in (x0 + 0.02, (x0 + x1) / 2, x1 - 0.02):
        for y in (y0 + 0.02, y1 - 0.02):
            B.box('PigeonWood', x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.0, SHELF_TOP)
    for z in SHELF_LEVELS + (SHELF_TOP - 0.02,):
        for k in range(4):
            ys = y0 + 0.01 + k * (y1 - y0 - 0.02) / 4
            B.box('PigeonWood', x0, x1, ys + 0.008, ys + (y1 - y0 - 0.02) / 4 - 0.008, z - 0.022, z)
        B.box('PigeonWood', x0, x1, y0, y0 + 0.02, z - 0.06, z - 0.022)
    B.box('PigeonWood', x0 + 0.02, x1 - 0.02, y1 - 0.01, y1, 1.0, 1.04)                       # a diagonal brace's stand-in
    cy = (y0 + y1) / 2
    for li, z in enumerate(SHELF_LEVELS):
        x = x0 + 0.06
        while x < x1 - 0.12:
            if li == 0:                                       # on the floor shelf: big pots and a stack of empty trays
                if x < x0 + 0.5:
                    for k in range(5):
                        n0 = B.mark()
                        t = 0.012
                        B.box('CrateWood', -0.18, 0.18, -0.12, 0.12, 0.0, 0.01)
                        B.box('CrateWood', -0.18, 0.18, -0.12, -0.108, 0.0, 0.05)
                        B.box('CrateWood', -0.18, 0.18, 0.108, 0.12, 0.0, 0.05)
                        B.box('CrateWood', -0.18, -0.168, -0.12, 0.12, 0.0, 0.05)
                        B.box('CrateWood', 0.168, 0.18, -0.12, 0.12, 0.0, 0.05)
                        B.xform(n0, TR(x + 0.18, cy, z + k * 0.05, rnd.uniform(-0.05, 0.05)))
                    x += 0.42
                else:
                    r = rnd.uniform(0.1, 0.12)
                    if x + 2 * r > x1 - 0.04:
                        break
                    pot(B, x + r, cy + rnd.uniform(-0.03, 0.03), z, r, r * 1.6, rnd, tag=names(), plant='dead')
                    x += 2 * r + 0.04
                continue
            if rnd.random() < 0.55 and x + 0.36 < x1 - 0.02 and li < 4:
                seed_tray(B, x + 0.18, cy + rnd.uniform(-0.02, 0.02), z, rnd, names(), yaw=rnd.uniform(-0.05, 0.05))
                x += 0.38 + rnd.uniform(0.0, 0.03)
            else:
                r = rnd.uniform(0.045, 0.07)
                if x + 2 * r > x1 - 0.03:
                    break
                pot(B, x + r, cy + rnd.uniform(-0.08, 0.08), z, r, r * 1.5, rnd, tag=names(), plant='dead' if rnd.random() < 0.85 else None)
                x += 2 * r + rnd.uniform(0.02, 0.05)


def build_bench(B, rnd, names):
    """The bench along the back wall, the plan chest under it (all but its lowest drawer), its cupboard, its shelf."""
    x0, x1, y0, y1, top = BENCH
    B.box('PupilWood', x0, x1, y0, y1, top - 0.06, top)
    B.face('Att17Atlas', [(x0, 0.95, top + 0.0005), (x1, 0.95, top + 0.0005), (x1, 0.954, top + 0.0005), (x0, 0.954, top + 0.0005)],
           [cell_mid('sw_seam')] * 4)
    for x in (x0 + 0.04, x1 - 0.04):
        for y in (y0 + 0.05, y1 - 0.05):
            B.box('PigeonWood', x - 0.035, x + 0.035, y - 0.035, y + 0.035, 0.0, top - 0.06)
    B.box('PigeonWood', x0 + 0.04, x1 - 0.04, y1 - 0.07, y1 - 0.03, top - 0.16, top - 0.06)      # back rail
    B.box('PigeonWood', x0 + 0.04, x1 - 0.04, y0 + 0.02, y0 + 0.05, top - 0.12, top - 0.06)      # front rail
    # Left of the chest: a low shelf, with a toolbox, tins, a sack, a crate of empty pots.
    sx0, sx1 = x0 + 0.07, CHEST[0]
    B.box('PigeonWood', sx0, sx1, y0 + 0.05, y1 - 0.05, 0.12, 0.145)
    B.box('PigeonWood', sx0, sx1, y0 + 0.05, y0 + 0.07, 0.06, 0.12)
    B.box('DepotGreen', 283.0, 283.5, 0.78, 1.0, 0.145, 0.33)
    B.box('DepotGreen', 282.99, 283.51, 0.77, 1.01, 0.33, 0.35)
    B.cyl('WornIron', (283.15, 0.89, 0.35), (283.15, 0.89, 0.39), 0.008, seg=6)
    B.cyl('WornIron', (283.35, 0.89, 0.35), (283.35, 0.89, 0.39), 0.008, seg=6)
    B.cyl('WornIron', (283.15, 0.89, 0.39), (283.35, 0.89, 0.39), 0.01, seg=6)
    for k, (tx, ty) in enumerate(((283.68, 0.85), (283.86, 0.9), (283.75, 1.08))):
        B.scyl('sw_tin', (tx, ty, 0.145), (tx, ty, 0.3), 0.075, seg=12)
        B.scyl(('sw_green', 'sw_red', 'sw_cream')[k], (tx, ty, 0.3), (tx, ty, 0.302), 0.07, seg=12)
    sack(B, (284.35, 1.0, 0.145), (0.4, 0.3, 0.32))
    for k in range(5):                                        # empty pots, nested
        B.cyl('PotClay', (284.85, 0.88, 0.145 + k * 0.035), (284.85, 0.88, 0.145 + k * 0.035 + 0.13), 0.06, 0.085, seg=12)
    # The plan chest: carcass, shallow drawers above the big one (the big one is Att17Drawer).
    c0, c1 = CHEST
    B.box('PigeonWood', c0, c0 + 0.08, CHEST_FRONT, y1 - 0.02, 0.06, top - 0.06)
    B.box('PigeonWood', c1 - 0.08, c1, CHEST_FRONT, y1 - 0.02, 0.06, top - 0.06)
    B.box('PigeonWood', c0, c1, y1 - 0.04, y1 - 0.02, 0.06, top - 0.06)
    B.box('DarkMetal', c0 + 0.03, c1 - 0.03, CHEST_FRONT + 0.03, y1 - 0.04, 0.0, 0.1)            # the plinth, set back
    B.box('PigeonWood', c0, c1, CHEST_FRONT, CHEST_FRONT + 0.03, 0.06, 0.115)                     # the bottom rail
    B.box('PigeonWood', c0 + 0.08, c1 - 0.08, CHEST_FRONT + 0.01, y1 - 0.04, 0.10, 0.115)        # the floor the drawer runs on
    B.box('PigeonWood', c0, c1, CHEST_FRONT, CHEST_FRONT + 0.03, 0.482, 0.502)                    # the rail over it
    B.box('PigeonWood', c0 + 0.08, c1 - 0.08, CHEST_FRONT + 0.03, y1 - 0.04, 0.482, 0.49)        # dust board
    pitch = (top - 0.06 - 0.505) / 4
    for k in range(4):
        z0 = 0.505 + k * pitch
        B.box('PigeonWood', DRAWER[0], DRAWER[1], DRAWER[2], CHEST_FRONT, z0 + 0.004, z0 + pitch - 0.004)
        for hx in (285.62, 286.38):
            B.box('HandledBrass', hx - 0.04, hx + 0.04, DRAWER[2] - 0.012, DRAWER[2], z0 + pitch * 0.32, z0 + pitch * 0.5)
        B.box('HandledBrass', 285.95, 286.05, DRAWER[2] - 0.003, DRAWER[2], z0 + pitch * 0.25, z0 + pitch * 0.75)
        B.decal(285.957, 286.043, z0 + pitch * 0.3, z0 + pitch * 0.7, DRAWER[2] - 0.0035, ('sw_label', 'sw_paper', 'sw_label', 'sw_paper')[k])
    # Right of the chest: a cupboard; then knee room, where the stool is.
    q0, q1 = c1, 287.5
    B.box('PigeonWood', q1 - 0.03, q1, CHEST_FRONT, y1 - 0.02, 0.0, top - 0.06)
    B.box('PigeonWood', q0, q1, y1 - 0.04, y1 - 0.02, 0.0, top - 0.06)
    B.box('PigeonWood', q0 + 0.01, q1 - 0.01, CHEST_FRONT - 0.02, CHEST_FRONT, 0.08, top - 0.08)
    for z0_, z1_ in ((0.14, 0.42), (0.48, 0.74)):
        B.box('PigeonWood', q0 + 0.06, q1 - 0.06, CHEST_FRONT - 0.03, CHEST_FRONT - 0.02, z0_, z1_)
    B.sphere('HandledBrass', (q1 - 0.07, CHEST_FRONT - 0.04, 0.6), 0.018, seg=8)
    B.box('DarkMetal', q0, q1, CHEST_FRONT + 0.01, y1 - 0.04, 0.0, 0.07)
    # The bench's shelf (right), with bean jars on it, and tins.
    s0, s1, sz = 286.0, 288.55, 1.55
    B.box('PigeonWood', s0, s1, 1.06, WALL_Y, sz - 0.025, sz)
    for bx in (s0 + 0.1, s1 - 0.1):
        B.prism_yz('WornIron', [(WALL_Y, sz - 0.025), (WALL_Y, sz - 0.2), (WALL_Y - 0.02, sz - 0.2), (1.08, sz - 0.025)], bx - 0.006, bx + 0.006)
    for k in range(7):
        bean_jar(B, s0 + 0.12 + k * 0.17, 1.17 + rnd.uniform(-0.02, 0.02), sz, rnd, names())
    for k, (tx, cell) in enumerate(((287.42, 'sw_tin'), (287.58, 'sw_red'), (287.74, 'sw_tin'))):
        B.scyl(cell, (tx, 1.18, sz), (tx, 1.18, sz + 0.13 + 0.02 * k), 0.055, seg=12)
    B.sbox('sw_label', 287.9, 288.4, 1.08, 1.28, sz, sz + 0.16)


def sack(B, base, size, lying=False):
    """A sack of compost: a soft, slumped bag, its neck folded over (not xformed: rounded_box isn't logged)."""
    x, y, z = base
    w, d, h = size
    d17.rounded_box((w, d, h), (x, y, z + h / 2), p=2.6, cuts=5, taper=lambda c: 1.0 - 0.12 * max(c, 0.0),
                    dents=((0.012, 6.0),), seed=x, bm=B.bm, mat=B.m('ParcelBrown'))
    if not lying:
        B.box('ParcelBrown', x - w * 0.3, x + w * 0.3, y - d * 0.15, y + d * 0.2, z + h * 0.92, z + h * 1.02)


def bean_jar(B, x, y, z, rnd, tag):
    """A jam jar gone dry (see-through, the game's Window glass): blotting paper rolled inside, a dry tide-mark at its
    foot; a bean against the glass, shrivelled dark, its root a dry thread; most with a dead stalk bent out over the
    rim; a name on it."""
    r, h = 0.034, 0.11
    B.cyl('Window', (x, y, z), (x, y, z + h), r, seg=12)
    B.torus('Window', (x, y, z + h - 0.004), (0, 0, 1), r * 0.95, 0.004, seg=12, rseg=4)
    B.scyl('sw_paper', (x, y, z + 0.004), (x, y, z + h * 0.82), r * 0.8, seg=10)
    B.scyl('sw_label', (x, y, z + 0.004), (x, y, z + 0.02), r * 0.81, seg=10)
    a = -math.pi / 2 + rnd.uniform(-0.45, 0.45)                 # the bean, between paper and glass, to the front
    bx, by, bz = x + r * 0.89 * math.cos(a), y + r * 0.89 * math.sin(a), z + rnd.uniform(0.05, 0.066)
    n0 = B.mark()
    B.sphere('Att17Atlas', (0, 0, 0), 0.011, seg=8, scale=(1.0, 0.36, 0.66), cell='sw_beandead')
    B.xform(n0, Matrix.Translation((bx, by, bz)) @ Matrix.Rotation(a + math.pi / 2, 4, 'Z') @ Matrix.Rotation(rnd.uniform(-0.6, 0.6), 4, 'Y'))
    B.scyl('sw_shrivel', (bx, by, bz - 0.004), (bx + rnd.uniform(-0.006, 0.006), by, bz - 0.022), 0.0013, 0.0008, seg=3)
    B.scyl('sw_shrivel', (bx + 0.002, by, bz - 0.02), (bx + rnd.uniform(-0.01, 0.01), by, bz - 0.04), 0.0009, 0.0006, seg=3)
    if rnd.random() < 0.7:                                    # its shoot, long dead, bent over the rim
        a2 = rnd.uniform(-2.4, -0.7)
        p0 = Vector((bx, by, bz + 0.005))
        p1 = Vector((x + 0.6 * r * math.cos(a2), y + 0.6 * r * math.sin(a2), z + h + rnd.uniform(0.02, 0.05)))
        p2 = p1 + Vector((0.05 * math.cos(a2), 0.05 * math.sin(a2), -0.06))
        B.scyl('sw_shrivel', p0, p1, 0.0022, 0.0018, seg=4)
        B.scyl('sw_shrivel', p1, p2, 0.0018, 0.0012, seg=3)
        n0 = B.mark()
        B.sbox('sw_deadleaf', -0.012, 0.012, -0.005, 0.005, -0.002, 0.0)
        B.xform(n0, Matrix.Translation(p2) @ Matrix.Rotation(a2, 4, 'Z') @ Matrix.Rotation(0.9, 4, 'X'))
    B.decal(x - 0.03, x + 0.03, z + 0.01, z + 0.01 + 0.06 * 40 / 128, y - r - 0.0015, 'tag%d' % tag)


def build_bench_top(B, rnd):
    """What's on the bench: vice, soldering iron, lamp, a tap in bits, pencils, glasses on a notebook, radio, mug,
    kettle; soil crumbs where the tray went over the edge."""
    top = BENCH[4]
    # The vice at the left end, a length of copper pipe in its jaws.
    B.box('WornIron', 283.02, 283.32, 0.635, 0.72, top, top + 0.1)
    B.box('WornIron', 283.02, 283.32, 0.585, 0.62, top - 0.06, top + 0.1)
    for vx in (283.07, 283.27):
        B.cyl('WornIron', (vx, 0.6, top - 0.04), (vx, 0.85, top - 0.04), 0.012, seg=8)
    B.cyl('WornIron', (283.17, 0.585, top + 0.03), (283.17, 0.47, top + 0.03), 0.012, seg=8)
    B.cyl('WornIron', (283.07, 0.475, top + 0.03), (283.27, 0.475, top + 0.03), 0.007, seg=6)
    for vx in (283.06, 283.28):
        B.sphere('WornIron', (vx, 0.475, top + 0.03), 0.013, seg=8)
    B.cyl('Copper', (282.9, 0.627, top + 0.07), (283.55, 0.627, top + 0.07), 0.011, seg=10)
    # The soldering iron in its stand, its flex to the socket; solder; a tin of flux.
    B.box('WornIron', 283.7, 283.86, 0.88, 0.98, top, top + 0.015)
    B.cyl('WornIron', (283.72, 0.93, top + 0.015), (283.85, 0.93, top + 0.09), 0.02, seg=10)
    B.cyl('PupilWood', (283.86, 0.93, top + 0.095), (284.0, 0.93, top + 0.17), 0.013, seg=8)
    B.cyl('WornIron', (283.86, 0.93, top + 0.095), (283.74, 0.93, top + 0.03), 0.004, seg=6)
    pts = [(284.0, 0.93, top + 0.17), (284.06, 0.98, top + 0.06), (284.1, 1.1, top + 0.005), (284.2, 1.22, top + 0.01), (284.22, 1.26, 1.0)]
    for a, b in zip(pts, pts[1:]):
        B.cyl('Cable', a, b, 0.004, seg=5)
    B.scyl('sw_steel', (283.6, 0.8, top), (283.6, 0.8, top + 0.03), 0.03, seg=12)
    B.scyl('sw_tin', (283.95, 0.78, top), (283.95, 0.78, top + 0.02), 0.025, seg=10)
    # The bench lamp: base, two arms, a shade aimed at the bench in front of the chest.
    base = Vector((284.62, 1.14, top))
    elbow = Vector((284.68, 1.12, 1.46))
    head = LAMP_HEAD
    aim = (LAMP_AIM - head).normalized()
    B.cyl('WornIron', base, base + Vector((0, 0, 0.025)), 0.07, seg=14)
    B.cyl('WornIron', base + Vector((0, 0, 0.025)), elbow, 0.008, seg=6)
    B.cyl('WornIron', elbow, head - aim * 0.02, 0.008, seg=6)
    B.sphere('WornIron', elbow, 0.014, seg=8)
    B.cyl('WinDado', head - aim * 0.02, head + aim * 0.15, 0.035, 0.08, seg=14)
    # A tap in pieces on a rag; a jar of pencils; a steel rule and a set square.
    B.sbox('sw_cloth', 284.75, 285.12, 0.7, 0.92, top, top + 0.004)
    for k, (px, py, r, h) in enumerate(((284.82, 0.78, 0.018, 0.05), (284.9, 0.84, 0.012, 0.03), (284.98, 0.76, 0.022, 0.012),
                                        (285.04, 0.85, 0.008, 0.04), (284.86, 0.88, 0.014, 0.008))):
        B.cyl('HandledBrass', (px, py, top + 0.004), (px, py, top + 0.004 + h), r, seg=8)
    B.cyl('HandledBrass', (284.93, 0.72, top + 0.012), (285.08, 0.74, top + 0.012), 0.008, seg=8)
    B.scyl('sw_tin', (285.25, 1.15, top), (285.25, 1.15, top + 0.1), 0.03, seg=10)
    for k in range(5):
        a = k * 1.25
        B.scyl('sw_pencil', (285.25 + 0.012 * math.cos(a), 1.15 + 0.012 * math.sin(a), top + 0.02),
               (285.25 + 0.03 * math.cos(a), 1.15 + 0.03 * math.sin(a), top + 0.17 + 0.01 * k), 0.0035, seg=6)
    B.sbox('sw_steel', 285.15, 285.75, 0.67, 0.695, top, top + 0.0015)
    n0 = B.mark()
    B.prism_yz('Att17Atlas', [(0.0, 0.0), (0.2, 0.0), (0.0, 0.14)], 0.0, 0.003, cell='sw_glass')
    B.xform(n0, Matrix.Translation((285.32, 0.82, top)) @ Matrix.Rotation(-math.pi / 2, 4, 'Y') @ Matrix.Rotation(0.3, 4, 'X'))
    # The notebook, open, and his reading glasses folded on it.
    B.sbox('sw_paper', 285.42, 285.74, 0.70, 0.92, top, top + 0.012)
    B.sheet('paper1', 285.5, 0.81, top + 0.0125, 0.15, 0.2, ang=0.02)
    B.sheet('paper1', 285.66, 0.81, top + 0.0125, 0.15, 0.2, ang=-0.02)
    gx, gy, gz = 285.6, 0.79, top + 0.03
    for s in (-1, 1):
        B.torus('HandledBrass', (gx + s * 0.026, gy, gz), (0, -0.45, 1), 0.021, 0.0017, seg=14, rseg=4)
        B.scyl('sw_glass', (gx + s * 0.026, gy, gz - 0.001), (gx + s * 0.026, gy + 0.0004, gz + 0.0005), 0.02, seg=12)
        B.cyl('HandledBrass', (gx + s * 0.047, gy + 0.008, gz), (gx - s * 0.02, gy + 0.03, gz - 0.012), 0.0014, seg=4)
    B.cyl('HandledBrass', (gx - 0.006, gy, gz + 0.008), (gx + 0.006, gy, gz + 0.008), 0.0016, seg=4)
    # The radio.
    rx0, rx1, ry0, ry1 = 286.2, 286.62, 1.02, 1.24
    B.tbox('Att17Atlas', rx0, rx1, ry0, ry1, top, top + 0.24, {'-y': 'radio', 'all': 'sw_bakelite'})
    B.box('PigeonWood', rx0 - 0.005, rx1 + 0.005, ry0 - 0.005, ry1 + 0.005, top + 0.24, top + 0.255)
    for kx in (rx0 + 0.07, rx1 - 0.07):
        B.scyl('sw_bakelite', (kx, ry0, top + 0.035), (kx, ry0 - 0.02, top + 0.035), 0.018, seg=10)
    B.cyl('WornIron', (rx1 - 0.03, ry1 - 0.03, top + 0.255), (rx1 + 0.05, ry1 + 0.02, top + 0.62), 0.003, seg=4)   # aerial
    # Soil crumbs on the bench's front edge, where the tray went over.
    for _ in range(14):
        cx, cy = rnd.uniform(285.5, 285.95), rnd.uniform(0.66, 0.8)
        B.sphere('Att17Atlas', (cx, cy, top), rnd.uniform(0.006, 0.014), seg=6, scale=(1, 1, 0.5), cell='sw_crust')
    # The mug, the kettle on its ring, a tea caddy.
    mx, my = 287.3, 0.8
    B.cyl('TeaEnamel', (mx, my, top), (mx, my, top + 0.095), 0.042, seg=14)
    B.scyl('sw_tea', (mx, my, top + 0.06), (mx, my, top + 0.085), 0.039, seg=14)
    B.torus('TeaEnamel', (mx + 0.05, my, top + 0.05), (0, 1, 0), 0.025, 0.006, seg=10, rseg=5)
    B.scyl('sw_blue', (mx, my, top + 0.093), (mx, my, top + 0.096), 0.043, seg=14)
    kx, ky = 287.95, 1.05
    B.cyl('WornIron', (kx, ky, top), (kx, ky, top + 0.06), 0.11, seg=14)
    B.cyl('DarkMetal', (kx, ky, top + 0.06), (kx, ky, top + 0.065), 0.09, seg=14)
    B.cyl('TeaEnamel', (kx, ky, top + 0.065), (kx, ky, top + 0.2), 0.095, 0.075, seg=16)
    B.sphere('TeaEnamel', (kx, ky, top + 0.2), 0.075, seg=14, scale=(1, 1, 0.35))
    B.sphere('DarkMetal', (kx, ky, top + 0.232), 0.012, seg=8)
    B.cyl('TeaEnamel', (kx - 0.08, ky - 0.02, top + 0.1), (kx - 0.16, ky - 0.05, top + 0.2), 0.02, 0.009, seg=8)
    B.torus('DarkMetal', (kx, ky, top + 0.2), (0, 1, 0), 0.075, 0.007, seg=16, rseg=5)
    B.scyl('sw_green', (288.25, 1.15, top), (288.25, 1.15, top + 0.14), 0.045, seg=12)


def build_stool(B):
    """The low stool at the bench's end; on it, the voice-card player and a folded cardigan."""
    x0, x1, y0, y1, top = STOOL
    B.box('PupilWood', x0, x1, y0, y1, top - 0.035, top)
    for x in (x0 + 0.06, x1 - 0.06):
        for y in (y0 + 0.06, y1 - 0.06):
            dx, dy = (x - (x0 + x1) / 2) * 0.12, (y - (y0 + y1) / 2) * 0.12
            B.cyl('PigeonWood', (x + dx, y + dy, 0.0), (x, y, top - 0.035), 0.022, 0.018, seg=8)
    for y in (y0 + 0.06, y1 - 0.06):
        B.cyl('PigeonWood', (x0 + 0.07, y, 0.14), (x1 - 0.07, y, 0.14), 0.012, seg=6)
    B.sbox('sw_wool', 288.16, 288.38, 0.40, 0.64, top, top + 0.06)
    B.sbox('sw_wool', 288.17, 288.37, 0.41, 0.63, top + 0.06, top + 0.075)


def place_card_player(B):
    """The voice-card player on the stool, its front to the camera, a card (att_volunteer) in its slot. Placed last:
    voice_props frees bmesh elements, after which MB.mark/since can no longer find new vertices."""
    vp = _voice_props()
    if vp is None:
        print('dl17: voice props not ready; no card player placed')
        return None
    info = vp.card_player(B, vp.xform(loc=PLAYER, turn=0.0), lid='closed', horn=35.0, card=True)
    print('dl17: card player', {k: tuple(round(c, 3) for c in v) if hasattr(v, '__len__') else round(v, 3)
                                for k, v in info.items() if k in ('card', 'top', 'mouth', 'height', 'crank_pivot')})
    return info


def build_board(B):
    """The tool board over the bench: the painted shadows (texture) and the tools still hung on them."""
    bx0, bx1, bz0, bz1, by = BOARD
    B.box('PigeonWood', bx0 - 0.03, bx1 + 0.03, by + 0.004, WALL_Y, bz0 - 0.03, bz1 + 0.03)
    u0, v0, u1, v1 = cell_uv('toolboard')
    B.face('Att17Atlas', [(bx0, by, bz0), (bx1, by, bz0), (bx1, by, bz1), (bx0, by, bz1)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    for kind, present, parts in tool_parts():
        if not present:
            continue
        for poly, m_, t in parts:
            B.prism_xz('WornIron' if m_ == 'metal' else 'PupilWood', [(bx0 + u, bz0 + v) for u, v in poly], by - 0.004 - t, by - 0.002)
        # its peg
        u, v = poly[0]
        B.cyl('WornIron', (bx0 + u, by, bz0 + v), (bx0 + u, by - 0.03, bz0 + v), 0.003, seg=4)
    # Pinned on the wall to the right: the bean chart, the volunteer's notice.
    B.decal(286.7, 287.3, 1.03, 1.48, WALL_Y - 0.002, 'chart')
    B.decal(288.05, 288.35, 1.2, 1.4, WALL_Y - 0.002, 'rota')
    B.decal(282.95, 283.55, 2.12, 2.27, WALL_Y - 0.002, 'seedlist')


def build_window(B, rnd, names):
    """The window into a dead light well, its shelf of pots under the grow-lamp, the drip line from the sink tap."""
    x0, x1, sill, head = WINDOW
    # The well behind: dark, a little way back.
    B.box('DarkMetal', x0 - 0.1, x1 + 0.1, 2.0, 2.1, sill - 0.1, head + 0.1)
    B.box('DarkMetal', x0 - 0.1, x0, WALL_Y2, 2.0, sill - 0.1, head + 0.1)
    B.box('DarkMetal', x1, x1 + 0.1, WALL_Y2, 2.0, sill - 0.1, head + 0.1)
    B.box('DarkMetal', x0, x1, WALL_Y2, 2.0, head, head + 0.1)
    B.box('DarkMetal', x0, x1, WALL_Y2, 2.0, sill - 0.1, sill)
    for hx0, hx1 in ((x0, x0 + 0.02), (x1 - 0.02, x1)):
        B.box('WorkPlaster', hx0, hx1, WALL_Y, WALL_Y2, sill, head)
    B.box('DirtyGlass', x0, x1, 1.415, 1.42, sill, head)
    fy0, fy1 = 1.38, 1.415
    for a, b in ((x0, x0 + 0.06), (x1 - 0.06, x1)):
        B.box('PigeonWood', a, b, fy0, fy1, sill, head)
    B.box('PigeonWood', x0, x1, fy0, fy1, head - 0.06, head)
    B.box('PigeonWood', x0, x1, fy0, fy1, sill, sill + 0.06)
    for gx in (x0 + (x1 - x0) * k / 4 for k in (1, 2, 3)):
        B.box('PigeonWood', gx - 0.018, gx + 0.018, fy0 + 0.008, fy1, sill, head)
    B.box('PigeonWood', x0 - 0.05, x1 + 0.05, WALL_Y - 0.04, fy1, sill - 0.03, sill)
    # The shelf, on brackets.
    s0, s1, sy0, sy1, st = WSHELF
    B.box('PigeonWood', s0, s1, sy0, sy1, st - 0.035, st)
    for bx in (s0 + 0.15, (s0 + s1) / 2, s1 - 0.15):
        B.prism_yz('WornIron', [(WALL_Y, st - 0.035), (WALL_Y, st - 0.32), (WALL_Y - 0.025, st - 0.32), (sy0 + 0.04, st - 0.035)],
                   bx - 0.007, bx + 0.007)
    # The pots: dry, dead, all of them; the one under the middle of the lamp has M. D. on its tag, a dry stalk in it.
    xs = [289.18, 289.42, 289.68, 289.95, 290.2, MD_POT[0], 290.8, 291.08, 291.34, 291.6, 291.84]
    drip = []
    for k, x in enumerate(xs):
        r = 0.075 if x == MD_POT[0] else rnd.uniform(0.05, 0.07)
        y = MD_POT[1] if x == MD_POT[0] else 1.04 + rnd.uniform(-0.06, 0.08)
        if x == MD_POT[0]:
            zs = pot(B, x, y, st, r, r * 1.5, rnd, tag=0, plant=None, tag_yaw=0.05)
            dead_plant(B, x + 0.01, y - 0.01, zs, rnd, n=2, h=0.15, cell='sw_shrivel', droop=1.2)
        else:
            zs = pot(B, x, y, st, r, r * 1.5, rnd, tag=names(), plant='dead')
        drip.append((x, y, zs, r))
    # The drip line: from the sink's tap along the wall, down to the shelf, along its back, a dropper into each pot.
    ly, lz = 1.255, st + 0.012
    tap = (292.5, 1.18, 1.05)
    path = [(292.5, 1.255, 1.05), (292.08, 1.255, 1.05), (292.08, ly, lz), (s0 + 0.05, ly, lz)]
    for a, b in zip(path, path[1:]):
        B.cyl('Cable', a, b, 0.005, seg=6)
    for x, y, zs, r in drip:
        B.cyl('Cable', (x, ly, lz), (x, y + r * 0.5, zs + 0.03), 0.0022, seg=4)
        B.cyl('Cable', (x, y + r * 0.5, zs + 0.03), (x, y + r * 0.45, zs + 0.005), 0.0022, seg=4)
    # The grow-lamp's hood and chains, its lampholders, its flex to the timer on the wall (the tubes: Att17GrowLamp).
    g0, g1, gy, gz = GROW
    hz = gz + 0.035
    B.box('WornIron', g0 - 0.07, g1 + 0.07, gy - 0.12, gy + 0.12, hz, hz + 0.03)
    for s in (-1, 1):
        B.box('WornIron', g0 - 0.07, g1 + 0.07, gy + s * 0.12 - 0.003, gy + s * 0.12 + 0.003, hz - 0.04, hz)
    for x in (g0 - 0.06, g1 + 0.06):
        B.box('WornIron', x - 0.012, x + 0.012, gy - 0.11, gy + 0.11, gz - 0.025, hz)
    for x in (g0 + 0.1, g1 - 0.1):
        B.cyl('WornIron', (x, gy, hz + 0.03), (x, gy, CEIL), 0.004, seg=4)
        for k in range(10):
            z = hz + 0.05 + k * 0.12
            B.torus('WornIron', (x, gy, z), (1, 0, 0) if k % 2 else (0, 1, 0), 0.012, 0.0025, seg=8, rseg=3)
    fl = [(g1 + 0.07, gy, hz + 0.015), (291.9, 1.2, hz + 0.08), (292.3, WALL_Y - 0.03, 1.5), (292.38, WALL_Y - 0.06, 1.46)]
    for a, b in zip(fl, fl[1:]):
        B.cyl('Cable', a, b, 0.004, seg=5)
    # Under the shelf: compost sacks, a stack of pots, the watering can.
    sack(B, (289.45, 1.02, 0.0), (0.42, 0.3, 0.4))
    sack(B, (289.92, 1.08, 0.0), (0.4, 0.28, 0.3), lying=True)
    for k in range(6):
        B.cyl('PotClay', (290.45, 1.05, k * 0.03), (290.45, 1.05, k * 0.03 + 0.12), 0.055, 0.08, seg=12)
    wx, wy = 291.2, 1.0
    B.cyl('WornIron', (wx, wy, 0.0), (wx, wy, 0.26), 0.1, seg=14)
    B.cyl('WornIron', (wx - 0.09, wy, 0.06), (wx - 0.32, wy, 0.32), 0.014, 0.01, seg=8)
    B.cyl('WornIron', (wx - 0.33, wy, 0.33), (wx - 0.36, wy, 0.35), 0.03, 0.035, seg=10)
    B.torus('WornIron', (wx, wy, 0.27), (0, 1, 0), 0.085, 0.008, seg=14, rseg=4)
    return tap


def build_sink(B, tap):
    """The butler sink, its tap (the drip line's T on it), a bucket; a broom in the corner by the stair door."""
    x0, x1 = SINK
    y0, y1, z0, z1 = 0.84, 1.28, 0.62, 0.86
    B.box('TeaEnamel', x0, x1, y0, y1, z0, z0 + 0.04)
    B.box('TeaEnamel', x0, x1, y0, y0 + 0.04, z0, z1)
    B.box('TeaEnamel', x0, x1, y1 - 0.04, y1, z0, z1)
    B.box('TeaEnamel', x0, x0 + 0.04, y0, y1, z0, z1)
    B.box('TeaEnamel', x1 - 0.04, x1, y0, y1, z0, z1)
    B.scyl('sw_black', ((x0 + x1) / 2, (y0 + y1) / 2, z0 + 0.04), ((x0 + x1) / 2, (y0 + y1) / 2, z0 + 0.041), 0.025, seg=10)
    for px in (x0 + 0.06, x1 - 0.06):
        B.box('WorkPlaster', px - 0.05, px + 0.05, y0 + 0.05, y1, 0.0, z0)
    tx, ty, tz = tap
    B.cyl('HandledBrass', (tx, WALL_Y, tz), (tx, ty, tz), 0.014, seg=8)
    B.cyl('HandledBrass', (tx, ty, tz), (tx, ty - 0.05, tz - 0.07), 0.011, seg=8)
    B.cyl('HandledBrass', (tx, ty + 0.03, tz), (tx, ty + 0.03, tz + 0.06), 0.008, seg=6)
    B.cyl('HandledBrass', (tx - 0.04, ty + 0.03, tz + 0.06), (tx + 0.04, ty + 0.03, tz + 0.06), 0.006, seg=6)
    B.cyl('HandledBrass', (tx, WALL_Y - 0.045, tz), (tx - 0.05, WALL_Y - 0.045, tz), 0.008, seg=6)
    B.sphere('DirtyGlass', (tx, ty - 0.055, tz - 0.085), 0.004, seg=6)
    B.cyl('WornIron', (292.5, 1.05, 0.0), (292.5, 1.05, 0.3), 0.12, 0.14, seg=14)
    B.torus('WornIron', (292.5, 1.05, 0.3), (0, 0, 1), 0.14, 0.006, seg=14, rseg=4)
    # A broom leaning in the corner by the door.
    bx, by = BROOM
    B.cyl('PigeonWood', (bx, by, 0.12), (bx + 0.16, by + 0.11, 1.45), 0.013, seg=6)
    n0 = B.mark()
    B.box('PigeonWood', -0.14, 0.14, -0.03, 0.03, 0.0, 0.06)
    B.sbox('sw_straw', -0.13, 0.13, -0.025, 0.025, -0.06, 0.0)
    B.xform(n0, TR(bx, by, 0.06, 0.2))


def build_door(B):
    """The way on, in the right end wall: the stair door's steel frame and architrave, its threshold; over it a blade
    sign, RESIDENTIAL ACCESS . RING A and an arrow up, with the Works' small cog; the bulkhead lamp on the back wall
    by the corner. (The leaf is Att17Door; the stair beyond, build_stairwell.)"""
    dy0, dy1, hd = DOOR17
    # The steel frame lining the opening, and the room side's timber architrave.
    for y0_, y1_ in ((dy0 - 0.02, dy0), (dy1, dy1 + 0.02)):
        B.box('WornIron', END_X, X1, y0_, y1_, 0.0, hd)
    B.box('WornIron', END_X, X1, dy0 - 0.02, dy1 + 0.02, hd, hd + 0.02)
    for (y0_, y1_, z0_, z1_) in ((dy0 - 0.09, dy0 - 0.02, 0.0, hd + 0.09), (dy1 + 0.02, dy1 + 0.09, 0.0, hd + 0.09),
                                 (dy0 - 0.09, dy1 + 0.09, hd + 0.02, hd + 0.09)):
        B.box('PigeonWood', END_X - 0.025, END_X, y0_, y1_, z0_, z1_)
    B.box('WornIron', END_X - 0.01, X1 + 0.01, dy0, dy1, 0.0, 0.012)                       # the threshold strip
    # The door stop on the stair side (the leaf closes against it).
    for y0_, y1_ in ((dy0, dy0 + 0.015), (dy1 - 0.015, dy1)):
        B.box('WornIron', X1 - LEAF_T - 0.02, X1 - LEAF_T - 0.002, y0_, y1_, 0.0, hd)
    B.box('WornIron', X1 - LEAF_T - 0.02, X1 - LEAF_T - 0.002, dy0, dy1, hd - 0.015, hd)
    # The blade sign, hung off the end wall over the door, its face to the room's open side.
    sx0, sx1, sz0, sz1 = SIGN17
    B.box('WornIron', sx0 - 0.015, sx1 + 0.015, -0.018, 0.018, sz0 - 0.015, sz1 + 0.015)
    B.decal(sx0, sx1, sz0, sz1, -0.0185, 'sign_works')
    bz = sz1 + 0.07
    B.box('WornIron', sx0 - 0.08, END_X, -0.012, 0.012, bz - 0.012, bz + 0.012)            # the bracket arm
    B.cyl('WornIron', (END_X, 0.0, bz - 0.24), (sx1 - 0.35, 0.0, bz), 0.008, seg=6)          # its strut
    B.box('WornIron', END_X - 0.012, END_X, -0.05, 0.05, bz - 0.28, bz + 0.04)              # the wall plate
    for hx in (sx0 + 0.12, sx1 - 0.12):                                                    # two hangers
        B.cyl('WornIron', (hx, 0.0, bz - 0.012), (hx, 0.0, sz1 + 0.015), 0.005, seg=5)
    # The bulkhead lamp on the back wall by the corner (its bulb is in Att17Bulbs).
    lx, ly, lz = DOOR_LAMP
    B.box('WornIron', lx - 0.08, lx + 0.08, WALL_Y - 0.02, WALL_Y, lz - 0.1, lz + 0.1)
    B.cyl('WornIron', (lx, WALL_Y - 0.02, lz), (lx, ly - 0.04, lz), 0.06, seg=12)
    B.torus('WornIron', (lx, ly - 0.01, lz), (0, 1, 0), 0.055, 0.004, seg=12, rseg=3)
    for a in range(4):
        ang = a * math.pi / 4
        B.cyl('WornIron', (lx + 0.055 * math.cos(ang), ly - 0.01, lz + 0.055 * math.sin(ang)),
              (lx - 0.055 * math.cos(ang), ly - 0.01, lz - 0.055 * math.sin(ang)), 0.003, seg=4)


def tread_top(i):
    """Tread i's (1..TREADS) top height; TREADS + 1 is the upper landing."""
    return RISE * i


def tread_x(i):
    """Tread i's (1..TREADS) going: x0 (its nosing's riser face) to x1."""
    return STAIR_X0 + (i - 1) * GOING, STAIR_X0 + i * GOING


def build_stairwell(B):
    """Beyond the door: a landing, then a straight flight up toward +x, out of the frame's top into a lit shaft. Seen
    from the room's open side in section: the stair's painted string, worn timber treads with iron nosings, the
    handrail on the back wall, the dado following the pitch; the room's ceiling carries over the landing and stops,
    and above the flight the shaft goes up to the warm lamp."""
    x0, x1, fy, wy, wy2, top = WELL
    y0, y1 = STAIR_Y
    nose = 0.022
    # The landing's floor (boards along x), the well's floor under the flight.
    B.box('CrateWood', x0, x1, FRONT_Y, wy2, -0.2, 0.0)                                   # flush with the room's front edge
    u0, v0, u1, v1 = cell_uv('sw_seam')
    su = ((u0 + u1) / 2, (v0 + v1) / 2)
    y = FRONT_Y + 0.07
    while y < wy:
        B.face('Att17Atlas', [(x0, y - 0.0025, 0.0006), (STAIR_X0, y - 0.0025, 0.0006), (STAIR_X0, y + 0.0025, 0.0006),
                              (x0, y + 0.0025, 0.0006)], [su] * 4)
        y += 0.14
    # The back wall, plaster; its dado, painted, following the pitch; the end wall.
    B.box('WorkPlaster', x0, x1 + 0.15, wy, wy2, 0.0, top)
    B.box('WorkPlaster', x1, x1 + 0.15, fy, wy, 0.0, top)
    slope = RISE / GOING
    xd = STAIR_X0 - 0.15
    dz = 0.8
    ztop = tread_top(TREADS + 1) + dz
    B.prism_xz('WinDado', [(x0, 0.0), (x1, 0.0), (x1, ztop), (xd + (ztop - dz) / slope, ztop), (xd, dz), (x0, dz)],
               wy - 0.012, wy)
    pts = [(x0, dz), (xd, dz), (xd + (ztop - dz) / slope, ztop), (x1, ztop)]
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):                                             # its rail
        B.cyl('PigeonWood', (ax, wy - 0.018, az), (bx, wy - 0.018, bz), 0.014, seg=6)
    # The ceiling over the landing (the room's, carried on), its edge; the shaft's top, out of sight.
    B.box('WorkPlaster', x0, WELL_FASCIA, fy, wy2, CEIL, CEIL + 0.15)
    B.box('PigeonWood', WELL_FASCIA - 0.14, WELL_FASCIA, fy, wy, CEIL - 0.16, CEIL)
    B.box('WorkPlaster', WELL_FASCIA, x1 + 0.15, fy, wy2, top, top + 0.15)
    # The flight: a painted mass in section (the string), its soffit parallel to the pitch.
    zl = tread_top(TREADS + 1)
    prof = [(STAIR_X0, 0.0)]
    for i in range(1, TREADS + 1):
        a, b = tread_x(i)
        prof += [(a, tread_top(i) - 0.03), (b, tread_top(i) - 0.03)]
    xs0 = STAIR_X0 + 0.5
    zs = zl - 0.24
    prof += [(tread_x(TREADS)[1], zl - 0.03), (x1, zl - 0.03), (x1, zs), (xs0 + zs / slope, zs), (xs0, 0.0)]
    B.prism_xz('WinDado', prof, y0, y1 - 0.002)
    B.box('PigeonWood', tread_x(TREADS)[1] + 0.1, x1, y0 - 0.02, y0, zs - 0.04, zl - 0.03)     # the landing's edge beam
    # Treads: worn timber boards with iron nosings; the upper landing's boards.
    for i in range(1, TREADS + 1):
        a, b = tread_x(i)
        z = tread_top(i)
        B.box('PupilWood', a - nose, b, y0, y1 - 0.004, z - 0.03, z)
        B.box('WornIron', a - nose - 0.003, a + 0.035, y0 - 0.002, y1 - 0.004, z - 0.032, z + 0.0015)
    a = tread_x(TREADS)[1]
    B.box('PupilWood', a - nose, x1, y0, y1 - 0.004, zl - 0.03, zl)
    B.box('WornIron', a - nose - 0.003, a + 0.035, y0 - 0.002, y1 - 0.004, zl - 0.032, zl + 0.0015)
    # The handrail on the back wall, on brackets, over the pitch (0.9 above the nosings), level over the landings.
    ry = wy - 0.065
    rz = lambda x: 0.9 + RISE + (x - STAIR_X0) * slope
    rpts = [(x0 + 0.25, 0.9 + 0.02), (STAIR_X0 - 0.1, 0.9 + 0.02), (STAIR_X0 + 0.1, rz(STAIR_X0 + 0.1)),
            (tread_x(TREADS)[1] - 0.05, rz(tread_x(TREADS)[1] - 0.05)), (tread_x(TREADS)[1] + 0.25, zl + 0.92), (x1 - 0.1, zl + 0.92)]
    for (ax, az), (bx, bz) in zip(rpts, rpts[1:]):
        B.cyl('WornIron', (ax, ry, az), (bx, ry, bz), 0.019, seg=10)
        B.sphere('WornIron', (bx, ry, bz), 0.019, seg=8)
    B.cyl('WornIron', (rpts[0][0], ry, rpts[0][1]), (rpts[0][0], wy, rpts[0][1]), 0.019, seg=8)
    for bx in (x0 + 0.6, STAIR_X0 + 0.9, STAIR_X0 + 2.2, STAIR_X0 + 3.5, x1 - 0.4):
        bzz = 0.92 if bx < STAIR_X0 else (rz(bx) if bx < tread_x(TREADS)[1] else zl + 0.92)
        B.cyl('WornIron', (bx, ry, bzz - 0.02), (bx, ry + 0.03, bzz - 0.06), 0.006, seg=5)
        B.cyl('WornIron', (bx, ry + 0.03, bzz - 0.06), (bx, wy, bzz - 0.06), 0.006, seg=5)
        B.cyl('WornIron', (bx, wy - 0.004, bzz - 0.06), (bx, wy, bzz - 0.06), 0.03, seg=10)
    # The landing's skirting.
    B.box('PigeonWood', x0, STAIR_X0, wy - 0.02, wy, 0.0, 0.12)
    # The lamp's fitting over the flight: a back plate and a cage (the glowing globe is Att17StairLamp).
    lx, ly, lz = STAIR_LAMP
    B.box('WornIron', lx - 0.09, lx + 0.09, wy - 0.02, wy, lz - 0.12, lz + 0.12)
    B.cyl('WornIron', (lx, wy - 0.02, lz), (lx, ly + 0.03, lz), 0.07, seg=12)
    B.torus('WornIron', (lx, ly - 0.02, lz), (0, 1, 0), 0.065, 0.004, seg=12, rseg=3)
    for a in range(4):
        ang = a * math.pi / 4
        B.cyl('WornIron', (lx + 0.065 * math.cos(ang), ly - 0.02, lz + 0.065 * math.sin(ang)),
              (lx - 0.065 * math.cos(ang), ly - 0.02, lz - 0.065 * math.sin(ang)), 0.003, seg=4)
    B.cyl('Cable', (lx, wy - 0.01, lz + 0.12), (lx, wy - 0.01, top), 0.008, seg=6)


def build_ceiling_lights(B):
    """The pendant over the bench (lit), one over the shelf end (dead); their cords."""
    for (x, y, z, lit) in ((PENDANT[0], PENDANT[1], PENDANT[2], True), (282.0, 0.6, 2.3, False)):
        B.cyl('Cable', (x, y, CEIL), (x, y, z + 0.1), 0.004, seg=5)
        B.cyl('WornIron', (x, y, z + 0.1), (x, y, z + 0.06), 0.018, seg=8)
        B.cyl('WinDado', (x, y, z + 0.09), (x, y, z - 0.03), 0.04, 0.2, seg=18)
        B.cyl('TeaEnamel', (x, y, z + 0.06), (x, y, z - 0.028), 0.035, 0.185, seg=18)
        if not lit:
            B.sphere('Att17Atlas', (x, y, z), 0.035, seg=10, cell='sw_glass')


def build_floor_things(B, rnd):
    """The mended pot by the chest, the spilled soil the tray left, a coil of hose in the foreground."""
    # The mended pot: cracked down one side toward the camera, the crack puttied, two bands of wire twisted tight.
    px, py = POT
    r, h = 0.13, 0.24
    B.cyl('PotClay', (px, py, 0.0), (px, py, h * 0.86), r * 0.74, r * 0.97, seg=18)
    B.torus('PotClay', (px, py, h * 0.92), (0, 0, 1), r * 0.99, h * 0.075, seg=18, rseg=5)
    B.scyl('sw_crust', (px, py, h * 0.8), (px, py, h * 0.9), r * 0.93, r * 0.97, seg=16)
    rad = lambda z: r * 0.74 + (r * 0.97 - r * 0.74) * min(z / (h * 0.86), 1.0) if z < h * 0.84 else r * 0.99 + h * 0.075
    az0 = math.radians(-102)
    zc, az = h, az0
    crack = []
    while zc > 0.02:
        crack.append((az, zc))
        zc -= rnd.uniform(0.025, 0.04)
        az += rnd.uniform(-0.12, 0.12)
    for (a1, z1), (a2, z2) in zip(crack, crack[1:]):
        p1 = Vector((px + (rad(z1) + 0.002) * math.cos(a1), py + (rad(z1) + 0.002) * math.sin(a1), z1))
        p2 = Vector((px + (rad(z2) + 0.002) * math.cos(a2), py + (rad(z2) + 0.002) * math.sin(a2), z2))
        B.scyl('sw_putty', p1, p2, 0.008, seg=5)
        B.scyl('sw_black', p1 + (p1 - Vector((px, py, p1.z))).normalized() * 0.0065,
               p2 + (p2 - Vector((px, py, p2.z))).normalized() * 0.0065, 0.0025, seg=4)
    ro, ri = r * 0.99 + h * 0.075, r * 0.99 - h * 0.075               # and over the rim, into the soil
    for (ra, za), (rb, zb_) in (((ro + 0.002, h * 0.9), (ro * 0.97, h * 0.995)), ((ro * 0.97, h * 0.995), (ri, h * 0.97)),
                                 ((ri, h * 0.97), (ri - 0.02, h * 0.905))):
        pa = Vector((px + ra * math.cos(az0), py + ra * math.sin(az0), za))
        pb = Vector((px + rb * math.cos(az0 + 0.04), py + rb * math.sin(az0 + 0.04), zb_))
        B.scyl('sw_putty', pa, pb, 0.008, seg=5)
        B.scyl('sw_black', pa + Vector((0, 0, 0.006)), pb + Vector((0, 0, 0.006)), 0.0022, seg=4)
    for zb in (0.07, 0.165):
        rr = rad(zb) + 0.0025
        B.torus('Att17Atlas', (px, py, zb), (0, 0, 1), rr, 0.0022, seg=28, rseg=4, cell='sw_wire')
        a = az0 + 0.25
        for k in range(3):                                        # the twist
            B.scyl('sw_wire', (px + rr * math.cos(a), py + rr * math.sin(a), zb + 0.004 * (k - 1)),
                   (px + (rr + 0.022) * math.cos(a + 0.05 * k), py + (rr + 0.022) * math.sin(a + 0.05 * k), zb - 0.004 * (k - 1)), 0.0022, seg=4)
    # Spilled soil: where the tray slid off the bench and landed; a heap under its raised back edge.
    for _ in range(18):
        cx, cy = TRAY[0] + rnd.uniform(-0.32, 0.32), TRAY[1] + rnd.uniform(0.12, 0.5)
        B.sphere('Att17Atlas', (cx, cy, 0.0), rnd.uniform(0.012, 0.035), seg=7, scale=(1.3, 1, 0.35),
                 cell=rnd.choice(('sw_crust', 'sw_soil_dry')))
    # Coil of hose, low in the foreground.
    for k in range(3):
        B.torus('Att17Atlas', (283.7 + 0.02 * k, -1.05 + 0.015 * k, 0.014 + 0.024 * k), (0, 0, 1), 0.2 - 0.01 * k, 0.013,
                seg=24, rseg=6, cell='sw_green')


def heap_under_tray(B):
    """The heap the tray's back edge rests on: its top meets the tray's bottom edge (computed from the tilt)."""
    M = tray_matrix()
    w, d, h = TRAY_SIZE
    for lx in (-0.12, 0.0, 0.12):
        p = M @ Vector((lx, d / 2 - 0.03, 0.0))
        B.sphere('Att17Atlas', (p.x, p.y, 0.0), 0.06, seg=8, scale=(1.4, 1.0, max(0.2, (p.z + 0.006) / 0.06)), cell='sw_crust')


def tray_matrix():
    ex, ey, ez = (math.radians(a) for a in TRAY_TILT)
    from mathutils import Euler
    R = Euler((ex, ey, ez), 'XYZ').to_matrix().to_4x4()
    w, d, h = TRAY_SIZE
    low = min((R @ Vector((sx * w / 2, sy * d / 2, 0.0))).z for sx in (-1, 1) for sy in (-1, 1))
    return Matrix.Translation((TRAY[0], TRAY[1], -low)) @ R


# =====================================================================================================================
# Vance's apprentice test rig (the expansion): its static parts (Att17Set)
# =====================================================================================================================
def pipe(B, pts, r=PIPE_R, mt='HandledBrass', seg=10):
    """A run of pipe through pts, with a round elbow at each bend."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        B.cyl(mt, a, b, r, seg=seg)
    for p in pts[1:-1]:
        B.sphere(mt, p, r * 1.3, seg=seg)


def chain(B, pts, pitch=0.032, w=0.015, t=0.0045, mt='WornIron'):
    """A chain along a polyline: flat links, each turned a quarter about the chain from the last."""
    k = 0
    for a, b in zip(pts, pts[1:]):
        a, b = Vector(a), Vector(b)
        d = b - a
        L = d.length
        if L < 1e-6:
            continue
        u = d / L
        n1 = u.cross(Vector((0, 0, 1)))
        if n1.length < 1e-3:
            n1 = u.cross(Vector((1, 0, 0)))
        n1.normalize()
        n2 = u.cross(n1)
        n = max(1, round(L / pitch))
        for i in range(n):
            ax, az = (n1, n2) if k % 2 == 0 else (n2, -n1)
            R = Matrix((u, ax, az)).transposed().to_4x4()
            B._log(add_box(B.bm, a + d * ((i + 0.5) / n), (L / n * 1.18, w, t), mat=B.m(mt), rot=R))
            k += 1


def pulley(B, c, axis, r, cheeks=True):
    """A small iron sheave: its wheel (a groove's two flanges), its hub; a strap either side of it."""
    c, ax = Vector(c), Vector(axis).normalized()
    B.cyl('WornIron', c - ax * 0.007, c - ax * 0.003, r * 1.12, seg=16)
    B.cyl('WornIron', c - ax * 0.003, c + ax * 0.003, r * 0.85, seg=16)
    B.cyl('WornIron', c + ax * 0.003, c + ax * 0.007, r * 1.12, seg=16)
    B.cyl('WornIron', c - ax * 0.016, c + ax * 0.016, 0.006, seg=6)
    if cheeks:
        for s_ in (-1, 1):
            B.cyl('WornIron', c + ax * 0.014 * s_, c + ax * 0.016 * s_ + Vector((0, 0, r + 0.03)), 0.005, seg=5)


def build_rig(B, rnd):
    """The test bench, its beds and levers, the pipes behind it, the tank on the wall, the valve's body and the feed,
    the float's chain and pulleys, the latch's keeper on the door's jamb, and Vance's card on the tank."""
    x0, x1, y0, y1, top = RIG
    # The bench: a scrubbed top on four legs, a front panel (the levers are on it; the cocks behind it), a back rail,
    # a low shelf with a bucket and a funnel.
    B.box('PupilWood', x0, x1, y0, y1, top - 0.04, top)
    for x in (x0 + 0.03, x1 - 0.03):
        for y in (y0 + 0.045, y1 - 0.03):
            B.box('PigeonWood', x - 0.025, x + 0.025, y - 0.025, y + 0.025, 0.0, top - 0.04)
    B.box('PigeonWood', x0 + 0.005, x1 - 0.005, y0, y0 + 0.02, 0.2, top - 0.04)
    B.box('PigeonWood', x0 + 0.05, x1 - 0.05, y1 - 0.05, y1 - 0.03, top - 0.1, top - 0.04)
    B.box('PigeonWood', x0 + 0.06, x1 - 0.06, y0 + 0.06, y1 - 0.06, 0.08, 0.1)
    B.cyl('WornIron', (294.7, 0.78, 0.1), (294.7, 0.78, 0.28), 0.09, 0.11, seg=14)
    B.torus('WornIron', (294.7, 0.78, 0.28), (0, 0, 1), 0.11, 0.006, seg=14, rseg=4)
    B.cyl('WornIron', (293.5, 0.7, 0.1), (293.5, 0.7, 0.16), 0.012, 0.012, seg=8)
    B.cyl('WornIron', (293.5, 0.7, 0.16), (293.5, 0.7, 0.24), 0.012, 0.07, seg=12)
    # The beds: wooden trays, a skin of dry soil in each, a few dead seedlings; the names on their fronts (to the right,
    # clear of the levers' grips).
    by0, by1 = BED_Y
    for i, (bx0, bx1) in enumerate(BEDS):
        t = BED_T
        B.box('CrateWood', bx0, bx1, by0, by0 + t, top, BED_TOP)
        B.box('CrateWood', bx0, bx1, by1 - t, by1, top, BED_TOP)
        B.box('CrateWood', bx0, bx0 + t, by0 + t, by1 - t, top, BED_TOP)
        B.box('CrateWood', bx1 - t, bx1, by0 + t, by1 - t, top, BED_TOP)
        B.box('CrateWood', bx0 + t, bx1 - t, by0 + t, by1 - t, top, WATER_Z)
        B.tbox('Att17Atlas', bx0 + t, bx1 - t, by0 + t, by1 - t, WATER_Z, WATER_Z + SOIL_T, {'+z': 'soilcrack', 'all': 'sw_crust'})
        for _ in range(5):
            dead_plant(B, rnd.uniform(bx0 + 0.06, bx1 - 0.06), rnd.uniform(by0 + 0.06, by1 - 0.08), WATER_Z + SOIL_T, rnd, n=1,
                       h=rnd.uniform(0.03, 0.06), cell=rnd.choice(('sw_shrivel', 'sw_deadleaf')), droop=rnd.uniform(1.2, 1.7))
        cx = bx1 - 0.11
        B.box('PupilWood', cx - 0.07, cx + 0.07, by0 - 0.004, by0, 0.608, 0.672)
        B.decal(cx - 0.064, cx + 0.064, 0.62, 0.66, by0 - 0.0045, 'bed%d' % (i + 1))
    # The levers' brackets on the front panel (the levers are Att17SluiceA/B/C), the letters under them; behind the
    # panel, the manifold and the cocks.
    py, pz = SLUICE_PIVOT
    my, mz = MANIFOLD
    for name, x, bed in SLUICES:
        B.box('WornIron', x - 0.04, x + 0.04, y0 - 0.006, y0, pz - 0.06, pz + 0.045)
        for s_ in (-1, 1):
            B.box('WornIron', x + s_ * 0.022 - 0.004, x + s_ * 0.022 + 0.004, py - 0.014, y0 - 0.006, pz - 0.02, pz + 0.02)
        B.cyl('WornIron', (x - 0.03, py, pz), (x + 0.03, py, pz), 0.005, seg=6)
        B.box('WornIron', x - 0.034, x + 0.034, y0 - 0.008, y0 - 0.006, 0.267, 0.333)
        B.decal(x - 0.03, x + 0.03, 0.27, 0.33, y0 - 0.0085, 'pl' + name)
        pipe(B, [(x, my, mz), (x, my, COCK_Z)], mt='Copper', r=0.014)
        B.sphere('HandledBrass', (x, my, COCK_Z), 0.03, seg=10)
        B.cyl('WornIron', (x, my - 0.03, COCK_Z), (x, y0 + 0.02, COCK_Z), 0.006, seg=6)
    # The three pipes: from each cock back under the bench top, up behind it, across, forward over a bed, down; all the
    # same brass. A feeds bed 3, B bed 1, C bed 2: A runs in front and lowest, B behind and highest; they cross.
    my_, mz_ = MOUTH
    for name, x, bed in SLUICES:
        sx = SPOUT_X[bed - 1]
        ry, rz = RISE_Y[name], RUN_Z[name]
        pipe(B, [(x, my + 0.03, COCK_Z), (x, ry, COCK_Z), (x, ry, rz), (sx, ry, rz), (sx, my_, rz), (sx, my_, mz_ + 0.03)])
        B.cyl('HandledBrass', (sx, my_, mz_ + 0.03), (sx, my_, mz_), PIPE_R, PIPE_R * 1.35, seg=10)          # the spout
        B.torus('HandledBrass', (sx, my_, mz_ + 0.004), (0, 0, 1), PIPE_R * 1.3, 0.003, seg=10, rseg=4)
        for cx_, cz_ in ((x, 0.80), ((x + sx) / 2 + (0.12 if name == 'C' else 0.0), rz)):         # clips to the board
            B.cyl('WornIron', (cx_, ry + PIPE_R, cz_), (cx_, BACKBOARD[2], cz_), 0.004, seg=5)
            B.torus('WornIron', (cx_, ry, cz_), (0, 0, 1) if cz_ == 0.80 else (1, 0, 0), PIPE_R + 0.003, 0.0025, seg=10, rseg=3)
    bx0, bx1, bby0, bby1, bz0, bz1 = BACKBOARD                       # the board behind them, painted cream
    B.box('TeaEnamel', bx0, bx1, bby0, bby1, bz0, bz1)
    B.box('PigeonWood', bx0 - 0.015, bx1 + 0.015, bby0 - 0.01, bby1, bz1, bz1 + 0.02)
    # The tank's down-pipe to the valve, the valve's body (its spindle and wheel are Att17Valve), on down under the
    # bench to the manifold. (Its refill, from the new pump: build_service.)
    tx0, tx1, ty0, ty1, tz0, tz1 = TANK
    vx, vy, vz = VALVE
    pipe(B, [(tx0 + 0.02, 0.95, tz0 + 0.06), (vx, 0.95, tz0 + 0.06), (vx, DOWN_Y, tz0 + 0.06), (vx, DOWN_Y, mz),
             (SLUICES[-1][1] + 0.05, my, mz)], mt='Copper', r=0.016)
    B.box('WornIron', tx0 - 0.03, tx0, 0.91, 0.99, tz0 + 0.02, tz0 + 0.1)                        # the outlet's flange
    B.sphere('WornIron', (vx, DOWN_Y, vz), 0.042, seg=12, scale=(1, 1, 1.25))                     # the valve's body
    for dz in (-0.055, 0.055):
        B.cyl('WornIron', (vx, DOWN_Y, vz + dz - 0.012), (vx, DOWN_Y, vz + dz + 0.012), 0.026, seg=8)
    B.cyl('WornIron', (vx, DOWN_Y, vz), (vx, 0.545, vz), 0.024, seg=10)                            # its bonnet
    B.cyl('HandledBrass', (vx, 0.545, vz), (vx, 0.53, vz), 0.016, seg=6)                           # the gland nut
    B.cyl('WornIron', (vx, DOWN_Y + 0.016, 1.3), (vx, WALL_Y, 1.3), 0.005, seg=5)                     # a stay to the wall
    # The tank: on two wall brackets, painted; rolled rim, two bands; the sight glass on its front with a scale behind.
    B.box('DepotGreen', tx0, tx1, ty0, ty1, tz0, tz1)
    B.box('WornIron', tx0 - 0.012, tx1 + 0.012, ty0 - 0.012, ty1 + 0.012, tz1 - 0.03, tz1)
    for z in (tz0 + 0.18, tz0 + 0.4):
        B.box('WornIron', tx0 - 0.005, tx1 + 0.005, ty0 - 0.005, ty1 + 0.005, z, z + 0.025)
    for bxx in (tx0 + 0.15, tx1 - 0.15):
        B.prism_yz('WornIron', [(WALL_Y, tz0), (ty0 + 0.02, tz0), (ty0 + 0.02, tz0 - 0.04), (WALL_Y - 0.08, tz0 - 0.04),
                                (WALL_Y, tz0 - 0.3)], bxx - 0.008, bxx + 0.008)
    sx_, sy_, sz0, sz1 = SIGHT
    B.decal(sx_ - 0.028, sx_ + 0.028, sz0 - 0.02, sz1 + 0.02, ty0 - 0.0008, 'sightscale')
    B.cyl('Window', (sx_, sy_, sz0 - 0.01), (sx_, sy_, sz1 + 0.01), 0.012, seg=12)
    for z in (sz0 - 0.02, sz1 + 0.02):
        B.cyl('HandledBrass', (sx_, sy_, z - 0.014), (sx_, sy_, z + 0.014), 0.017, seg=10)
        B.cyl('HandledBrass', (sx_, sy_, z), (sx_, ty0, z), 0.01, seg=8)
    for s_ in (-1, 1):                                                                              # its guard rods
        B.cyl('WornIron', (sx_ + s_ * 0.02, sy_ - 0.012, sz0 - 0.01), (sx_ + s_ * 0.02, sy_ - 0.012, sz1 + 0.01), 0.003, seg=4)
    # Vance's card in a brass holder on the tank's front: APPRENTICE TEST: WATER BED 1 ONLY. ONE TANK.
    cx0, cx1, cz0, cz1 = RIGCARD
    B.box('HandledBrass', cx0 - 0.012, cx1 + 0.012, ty0 - 0.004, ty0, cz0 - 0.012, cz1 + 0.006)
    B.decal(cx0, cx1, cz0, cz1, ty0 - 0.0048, 'rigcard')
    for (a, b, c, d) in ((cx0 - 0.012, cx0 + 0.004, cz0 - 0.012, cz1), (cx1 - 0.004, cx1 + 0.012, cz0 - 0.012, cz1),
                         (cx0 - 0.012, cx1 + 0.012, cz0 - 0.012, cz0 + 0.004)):
        B.box('HandledBrass', a, b, ty0 - 0.009, ty0 - 0.004, c, d)
    # The float's chain: up from bed 1 to a pulley on the beam, along under the ceiling to a pulley on the end wall,
    # down beside the door's architrave, across under the door's head and down to the latch's eye. (The float carries
    # the chain's lowest 0.12, so there is no gap as it rises.)
    fx, fy, fz = FLOAT
    f_top = fz + 2 * FLOAT_R + 0.016 + FLOAT_RISE
    p1, p2, p3, p4 = PULLEY1, PULLEY2, PULLEY3, PULLEY4
    eye_z = LATCH[2] + 0.012 + 0.012
    chain(B, [(fx, CHAIN_Y, f_top - 0.01), (p1[0] - p1[3], CHAIN_Y, p1[2])])
    chain(B, [(p1[0], CHAIN_Y, p1[2] + p1[3]), (p2[0], CHAIN_Y, p2[2] + p2[3])])
    chain(B, [(p2[0] + p2[3], CHAIN_Y, p2[2]), (p3[0], p3[1] + p3[3], p3[2])])
    chain(B, [(p3[0], p3[1], p3[2] - p3[3]), (p4[0], p4[1], p4[2] + p4[3])])
    chain(B, [(p4[0], p4[1] - p4[3], p4[2]), (LATCH_EYE, p4[1] - p4[3], eye_z)])
    pulley(B, p1[:3], (0, 1, 0), p1[3])
    B.box('WornIron', p1[0] - 0.03, p1[0] + 0.03, CHAIN_Y - 0.03, CHAIN_Y + 0.03, CEIL - 0.165, CEIL - 0.16)   # its plate
    pulley(B, p2[:3], (0, 1, 0), p2[3], cheeks=False)
    B.box('WornIron', p2[0] - 0.01, END_X, CHAIN_Y - 0.02, CHAIN_Y + 0.02, p2[2] - 0.006, p2[2] + 0.006)       # its arm
    B.box('WornIron', END_X - 0.008, END_X, CHAIN_Y - 0.04, CHAIN_Y + 0.04, p2[2] - 0.06, p2[2] + 0.06)
    pulley(B, p3[:3], (1, 0, 0), p3[3], cheeks=False)
    B.cyl('WornIron', (p3[0], p3[1], p3[2]), (END_X, p3[1], p3[2]), 0.006, seg=6)                             # its axle
    B.box('WornIron', END_X - 0.006, END_X, p3[1] - 0.03, p3[1] + 0.03, p3[2] - 0.04, p3[2] + 0.04)
    pulley(B, p4[:3], (1, 0, 0), p4[3], cheeks=False)
    for s_ in (-1, 1):                                                                                          # hung from the head
        B.box('WornIron', p4[0] + s_ * 0.013 - 0.002, p4[0] + s_ * 0.013 + 0.002, p4[1] - 0.008, p4[1] + 0.008, p4[2], DOOR17[2])
    # The latch's bracket on the door's free jamb (the steel lining's face, y -0.5), its pin across to the bar.
    lx, ly, lz = LATCH
    B.box('WornIron', lx - 0.025, lx + 0.03, DOOR17[0], DOOR17[0] + 0.006, lz - 0.05, lz + 0.05)
    B.cyl('WornIron', (lx, DOOR17[0] + 0.006, lz), (lx, ly + 0.012, lz), 0.006, seg=6)
    B.cyl('HandledBrass', (lx, ly + 0.012, lz), (lx, ly + 0.018, lz), 0.009, seg=8)


def build_service(B):
    """The present-day service thread: the new cable (glossy black, galvanised clips about every metre, two taped
    joints) in through the left wall, along the top of the back wall, a jumper down to the new pump-and-relay box by
    the tank, on through the end wall by the stair door and up the stairwell, clipped to the well's wall, toward ring A.
    The box (galvanised, clean): the old main comes down into it, the little pump under it, and out of it the tank's
    refill, a recently repaired pipe: a bright new coupling, fresh tape. Its pilot lamp is Att17RelayLamp."""
    # The cable's path: dipping a little between its clips on the long runs.
    x0w = LWALL[1]
    run = [Vector((x0w - 0.02, CABLE_Y, CABLE_Z))]
    x = x0w + 0.35
    clips = []
    while x < END_X - 0.25:
        run.append(Vector((x - 0.5, CABLE_Y, CABLE_Z - 0.012)) if x - 0.5 > x0w + 0.1 else None)
        run.append(Vector((x, CABLE_Y, CABLE_Z)))
        clips.append((Vector((x, CABLE_Y, CABLE_Z)), Vector((1, 0, 0)), Vector((0, -1, 0))))
        x += 1.05
    run = [p for p in run if p is not None]
    run += [Vector((END_X - 0.03, CABLE_Y, CABLE_Z)), Vector((END_X - 0.03, WELL_CABLE_Y, CABLE_Z)),
            Vector((X1 + 0.04, WELL_CABLE_Y, CABLE_Z))]
    clips.append((Vector((END_X - 0.03, (CABLE_Y + WELL_CABLE_Y) / 2, CABLE_Z)), Vector((0, 1, 0)), Vector((-1, 0, 0))))
    slope = RISE / GOING
    xr = STAIR_X0 + (CABLE_Z - (RISE + 1.5)) / slope                 # where 1.5 over the nosings reaches the cable
    xt = xr + (WELL[5] - 0.05 - CABLE_Z) / slope                     # and where it goes out of the top of the well
    well = [Vector((X1 + 0.04, WELL_CABLE_Y, CABLE_Z)), Vector((xr, WELL_CABLE_Y, CABLE_Z)), Vector((xt, WELL_CABLE_Y, WELL[5] - 0.05))]
    for a, b in zip(well, well[1:]):
        L_ = (b - a).length
        k = 1
        while k * 1.05 < L_:
            p = a.lerp(b, k * 1.05 / L_)
            clips.append((p, (b - a).normalized(), Vector((0, -1, 0))))
            k += 1
    path = run + well[1:]
    for a, b in zip(path, path[1:]):
        B.cyl('NewCable', a, b, 0.011, seg=6)
    for p in path[1:-1]:
        B.sphere('NewCable', p, 0.011, seg=6)
    for p, d, n in clips:                                             # galvanised saddles, screwed to the wall
        side = d.cross(n).normalized()
        for s_ in (-1, 1):
            B._log(add_box(B.bm, p + side * s_ * 0.022 - n * 0.004, (0.012, 0.012, 0.012), mat=B.m('NewSteel')))
        B.cyl('NewSteel', p - side * 0.026 + n * 0.004, p + side * 0.026 + n * 0.004, 0.0065, seg=4)
    for t in (0.3, 0.72):                                             # taped joints
        k = int(len(run) * t)
        a, b = run[k], run[k + 1]
        B.cyl('NewCable', a.lerp(b, 0.4), a.lerp(b, 0.4) + (b - a).normalized() * 0.06, 0.016, seg=6)
    B.torus('NewSteel', (x0w + 0.004, CABLE_Y, CABLE_Z), (1, 0, 0), 0.016, 0.005, seg=10, rseg=4)     # its grommets
    B.torus('NewSteel', (END_X - 0.03, WELL_CABLE_Y, CABLE_Z), (0, 1, 0), 0.016, 0.005, seg=10, rseg=4)
    # The pump-and-relay box: galvanised, clean, a screwed lid, a gland for the jumper; the pump under it.
    bx0, bx1, by, bz0, bz1 = PUMP
    B.box('NewSteel', bx0, bx1, by, WALL_Y, bz0, bz1)
    B.box('NewSteel', bx0 + 0.012, bx1 - 0.012, by - 0.006, by, bz0 + 0.012, bz1 - 0.012)
    for xx in (bx0 + 0.03, bx1 - 0.03):
        for zz in (bz0 + 0.03, bz1 - 0.03):
            B.cyl('NewSteel', (xx, by - 0.006, zz), (xx, by - 0.011, zz), 0.007, seg=6)
    lx, ly, lz = RELAY_LAMP
    B.torus('NewSteel', (lx, by - 0.007, lz), (0, 1, 0), 0.016, 0.004, seg=12, rseg=4)            # the pilot's bezel
    gx = bx1 - 0.08
    B.cyl('NewSteel', (gx, (by + WALL_Y) / 2, bz1), (gx, (by + WALL_Y) / 2, bz1 + 0.03), 0.018, seg=8)
    pipe(B, [(gx, (by + WALL_Y) / 2, bz1 + 0.03), (gx, CABLE_Y, bz1 + 0.12), (gx, CABLE_Y, CABLE_Z - 0.01)], mt='NewCable', r=0.008)
    my_ = (by + WALL_Y) / 2
    B.cyl('NewSteel', (bx0 + 0.04, my_, bz0 - 0.09), (bx1 - 0.06, my_, bz0 - 0.09), 0.055, seg=14)  # the pump
    for xx in (bx0 + 0.04, bx1 - 0.06):
        B.cyl('NewSteel', (xx - 0.006, my_, bz0 - 0.09), (xx + 0.006, my_, bz0 - 0.09), 0.06, seg=14)
    B.box('NewSteel', bx0 + 0.08, bx1 - 0.1, my_ - 0.03, WALL_Y, bz0 - 0.16, bz0 - 0.14)          # its foot, to the wall
    B.cyl('NewSteel', ((bx0 + bx1) / 2, my_, bz0 - 0.04), ((bx0 + bx1) / 2, my_, bz0), 0.014, seg=8)
    # The old main comes down into it; out of its side, the tank's refill (old copper, a newly repaired joint).
    ix = bx0 + 0.1
    pipe(B, [(ix, my_ + 0.02, CEIL), (ix, my_ + 0.02, bz1)], mt='Copper', r=0.012)
    tx1, tz1, ry = TANK[1], TANK[5], 1.17
    ox = tx1 + 0.1
    pipe(B, [(bx0, ry, bz1 - 0.05), (ox, ry, bz1 - 0.05), (ox, ry, tz1 + 0.12), (TANK[0] + 1.05, ry, tz1 + 0.12),
             (TANK[0] + 1.05, ry, tz1 - 0.02)], mt='Copper', r=0.012)
    cx = (ox + TANK[0] + 1.05) / 2
    B.cyl('NewSteel', (cx - 0.028, ry, tz1 + 0.12), (cx + 0.028, ry, tz1 + 0.12), 0.019, seg=10)    # the new coupling
    for xx in (cx - 0.028, cx + 0.028):
        B.cyl('NewSteel', (xx - 0.004, ry, tz1 + 0.12), (xx + 0.004, ry, tz1 + 0.12), 0.022, seg=6)
    for xx in (cx - 0.06, cx + 0.06):                                                               # fresh tape
        B.cyl('NewCable', (xx - 0.013, ry, tz1 + 0.12), (xx + 0.013, ry, tz1 + 0.12), 0.0155, seg=8)


def build_relay_lamp(coll):
    """Att17RelayLamp: the new box's tiny green pilot lamp (EMIT Att17RelayLamp); origin its centre."""
    B = MB()
    B.sphere('Att17RelayLamp', RELAY_LAMP, 0.011, seg=10, scale=(1, 0.6, 1))
    return B.obj('Att17RelayLamp', coll, origin=RELAY_LAMP)


# =====================================================================================================================
# The rig's moving parts (own objects, origins at their pivots)
# =====================================================================================================================
def t_key(B):
    """Vance's T-key, its socket's centre at the origin, its shaft toward -y, its bar along x."""
    B.box('WornIron', -0.012, 0.012, -0.026, 0.012, -0.012, 0.012)
    B.cyl('WornIron', (0, -0.026, 0), (0, -0.056, 0), 0.0065, seg=8)
    B.sphere('HandledBrass', (0, -0.058, 0), 0.011, seg=8)
    B.cyl('WornIron', (-0.07, -0.064, 0), (0.07, -0.064, 0), 0.0075, seg=8)
    for x in (-0.07, 0.07):
        B.sphere('WornIron', (x, -0.064, 0), 0.01, seg=8)


def set_parent(child, parent):
    """Parent child to parent, keeping where it is (parent unrotated): the child's location becomes relative."""
    child.parent = parent
    child.matrix_parent_inverse = Matrix.Identity(4)
    child.location = child.location - parent.location


def build_valve(coll):
    """Att17Valve: the valve's wheel (spokes, rim, hub), its spindle and the spindle's square end; origin the wheel's
    centre. It spins about Blender y (game z) while the water runs."""
    B = MB()
    vx, vy, vz = VALVE
    r = VALVE_R
    B.torus('WornIron', (vx, vy, vz), (0, 1, 0), r, 0.009, seg=24, rseg=6)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        B.cyl('WornIron', (vx, vy, vz), (vx + r * math.cos(a), vy, vz + r * math.sin(a)), 0.006, seg=6)
    B.cyl('WornIron', (vx, vy + 0.012, vz), (vx, vy - 0.012, vz), 0.016, seg=10)
    B.cyl('WornIron', (vx, 0.53, vz), (vx, SPINDLE_TIP + 0.01, vz), 0.006, seg=6)
    B.box('WornIron', vx - 0.007, vx + 0.007, SPINDLE_TIP, SPINDLE_TIP + 0.012, vz - 0.007, vz + 0.007)
    B.sphere('Att17Atlas', (vx + r * 0.7, vy - 0.006, vz + r * 0.7), 0.01, seg=6, cell='sw_red')   # a dab of red paint
    return B.obj('Att17Valve', coll, origin=VALVE)


def build_valve_key(coll, valve):
    """Att17ValveKey: the T-key on the valve's spindle (hidden until he has it); origin on the spindle's end. A child of
    Att17Valve, so it turns with the wheel."""
    B = MB()
    t_key(B)
    ob = B.obj('Att17ValveKey', coll)
    ob.location = (VALVE[0], SPINDLE_TIP, VALVE[2])
    set_parent(ob, valve)
    return ob


def build_key(coll, drawer):
    """Att17Key: the T-key in the drawer, lying on the papers (hidden once he has read: he takes it); origin its socket's
    centre. A child of Att17Drawer, so it slides out with it."""
    B = MB()
    n0 = B.mark()
    t_key(B)
    B.xform(n0, Matrix.Rotation(KEY_AT[3], 4, 'Z'))
    ob = B.obj('Att17Key', coll)
    ob.location = KEY_AT[:3]
    set_parent(ob, drawer)
    return ob


def build_sluice(coll, name, x):
    """Att17Sluice<name>: the lever, OPEN (handle up): its hub on the pivot (along x), a flat iron arm, a turned grip;
    origin the pivot. Shut = +80 degrees about x (the grip comes forward, toward the camera)."""
    B = MB()
    py, pz = SLUICE_PIVOT
    B.cyl('WornIron', (x - 0.016, py, pz), (x + 0.016, py, pz), 0.016, seg=10)
    B.box('WornIron', x - 0.008, x + 0.008, py - 0.006, py + 0.006, pz - 0.012, pz + LEVER_L - 0.05)
    B.cyl('PupilWood', (x, py, pz + LEVER_L - 0.06), (x, py, pz + LEVER_L - 0.012), 0.013, 0.015, seg=10)
    B.sphere('PupilWood', (x, py, pz + LEVER_L - 0.012), 0.016, seg=10, scale=(1, 1, 0.75))
    return B.obj('Att17Sluice' + name, coll, origin=(x, py, pz))


def build_tank_water(coll):
    """Att17TankWater: the water in the sight glass, full; origin the glass's bottom; scales in z."""
    B = MB()
    sx_, sy_, sz0, sz1 = SIGHT
    B.cyl('Water', (sx_, sy_, sz0), (sx_, sy_, sz1), 0.009, seg=10)
    return B.obj('Att17TankWater', coll, origin=(sx_, sy_, sz0))


def build_bed_water(coll, i):
    """Att17Water<i>: bed i's water, full (0.13 deep); origin the middle of the tray's floor; scales in z (0 to 1)."""
    B = MB()
    bx0, bx1 = BEDS[i - 1]
    by0, by1 = BED_Y
    t = BED_T + 0.001
    B.box('Water', bx0 + t, bx1 - t, by0 + t, by1 - t, WATER_Z, WATER_Z + WATER_D)
    return B.obj('Att17Water%d' % i, coll, origin=((bx0 + bx1) / 2, (by0 + by1) / 2, WATER_Z))


def build_stream(coll, i):
    """Att17Stream<i>: the water falling from the spout over bed i to the tray's floor; origin the spout's mouth."""
    B = MB()
    x, (y, z) = SPOUT_X[i - 1], MOUTH
    B.cyl('Water', (x, y, z), (x, y, WATER_Z + 0.004), 0.009, 0.006, seg=8)
    B.cyl('Water', (x + 0.003, y - 0.002, z - 0.02), (x - 0.002, y + 0.003, WATER_Z + 0.004), 0.005, 0.004, seg=6)
    return B.obj('Att17Stream%d' % i, coll, origin=(x, y, z))


def build_float(coll):
    """Att17Float: a copper ball float in bed 1, low, an eye on its top and the chain's lowest 0.12 hanging from it;
    origin its bottom. It rises 0.12 with bed 1's water."""
    B = MB()
    fx, fy, fz = FLOAT
    r = FLOAT_R
    B.sphere('Copper', (fx, fy, fz + r), r, seg=14)
    B.torus('Copper', (fx, fy, fz + 2 * r), (0, 0, 1), r * 0.4, 0.004, seg=12, rseg=4)
    B.torus('WornIron', (fx, fy, fz + 2 * r + 0.008), (0, 1, 0), 0.008, 0.0025, seg=8, rseg=3)
    chain(B, [(fx, fy, fz + 2 * r + 0.016), (fx, fy, fz + 2 * r + 0.016 + FLOAT_RISE)])
    return B.obj('Att17Float', coll, origin=FLOAT)


def build_latch(coll):
    """Att17Latch: the stair door's drop latch, DOWN (locked): a flat iron bar pivoted on a bracket on the free jamb at
    the wall's face, running +x across the reveal; its nib drops into the keeper on the leaf's room face (part of
    Att17Door), so the leaf can't be pushed open; the chain's eye on its top. Origin the pivot. Up: 70 degrees about
    Blender -y (game +z: three.js rotateZ(+70 deg)), its end rising 0.12 and back out of the keeper. On the frame, not
    the door: it stays where it is when the door swings."""
    B = MB()
    lx, ly, lz = LATCH
    B.cyl('WornIron', (lx, ly - 0.012, lz), (lx, ly + 0.012, lz), 0.018, seg=12)                 # its hub on the pin
    B.box('WornIron', lx, lx + LATCH_L, ly - 0.005, ly + 0.005, lz - 0.012, lz + 0.012)
    B.box('WornIron', lx + LATCH_L - 0.012, lx + LATCH_L, ly - 0.005, ly + 0.005, lz - 0.042, lz - 0.012)   # its nib
    B.torus('WornIron', (LATCH_EYE, ly, lz + 0.012 + 0.006), (0, 1, 0), 0.008, 0.0025, seg=8, rseg=3)
    B.box('WornIron', lx + 0.02, lx + 0.05, ly - 0.005, ly + 0.005, lz + 0.012, lz + 0.024)       # a thumb tab
    return B.obj('Att17Latch', coll, origin=LATCH)


# =====================================================================================================================
# What the game moves
# =====================================================================================================================
def build_drawer(coll):
    """The PLACEMENTS drawer, shut: its front with a bar pull and a label, its box, the papers it is full of; on top,
    Mara's irrigation drawing (the right, beside the mended pot when it is out), a pencil on it, and her placement
    card on the left; other children's cards and papers under them."""
    B = MB()
    x0, x1, fy, z0, z1 = DRAWER
    fb = CHEST_FRONT
    B.box('PupilWood', x0, x1, fy, fb, z0, z1)
    for (a, b, c, d) in ((x0 + 0.03, x1 - 0.03, z0 + 0.03, z0 + 0.045), (x0 + 0.03, x1 - 0.03, z1 - 0.045, z1 - 0.03),
                         (x0 + 0.03, x0 + 0.045, z0 + 0.03, z1 - 0.03), (x1 - 0.045, x1 - 0.03, z0 + 0.03, z1 - 0.03)):
        B.box('PupilWood', a, b, fy - 0.006, fy, c, d)                                     # the bead round its panel
    cx = (x0 + x1) / 2
    for hx in (cx - 0.11, cx + 0.11):
        B.cyl('HandledBrass', (hx, fy, 0.28), (hx, fy - 0.04, 0.28), 0.009, seg=8)
    B.cyl('HandledBrass', (cx - 0.13, fy - 0.04, 0.28), (cx + 0.13, fy - 0.04, 0.28), 0.0105, seg=10)
    lx0, lx1, lz0, lz1 = cx - 0.24, cx + 0.24, 0.36, 0.45
    for (a, b, c, d) in ((lx0 - 0.012, lx1 + 0.012, lz0 - 0.012, lz0), (lx0 - 0.012, lx1 + 0.012, lz1, lz1 + 0.012),
                         (lx0 - 0.012, lx0, lz0, lz1), (lx1, lx1 + 0.012, lz0, lz1)):
        B.box('HandledBrass', a, b, fy - 0.01, fy, c, d)
    B.decal(lx0, lx1, lz0, lz1, fy - 0.0072, 'placements')
    # The box.
    bx0, bx1, by1, bz0, bz1 = 285.30, 286.70, 1.235, 0.13, 0.44
    B.box('PigeonWood', bx0, bx0 + 0.015, fb, by1, bz0, bz1)
    B.box('PigeonWood', bx1 - 0.015, bx1, fb, by1, bz0, bz1)
    B.box('PigeonWood', bx0, bx1, by1 - 0.015, by1, bz0, bz1)
    B.box('PigeonWood', bx0, bx1, fb, by1, bz0, bz0 + 0.015)
    # The papers it is full of, and what lies on top.
    ix0, ix1, iy0, iy1 = bx0 + 0.016, bx1 - 0.016, fb + 0.002, by1 - 0.016
    B.sbox('sw_paper', ix0, ix1, iy0, iy1, bz0 + 0.015, CONTENT_Z - 0.006)
    for k in range(6):                                        # sheets' edges, uneven, along the front of the stack
        z = CONTENT_Z - 0.03 - k * 0.035
        B.sbox(('sw_white', 'sw_label', 'sw_paper')[k % 3], ix0 + 0.01 * (k % 2), ix1 - 0.012 * (k % 3), iy0 - 0.0015, iy0, z, z + 0.012)
    z = CONTENT_Z - 0.005
    for (cell, sx, sy, w, d, ang) in (('sw_white', 285.6, 0.95, 0.42, 0.52, 0.04), ('paper2', 285.52, 0.97, 0.21, 0.297, 0.14),
                                      ('seedlist', 285.62, 1.08, 0.3, 0.075, -0.06), ('paper1', 285.82, 1.0, 0.21, 0.297, -0.07),
                                      ('cardC', 285.55, 0.745, 0.2, 0.125, -0.12), ('cardB', 285.5, 0.86, 0.2, 0.125, 0.2),
                                      ('sw_label', 286.38, 0.88, 0.56, 0.41, -0.025)):
        z += 0.0009
        B.sheet(cell, sx, sy, z, w, d, ang)
    z += 0.0012
    dwg = (286.385, 0.86, z, 0.50, 0.35, 0.03)
    B.sheet('drawing', *dwg, edge=0.0008)
    card = (285.93, 0.82, z + 0.0012, 0.20, 0.125, -0.09)
    B.sheet('card', *card, edge=0.0006)
    # A pencil on the drawing, sharpened; a rubber.
    p0, p1 = Vector((286.085, 0.92, z + 0.0045)), Vector((286.1, 0.75, z + 0.0045))
    B.scyl('sw_pencil', p0, p1, 0.0038, seg=6)
    B.scyl('sw_lolly', p1, p1 + (p1 - p0).normalized() * 0.016, 0.0038, 0.001, seg=6)
    B.sbox('sw_red', 285.36, 285.4, 0.69, 0.71, z - 0.004, z + 0.004)
    global DRAWING_AT, CARD_AT
    DRAWING_AT, CARD_AT = dwg, card
    ob = B.obj('Att17Drawer', coll, origin=DRAWER_ORIGIN)
    return ob


DRAWING_AT = CARD_AT = None


def build_tray(coll):
    """Att17Tray: a heavy wooden seed tray, its soil dried hard, shrunk from the sides and cracked into plates, its
    seedlings long dead (shrivelled brown stalks, fallen flat); a name tag (T. ORME). Built level about its bottom
    centre; the object's rotation tips it where it lies."""
    B = MB()
    w, d, h = TRAY_SIZE
    t = 0.014
    B.box('CrateWood', -w / 2, w / 2, -d / 2, -d / 2 + t, 0.006, h)
    B.box('CrateWood', -w / 2, w / 2, d / 2 - t, d / 2, 0.006, h)
    B.box('CrateWood', -w / 2, -w / 2 + t, -d / 2 + t, d / 2 - t, 0.006, h)
    B.box('CrateWood', w / 2 - t, w / 2, -d / 2 + t, d / 2 - t, 0.006, h)
    for k in range(4):                                        # the slatted bottom
        y = -d / 2 + t + k * (d - 2 * t) / 4
        B.box('CrateWood', -w / 2 + t, w / 2 - t, y + 0.002, y + (d - 2 * t) / 4 - 0.002, 0.006, 0.016)
    for sx in (-1, 1):                                        # two runners under it
        B.box('CrateWood', -w / 2 + 0.01, w / 2 - 0.01, sx * (d / 2 - 0.035) - 0.012, sx * (d / 2 - 0.035) + 0.012, 0.0, 0.006)
    # The soil: dried hard, shrunk from the tray's sides (a dark gap all round), cracked into plates.
    rnd = random.Random(1760)
    sx0, sx1, sy0, sy1 = -w / 2 + t, w / 2 - t, -d / 2 + t, d / 2 - t
    g = 0.008
    ax0, ax1, ay0, ay1 = sx0 + g, sx1 - g, sy0 + g, sy1 - g
    zs = h - 0.026                                             # the crust's top
    B.sbox('sw_soil_dark', sx0, sx1, sy0, sy1, 0.016, zs - 0.03)
    B.sbox('sw_crust', ax0, ax1, ay0, ay1, zs - 0.03, zs - 0.004)
    nx, ny = 10, 7
    cu0, cv0, cu1, cv1 = cell_uv('soilcrack')
    asp = (ay1 - ay0) / (ax1 - ax0)
    verts, uvs = [[None] * (ny + 1) for _ in range(nx + 1)], {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x, y = ax0 + (ax1 - ax0) * i / nx, ay0 + (ay1 - ay0) * j / ny
            edge = i in (0, nx) or j in (0, ny)
            zz = zs - (0.003 if edge else rnd.uniform(-0.002, 0.003))
            v = B.bm.verts.new((x, y, zz))
            verts[i][j] = v
            uvs[v] = (cu0 + (cu1 - cu0) * i / nx, cv0 + (cv1 - cv0) * asp * j / ny)
    sm = B.m('Att17Atlas')
    for i in range(nx):
        for j in range(ny):
            f = B.bm.faces.new((verts[i][j], verts[i + 1][j], verts[i + 1][j + 1], verts[i][j + 1]))
            f.material_index = sm
            f[B.flat] = 1
            for lp in f.loops:
                lp[B.uv].uv = uvs[lp.vert]
    # A few plates lifted at their edges, curled.
    for _ in range(5):
        cx, cy = rnd.uniform(ax0 + 0.04, ax1 - 0.04), rnd.uniform(ay0 + 0.03, ay1 - 0.03)
        n0 = B.mark()
        B.sbox('sw_crust', -0.02, 0.02, -0.014, 0.014, -0.002, 0.003)
        B.xform(n0, Matrix.Translation((cx, cy, zs + 0.004)) @ Matrix.Rotation(rnd.uniform(0, 3.1), 4, 'Z') @
                Matrix.Rotation(rnd.uniform(0.15, 0.3), 4, 'X'))
    # The seedlings, long dead: shrivelled brown stalks, fallen over on the crust.
    for i in range(4):
        for j in range(7):
            if rnd.random() < 0.2:
                continue
            x, y = sx0 + 0.035 + j * (sx1 - sx0 - 0.07) / 6, sy0 + 0.035 + i * (sy1 - sy0 - 0.07) / 3
            dead_plant(B, x, y, zs, rnd, n=1, h=rnd.uniform(0.03, 0.06), cell=rnd.choice(('sw_shrivel', 'sw_deadleaf', 'sw_straw')),
                       droop=rnd.uniform(1.2, 1.8))
    name_tag(B, sx1 - 0.04, sy0 + 0.03, zs, 1, 0.1, tall=0.075)
    B.decal(-0.06, 0.06, 0.028, 0.028 + 0.12 * 40 / 128, -d / 2 - 0.0008, 'tag1')
    ob = B.obj('Att17Tray', coll)
    M = tray_matrix()
    ob.matrix_world = M
    return ob


def build_growlamp(coll):
    B = MB()
    g0, g1, gy, gz = GROW
    for dy in (-0.045, 0.045):
        B.cyl('Att17GrowLamp', (g0, gy + dy, gz), (g1, gy + dy, gz), 0.014, seg=10)
    return B.obj('Att17GrowLamp', coll, origin=((g0 + g1) / 2, gy, gz))


def build_door_leaf(coll):
    """Att17Door: the stair door's leaf, shut, hung flush with the end wall's stair-side face; steel-faced, green, a
    wired-glass light (the game's see-through Window glass, the lit stair behind it), a kick plate, lever handles both
    sides. Origin on its hinge axis at floor level: the back jamb's stair-side corner, HINGE. It opens away from the
    room, toward the stair: +90 degrees about Blender +z (game +y); open, it stands along the stairwell's back,
    x 296.0 to 297.0, y 0.455 to 0.5, clear of the first riser (x 297.1) and of the lane."""
    B = MB()
    hx, hy, _ = HINGE
    dy0, dy1, hd = DOOR17
    fx0, fx1 = hx - LEAF_T, hx                                  # its faces: room side, stair side
    ly0, ly1, lz0, lz1 = dy0 + 0.005, dy1 - 0.005, 0.008, hd - 0.006
    gy0, gy1, gz0, gz1 = -0.2, 0.2, 1.2, 1.82                  # the glass light
    for (a, b, c, d_) in ((ly0, ly1, lz0, gz0), (ly0, ly1, gz1, lz1), (ly0, gy0, gz0, gz1), (gy1, ly1, gz0, gz1)):
        B.box('DepotGreen', fx0, fx1, a, b, c, d_)
    B.box('Window', fx0 + 0.016, fx1 - 0.016, gy0, gy1, gz0, gz1)
    for fx, s in ((fx0, -1), (fx1, 1)):                          # beads round the glass, both faces; the wire mesh in it
        for (a, b, c, d_) in ((gy0 - 0.02, gy1 + 0.02, gz0 - 0.02, gz0), (gy0 - 0.02, gy1 + 0.02, gz1, gz1 + 0.02),
                              (gy0 - 0.02, gy0, gz0, gz1), (gy1, gy1 + 0.02, gz0, gz1)):
            B.box('WornIron', min(fx, fx + s * 0.006), max(fx, fx + s * 0.006), a, b, c, d_)
    for k in range(1, 6):
        z = gz0 + (gz1 - gz0) * k / 6
        B.box('WornIron', (fx0 + fx1) / 2 - 0.001, (fx0 + fx1) / 2 + 0.001, gy0, gy1, z - 0.0012, z + 0.0012)
    for k in range(1, 4):
        y = gy0 + (gy1 - gy0) * k / 4
        B.box('WornIron', (fx0 + fx1) / 2 - 0.001, (fx0 + fx1) / 2 + 0.001, y - 0.0012, y + 0.0012, gz0, gz1)
    B.box('WornIron', fx0 - 0.004, fx0, ly0 + 0.03, ly1 - 0.03, 0.03, 0.27)                  # kick plate (room side)
    B.box('HandledBrass', fx0 - 0.003, fx0, ly0 + 0.06, ly0 + 0.16, 1.15, 1.45)             # finger plate, by the free edge
    for fx, s in ((fx0, -1), (fx1, 1)):                          # lever handles, by the free edge
        hy_ = ly0 + 0.08
        B.cyl('HandledBrass', (fx, hy_, 1.0), (fx + s * 0.012, hy_, 1.0), 0.03, seg=12)
        B.cyl('HandledBrass', (fx + s * 0.012, hy_, 1.0), (fx + s * 0.055, hy_, 1.0), 0.009, seg=8)
        B.cyl('HandledBrass', (fx + s * 0.055, hy_, 1.0), (fx + s * 0.06, hy_ + 0.12, 1.0), 0.009, seg=8)
        B.box('HandledBrass', min(fx, fx + s * 0.004), max(fx, fx + s * 0.004), hy_ - 0.012, hy_ + 0.012, 0.86, 0.92)   # keyhole plate
    lx, ly, lz = LATCH                                           # the keeper the latch's nib drops into (a pocket)
    B.box('WornIron', fx0 - 0.004, fx0, ly - 0.022, ly + 0.022, lz - 0.075, lz - 0.005)
    B.box('WornIron', fx0 - 0.027, fx0, ly - 0.022, ly + 0.022, lz - 0.075, lz - 0.065)
    B.box('WornIron', fx0 - 0.027, fx0 - 0.022, ly - 0.022, ly + 0.022, lz - 0.065, lz - 0.018)
    for z in (0.25, 1.05, 1.85):                                 # hinge knuckles on the stair side
        B.cyl('WornIron', (hx + 0.006, hy - 0.004, z - 0.06), (hx + 0.006, hy - 0.004, z + 0.06), 0.011, seg=8)
        B.box('WornIron', fx1, fx1 + 0.003, hy - 0.09, hy - 0.006, z - 0.05, z + 0.05)
    return B.obj('Att17Door', coll, origin=HINGE)


def build_stairlamp(coll):
    """Att17StairLamp: the globe of the bulkhead lamp over the flight, high on the stairwell's back wall."""
    B = MB()
    lx, ly, lz = STAIR_LAMP
    B.sphere('Att17StairLamp', (lx, ly, lz), 0.055, seg=12, scale=(1, 0.7, 1))
    return B.obj('Att17StairLamp', coll, origin=STAIR_LAMP)


def build_bulbs(coll):
    B = MB()
    B.sphere('Att17Bulb', PENDANT, 0.04, seg=12)
    aim = (LAMP_AIM - LAMP_HEAD).normalized()
    B.sphere('Att17Bulb', LAMP_HEAD + aim * 0.07, 0.03, seg=10)
    lx, ly, lz = DOOR_LAMP
    B.sphere('Att17Bulb', (lx, ly - 0.01, lz), 0.04, seg=10, scale=(1, 0.7, 1))
    return B.obj('Att17Bulbs', coll)


# =====================================================================================================================
def tris(ob):
    if ob.type != 'MESH':
        return 0
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


PLAYER_INFO = None


def build_set(dl01, m, coll):
    global PLAYER_INFO
    make_textures()
    rnd = random.Random(1717)
    names = Names()
    B = MB()
    build_shell(B)
    build_entry(B)
    build_shelf(B, rnd, names)
    build_bench(B, rnd, names)
    build_bench_top(B, rnd)
    build_board(B)
    build_stool(B)
    tap = build_window(B, rnd, names)
    build_sink(B, tap)
    build_door(B)
    build_stairwell(B)
    build_ceiling_lights(B)
    build_floor_things(B, rnd)
    heap_under_tray(B)
    build_rig(B, random.Random(1790))
    build_service(B)
    PLAYER_INFO = place_card_player(B)
    objs = [B.obj('Att17Set', coll)]
    drawer = build_drawer(coll)
    objs.append(drawer)
    objs.append(build_tray(coll))
    objs.append(build_growlamp(coll))
    objs.append(build_bulbs(coll))
    door = build_door_leaf(coll)
    objs.append(door)
    objs.append(build_stairlamp(coll))
    # The test rig's moving parts (the expansion).
    valve = build_valve(coll)
    objs += [valve, build_valve_key(coll, valve), build_key(coll, drawer), build_latch(coll)]
    objs += [build_sluice(coll, name, x) for name, x, bed in SLUICES]
    objs.append(build_tank_water(coll))
    objs += [build_bed_water(coll, i) for i in (1, 2, 3)]
    objs += [build_stream(coll, i) for i in (1, 2, 3)]
    objs.append(build_float(coll))
    objs.append(build_relay_lamp(coll))
    bpy.context.view_layer.update()
    total_t, total_p = 0, 0
    for ob in objs:
        t = tris(ob)
        prim = len(ob.material_slots)
        total_t += t
        total_p += prim
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        print('dl17: %-14s tris %6d mats %-2d origin %s%s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f %s' % (
            ob.name, t, prim, tuple(round(c, 4) for c in ob.matrix_world.translation),
            ' (child of %s, local %s)' % (ob.parent.name, tuple(round(c, 4) for c in ob.location)) if ob.parent else '',
            min(v.x for v in bb), max(v.x for v in bb), min(v.y for v in bb), max(v.y for v in bb), min(v.z for v in bb),
            max(v.z for v in bb), [s.material.name for s in ob.material_slots]))
    print('dl17: total tris %d, draw calls (material slots) %d' % (total_t, total_p))
    print('dl17: drawing at', DRAWING_AT, 'card at', CARD_AT)
    print('dl17: treads (x0, x1, top):', [tuple(round(c, 3) for c in tread_x(i)) + (round(tread_top(i), 3),) for i in range(1, TREADS + 1)],
          'upper landing from x %.3f at %.3f' % (tread_x(TREADS)[1], tread_top(TREADS + 1)))
    print('dl17: tray rotation (deg)', tuple(round(math.degrees(a), 2) for a in objs[2].rotation_euler), 'loc', tuple(objs[2].location))


REPORT = """DL-17 A Different Lesson (art/ch1/dl17.py). Blender (x, y, z) -> game (x, z, -y). Built 21 October 2026,
revised the same day for rev 0.3 (her drawing with his notes beside it, the card, the dead trays, the stair door).

MOVED / ANIMATED (origin = pivot, world coordinates)
- Att17Drawer: built SHUT. Origin = middle of its front face, Blender (286.0, 0.62, 0.30) = game (286.0, 0.30, -0.62).
  The front is x 285.3-286.7, z 0.12-0.48. Slide 0.45 toward the camera: Blender -y (game +z). Open origin is
  Blender y 0.17 (game z -0.17). Its contents are part of its mesh: papers, other children's cards (R. ABEL,
  T. ORME), the drawing, a pencil, a rubber, and the card. The label PLACEMENTS sits in a brass frame above a bar pull.
- Att17Tray: the carried seed tray, 0.42 x 0.30 x 0.09: soil dried hard, shrunk from the sides, cracked into plates
  (crust top 0.064 above its bottom), shrivelled brown stalks fallen on it, tag "T. ORME". Nothing green.
  The mesh is built level about its bottom centre. Lying pose: location Blender (285.7, 0.05, 0.026) = game
  (285.7, 0.026, -0.05); rotation_euler XYZ (10, 0, -9) degrees (its back edge is up on a heap of spilled soil).
  Zero rotation = level, as carried; when level, its bottom is at the origin.
  Its footprint (Blender y -0.16..0.23) overlaps the open drawer's front (y 0.17), so the drawer is blocked until
  the tray moves. It can't literally touch the handle (handle at y 0.58, tray centre given as y 0.05).
- Att17GrowLamp: EMIT, two tubes x 289.42-291.58 at Blender y 1.005 / 1.095, z 1.60. Origin Blender (290.5, 1.05, 1.60)
  = game (290.5, 1.60, -1.05). Rev 0.3: switch it off (nothing under it is alive).
- Att17Door: the stair door's leaf, built SHUT, in the right end wall's doorway. Origin = its hinge axis at the floor,
  Blender (296.0, 0.5, 0.0) = game (296.0, 0.0, -0.5): the stair-side face of the end wall (x 296.0), at the back
  jamb. Shut, the leaf is x 295.955-296.0, Blender y -0.495..0.495 (game z -0.495..0.495), z 0.008-2.144 (handles
  stand to x 295.895 on the room side). OPEN: rotate +90 degrees about the vertical axis, i.e. Blender rotation z
  +pi/2 = three.js rotation.y += +pi/2 (game +y). The free edge (game z +0.495, the camera side) swings away from the
  room, round into +x. Open, the leaf stands along the stairwell's back: x 296.0-297.0, game z -0.5..-0.455, clear
  of the lane and of the first riser (x 297.1). A wired-glass light in it (Window glass, see-through) shows the lit
  stair while it is shut.
Static extras: Att17Bulbs (EMIT Att17Bulb: pendant (285.95, 0.80, 2.215), bench lamp (285.05, 0.89, 1.33), bulkhead
by the door on the back wall (295.25, 1.19, 2.25)); Att17StairLamp (EMIT Att17StairLamp, the globe of the lamp over
the flight: Blender (299.3, 0.84, 3.62) = game (299.3, 3.62, -0.84)); Att17Set (everything else).
REMOVED: Att17Shoot (the living shoot) and its use of AttShoot. M. D.'s pot under the grow lamp now holds dry soil
and a dead stalk, like the rest.

THE TEST RIG (the expansion, docs/chapter1_expansion_build.md "DL-17 changes"). Numbers in this file's OLD x: the
builder adds +44 (292.55 here is 336.55 in the game). Blender (x, y, z) -> game (x, z, -y).
- Att17Valve: origin = the wheel's centre, Blender (292.55, 0.50, 0.70) = game (292.55, 0.70, -0.50). A spoked iron
  wheel r 0.085 facing the camera (rim y 0.491-0.509), its hub and spindle back to the valve's body on the down-pipe
  (Blender y 0.60); the spindle's square end at y 0.47-0.482. Spins about Blender y = game z (three.js rotateZ).
- Att17ValveKey: Vance's T-key on the spindle, built visible. A CHILD of Att17Valve (it turns with the wheel): local
  Blender (0, -0.03, 0) = glTF local (0, 0, +0.03); world origin (292.55, 0.47, 0.70) = game (292.55, 0.70, -0.47), the
  socket over the spindle's end. Shaft toward the camera, the bar along x: x 292.47-292.63, Blender y 0.396-0.42 (its
  nearest point to the lane, game z -0.396), z 0.69-0.71.
- Att17Key: the same T-key in the drawer, lying on the papers (left of her card), turned 0.5 rad. A CHILD of
  Att17Drawer (it slides out with it): local Blender (-0.40, 0.42, 0.1065) = glTF local (-0.40, 0.1065, -0.42). World
  origin (its socket's centre) shut (285.60, 1.04, 0.4065), open (285.60, 0.59, 0.4065) = game (285.60, 0.4065, -0.59);
  footprint x 285.56-285.70, y 0.94-1.06 shut (0.49-0.61 open, out of the carcass), z 0.395-0.419.
- Att17SluiceA / B / C: built OPEN, handle up. Origins = the pivots, Blender (293.45 / 294.10 / 294.80, 0.33, 0.45) =
  game (x, 0.45, -0.33): a hub on a pin along x in an iron bracket on the bench's front panel, a flat iron arm, a
  turned wooden grip to z 0.60. SHUT = +80 deg about x (three.js rotateX(+80 deg)): the grip comes forward, toward the
  camera, to Blender y ~0.18 (game z -0.18), z 0.48. Enamel letters A, B, C under them on the panel (z 0.27-0.33).
- The pipes, all the same brass (HandledBrass, r 0.013), plainly crossing on a cream board behind the bench
  (x 293.0-295.35, z 0.56-1.40, face y 1.255): from each sluice's cock, back under the bench top, up behind it:
    A: riser x 293.45 at y 1.02 (in front), runs RIGHT at z 0.95 to x 294.98, forward, spout over BED 3.
    B: riser x 294.10 at y 1.18 (at the back), runs LEFT at z 1.25 to x 293.25, forward, spout over BED 1.
    C: riser x 294.80 at y 1.10, runs LEFT at z 1.10 to x 293.95, forward, spout over BED 2.
  A's run passes in front of B's and C's risers; C's run in front of B's; C's spout comes forward over A's run.
  Spout mouths at Blender y 0.66, z 0.86.
- Att17Stream1 / 2 / 3 (EVERY one is "the water over bed N", not by lever): origins = the spout's mouth, Blender
  (293.25 / 293.95 / 294.98, 0.66, 0.86) = game (x, 0.86, -0.66); a falling thread (r 0.009 to 0.006) down to the
  tray's floor (0.569). Built visible; material Water.
- The test bench: x 293.05-295.30, Blender y 0.35-0.95, top 0.55 (front panel y 0.35-0.37, z 0.2-0.51). Beds on it:
  bed 1 x 293.10-293.75 (M. D.), bed 2 293.80-294.45 (R. A.), bed 3 294.50-295.15 (T. O.); y 0.45-0.85; trays 0.015
  thick, floor top 0.565, rims 0.70; a skin of dry soil to 0.58 and a few dead seedlings; name cards in Vance's ink on
  the trays' fronts (right of centre, clear of the levers), z 0.62-0.66.
- Att17Water1 / 2 / 3: built FULL (0.13 deep, z 0.565-0.695). Origins = the middle of each tray's floor, Blender
  (293.425 / 294.125 / 294.825, 0.65, 0.565) = game (x, 0.565, -0.65); each 0.618 x 0.368. Scale y (game) 0..1.
- Att17Float: a copper ball r 0.045 with an eye, LOW: origin = its bottom on bed 1's soil, Blender (293.60, 0.64, 0.58)
  = game (293.60, 0.58, -0.64); the chain's lowest 0.12 hangs from it (to z 0.806), so it rises 0.12 without a gap.
- The tank: x 293.0-294.2, Blender y 0.76-1.24, z 1.70-2.30, painted (DepotGreen), on two wall brackets; a copper feed
  into its top from the ceiling (it refills); its down-pipe (copper r 0.016) leaves its left end at z 1.76, runs to x
  292.55, forward to y 0.60, down through the valve (body at z 0.70) to z 0.30, then along under the bench (y 0.60) to
  the three cocks. The sight glass on its front: x 293.95, axis y 0.735, z 1.78-2.22, a scale behind it.
- Att17TankWater: the water in the sight glass, FULL: origin = the glass's bottom, Blender (293.95, 0.735, 1.78) =
  game (293.95, 1.78, -0.735); 0.44 tall, r 0.009. Scale y (game) 0..1.
- Vance's card in a brass holder on the tank's front: x 293.10-293.40, z 1.92-2.10 (face y 0.755): "APPRENTICE TEST:
  WATER BED 1 ONLY. ONE TANK. - E.V." (atlas cell rigcard).
- The chain (static, in Att17Set): from the float up at (293.60, y 0.64) to a pulley hung from the beam at 293.6
  (centre z 2.76, r 0.04), along under the ceiling at z 2.80 to a pulley on the end wall (295.705, z 2.76), down beside
  the door's architrave (x 295.745, y 0.64) to a pulley at z 2.15, across under the door's head (z 2.13) to a pulley
  over the latch (295.925, y -0.45, z 2.11), down to the latch's eye (z 1.924).
- Att17Latch: the stair door's drop latch, DOWN (locked), on the frame (NOT a child of the door: it stays put when the
  door swings). Origin = its pivot, Blender (295.82, -0.47, 1.90) = game (295.82, 1.90, 0.47), on a bracket on the
  free jamb's lining (Blender y -0.5) at the wall's face. A flat iron bar runs +x across the reveal to x 295.947; its
  nib drops into a keeper (pocket) on the leaf's room face (part of Att17Door's mesh, x 295.928-295.955, z 1.825-1.895).
  UP = 70 deg about Blender -y = game +z (three.js rotateZ(+70 deg)): the bar's end rises to z ~2.02, the nib clear.
- Moved for the rig: the broom (now in the corner by the stair door, x 295.4-295.7, behind the lane).
- Clear of the lane and the existing interactions: nothing new is in front of Blender y 0.30 except the shut sluices'
  grips (to y 0.18) and the latch in the doorway's reveal (x 295.8-295.95, z 1.83-1.93, above him). The tray (285.7),
  the drawer (286.0), the card player (288.0) and the stair door (295.8) are untouched.

DRAWER CONTENTS (Blender; open = shut y - 0.45)
- Drawing 0.50 x 0.35, face up, top of image toward +y, turned 0.03 rad: centre shut (286.385, 0.86, 0.3945),
  open (286.385, 0.41, 0.3945) = game (286.385, 0.3945, -0.41). All in her pencil (graphite): the tree made a bed,
  sluices A B C, the settling loop, her section A-A, NOTES 1-4, title block (DRAWN M. D., AGE 14, CHECKED). His blue
  pencil, beside her lines: "fall 1 in 100 / or it scours" under her "FALL 1 IN 40" (bottom left); "levels!" and a
  datum mark by the TANK (bottom middle); his shallower section with "wider, shallower / sides 1 in 2" under hers
  (top right); "The knot works! - E.V." and a tick over the loop (top middle); "E. V." and a tick at CHECKED.
  Expansion: her plan (all of the above but the right-hand column) is shrunk to 0.78 into the upper left; along the
  bottom, her working for the test rig: the rig from the front to scale (bench, beds "1 M.D.", "2 R.A.", "3 T.O.",
  levers A B C), the three pipes traced from each lever up behind the bench to the bed it feeds, broken where one
  passes behind another (A to bed 3, B to bed 1, C to bed 2, as in the world: drawn, never written out; no notes of
  hers on it). Beside it, his red pencil, an arrow to her pipes: "Good eye. Most of them never look behind the bench.
  - E.V." The atlas cell is where it
  was: drawing (0, 0, 1280, 896); her card (1280, 0, 2048, 480).
- Card 0.20 x 0.125, turned -0.09 rad: shut (285.93, 0.82, 0.3957), open (285.93, 0.37, 0.396) = game (285.93, 0.396, -0.37).
  Typed: NAME M. D., AGE 14, PLACED WITH WORKS DEPT., RING A, TRADE WATER AND IRRIGATION, SPONSOR E. VANCE,
  APPLICATION BY THE PUPIL, REPORT VIA RESIDENTIAL ACCESS, RING A (WORKS GATE SEALED). Signed: Pupil "Mara D."
  (pencil), Sponsor "E. Vance" (ink). Stamp: ACCEPTED, WORKS DEPT . RING A, P.A. 316. No. 0417.
- Mended pot on the floor: centre (286.9, 0.35), r 0.13, rim 0.255 = game (286.9, 0, -0.35).
CLOSE-UP CAMERAS (drawer open; game coordinates; vertical FOV for 16:9)
- Drawing beside the pot: pos (286.62, 0.92, -0.06), look (286.62, 0.33, -0.42), 24 mm = vFOV 45.7 deg (0.69 m).
- Drawing alone: pos (286.385, 0.83, -0.08), look (286.385, 0.394, -0.41), 35 mm = vFOV 32.3 deg (0.55 m).
- Card: pos (285.93, 0.75, -0.05), look (285.93, 0.396, -0.37), 35 mm = vFOV 32.3 deg (0.48 m).
  Keep the camera at least 0.8 m high. Lower down, the drawer's front (top 0.48) hides the near edge of the drawing.

SURFACES / LIMITS
- Floor top 0 from x 280.0 to 297.1 (the room to 295.8, the doorway's threshold strip x 295.79-296.01 0.012 high,
  then the stair landing x 296.0-297.1). The lane (y -0.3..0.3) is clear from 280 to the first riser at 297.1 except
  the tray (x ~285.49-285.91, top 0.09 when level), the shut door leaf (x 295.955-296.0), and the rig's shut sluice
  grips (x 293.45 / 294.1 / 294.8 +-0.016, down to y 0.18, z ~0.48).
- Left wall x 280.0-280.15, with a doorway in it at Blender y -0.45..0.55 (game z -0.55..0.45), head 2.1.
- Right end wall x 295.8-296.0 (its room face x 295.8), with the stair doorway at Blender y -0.5..0.5 (game z
  -0.5..0.5), head 2.15: clear width 1.0 for D-17 (0.35 wide, 0.6 tall). Ceiling 3.0, with beams across the lane
  (bottom 2.84) at x 281.6, 284.0, 286.4, 288.8, 291.2 and 293.6, each +-0.07.
- Over the door, a blade sign hung off the end wall in the plane y 0, its face to the camera: RESIDENTIAL ACCESS .
  RING A, an arrow up, the Works' cog with WORKS. Sign x 294.62-295.72, z 2.42-2.72; its bracket arm z 2.79.
- THE STAIR (beyond the door; game x = Blender x, tread top = game y). Width Blender y -0.6..0.9 (game z -0.9..0.6).
  Landing x 296.0-297.1 at 0. Then 18 treads, rise 0.18, going 0.26 (34.7 deg): tread i (1..18) runs
  x 297.1 + 0.26 (i - 1) to 297.1 + 0.26 i, top 0.18 i; each nosing overhangs 0.022 toward -x (iron, 1.5 mm proud).
    i:   1      2      3      4      5      6      7      8      9      10     11     12     13     14     15     16     17     18
    x0:  297.10 297.36 297.62 297.88 298.14 298.40 298.66 298.92 299.18 299.44 299.70 299.96 300.22 300.48 300.74 301.00 301.26 301.52
    top: 0.18   0.36   0.54   0.72   0.90   1.08   1.26   1.44   1.62   1.80   1.98   2.16   2.34   2.52   2.70   2.88   3.06   3.24
  Upper landing from x 301.78 at 3.42 to the stairwell's end wall at x 303.0 (out of frame).
  The pitch line through the nosings: top = 0.18 + (x - 297.1) * 0.6923.
  Stairwell: back wall face Blender y 0.9 (game z -0.9), handrail on it 0.9 above the nosings; the room's ceiling
  (3.0) carries on over the landing to x 298.2 (fascia beam bottom 2.84 at x 298.06-298.2); beyond it the shaft
  is open up to 5.2. Headroom under the fascia over tread 5 (top 0.9): 1.94.
- Behind the lane (not on his path): bench top 0.9 (x 282.8-288.6, y 0.65-1.3); stool top 0.45
  (x 287.6-288.4, y 0.30-0.70); window shelf top 0.92 (x 289.0-292.0, y 0.82-1.3); sink top 0.86 (292.1-292.9);
  the test bench top 0.55, its beds' rims 0.70 (x 293.05-295.3, y 0.35-0.95).
  The back wall (y 1.3) is now plain where the old stair door was (x 293.75-294.85).
- The game's ATT2.x1 / ATT.x1 (295.6) stop him short of the doorway: extend them for the exit through it and the climb.

VOICE PLAYER (att_volunteer): on the stool, base Blender (288.0, 0.48, 0.45) = game (288.0, 0.45, -0.48), front to
the camera. Card (288.0, 0.435, 0.602), top 0.598, horn mouth (288.18, 0.374, 0.798), crank pivot (288.11, 0.48, 0.538).

RECOMMENDED GAME LIGHTS (game x, y, z)
- Pendant pool: spot at (285.95, 2.15, -0.80), aimed down at (285.95, 0, -0.6). Colour (1, .76, .48), wide
  (about 120 deg). Warm key on the bench, the drawer and the pot.
- Bench lamp: spot at (285.04, 1.34, -0.90), aimed at (285.5, 0.9, -0.70). Colour (1, .8, .55), 75 deg, low.
- Drawer reveal fill: spot at (286.2, 1.8, 1.6), aimed at (286.2, 0.3, -0.45). Colour (1, .84, .62), narrow (40 deg).
  Raise it when the drawer opens.
- Grow lamp: off (rev 0.3). (Was: cool (.74, .82, 1.0) under the tubes at (290.5, 1.57, -1.05).)
- Door bulkhead: small point at (295.25, 2.2, -0.95). Colour (.95, .88, .75), dim.
- The stair, warm from above: spot at (298.6, 4.6, -0.2) aimed at (298.2, 0.8, -0.1), colour (1, .8, .55), about
  75 deg, strong enough that the treads read brighter than the workshop; plus a dim warm point at the lamp,
  (299.3, 3.5, -0.7), and a low warm fill on the landing and first treads, e.g. a point at (297.0, 1.6, -0.2),
  so he reads as he steps through. Through the door's glass while it is shut, a warm patch; when it opens, the pool.
- Entry: warm point at (281.2, 2.6, -0.2), dim.
- The test rig (expansion): a warm spot at (294.2, 2.7, 0.9) aimed at (294.2, 0.85, -0.9), about 70 deg, so the
  brass pipes on the cream board, the beds and the levers read; a dim point near the valve, (292.6, 1.2, 0.3).

NEW MATERIALS (index.html format)
WORN (already in index.html; DampSoil is no longer used by DL-17):
  WorkPlaster: { base: [.33, .27, .18], dirt: [.17, .13, .08], chip: [.23, .19, .14], rough: .9, chipRough: .85, metal: 0, grime: 3, chipScale: 18, chipAmt: .7, dust: [.26, .22, .16], dustAmt: .4, streak: .5 },   // chapter 1, DL-17
  PotClay: { base: [.34, .15, .075], dirt: [.16, .1, .06], chip: [.42, .36, .28], rough: .9, chipRough: .95, metal: 0, grime: 10, chipScale: 40, chipAmt: .72, dust: [.36, .32, .26], dustAmt: .5, streak: .3 },
EMIT:
  Att17GrowLamp: [.78, .84, 1, 3], Att17Bulb: [1, .78, .5, 5],
  Att17StairLamp: [1, .8, .55, 6],   // NEW (rev 0.3): the lamp over the stair
Reused materials: WinDado, PigeonWood, CrateWood, PupilWood, WornIron, HandledBrass, DarkMetal, WornStrap,
DepotGreen, ParcelBrown, DirtyGlass, TeaEnamel, Cable, Copper, Window (GLASSY: the bean jars, the door's light, the
sight glass), Water (PLAIN, the game's see-through water: the rig's tank, beds and streams),
plus the voice-prop materials (Brass, HandWorn, ParcelPaper). No longer used: AttShoot, DampSoil. Image material:
Att17Atlas (textures/dl17_atlas.png, 2048 square; new cells: soilcrack, and the sign_works cell redrawn as the
RESIDENTIAL ACCESS sign).

BUDGET: 40,092 triangles (set 37,062; drawer 428; tray 1,470; lamp 72; bulbs 320; door 620; stair lamp 120);
34 material slots.
"""
