"""Splice vertical slice, steps 8-10, phase 3: extend L_Mine (idempotent).

- Opens the far end of the exit room into the Party Room: 30 x 20 m, a lower floor, a
  catwalk along one wall, and a ramp at each end of the catwalk.
- Places the time-of-day actor, the night trigger, the checkpoint and respawn point,
  3 banned pieces, 5 raiders, and moves the end pad to the far side of the Party Room.

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
    "NightTint": (0.46, 0.44, 0.70, 1.0), "NightFog": (0.035, 0.025, 0.07, 0.50),
}

print(py("PRESETS = " + repr(PRESETS) + r'''
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

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
T = 20.0
def mat(name):
    return unreal.load_asset(f"/Game/Splice/Materials/{name}")
def bpc(name):
    return unreal.load_class(None, f"/Game/Splice/Blueprints/{name}.{name}_C")

# Remove what this script owns, plus the old end wall of the exit room.
OWNED = ("PR_", "Slice_", "Raider_", "Frag_Banned", "ExitPad")
game = None
for a in eas.get_all_level_actors():
    l = a.get_actor_label()
    if l.startswith(OWNED) or l == "ExitEndWall":
        eas.destroy_actor(a)
    elif l == "Game":
        game = a

# The game-state actor must exist; recreate it if something removed it.
if game is None:
    game = eas.spawn_actor_from_class(bpc("BP_SpliceGame"), unreal.Vector(120, 0, 50))
    game.set_actor_label("Game")
    game.set_folder_path("Gameplay")
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "BotSpawn":
            game.set_editor_property("BotSpawn", a)

def box(label, x0, x1, y0, y1, z0, z1, m, folder="Mine/PartyRoom"):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    smc = a.static_mesh_component
    smc.set_static_mesh(CUBE)
    smc.set_material(0, mat(m))
    smc.set_collision_profile_name("BlockAll")
    a.set_actor_scale3d(unreal.Vector((x1 - x0) / 100, (y1 - y0) / 100, (z1 - z0) / 100))
    a.set_actor_label(label)
    a.set_folder_path(folder)
    return a

# ---- Party Room shell: x 4000-7000, y -1000..1000, 7 m high.
X0, X1, HW, H = 4000.0, 7000.0, 1000.0, 700.0
box("PR_Floor", X0, X1, -HW - T, HW + T, -T, 0, "M_MineFloor")
box("PR_Ceiling", X0, X1, -HW - T, HW + T, H, H + T, "M_MineCeiling")
box("PR_WallL", X0, X1, -HW - T, -HW, 0, H, "M_MineWall")
box("PR_WallR", X0, X1, HW, HW + T, 0, H, "M_MineWall")
box("PR_EndWall", X1, X1 + T, -HW - T, HW + T, 0, H, "M_MineWall")
# Entry wall with a doorway the size of the exit room (8 m wide, 4 m high).
box("PR_EntryL", X0, X0 + T, -HW, -400, 0, H, "M_MineWall")
box("PR_EntryR", X0, X0 + T, 400, HW, 0, H, "M_MineWall")
box("PR_EntryLintel", X0, X0 + T, -400, 400, 400, H, "M_MineWall")

# ---- Catwalk along the +Y wall, 3 m up, with a ramp at each end.
CW_Z, CW_Y0 = 300.0, 650.0
box("PR_Catwalk", 4900, 6100, CW_Y0, HW, CW_Z - T, CW_Z, "M_Gray")
for i, x in enumerate((4900, 5300, 5700, 6100)):
    box(f"PR_CatwalkPost{i}", x - 10, x + 10, CW_Y0, CW_Y0 + 20, 0, CW_Z - T, "M_Dark")
import math
run, rise = 700.0, CW_Z
length = math.hypot(run, rise)
pitch = math.degrees(math.atan2(rise, run))
for label, cx, sign in (("PR_RampA", 4900 - run / 2, 1.0), ("PR_RampB", 6100 + run / 2, -1.0)):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(cx, (CW_Y0 + HW) / 2, rise / 2 - 10),
                                   unreal.Rotator(pitch=sign * pitch, yaw=0.0, roll=0.0))
    smc = a.static_mesh_component
    smc.set_static_mesh(CUBE)
    smc.set_material(0, mat("M_Gray"))
    smc.set_collision_profile_name("BlockAll")
    a.set_actor_scale3d(unreal.Vector(length / 100, (HW - CW_Y0) / 100, T / 100))
    a.set_actor_label(label)
    a.set_folder_path("Mine/PartyRoom")

# ---- Gameplay.
def spawn(cls_name, label, loc, folder="Gameplay", rot=None):
    a = eas.spawn_actor_from_class(bpc(cls_name), unreal.Vector(*loc), rot or unreal.Rotator(pitch=0, yaw=0, roll=0))
    a.set_actor_label(label)
    a.set_folder_path(folder)
    return a

tod = spawn("BP_TimeOfDay", "Slice_TimeOfDay", (100, 0, 300))
for k, v in PRESETS.items():
    tod.set_editor_property(k, unreal.LinearColor(*v))

# Walking out of the drilled tunnel into the exit room turns day into night.
night = spawn("BP_PhaseTrigger", "Slice_NightTrigger", (3320, 0, 175))
night.set_actor_scale3d(unreal.Vector(0.5, 8.0, 3.5))
night.set_editor_property("PhaseIndex", 3)
night.set_editor_property("Objective", "Find the blue glow")

spawn("BP_Checkpoint", "Slice_Checkpoint", (300, -330, 100))
# Clear of the back wall, so the camera behind the player has room.
respawn = eas.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(520, 90, 100), unreal.Rotator(pitch=0, yaw=0, roll=0))
respawn.set_actor_label("Slice_RespawnPoint")
respawn.set_folder_path("Gameplay")
game.set_editor_property("RespawnPoint", respawn)
game.set_editor_property("Tuning", unreal.load_asset("/Game/Splice/Data/DA_Tuning"))

# Three banned pieces: one on the floor mid-room, one on the catwalk, one in the far corner.
for i, loc in enumerate(((5600, -250, 60), (5500, 825, CW_Z + 60), (6750, -750, 60))):
    f = spawn("BP_Fragment", f"Frag_Banned{i + 1}", loc, "Gameplay/Fragments")
    f.set_actor_scale3d(unreal.Vector(0.9, 0.9, 0.9))
    f.set_editor_property("ItemName", "Banned piece")
    f.set_editor_property("bIsBanned", True)
    f.get_component_by_class(unreal.StaticMeshComponent).set_material(0, mat("M_Pad"))

# Five raiders on the lower floor.
for i, (x, y) in enumerate(((4800, -400), (5400, 100), (5900, -600), (6300, 250), (5200, -780))):
    spawn("BP_Raider", f"Raider_{i + 1}", (x, y, 96), "Gameplay/Raiders")

# The end pad moves to the far side of the Party Room until the boss and ending are built.
pad = spawn("BP_EndTrigger", "ExitPad", (6820, -250, 0))

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
n_rubble = len([a for a in eas.get_all_level_actors() if a.get_actor_label().startswith("RubbleBP_")])
f"party room built: catwalk, 2 ramps, night trigger, checkpoint, 3 banned pieces, 5 raiders; end pad moved; rubble pieces={n_rubble}; game BotSpawn set={game.get_editor_property('BotSpawn') is not None}"
'''))
