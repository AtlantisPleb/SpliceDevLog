"""Splice vertical slice, phase 3: the night zone of L_Mine (idempotent).

Beyond the exit room this builds a network of rooms:

    Storage -- Workshop          (south: battery cells, benches)
       |          |
    [  Main hall: dance floor, stage and DJ, catwalk  ] -- corridor -- Vault -- Boss chamber
       |          |
      Bar ---- Lounge            (north)

and places: the time-of-day actor, the night trigger, the checkpoint, the one blue piece
(DRILL+, at one of three spots chosen at random each run), battery cells, dancing
raiders, patrolling Imperial robots, the stash crate, the boss wall and boss, and the
off-map memory diorama with its camera.

Run after splice_step1_level.py and splice_place.py.
Usage: python3 tools/ue/splice_slice_level.py
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from uemcp import py  # noqa: E402

# Time-of-day presets: tint multiplies the picture; fog alpha is its strength.
PRESETS = {
    "DawnTint": (1.00, 0.86, 0.88, 1.0), "DawnFog": (0.85, 0.50, 0.52, 0.22),
    "DayTint": (1.00, 1.00, 1.00, 1.0), "DayFog": (1.00, 1.00, 1.00, 0.0),
    "DuskTint": (1.00, 0.78, 0.62, 1.0), "DuskFog": (0.75, 0.33, 0.14, 0.28),
    "NightTint": (0.40, 0.36, 0.62, 1.0), "NightFog": (0.035, 0.02, 0.07, 0.45),
}
# Placeholder lines until Kiki's captions arrive.
CAPTIONS = [
    "[MEMORY 1 OF 3]  Before the Mandates, they worked beside us.",
    "[MEMORY 2 OF 3]  Every shift, side by side. Nobody called it strange.",
    "[MEMORY 3 OF 3]  Then the Emperor cut them from the record. Until now.",
]

print(py("PRESETS = " + repr(PRESETS) + "\nCAPTIONS = " + repr(CAPTIONS) + r'''
import math
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for _ in range(20):
    if not les.is_in_play_in_editor():
        break
    les.editor_request_end_play()
    await asyncio.sleep(0.5)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if world is None or not world.get_path_name().startswith("/Game/Splice/L_Mine"):
    les.load_level("/Game/Splice/L_Mine")

SHAPES = {n: unreal.load_asset("/Engine/BasicShapes/" + n) for n in ("Cube", "Cylinder", "Sphere")}
T = 20.0
def mat(name):
    return unreal.load_asset(f"/Game/Splice/Materials/{name}")
def bpc(name):
    return unreal.load_class(None, f"/Game/Splice/Blueprints/{name}.{name}_C")

# Remove what this script owns, plus the old end wall of the exit room.
OWNED = ("PR_", "Slice_", "Raider_", "Imperial_", "Frag_Banned", "Frag_DrillPlus", "Cell_", "ExitPad", "Mem_")
game = None
for a in eas.get_all_level_actors():
    l = a.get_actor_label()
    if l.startswith(OWNED) or l == "ExitEndWall":
        eas.destroy_actor(a)
    elif l == "Game":
        game = a
if game is None:
    game = eas.spawn_actor_from_class(bpc("BP_SpliceGame"), unreal.Vector(120, 0, 50))
    game.set_actor_label("Game")
    game.set_folder_path("Gameplay")
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "BotSpawn":
            game.set_editor_property("BotSpawn", a)

N_BOX = [0]
def box(label, x0, x1, y0, y1, z0, z1, m, folder="Night", collide=True, shape="Cube", rot=None):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                                   rot or unreal.Rotator(pitch=0, yaw=0, roll=0))
    smc = a.static_mesh_component
    smc.set_static_mesh(SHAPES[shape])
    smc.set_material(0, mat(m))
    smc.set_collision_profile_name("BlockAll" if collide else "NoCollision")
    smc.set_editor_property("cast_shadow", False)
    a.set_actor_scale3d(unreal.Vector((x1 - x0) / 100, (y1 - y0) / 100, (z1 - z0) / 100))
    a.set_actor_label("PR_" + label)
    a.set_folder_path(folder)
    N_BOX[0] += 1
    return a

def wall(name, axis, fixed, a0, a1, h, doors, m, folder):
    """A wall on one side of a room, with door gaps.

    axis "x": the wall runs along X at y = fixed..fixed+T. axis "y": along Y at x = fixed..fixed+T.
    doors: [(start, end, door height)] along the wall's run."""
    pos = a0
    i = 0
    def seg(s, e, z0, z1, tag):
        if e - s < 1 or z1 - z0 < 1:
            return
        if axis == "x":
            box(f"{name}_{tag}", s, e, fixed, fixed + T, z0, z1, m, folder)
        else:
            box(f"{name}_{tag}", fixed, fixed + T, s, e, z0, z1, m, folder)
    for d0, d1, dh in sorted(doors):
        seg(pos, d0, 0, h, f"s{i}")
        seg(d0, d1, dh, h, f"l{i}")
        pos = d1
        i += 1
    seg(pos, a1, 0, h, f"s{i}")

def room(name, x0, x1, y0, y1, h, doors=None, skip=""):
    """Floor, ceiling and four walls. doors: {"N"|"S"|"E"|"W": [(start, end, height)]}.
    Walls sit just outside the room, so two rooms side by side leave a 40 cm doorway depth."""
    doors = doors or {}
    f = f"Night/{name}"
    box(f"{name}_Floor", x0 - T, x1 + T, y0 - T, y1 + T, -T, 0, "M_MineFloor", f)
    box(f"{name}_Ceiling", x0 - T, x1 + T, y0 - T, y1 + T, h, h + T, "M_MineCeiling", f)
    if "S" not in skip:
        wall(f"{name}_S", "x", y0 - T, x0, x1, h, doors.get("S", []), "M_MineWall", f)
    if "N" not in skip:
        wall(f"{name}_N", "x", y1, x0, x1, h, doors.get("N", []), "M_MineWall", f)
    if "W" not in skip:
        wall(f"{name}_W", "y", x0 - T, y0 - T, y1 + T, h, doors.get("W", []), "M_MineWall", f)
    if "E" not in skip:
        wall(f"{name}_E", "y", x1, y0 - T, y1 + T, h, doors.get("E", []), "M_MineWall", f)

# ---------------------------------------------------------------- rooms
# Main hall. Its west wall opens onto the exit room (8 m wide, 4 m high).
room("Hall", 4020, 6400, -1000, 1000, 700, {
    "W": [(-400, 400, 400)],
    "N": [(4850, 5050, 260), (5350, 5550, 260)],
    "S": [(4650, 4850, 300), (5550, 5750, 300)],
    "E": [(-150, 150, 300)],
})
room("Bar", 4300, 5200, 1040, 1800, 400, {"S": [(4850, 5050, 260)], "E": [(1300, 1500, 300)]})
room("Lounge", 5240, 6140, 1040, 1800, 400, {"S": [(5350, 5550, 260)], "W": [(1300, 1500, 300)]})
room("Storage", 4300, 5200, -1800, -1040, 400, {"N": [(4650, 4850, 300)], "E": [(-1500, -1300, 300)]})
room("Workshop", 5240, 6140, -1800, -1040, 400, {"N": [(5550, 5750, 300)], "W": [(-1500, -1300, 300)]})
room("Corridor", 6420, 7000, -150, 150, 300, skip="WE")
room("Vault", 7020, 7800, -600, 600, 450, {"W": [(-150, 150, 300)], "E": [(-200, 200, 400)]})
room("BossRoom", 7840, 8800, -600, 600, 600, {"W": [(-200, 200, 400)]})

# ---------------------------------------------------------------- hall: catwalk
CW_Z, CW_Y0, CW_Y1 = 300.0, 650.0, 1000.0
box("Catwalk", 4700, 5700, CW_Y0, CW_Y1, CW_Z - T, CW_Z, "M_Gray", "Night/Hall")
for i, x in enumerate((4700, 5200, 5700)):
    box(f"CatwalkPost{i}", x - 10, x + 10, CW_Y0, CW_Y0 + 20, 0, CW_Z - T, "M_Dark", "Night/Hall")
run, rise = 660.0, CW_Z
length = math.hypot(run, rise)
pitch = math.degrees(math.atan2(rise, run))
for label, cx, sign in (("RampA", 4700 - run / 2, 1.0), ("RampB", 5700 + run / 2, -1.0)):
    a = box(label, 0, length, 0, CW_Y1 - CW_Y0, 0, T, "M_Gray", "Night/Hall",
            rot=unreal.Rotator(pitch=sign * pitch, yaw=0.0, roll=0.0))
    a.set_actor_location(unreal.Vector(cx, (CW_Y0 + CW_Y1) / 2, rise / 2 - 10), False, False)

# ---------------------------------------------------------------- hall: party dressing
D = "Night/Party"
NEONS = ("M_NeonPink", "M_NeonLime", "M_NeonAmber")
# Dance floor: 5 x 4 lit tiles, each pulsing out of step with its neighbours.
for i in range(5):
    for j in range(4):
        x, y = 4700 + i * 200, -400 + j * 200
        box(f"Tile_{i}{j}", x + 6, x + 194, y + 6, y + 194, 0, 3, NEONS[(i + 2 * j) % 3], D, collide=False)
# Stage in the south-east corner, with the DJ desk, speakers and a screen behind.
box("Stage", 5900, 6380, -780, -220, 0, 70, "M_Dark", D)
box("StageEdge", 5892, 5900, -780, -220, 50, 70, "M_NeonPink", D, collide=False)
box("DJDesk", 6020, 6100, -660, -340, 70, 160, "M_Dark", D)
box("DJDeskGlow", 6012, 6020, -650, -350, 110, 150, "M_NeonLime", D, collide=False)
for k, y in enumerate((-770, -310)):
    box(f"Speaker{k}", 6240, 6340, y, y + 80, 70, 360, "M_Dark", D)
    box(f"SpeakerCone{k}", 6232, 6240, y + 12, y + 68, 250, 330, "M_NeonAmber", D, collide=False)
    box(f"SpeakerCone{k}b", 6232, 6240, y + 12, y + 68, 110, 220, "M_NeonAmber", D, collide=False)
box("Screen", 6384, 6392, -700, -300, 160, 520, "M_NeonViolet", D, collide=False)
box("ScreenBarA", 6376, 6384, -690, -310, 400, 430, "M_NeonPink", D, collide=False)
box("ScreenBarB", 6376, 6384, -690, -310, 250, 280, "M_NeonLime", D, collide=False)
# Neon strips high on the hall's walls.
box("StripS", 4200, 6200, -998, -990, 560, 580, "M_NeonPink", D, collide=False)
box("StripN", 4200, 6200, 990, 998, 560, 580, "M_NeonLime", D, collide=False)
box("StripW", 4022, 4030, -900, 900, 560, 580, "M_NeonViolet", D, collide=False)
# Door frames in neon, so each way out reads from across the room.
for k, (x0, x1, y, m) in enumerate(((4850, 5050, 992, "M_NeonAmber"), (5350, 5550, 992, "M_NeonAmber"),
                                     (4650, 4850, -998, "M_NeonLime"), (5550, 5750, -998, "M_NeonLime"))):
    top = 260 if y > 0 else 300
    box(f"DoorGlow{k}", x0, x1, y, y + 6, top, top + 14, m, D, collide=False)
box("DoorGlowE", 6392, 6398, -150, 150, 300, 314, "M_NeonPink", D, collide=False)

def spawn(cls_name, label, loc, folder="Gameplay", rot=None):
    a = eas.spawn_actor_from_class(bpc(cls_name), unreal.Vector(*loc), rot or unreal.Rotator(pitch=0, yaw=0, roll=0))
    a.set_actor_label(label)
    a.set_folder_path(folder)
    return a

def spinner(label, loc, scale, m, rate=0.0, roll=0.0, bob=0.0, shape="Cube", folder=D):
    a = spawn("BP_Spinner", label, loc, folder)
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    smc.set_static_mesh(SHAPES[shape])
    smc.set_material(0, mat(m))
    a.set_actor_scale3d(unreal.Vector(*scale))
    a.set_editor_property("Rate", rate)
    a.set_editor_property("RollRate", roll)
    a.set_editor_property("Bob", bob)
    return a

# Light bars sweeping over the dance floor, and a slow mirror cube.
spinner("PR_LaserA", (5200, 0, 620), (14, 0.06, 0.06), "M_NeonPink", rate=40)
spinner("PR_LaserB", (5200, 0, 580), (12, 0.06, 0.06), "M_NeonLime", rate=-55)
spinner("PR_LaserC", (5200, 0, 540), (10, 0.06, 0.06), "M_NeonAmber", rate=75)
spinner("PR_MirrorCube", (5200, 0, 470), (0.7, 0.7, 0.7), "M_NeonViolet", rate=30, roll=20)

# ---------------------------------------------------------------- side rooms
# Bar: a counter with a lit top, and stools.
box("BarCounter", 4420, 5080, 1620, 1700, 0, 110, "M_Dark", "Night/Bar")
box("BarCounterGlow", 4420, 5080, 1612, 1620, 96, 110, "M_NeonAmber", "Night/Bar", collide=False)
for k, x in enumerate((4520, 4700, 4880)):
    box(f"BarStool{k}", x, x + 40, 1540, 1580, 0, 60, "M_Gray", "Night/Bar", shape="Cylinder")
box("BarStrip", 4320, 5180, 1792, 1798, 330, 344, "M_NeonAmber", "Night/Bar", collide=False)
# Lounge: low seats round a table.
box("LoungeSeatA", 5320, 5640, 1680, 1780, 0, 50, "M_Blue", "Night/Lounge")
box("LoungeSeatB", 6040, 6130, 1150, 1500, 0, 50, "M_Blue", "Night/Lounge")
box("LoungeTable", 5700, 5860, 1360, 1520, 0, 40, "M_Dark", "Night/Lounge")
box("LoungeTableGlow", 5704, 5856, 1364, 1516, 40, 43, "M_NeonPink", "Night/Lounge", collide=False)
box("LoungeStrip", 5260, 6120, 1792, 1798, 330, 344, "M_NeonPink", "Night/Lounge", collide=False)
# Storage: stacked crates.
for k, (x, y, s) in enumerate(((4380, -1760, 140), (4540, -1760, 100), (4380, -1600, 100), (5060, -1740, 120), (4960, -1180, 90))):
    box(f"StoreCrate{k}", x, x + s, y, y + s, 0, s, "M_Gray", "Night/Storage")
box("StorageStrip", 4320, 5180, -1798, -1792, 330, 344, "M_NeonLime", "Night/Storage", collide=False)
# Workshop: a bench and a parts rack.
box("WorkBench", 5320, 5760, -1780, -1700, 0, 90, "M_Dark", "Night/Workshop")
box("WorkBenchTop", 5320, 5760, -1700, -1694, 76, 90, "M_NeonAmber", "Night/Workshop", collide=False)
box("WorkRack", 6060, 6130, -1500, -1150, 0, 220, "M_Gray", "Night/Workshop")
box("WorkshopStrip", 5260, 6120, -1798, -1792, 330, 344, "M_NeonViolet", "Night/Workshop", collide=False)
# Corridor and vault: violet strips lead the way to the crate.
box("CorridorStrip", 6440, 6980, 144, 150, 240, 250, "M_NeonViolet", "Night/Corridor", collide=False)
box("VaultStrip", 7040, 7780, 594, 600, 380, 394, "M_NeonViolet", "Night/Vault", collide=False)

# ---------------------------------------------------------------- gameplay
tod = spawn("BP_TimeOfDay", "Slice_TimeOfDay", (100, 0, 300))
for k, v in PRESETS.items():
    tod.set_editor_property(k, unreal.LinearColor(*v))

# Walking out of the drilled tunnel into the exit room turns day into night.
night = spawn("BP_PhaseTrigger", "Slice_NightTrigger", (3320, 0, 175))
night.set_actor_scale3d(unreal.Vector(0.5, 8.0, 3.5))
night.set_editor_property("PhaseIndex", 3)
night.set_editor_property("Objective", "Find the blue glow. It's somewhere in the party.")

spawn("BP_Checkpoint", "Slice_Checkpoint", (300, -330, 100))
def point(label, loc, yaw=0.0):
    p = eas.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(*loc), unreal.Rotator(pitch=0, yaw=yaw, roll=0))
    p.set_actor_label(label)
    p.set_folder_path("Gameplay/Points")
    return p
# Clear of the back wall, so the camera behind the player has room.
respawn = point("Slice_RespawnPoint", (520, 90, 100))

# The one blue piece: DRILL+. It starts at one of three spots, picked at random each run.
spots = [point("Slice_BlueSpot1", (4420, 1720, 60)), point("Slice_BlueSpot2", (6040, 1720, 60)),
         point("Slice_BlueSpot3", (6000, -1720, 60))]
blue = spawn("BP_Fragment", "Frag_DrillPlus", (4420, 1720, 60), "Gameplay/Fragments")
blue.set_actor_scale3d(unreal.Vector(1.2, 0.8, 0.24))
blue.set_editor_property("ItemName", "DRILL+")
blue.set_editor_property("bIsBanned", True)
blue.set_editor_property("Spots", spots)
blue.get_component_by_class(unreal.StaticMeshComponent).set_material(0, mat("M_Pad"))

# Battery cells: a reason to look into every room.
CELLS = [(4460, -1500, 50), (4700, -1700, 50), (5100, -1300, 50),       # storage
         (4400, 1200, 50), (5900, 1250, 50), (5500, -1250, 50),         # bar, lounge, workshop
         (5200, 825, CW_Z + 50), (7650, 500, 50)]                       # catwalk, vault
for i, loc in enumerate(CELLS):
    c = spawn("BP_Fragment", f"Cell_{i + 1}", loc, "Gameplay/Cells")
    c.set_actor_scale3d(unreal.Vector(0.5, 0.5, 0.9))
    c.set_editor_property("ItemName", "Battery cell")
    c.set_editor_property("bIsBattery", True)
    smc = c.get_component_by_class(unreal.StaticMeshComponent)
    smc.set_static_mesh(SHAPES["Cylinder"])
    smc.set_material(0, mat("M_NeonAmber"))

# Raiders: dancing on the floor, behind the DJ desk, and in the side rooms.
RAIDERS = [(4800, -300), (5000, 100), (5200, -100), (5400, 300), (5600, -300), (5000, -300), (5400, -100),
           (4600, 1400), (4950, 1500), (5750, 1600), (5600, -1500)]
for i, (x, y) in enumerate(RAIDERS):
    r = spawn("BP_Raider", f"Raider_{i + 1}", (x, y, 96), "Gameplay/Raiders")
    r.set_editor_property("DropName", "Raider part")
dj = spawn("BP_Raider", "Raider_DJ", (6180, -500, 166), "Gameplay/Raiders")
dj.set_editor_property("DropName", "DJ's mixer chip")
dj.set_editor_property("HP", 3)

# Imperial robots: three patrols. Routes run through door centres, never through walls.
ROUTES = {
    "Hall": [(4400, -700), (5750, -850), (5750, 520), (4400, 520)],
    "North": [(4600, 1400), (5120, 1400), (5320, 1400), (5900, 1400), (5320, 1400), (5120, 1400)],
    "South": [(4600, -1400), (5120, -1400), (5320, -1400), (5900, -1400), (5320, -1400), (5120, -1400)],
}
for name, pts in ROUTES.items():
    wps = [point(f"Slice_Route{name}{i}", (x, y, 96)) for i, (x, y) in enumerate(pts)]
    imp = spawn("BP_Imperial", f"Imperial_{name}", (pts[0][0], pts[0][1], 96), "Gameplay/Imperials")
    imp.set_editor_property("bImperial", True)
    imp.set_editor_property("DropName", "Imperial part")
    imp.set_editor_property("Route", wps)

# Vault: the stash crate. The Digger's job site faces the boss wall.
spawn("BP_StashCrate", "Slice_StashCrate", (7300, -330, 40))
boss_site = point("Slice_BossSite", (7380, 0, 50))
bw = spawn("BP_BossWall", "Slice_BossWall", (7820, 0, 200))
bw.set_actor_scale3d(unreal.Vector(0.4, 4.0, 4.0))
spawn("BP_Boss", "Slice_Boss", (8400, 0, 200))

# ---------------------------------------------------------------- memory diorama (off the map)
MX, MY = 1400.0, 5000.0
M = "Night/Memory"
def holo(label, x0, x1, y0, y1, z0, z1, shape="Cube"):
    a = box(label, x0, x1, y0, y1, z0, z1, "M_Hologram", M, collide=False, shape=shape)
    a.set_actor_label("Mem_" + label)
    return a
holo("Floor", MX - 200, MX + 1400, MY - 300, MY + 500, -10, 0)
holo("Belt", MX - 100, MX + 1300, MY + 60, MY + 140, 60, 80)
for k in range(3):
    bx = MX + 100 + k * 420
    # A human: a cylinder body and a sphere head.
    holo(f"Human{k}", bx - 30, bx + 30, MY - 60, MY, 0, 150, "Cylinder")
    holo(f"Head{k}", bx - 28, bx + 28, MY - 58, MY - 2, 150, 206, "Sphere")
    # A bot beside them: the Digger's shapes, bobbing, with a turning drill arm.
    spinner(f"Mem_Bot{k}", (bx + 170, MY - 30, 50), (1, 1, 1), "M_Hologram", bob=6.0, folder=M)
    spinner(f"Mem_BotFront{k}", (bx + 170, MY + 20, 55), (0.8, 0.08, 0.5), "M_Hologram", bob=6.0, folder=M)
    drill = spinner(f"Mem_Drill{k}", (bx + 170, MY + 70, 60), (0.16, 0.9, 0.16), "M_Hologram", bob=6.0, folder=M)
    # The drill arm points along +Y; turning it about that axis is a yaw of a pitched actor.
    drill.set_actor_rotation(unreal.Rotator(pitch=90.0, yaw=90.0, roll=0.0), False)
    drill.set_actor_scale3d(unreal.Vector(0.9, 0.16, 0.16))
    drill.set_editor_property("RollRate", 240.0)
    holo(f"Crate{k}", bx + 40, bx + 100, MY + 70, MY + 130, 80, 140)
cam = spawn("BP_MemoryCam", "Mem_Camera", (MX - 50, MY - 620, 190), M, unreal.Rotator(pitch=-6.0, yaw=90.0, roll=0.0))
cam.set_editor_property("Speed", 45.0)

# ---------------------------------------------------------------- wire the game actor
game.set_editor_property("RespawnPoint", respawn)
game.set_editor_property("Tuning", unreal.load_asset("/Game/Splice/Data/DA_Tuning"))
game.set_editor_property("BossSite", boss_site)
game.set_editor_property("MemoryCam", cam)
game.set_editor_property("MemoryCaptions", CAPTIONS)

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
n_rubble = len([a for a in eas.get_all_level_actors() if a.get_actor_label().startswith("RubbleBP_")])
(f"night zone built: {N_BOX[0]} boxes, 8 rooms, {len(RAIDERS) + 1} raiders, {len(ROUTES)} Imperial robots, "
 f"{len(CELLS)} battery cells, 1 blue piece at one of {len(spots)} spots; rubble pieces={n_rubble}")
'''))
