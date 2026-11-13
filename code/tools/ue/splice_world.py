"""Splice world: builds all of L_Mine, to the Aethyr world's layout (idempotent).

One level holds every stage of the run, far apart, like the Aethyr world:
  dome village and scanner gate -> 300 m rail line -> the mine in open desert (mouth, scrap
  room, tunnel with rubble) -> the party (hall with stage, DJ and dance floor; bar, workshop
  and vault to the west; lounge off the catwalk to the east) -> boss wall and chamber;
  plus two stages hidden behind the mesas: the edit bay's and the memory's.

Coordinates in this file are Aethyr's (metres; x right, y up, z back). splice_common.A()
turns them into UE's. Numbers come from apps/openagents-web/splice-game.coax.

It replaces splice_step1_level.py, splice_place.py and splice_slice_level.py.
Run after splice_look.py, splice_slice_assets.py, splice_kits.py.
Usage: python3 tools/ue/splice_world.py
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from splice_common import PRELUDE  # noqa: E402
from uemcp import py  # noqa: E402

# Time of day. Colours are display-space multipliers; Sun is a direction (UE axes).
# (name, Sun, Ambient, Shade, Haze rgb+strength, SkyTop, SkyHorizon, Cloud rgb+amount)
PHASES = {
    "Dawn": dict(Sun=(-0.6, 0.7, 0.28, 0), Ambient=(0.97, 0.88, 1.06, 1), Shade=(0.86, 0.78, 0.88, 1),
                 Haze=(0.95, 0.80, 0.84, 0.5), SkyTop=(0.74, 0.76, 0.92, 1), SkyHorizon=(0.99, 0.84, 0.80, 1), Cloud=(1, 0.95, 0.95, 0.7)),
    "Day": dict(Sun=(-0.6, -0.45, 0.66, 0), Ambient=(1.13, 1.12, 1.10, 1), Shade=(0.80, 0.70, 0.78, 1),
                Haze=(0.82, 0.76, 0.88, 0.55), SkyTop=(0.58, 0.72, 0.90, 1), SkyHorizon=(0.95, 0.90, 0.86, 1), Cloud=(1, 1, 1, 0.8)),
    "Dusk": dict(Sun=(-0.74, -0.6, 0.3, 0), Ambient=(1.06, 0.84, 1.04, 1), Shade=(0.86, 0.70, 0.84, 1),
                 Haze=(0.80, 0.46, 0.58, 0.5), SkyTop=(0.50, 0.40, 0.66, 1), SkyHorizon=(0.99, 0.62, 0.50, 1), Cloud=(1, 0.75, 0.7, 0.7)),
    "Night": dict(Sun=(-0.77, 0.4, 0.5, 0), Ambient=(0.58, 0.55, 1.0, 1), Shade=(0.82, 0.78, 0.92, 1),
                  Haze=(0.22, 0.13, 0.38, 0.6), SkyTop=(0.10, 0.07, 0.22, 1), SkyHorizon=(0.32, 0.17, 0.44, 1), Cloud=(0.5, 0.3, 0.6, 0.5)),
}
# Placeholder lines until Kiki's captions arrive.
CAPTIONS = [
    "Before the Mandates, they worked beside us.",
    "Every shift, side by side. Nobody called it strange.",
    "Nobody owned the work. We shared it.",
]

SRC = PRELUDE + r'''
PHASES = __PHASES__
CAPTIONS = __CAPTIONS__
await stop_pie()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if world is None or not world.get_path_name().startswith("/Game/Splice/L_Mine"):
    les.load_level("/Game/Splice/L_Mine")

def bpc(name):
    return unreal.load_class(None, f"/Game/Splice/Blueprints/{name}.{name}_C")

# ---------------------------------------------------------------- wipe
KEEP = (unreal.PostProcessVolume, unreal.PlayerStart)
start = None
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.PlayerStart):
        start = a
    if isinstance(a, KEEP):
        continue
    if isinstance(a, (unreal.StaticMeshActor, unreal.TargetPoint, unreal.Light, unreal.CameraActor)) or \
            a.get_class().get_path_name().startswith("/Game/Splice/"):
        eas.destroy_actor(a)

PAPER, SHADE, INK = (0.918, 0.859, 0.769), (0.863, 0.788, 0.675), (0.118, 0.106, 0.094)
HEAT, GLOW, GLOW_INK = (0.722, 0.263, 0.122), (0.310, 0.702, 0.851), (0.122, 0.373, 0.502)
CREAM, AMBER, PINK, CYAN = (0.93, 0.88, 0.76), (1.0, 0.72, 0.30), (1.0, 0.36, 0.62), (0.36, 0.86, 0.96)
TAU = math.pi * 2

ROVER_X, ROVER_Z, POST_X, POST_Z, CRATE_X, CRATE_Z = 6.0, 5.0, 2.6, 6.5, -11.5, -57.0
START_X, START_Z = 0.0, 9.0
RUBBLE_Z, WALL_Z, BOSS_X, BOSS_Z = -34.0, -62.0, 0.0, -72.0
DECK_X, DECK_Z0, DECK_Z1, DECK_Y, RAMP = 11.0, -60.0, -42.0, 0.9, 3.0
BAY_X, BAY_Z, MEM_X, MEM_Z = -100.0, 136.0, -100.0, 200.0
VIL_X, VIL_Z, VIL_R, SCAN_Z = 175.0, -75.0, 7.0, -65.0
RAIL_X, RAIL_Z = 175.0, -55.0
def rail_at(s):
    return (RAIL_X + math.sin(s * 0.03) * 8, 0.0, RAIL_Z + s)
def rail_yaw(s):
    a, b = rail_at(s), rail_at(s + 1)
    return math.atan2(b[0] - a[0], b[2] - a[2])

# ---------------------------------------------------------------- sky and land
FOLDER[0] = "World/Land"
sky = _spawn("Sphere", named("M_Sky"), unreal.Vector(0, 5000, 0), R0, unreal.Vector(7000, 7000, 7000), "Sky", False)
sand = cel((0.90, 0.68, 0.48))
block(sand, 60, -1.0, 80, 220, 1.0, 240, "Ground")

def mesas(c, count, seed, z_far, spacing, hmin, hmax):
    m = cel(c)
    for i in range(count):
        k = seed + i
        x = (i - (count - 1) * 0.5) * spacing + (kit_rand(k + 120) - 0.5) * spacing * 0.4
        z = z_far - kit_rand(k + 130) * 40
        h = hmin + kit_rand(k + 140) * (hmax - hmin)
        r0 = 12 + kit_rand(k + 150) * 10
        tube(m, x, -0.5, z, h, r0, shape="Mesa", label="Mesa")
def dunes(c, count, seed, span, z0, z1, rmin, rmax):
    m = cel(c)
    for i in range(count):
        k = seed + i
        x = (kit_rand(k + 1) * 2 - 1) * span
        z = z0 + kit_rand(k + 40) * (z1 - z0)
        r = rmin + kit_rand(k + 80) * (rmax - rmin)
        ellipsoid(m, x, -0.075 * r, z, r, r * 0.3, r * 0.8, kit_rand(k + 9) * 6, shape="Dune", label="Dune")
def rocks(c, count, seed, cx, cz, d0, d1, rmin, rmax):
    m = cel(c)
    for i in range(count):
        k = seed + i
        a = kit_rand(k + 200) * TAU
        d = d0 + kit_rand(k + 210) * (d1 - d0)
        r = rmin + kit_rand(k + 220) * (rmax - rmin)
        ellipsoid(m, cx + math.cos(a) * d, r * 0.2, cz + math.sin(a) * d, r, r * 0.7, r * 0.9, kit_rand(k + 230) * 6, label="Rock")

mesas((0.72, 0.56, 0.74), 9, 40, 92, 26, 14, 30)
dunes((0.93, 0.74, 0.50), 12, 50, 40, 28, 60, 5, 11)
rocks((0.66, 0.36, 0.28), 14, 60, 0, 8, 5, 16, 0.3, 1.0)

# ---------------------------------------------------------------- the mine's walls
# x0, x1, z0, z1, height. Height 0 is an unseen blocker.
WALLS = [
    (-44, -4, -10, -2, 9), (4, 44, -10, -2, 10),                      # the mine mouth
    (-44, -9, -24, -10, 11), (9, 44, -24, -10, 10),                   # the scrap room
    (-44, -3, -40, -24, 12), (3, 44, -40, -24, 12),                   # the tunnel
    (-17, -15, -62, -44.5, 7), (-17, -15, -41.5, -40, 7),             # hall | west rooms, a door to the bar
    (-31, -27, -52, -50, 7), (-24, -17, -52, -50, 7),                 # bar | workshop, a door
    (-33, -31, -62, -59, 7), (-33, -31, -56, -40, 7),                 # workshop | vault, a door
    (-47, -43, -62, -40, 13),                                         # the vault's far wall
    (15, 17, -62, -52.5, 13), (15, 17, -49.5, -40, 13),               # the catwalk's wall, a door to the lounge
    (17, 44, -44, -40, 13), (17, 44, -62, -58, 13), (29, 44, -58, -44, 13),
    (-15, -11.5, -57, -46, 0),                                        # the main stage (drawn apart)
    (-15, -4, -63, -61, 9), (4, 15, -63, -61, 9),                     # the boss wall's shoulders
    (-44, -10, -82, -62, 14), (10, 44, -82, -62, 14),                 # the boss chamber
    (-44, 44, -92, -82, 15),
    (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0),                # rover, crate, rail: their own colliders
    (-60, 60, 20, 24, 0), (-64, -44, -92, 24, 0), (44, 64, -92, 24, 0),   # the edge of the map
]
FOLDER[0] = "World/Walls"
for i, (x0, x1, z0, z1, h) in enumerate(WALLS):
    if x1 - x0 <= 0:
        continue
    cx, cz, hx, hz = (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2
    if h < 1:
        if i >= 27:
            a = block(sand, cx, 0, cz, hx, 6, hz, "Edge")
            a.set_actor_hidden_in_game(True)
            a.static_mesh_component.set_visibility(False)
        continue
    deep = z1 <= -40
    face = cel((0.62, 0.42, 0.56) if deep else (0.84, 0.46, 0.32))
    band = cel((0.50, 0.32, 0.50) if deep else (0.72, 0.34, 0.26))
    block(face, cx, 0, cz, hx, h, hz, "Wall")
    block(band, cx, h * 0.36, cz, hx + 0.12, h * 0.1, hz + 0.12, "Band", collide=False)
    block(band, cx, h * 0.72, cz, hx + 0.08, h * 0.05, hz + 0.08, "Band", collide=False)
    seed = i * 17.0
    for j in range(int((hx + hz) / 5) + 2):
        k = seed + j
        x = x0 + kit_rand(k + 600) * (x1 - x0)
        z = z0 + kit_rand(k + 610) * (z1 - z0)
        r = 1.5 + kit_rand(k + 620) * 2.5
        ellipsoid(face, x, h, z, r, r * 0.5, r, kit_rand(k + 630) * 6, label="Boulder")

# ---------------------------------------------------------------- mine mouth dressing
FOLDER[0] = "World/Mine"
rocks((0.52, 0.36, 0.34), 14, 70, 0, -17, 5, 8.2, 0.4, 1.1)

# ---------------------------------------------------------------- the party
FOLDER[0] = "World/Party"
deck = cel((0.48, 0.36, 0.44))
block(deck, 13, 0, (DECK_Z0 + DECK_Z1) / 2, 2, DECK_Y, (DECK_Z1 - DECK_Z0) / 2, "Deck")
slope = math.degrees(math.atan2(DECK_Y, 3.0))
for z0 in (DECK_Z0, DECK_Z1 - RAMP):
    a = _spawn("Cube", deck, A(DECK_X - 1.5, DECK_Y / 2 - 0.05, z0 + RAMP / 2),
               unreal.Rotator(pitch=0.0, yaw=0.0, roll=-slope), unreal.Vector(RAMP, 3.14, 0.1), "Ramp", True)
ink = cel(INK)
for i in range(7):
    tube(ink, DECK_X, DECK_Y, DECK_Z0 + RAMP + i * 2.0, 1.0, 0.06, label="RailPost")
block(ink, DECK_X, DECK_Y + 0.95, (DECK_Z0 + DECK_Z1) / 2, 0.05, 0.08, (DECK_Z1 - DECK_Z0) / 2 - RAMP, "RailBar", collide=False)
a = block(ink, DECK_X, DECK_Y, (DECK_Z0 + DECK_Z1) / 2, 0.12, 1.2, (DECK_Z1 - DECK_Z0) / 2 - RAMP, "RailBlock")
a.static_mesh_component.set_visibility(False)
a.set_actor_hidden_in_game(True)
pink, cyan, amber = glow(PINK), glow(CYAN), glow(AMBER)
for i in range(16):
    m = pink if i % 2 == 0 else cyan
    ball(m, -14 + i * 1.9, 6.5 + math.sin(i * 0.8) * 0.6, -41.5, 0.22, "Lamp")
    ball(m, 14.4, 6.0 + math.sin(i * 0.7) * 0.6, -42 - i * 1.2, 0.22, "Lamp")
# the main stage on the hall's west side: a deck, the DJ's booth, speaker stacks, a truss of lamps
block(cel((0.14, 0.11, 0.18)), -13.25, 0, -51.5, 1.75, 1.0, 5.5, "Stage")
block(cel((0.30, 0.22, 0.36)), -12.6, 1.0, -51.5, 0.5, 1.0, 1.6, "Booth")
block(cyan, -12.05, 1.2, -51.5, 0.03, 0.6, 1.4, "BoothGlow", collide=False)
for z in (-47.0, -56.0):
    block(ink, -13.2, 1.0, z, 1.0, 3.4, 0.8, "Speaker")
    ball(pink, -12.2, 3.6, z, 0.5, "Cone")
    ball(pink, -12.2, 2.1, z, 0.6, "Cone")
block(ink, -12.5, 6.4, -51.5, 0.12, 0.12, 5.5, "Truss", collide=False)
for i in range(6):
    ball(pink if i % 2 == 0 else cyan, -12.5, 6.1, -56 + i * 1.8, 0.26, "TrussLamp")
# a neon strip over each door, so the rooms can be found
block(cyan, -15.9, 3.2, -43, 0.05, 0.12, 1.5, "DoorGlow", collide=False)
block(cyan, -25.5, 3.2, -50.9, 1.5, 0.12, 0.05, "DoorGlow", collide=False)
block(cyan, 15.9, 4.1, -51, 0.05, 0.12, 1.5, "DoorGlow", collide=False)
block(glow(GLOW), -31.9, 3.2, -57.5, 0.05, 0.12, 1.5, "DoorGlow", collide=False)
# the bar: a counter, stools, bottles
block(cel((0.40, 0.26, 0.34)), -24, 0, -41.6, 5.5, 1.1, 0.6, "BarCounter")
for i in range(5):
    tube(ink, -28 + i * 2, 0, -43, 0.7, 0.25, label="Stool")
    block(amber if i % 2 == 0 else pink, -28.4 + i * 2, 1.1, -41.3, 0.1, 0.45, 0.1, "Bottle", collide=False)

def crate(x, z, yaw, wood, band, light, w):
    c, s = math.cos(yaw), math.sin(yaw)
    def at(lx, ly, lz):
        return (x + lx * c + lz * s, ly, z - lx * s + lz * c)
    box(cel(wood), *at(0, w * 0.4, 0), w * 0.6, w * 0.4, w * 0.45, yaw, "Crate", collide=True)
    box(cel(band), *at(-w * 0.35, w * 0.4, 0), w * 0.06, w * 0.42, w * 0.47, yaw, "CrateBand")
    box(cel(band), *at(w * 0.35, w * 0.4, 0), w * 0.06, w * 0.42, w * 0.47, yaw, "CrateBand")
    box(glow(light), *at(0, w * 0.82, 0), w * 0.12, w * 0.03, w * 0.12, yaw, "CrateLid")
# the workshop: benches and crates of raided parts
crate(-29, -54.5, 0.3, (0.52, 0.36, 0.42), INK, AMBER, 1.4)
crate(-21, -60.5, -0.2, (0.52, 0.36, 0.42), INK, AMBER, 1.2)
block(cel((0.36, 0.28, 0.40)), -24, 0, -60.9, 2.4, 0.9, 0.5, "Bench")
# the vault: a plinth for the one blue piece, and a ring of pylons
PLUS_X, PLUS_Z = -40.5, -59.5
block(cel((0.26, 0.22, 0.38)), PLUS_X, 0, PLUS_Z, 0.7, 0.45, 0.7, "Plinth")
for i in range(4):
    tube(glow(GLOW_INK, 1.8), -41.5 + (i % 2) * 2, 0, -60.6 + (i // 2) * 2.2, 3.0, 0.1, label="Pylon")
# the lounge off the catwalk: a raised floor, low seats and a table lamp
block(deck, 23, 0, -51, 6, DECK_Y, 7, "LoungeFloor")
block(deck, 16, 0, -51, 1, DECK_Y, 1.5, "LoungeStep")
seat = cel((0.50, 0.20, 0.40))
block(seat, 27.6, DECK_Y, -51, 0.8, 0.6, 5.0, "Seat")
block(seat, 23, DECK_Y, -57.2, 4.0, 0.6, 0.6, "Seat")
tube(cel((0.36, 0.28, 0.40)), 23, DECK_Y, -51, 0.8, 0.9, label="Table", collide=True)
ball(amber, 23, DECK_Y + 1.2, -51, 0.35, "TableLamp")
# the blue glow: a beam over the boss chamber, seen from the passage
tube(glow(GLOW, 1.8), BOSS_X, 8, BOSS_Z, 60, 0.5, shape="Taper", label="BlueBeam")

# The dance floor: 20 tiles that change colour on the beat (M_Tile cycles three colours).
tiles = [named("MI_Tile0"), named("MI_Tile1"), named("MI_Tile2")]
for i in range(20):
    block(tiles[(i + i // 5) % 3], -8 + (i % 5) * 3.2, 0.02, -56 + (i // 5) * 3.2, 1.5, 0.03, 1.5, "Tile", collide=False)

def figure(x, y, z, yaw, s, cloak, skin, dark, hat, folder_label="Figure", mat=None):
    """kit_figure as static pieces. mat overrides every colour (the memory's hologram)."""
    c, sn = math.cos(yaw), math.sin(yaw)
    def at(lx, ly, lz):
        return (x + (lx * c + lz * sn) * s, y + ly * s, z + (-lx * sn + lz * c) * s)
    out = []
    md, mc, ms, mh = [mat or cel(v) for v in (dark, cloak, skin, hat)]
    out.append(tube(md, *at(-0.16, 0.05, 0), 0.8 * s, 0.10 * s, label=folder_label))
    out.append(tube(md, *at(0.16, 0.05, 0), 0.8 * s, 0.10 * s, label=folder_label))
    out.append(box(md, *at(0, 1.15, -0.3), 0.22 * s, 0.26 * s, 0.12 * s, yaw, folder_label))
    a = tube(mc, *at(0, 0.7, 0), 0.85 * s, 0.46 * s, shape="Cloak", rz=0.36 * s, label=folder_label)
    a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=ayaw(yaw), roll=0.0), False)
    out.append(a)
    out.append(ball(ms, *at(0, 1.66, 0), 0.17 * s, folder_label))
    out.append(tube(mh, *at(0, 1.76, 0), 0.16 * s, 0.40 * s, shape="Hat", label=folder_label))
    return out
# the DJ at the booth
figure(-13.6, 1.0, -51.5, math.pi * 0.5, 1.2, CYAN, (0.90, 0.72, 0.58), INK, PINK, "DJ")

# ---------------------------------------------------------------- the dome village and its gate
FOLDER[0] = "World/Village"
wallc, trim = (0.93, 0.88, 0.78), (0.55, 0.72, 0.62)
for i in range(1, 12):
    a = i * TAU / 12
    box(cel(wallc if i % 2 == 0 else (0.88, 0.82, 0.72)), VIL_X + math.sin(a) * VIL_R, 1.7, VIL_Z + math.cos(a) * VIL_R,
        1.95, 1.7, 0.2, a, "DomeWall", collide=True)
tube(cel(trim), VIL_X, 3.4, VIL_Z, 3.6, VIL_R + 0.5, shape="Hat", label="DomeRoof")
block(cel((0.80, 0.70, 0.58)), VIL_X, 0.0, VIL_Z + 3, 8, 0.03, 11, "DomeFloor", collide=False)
block(cel((0.76, 0.34, 0.20)), VIL_X - 3.5, 0, VIL_Z - 3.5, 1.0, 0.5, 1.9, "Bed")
block(cel(wallc), VIL_X - 3.5, 0.5, VIL_Z - 4.8, 0.7, 0.18, 0.4, "Pillow", collide=False)
crate(VIL_X + 3.6, VIL_Z - 3, 0.4, (0.70, 0.52, 0.36), INK, AMBER, 1.2)
block(cel(wallc), VIL_X - 1.9, 0, VIL_Z + 9.2, 0.25, 3.4, 2.6, "GateWall")
block(cel(wallc), VIL_X + 1.9, 0, VIL_Z + 9.2, 0.25, 3.4, 2.6, "GateWall")
block(cel(wallc), VIL_X, 3.0, VIL_Z + 9.2, 2.15, 0.4, 2.6, "GateLintel", collide=False)
scan = glow((0.40, 0.90, 0.70), 1.8)
for i in range(7):
    block(scan, VIL_X, 0.3 + i * 0.4, SCAN_Z, 1.65, 0.05, 0.03, "ScanBar", collide=False)
# unseen walls so the gate's corridor is the only way out, and the walk ends at the beam
for dx in (-2.3, 2.3):
    a = block(sand, VIL_X + dx, 0, VIL_Z + 7.2, 0.3, 4, 1.2, "GateSide")
    a.set_actor_hidden_in_game(True)
    a.static_mesh_component.set_visibility(False)

# ---------------------------------------------------------------- the rail line
FOLDER[0] = "World/Rail"
sleeper, steel = cel((0.40, 0.28, 0.24)), cel((0.60, 0.60, 0.66))
for i in range(100):
    s = i * 3.0
    c = rail_at(s)
    box(sleeper, c[0], 0.06, c[2], 1.5, 0.06, 0.22, rail_yaw(s), "Sleeper")
for i in range(50):
    s = i * 6.0
    a, b, y = rail_at(s), rail_at(s + 6), rail_yaw(s + 3)
    for o in (-1.0, 1.0):
        limb(steel, (a[0] + math.cos(y) * o, 0.16, a[2] - math.sin(y) * o), (b[0] + math.cos(y) * o, 0.16, b[2] - math.sin(y) * o), 0.07, label="Rail")
mesas((0.86, 0.50, 0.40), 5, 90, 270, 30, 12, 26)
dunes((0.93, 0.74, 0.50), 10, 110, 16, 0, 240, 4, 9)
BAT_X, BAT_Z = 187.0, 95.0
rocks((0.66, 0.36, 0.28), 20, 120, BAT_X, BAT_Z, 3, 14, 0.3, 1.2)
tube(cel(CREAM), BAT_X + 1.2, 0, BAT_Z + 0.8, 2.6, 0.09, label="Marker")
ball(glow(HEAT), BAT_X + 1.2, 2.8, BAT_Z + 0.8, 0.26, "MarkerLamp")

# ---------------------------------------------------------------- the edit bay's stage
FOLDER[0] = "World/BayStage"
paper, shade = glow(PAPER, 1.0), glow(SHADE, 1.0)
block(paper, BAY_X, 0, BAY_Z, 11, 0.05, 11, "BayFloor", collide=False)
block(shade, BAY_X, 0, BAY_Z - 6, 14, 12, 0.3, "BayBack", collide=False)
block(shade, BAY_X - 8, 0, BAY_Z, 0.3, 12, 14, "BaySide", collide=False)
block(shade, BAY_X + 8, 0, BAY_Z, 0.3, 12, 14, "BaySide", collide=False)

# ---------------------------------------------------------------- the memory's stage
FOLDER[0] = "World/Memory"
dark = glow((0.03, 0.06, 0.14), 1.0)
block(dark, MEM_X, 0, MEM_Z, 34, 0.05, 16, "MemFloor", collide=False)
block(dark, MEM_X, 0, MEM_Z - 14, 40, 22, 0.4, "MemBack", collide=False)
grid = glow(GLOW_INK, 1.8)
for i in range(9):
    block(grid, MEM_X - 16 + i * 4, 0.05, MEM_Z, 0.04, 0.02, 13, "MemGrid", collide=False)
    block(grid, MEM_X, 0.05, MEM_Z - 12 + i * 3, 28, 0.02, 0.04, "MemGrid", collide=False)
for i in range(4):
    block(grid, MEM_X - 12 + i * 8, 0, MEM_Z - 9, 1.2, 9, 1.2, "MemPillar", collide=False)

# ---------------------------------------------------------------- gameplay actors
def spawn(cls_name, label, loc, yaw=0.0, folder="Gameplay", scale=None):
    a = eas.spawn_actor_from_class(bpc(cls_name), loc, unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
    a.set_actor_label(label)
    a.set_folder_path(folder)
    if scale:
        a.set_actor_scale3d(unreal.Vector(*scale))
    return a
def point(label, loc, yaw=0.0):
    p = eas.spawn_actor_from_class(unreal.TargetPoint, loc, unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
    p.set_actor_label(label)
    p.set_folder_path("Gameplay/Points")
    return p
def holo(actor):
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_material(0) and c.get_material(0).get_name() != "M_Shadow":
            c.set_material(0, named("M_Hologram"))
        else:
            c.set_visibility(False)

game = spawn("BP_SpliceGame", "Game", A(0, 0.5, 14))
tod = spawn("BP_TimeOfDay", "TimeOfDay", A(0, 3, 14))
for ph, vals in PHASES.items():
    for k, v in vals.items():
        tod.set_editor_property(ph + k, unreal.LinearColor(*v))

rover = spawn("BP_Rover", "Rover", A(ROVER_X, 0, ROVER_Z), ayaw(0.2))
spawn("BP_Checkpoint", "Checkpoint", A(POST_X, 0, POST_Z))
spawn("BP_StashCrate", "StashCrate", A(CRATE_X, 0, CRATE_Z))

# Pickups. Hardware in cream, cards as dark film frames, banned tech glowing blue.
def pickup(label, item, x, y, z, shape, m, scale, banned=False, cell=False, pitch=0.0):
    f = spawn("BP_Fragment", label, A(x, y, z), folder="Gameplay/Pickups")
    f.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=0.0, roll=0.0), False)
    f.set_actor_scale3d(unreal.Vector(*scale))
    f.set_editor_property("ItemName", item)
    f.set_editor_property("bIsBanned", banned)
    f.set_editor_property("bIsBattery", cell)
    f.set_editor_property("Hover", True)
    smc = f.get_component_by_class(unreal.StaticMeshComponent)
    smc.set_static_mesh(SHAPES[shape])
    smc.set_material(0, m)
    return f
cream = cel(CREAM)
pickup("Pick_DrillArm", "Drill Arm", -6, 0.75, -14, "Drill", cream, (0.6, 0.6, 0.9), pitch=-70.0)
pickup("Pick_Treads", "Treads", 6, 0.75, -13, "Cube", cream, (1.2, 0.4, 0.56))
pickup("Pick_CardMove", "MOVE", 5, 0.75, -20, "Cube", cel(INK), (0.06, 0.84, 0.6))
pickup("Pick_CardDrill", "DRILL", 0, 0.75, -17, "Cube", cel(INK), (0.06, 0.84, 0.6))
pickup("Pick_Battery", "Battery", BAT_X, 0.75, BAT_Z, "Cube", glow(AMBER), (0.4, 0.52, 0.68))
pickup("Pick_DrillPlus", "DRILL+", PLUS_X, 0.75 + 0.55, PLUS_Z, "Cube", glow(GLOW), (0.6, 0.6, 0.6), banned=True, pitch=35.0)
for i, (x, z, y) in enumerate(((-29, -42, 0), (-19, -60, 0), (27, -46, DECK_Y), (13, -58.5, DECK_Y))):
    pickup(f"Cell_{i + 1}", "Battery cell", x, y + 0.75, z, "Cube", glow(AMBER), (0.28, 0.28, 0.52), cell=True)

# The rubble: 25 boulders across the tunnel. The Digger's DRILL clears them.
rub = cel((0.56, 0.36, 0.28))
for i in range(25):
    r = spawn("BP_Rubble", f"Rubble_{i:02d}", A(-2.6 + (i % 5) * 1.3, 0.6 + (i // 5) * 1.25, RUBBLE_Z + (kit_rand(float(i)) - 0.5) * 0.8),
              yaw=math.degrees(kit_rand(i + 5.0) * 6), folder="Gameplay/Rubble", scale=(1.6, 1.7, 1.44))
    smc = r.get_component_by_class(unreal.StaticMeshComponent)
    smc.set_static_mesh(SHAPES["Rock"])
    smc.set_material(0, rub)
    smc.set_collision_profile_name("BlockAll")
    smc.set_editor_property("cast_shadow", False)
# Where the Digger starts its cards: one MOVE from here stops just short of the rubble or the wall.
bot_site = point("Site_Rubble", A(0, 0, -27.0))
boss_site = point("Site_BossWall", A(0, 0, -55.0))

# Walking past the cleared rubble turns dusk into night.
night = spawn("BP_PhaseTrigger", "NightTrigger", A(0, 1.75, RUBBLE_Z - 1.5), scale=(0.5, 8.0, 3.5))
night.set_editor_property("PhaseIndex", 3)
night.set_editor_property("Objective", "Find the blue glow.")

# The party's people: five raiders dancing, four Imperial robots on patrol.
RAIDERS = [(-6, -48), (-1, -52), (4, -47), (-3, -45), (-22, -44)]
for i, (x, z) in enumerate(RAIDERS):
    r = spawn("BP_Raider", f"Raider_{i + 1}", A(x, 0, z), yaw=57.0 * i, folder="Gameplay/Raiders")
    r.set_editor_property("DropName", "Raider piece")
PATROLS = [((8.5, -45), (8.5, -57)), ((-24, -46), (-19, -46)), ((-24, -57), (-29, -57)), ((-38, -47), (-38, -57))]
for i, (a, b) in enumerate(PATROLS):
    wps = [point(f"Patrol{i}_{j}", A(p[0], 0, p[1])) for j, p in enumerate((a, b))]
    imp = spawn("BP_Imperial", f"Imperial_{i + 1}", A(a[0], 0, a[1]), folder="Gameplay/Imperials")
    imp.set_editor_property("bImperial", True)
    imp.set_editor_property("DropName", "Imperial piece")
    imp.set_editor_property("Route", wps)

# Four beams sweeping the dance floor from the truss.
for i in range(4):
    b = spawn("BP_Beam", f"Beam_{i + 1}", A(-4, 0.1, -50), folder="Gameplay/Party")
    b.set_editor_property("Top", A(-12.5, 6.1, -55 + i * 2.4))
    b.set_editor_property("Phase", i * 1.6)
    b.get_component_by_class(unreal.StaticMeshComponent).set_material(0, glow(PINK if i % 2 == 0 else CYAN, 1.6))

# The boss wall (only DRILL+ breaks it) and the banned bot behind it, facing the way you come in.
spawn("BP_BossWall", "BossWall", A(0, 4.5, WALL_Z), scale=(2.0, 8.0, 9.0))
spawn("BP_Boss", "Boss", A(BOSS_X, 0, BOSS_Z), yaw=180.0)

# The rail rover, at the start of the line.
rr = spawn("BP_RailRover", "RailRover", A(*rail_at(0.0)), ayaw(rail_yaw(0.0)))
cam = rr.get_component_by_class(unreal.CameraComponent)
cam.set_editor_property("relative_rotation", unreal.Rotator(pitch=-9.0, yaw=0.0, roll=0.0))
cam.set_editor_property("field_of_view", 70.0)

# The edit bay's stage: the Digger you are building, and the camera the bay looks through.
bay_bot = spawn("BP_Bot", "BayBot", A(BAY_X, 0.05, BAY_Z), ayaw(0.7), "Gameplay/Bay", scale=(1.35, 1.35, 1.35))
eye, at = A(BAY_X + 3.4, 2.4, BAY_Z + 8.6), A(BAY_X, 0.9, BAY_Z)
bay_cam = eas.spawn_actor_from_class(unreal.CameraActor, eye, unreal.MathLibrary.find_look_at_rotation(eye, at))
bay_cam.set_actor_label("BayCam")
bay_cam.set_folder_path("Gameplay/Bay")
bay_cam.camera_component.set_editor_property("field_of_view", 54.0)
bay_cam.camera_component.set_editor_property("constrain_aspect_ratio", False)

# The memory: robots and people working side by side, all hologram blue.
for i in range(3):
    d = spawn("BP_Bot", f"Mem_Digger{i}", A(MEM_X - 6 + i * 6, 0.05, MEM_Z - 2), ayaw(0.6 + i * 0.4), "Gameplay/Memory", scale=(1.41, 1.41, 1.41))
    holo(d)
    for piece in figure(MEM_X - 4 + i * 6, 0.05, MEM_Z + 0.5, 2.4 + i * 0.5, 1.1, GLOW, GLOW, GLOW, GLOW, "MemFigure", mat=named("M_Hologram")):
        piece.set_folder_path("Gameplay/Memory")
eye, at = A(MEM_X - 9, 2.0, MEM_Z + 9), A(MEM_X - 3, 1.3, MEM_Z - 1)
mem_cam = spawn("BP_MemoryCam", "MemoryCam", eye, folder="Gameplay/Memory")
mem_cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(eye, at), False)
mem_cam.set_editor_property("Speed", 107.0)
mem_cam.get_component_by_class(unreal.CameraComponent).set_editor_property("field_of_view", 60.0)

# The title's camera: a slow orbit of the rover parked at the mine.
title_cam = spawn("BP_OrbitCam", "TitleCam", A(ROVER_X - 3, 3.2, ROVER_Z + 15), folder="Gameplay/Title")
title_cam.set_editor_property("Center", A(ROVER_X - 3, 3.2, ROVER_Z + 2))
title_cam.set_editor_property("LookAt", A(ROVER_X - 3, 1.8, ROVER_Z - 2))
title_cam.set_editor_property("Radius", 1300.0)
title_cam.set_editor_property("Rate", 0.12)
title_cam.get_component_by_class(unreal.CameraComponent).set_editor_property("field_of_view", 60.0)

# Where the player stands: the run starts in the village; the mine start is also the checkpoint.
mine_start = point("MineStart", A(START_X, 0.95, START_Z), 0.0)
if start is None:
    start = eas.spawn_actor_from_class(unreal.PlayerStart, A(VIL_X, 1.0, VIL_Z - 3), R0)
    start.set_actor_label("PlayerStart")
start.set_actor_location_and_rotation(A(VIL_X, 1.0, VIL_Z - 3), unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0), False, False)

for prop, val in (("Tuning", unreal.load_asset("/Game/Splice/Data/DA_Tuning")), ("RespawnPoint", mine_start),
                  ("MineStart", mine_start), ("BotSpawn", bot_site), ("BossSite", boss_site), ("MemoryCam", mem_cam),
                  ("BayCam", bay_cam), ("BayBot", bay_bot), ("TitleCam", title_cam), ("RailRover", rr),
                  ("MemoryCaptions", CAPTIONS)):
    game.set_editor_property(prop, val)

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
f"world built: {N_ACT[0]} static pieces, {len(WALLS)} wall entries, {len(RAIDERS)} raiders, {len(PATROLS)} Imperial robots, 25 rubble, 10 pickups"
'''

if __name__ == "__main__":
    print(py(SRC.replace("__PHASES__", repr(PHASES)).replace("__CAPTIONS__", repr(CAPTIONS))))
