"""Data for the Unity export (U-12): how the set splits into regions, the checkpoints, and the mechanism names.

No bpy here: export_regions.py (Blender) and report.py (plain Python) both import it.
Coordinates are the game's lane x (Blender x). Sources are game/undelivered/index.html line numbers (read only) and
docs/unity/port_architecture.md (§0.3 regions, §5 scenes, mechanism IDs and checkpoints).
"""
import hashlib

# ---- Regions -----------------------------------------------------------------------------------------------------
# One Unity export per scene (port_architecture §6.1: "split the current monolithic set.glb by scene"; §7 streams scenes).
# A top-level object goes to the region its bounding-box centre x falls in (the rule §5's counts were measured with);
# an object wider than BACKDROP_WIDTH goes to the backdrop instead. Boundaries are index.html's own scene cuts
# (sceneName, L8135-L8144): SH.x0 12.0, SH.x1 25.0 (L3887), GATE_X = OFF2 + 17.6 = 30.6 (L323), RATION5 47.9 / 59.8
# (L3447), REGION4_X = OFF3 + 47.75 = 80.75 (L3007), CG.x0 = OFF3 + 64.6 = 97.6 (L3899), UPONLY.x0 = OFF4 + 76.8 = 118.8
# (L3455), REGION5_X = OFF5 + 73.9 = 127.9 (L3446). DL-06 and DL-07 share one floor, one carrier line and one builder
# (§5 cross-scene notes; sceneName tells them apart by game state, not x), so they export together.
BACKDROP_WIDTH = 30.0
BACKDROP = 'DL-09_Atrium'

PROLOGUE = [
    # name, Unity scenes it serves, game region (§0.3), lane x from, lane x to (assignment range)
    ('DL-01', ['DL-01'], 1, -20.0, 12.0),
    ('DL-02', ['DL-02'], 2, 12.0, 25.0),
    ('DL-03', ['DL-03'], 2, 25.0, 30.6),
    ('DL-04', ['DL-04'], 2, 30.6, 47.9),
    ('DL-05', ['DL-05'], 2, 47.9, 59.8),
    ('DL-06_07', ['DL-06', 'DL-07'], 3, 59.8, 80.75),
    ('DL-08', ['DL-08'], 4, 80.75, 97.6),
    ('DL-09', ['DL-09'], 4, 97.6, 118.8),
    ('DL-10', ['DL-10'], 4, 118.8, 127.9),
    ('DL-11', ['DL-11'], 5, 127.9, 199.0),
]
# The far backdrop (>30 m wide: atrium, city, cut bridge), loaded with DL-09 and kept through DL-11 (§7).
PROLOGUE_BACKDROP = (BACKDROP, ['DL-09', 'DL-10', 'DL-11'], 4, None, None)

# Chapter 1 (art/ch1/build_attendance.py, attendance.glb): sceneName's region-6 cuts (L8137).
CHAPTER1 = [
    ('DL-12', ['DL-12'], 6, 199.0, 216.0),
    ('DL-13', ['DL-13'], 6, 216.0, 232.0),
    ('DL-14', ['DL-14'], 6, 232.0, 248.0),
    ('DL-14a', ['DL-14a'], 6, 248.0, 263.0),
    ('DL-14b', ['DL-14b'], 6, 263.0, 278.0),
    ('DL-15', ['DL-15'], 6, 278.0, 294.0),
    ('DL-16', ['DL-16'], 6, 294.0, 310.0),
    ('DL-16a', ['DL-16a'], 6, 310.0, 324.0),
    ('DL-17', ['DL-17'], 6, 324.0, 400.0),
]


def region_for_x(table, x):
    for name, _scenes, _r, x0, x1 in table:
        if x0 <= x < x1:
            return name
    return None


# ---- Checkpoints -------------------------------------------------------------------------------------------------
# CHECKPOINTS, index.html L7975-L8014, with the offsets resolved (port_architecture §5 lists the same values):
# name, lane x, height y (the floor D-17 respawns on), game region. Order is the list order (it is the save order).
CHECKPOINTS = [
    ('start', 1.0, 0.0, 1), ('shutter', 2.9, 0.0, 1), ('hall', 8.35, 0.0, 1), ('door', 9.62, 0.0, 1),
    ('room', 13.2, 0.0, 2), ('weighroom', 25.9, 0.0, 2), ('solved', 29.95, 0.0, 2), ('bay', 47.1, 0.0, 2),
    ('ration', 48.6, 0.0, 2), ('hatch', 57.05, 0.0, 2),
    ('scanned', 63.3, 0.0, 3), ('landing', 73.0, 0.0, 3), ('gallery', 75.3, 0.0, 3),
    ('goods', 81.9, 0.0, 4), ('latched', 89.2, 0.0, 4), ('cage', 100.8, 3.4, 4), ('landing8', 103.3, 1.6, 4),
    ('tunnel', 107.7, 0.0, 4), ('uponly', 119.4, 1.6, 4),
    ('ringc', 135.25, 0.0, 5), ('bedroom', 164.1, 0.0, 5), ('forwarded', 167.1, 0.0, 5),
    # Chapter 1 (region 6). window and hatch14 share x 234.8 (port_architecture §9 #12).
    ('school', 200.8, 0.0, 6), ('register', 210.0, 0.0, 6), ('lesson', 216.8, 0.0, 6), ('gallery13', 228.4, 2.05, 6),
    ('window', 234.8, 0.0, 6), ('hatch14', 234.8, 0.0, 6), ('dorm', 249.4, 1.15, 6), ('corridor', 263.6, 0.0, 6),
    ('sickbay', 279.0, 1.6, 6), ('class6', 282.7, 0.0, 6), ('dismissed', 292.6, 0.0, 6), ('crossing', 294.6, 0.0, 6),
    ('store', 300.6, 0.0, 6), ('kitchen', 310.6, 0.0, 6), ('workshop', 325.0, 0.0, 6),
]

# ---- Mechanisms --------------------------------------------------------------------------------------------------
# MECH_<Type>_<scene>_<name>[__<part>] (docs/unity/asset_conventions.md). IDs are port_architecture §5's MechanismIds.
# Each entry: type, id, root source object (renamed MECH_<Type>_<id>) or None, part source objects (renamed
# MECH_<Type>_<id>__<source>). With no root, the export adds an empty anchor at the parts' centre. Only mappings that
# index.html makes certain are listed (the refs it groups and moves together); the rest of the objects the game looks
# up by name are listed per region as "driven" in docs/unity/name_map.csv, still under their source names.
# Types are provisional names for U-10's mechanism classes (§4.13); change them here, not in the generators.
# <Type> is U-10's Core class name (#9 review), so the importer binds MECH_<Type>_... with no lookup table.
MECHANISMS = [
    # DL-01 (L1383-L1402, L3990-L4013)
    ('Door', 'dl01.shutter', 'Shutter', ['ShutterRail', 'Pulley', 'Counterweight', 'CounterweightStripes']),
    ('Latch', 'dl01.latch', 'LatchLever', ['LatchTag']),
    ('PulseSequencer', 'dl01.relay', None, ['RelayLamp0', 'RelayLamp1', 'RelayLamp2']),
    ('CrankActuator', 'dl01.crank', 'CrankWheel', []),
    ('Door', 'dl01.door', 'ExitDoor', []),
    ('TippingBridge', 'dl01.cart', 'DepotCart', []),
    ('LoadPlate', 'dl01.scale', None, ['ScaleNeedle']),
    # DL-02
    ('Press', 'dl02.press', 'PressRam', ['PressFlywheel']),
    ('Carryable', 'dl02.box', 'CarryBox', []),
    # DL-03 (L1385-L1386)
    ('Carryable', 'dl03.weight', 'SortWeight', ['SortWeightBand']),
    ('Pushable', 'dl03.trolley', 'Trolley', ['TrolleyGrip', 'TrolleyWheel0', 'TrolleyWheel1', 'TrolleyWheel2', 'TrolleyWheel3']),
    ('LoadPlate', 'dl03.plate', 'FloorPlate', []),
    ('FollowerActuator', 'dl03.gate', 'Gate', ['GateNeedle']),
    # DL-04
    ('Pushable', 'dl04.courier', 'FallenCourier', []),
    ('LoadPlate', 'dl04.bayPlate', 'BayPlate', []),
    ('Cradle', 'dl04.cradle', None, ['CradleArmL', 'CradleArmR']),
    ('PlateDoor', 'dl04.bayDoor', 'BayDoor', []),
    # DL-05 (L4011-L4012, L4921: the shutter is the hatch the crawl passes under)
    ('Pushable', 'dl05.drum', 'RationDrum', []),
    ('Draggable', 'dl05.body', 'RationBody', []),
    ('WeighScale', 'dl05.weighIn', 'RationScalePlate', ['RationScaleNeedle']),
    ('Door', 'dl05.hatch', 'RationShutter', []),
    ('Door', 'dl05.servedFlag', 'RationServedFlag', []),
    # DL-06 / DL-07 (L2553-L2554, L3996-L3997)
    ('Scanner', 'dl06.scanner', 'ScanBar', []),
    ('PointsLever', 'dl06.stopLever', 'StopLever', []),
    ('PointsLever', 'dl06.points', 'PointsLever', ['PointsBlade']),
    ('CarrierLine', 'dl06.line', None, ['CarrierTub', 'CarrierChassis', 'CarrierLamp', 'CarrierPlate',
                                        'ChainBelt0', 'ChainBelt1', 'ChainBelt2']),
    ('Carryable', 'dl07.weight0', 'HeapWeight0', []),
    ('Carryable', 'dl07.weight1', 'HeapWeight1', []),
    ('BucketGate', 'dl07.gate', 'GalleryGate', ['GatePulley', 'GateSheave', 'GateBucket']),  # the bucket is its input (U-10)
    ('Collapse', 'dl07.collapse', 'GalleryCollapse', ['GalleryCollapseEdges']),
    # DL-08 (L3040-L3042)
    ('Pushable', 'dl08.trolley', 'GoodsTrolley', ['GoodsTrolleyGrip', 'GoodsBallast', 'GoodsStraps',
                                                  'GoodsWheel0', 'GoodsWheel1', 'GoodsWheel2', 'GoodsWheel3']),
    ('LoadPlate', 'dl08.pan', 'GoodsPan', ['HeadDrum', 'PanPulley']),
    ('CounterweightLift', 'dl08.platform', 'GoodsPlatform', ['GoodsPlatformFrame', 'GoodsPlatformRail']),
    ('Pawl', 'dl08.pawl', 'Pawl', ['PawlLever', 'PawlLamp']),
    ('ReturnsBelt', 'dl08.belt', 'ReturnsBelt', ['ReturnCrate0', 'ReturnCrate1', 'ReturnCrate2']),
    # DL-09 (L3998-L4001; CW8.plates L7320)
    ('LoadPlate', 'dl09.plate0', 'CwPlate0', []),
    ('LoadPlate', 'dl09.plate1', 'CwPlate1', []),
    ('SlippingCage', 'dl09.cage', 'Cage', ['CageCounterweight', 'CageSheave']),
    ('CageCatch', 'dl09.cagePawl', 'CagePawl', ['CagePawlLever']),
    # DL-10 (L4007-L4010)
    ('Carryable', 'dl10.case', 'Suitcase114', ['Suitcase114Tag']),
    ('RelocationLift', 'dl10.lift', 'LiftCar', ['LiftDoorL', 'LiftDoorR', 'LiftRopeCar']),
    ('LoadPlate', 'dl10.carPlate', 'LiftFloorPlate', ['LiftLoadNeedle']),
    ('Button', 'dl10.upButton', 'LiftUpButton', []),
    ('CrankActuator', 'dl10.serviceCrank', 'ServiceCrank', ['ServiceChain']),
    ('Door', 'dl10.serviceDoor', 'ServiceDoor', []),
    ('Button', 'dl10.serviceUp', 'ServiceUpButton', []),
    ('Counterweight', 'dl10.counterweight', 'LiftCounterweight', ['LiftSheave', 'LiftSheaveIdler', 'LiftRopeCW']),
    # DL-11 (L4002-L4005, L3475; DUCT9 = OFF5 + 94.0, L3903)
    ('Bell', 'dl11.bell', 'C108Bell', ['C108Gong']),
    ('Lever', 'dl11.junction', 'JunctionLever', []),
    ('TippingBridge', 'dl11.duct', 'PushDuct', []),
    ('Door', 'dl11.c114Door', 'C114FrontDoor', ['C114DoorHandle', 'C114DoorCord']),
    ('Facade', 'dl11.facade', 'C114Facade', []),
    ('Draggable', 'dl11.desk', 'ChildDesk', []),
    ('Terminal', 'dl11.terminal', 'ForwardTerminal', []),
]

# The region a mechanism's scene belongs to: a mechanism's objects export with their scene, whatever their centre x.
SCENE_REGION = {
    'dl01': 'DL-01', 'dl02': 'DL-02', 'dl03': 'DL-03', 'dl04': 'DL-04', 'dl05': 'DL-05', 'dl06': 'DL-06_07',
    'dl07': 'DL-06_07', 'dl08': 'DL-08', 'dl09': 'DL-09', 'dl10': 'DL-10', 'dl11': 'DL-11',
}


def mech_name(type_, mech_id, part=None):
    scene, name = mech_id.split('.')
    n = f'MECH_{type_}_{scene}_{name}'
    return n + '__' + part if part else n


# ---- Markers still to author (per region; docs/unity/asset_conventions.md carries the same list) ------------------
TODO = {
    'COL': 'lane collision is code in index.html (floorAt/surfaceAt/ceilingAt, L1617-L1769, L4135-L4201): author COL_ boxes',
    'LGT': 'every light is created in code (port_architecture §4.20, ~160 proxies): author LGT_ empties',
    'CAM': 'framing zones are code (frameFor L7644-L7806; Core PrologueFraming has DL-01..07): author CAM_ empties',
}


# ---- Stable GUIDs (same scheme as Core StableGuid / the audio importer) --------------------------------------------
def stable_guid(asset_path):
    return hashlib.md5(asset_path.replace('\\', '/').encode('utf-8')).hexdigest()


def file_meta(asset_path):
    return f'fileFormatVersion: 2\nguid: {stable_guid(asset_path)}\n'


def folder_meta(asset_path):
    return (f'fileFormatVersion: 2\nguid: {stable_guid(asset_path)}\nfolderAsset: yes\nDefaultImporter:\n'
            '  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n')


def blender_to_unity(v):
    """Blender (x, y, z) to the port's Unity axes (port_architecture §0.2): (x, z, y)."""
    return [round(v[0], 4), round(v[2], 4), round(v[1], 4)]
