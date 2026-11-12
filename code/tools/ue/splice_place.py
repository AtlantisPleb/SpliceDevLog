"""Splice phase 3: place the gameplay actors in L_Mine (idempotent)."""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from uemcp import py  # noqa: E402

print(py(r'''
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

def bpc(name):
    return unreal.load_class(None, f"/Game/Splice/Blueprints/{name}.{name}_C")
def mat(name):
    return unreal.load_asset(f"/Game/Splice/Materials/{name}")

GAMEPLAY = ("Game", "Rover", "Frag_", "BotSpawn", "ExitPad", "RubbleBP_")
old_rubble = []
for a in eas.get_all_level_actors():
    l = a.get_actor_label()
    if l.startswith(GAMEPLAY):
        eas.destroy_actor(a)
    elif l.startswith("Rubble_"):
        old_rubble.append(a)

# Rubble: each placeholder cube becomes a BP_Rubble with the same transform.
n = 0
for a in old_rubble:
    t = a.get_actor_transform()
    r = eas.spawn_actor_from_class(bpc("BP_Rubble"), t.translation, t.rotation.rotator())
    r.set_actor_scale3d(t.scale3d)
    r.get_component_by_class(unreal.StaticMeshComponent).set_material(0, mat("M_Rubble"))
    r.set_actor_label(f"RubbleBP_{n:02d}")
    r.set_folder_path("Gameplay/Rubble")
    eas.destroy_actor(a)
    n += 1
if n == 0:  # already converted on an earlier run: re-label existing BP_Rubble actors
    for a in eas.get_all_level_actors():
        if a.get_class() == bpc("BP_Rubble"):
            n += 1

spawn = eas.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(2280, 0, 50), unreal.Rotator(pitch=0, yaw=0, roll=0))
spawn.set_actor_label("BotSpawn")
spawn.set_folder_path("Gameplay")

game = eas.spawn_actor_from_class(bpc("BP_SpliceGame"), unreal.Vector(120, 0, 50))
game.set_actor_label("Game")
game.set_folder_path("Gameplay")
game.set_editor_property("BotSpawn", spawn)

rover = eas.spawn_actor_from_class(bpc("BP_Rover"), unreal.Vector(550, -180, 0))
rover.set_actor_label("Rover")
rover.set_folder_path("Gameplay")

FRAGS = [  # label, item name, material, location, actor scale
    ("Frag_DrillArm", "Drill Arm", "M_Orange", (1100, -300, 60), (1, 1, 1)),
    ("Frag_Treads", "Treads", "M_Blue", (1350, 320, 60), (1, 1, 1)),
    ("Frag_Battery", "Battery", "M_Green", (1620, -260, 60), (1, 1, 1)),
    ("Frag_CardMove", "MOVE", "M_White", (1500, 380, 45), (1.2, 0.8, 0.12)),
    ("Frag_CardDrill", "DRILL", "M_White", (1050, 250, 45), (1.2, 0.8, 0.12)),
]
for label, item, m, loc, sc in FRAGS:
    f = eas.spawn_actor_from_class(bpc("BP_Fragment"), unreal.Vector(*loc))
    f.set_actor_label(label)
    f.set_folder_path("Gameplay/Fragments")
    f.set_actor_scale3d(unreal.Vector(*sc))
    f.set_editor_property("ItemName", item)
    f.get_component_by_class(unreal.StaticMeshComponent).set_material(0, mat(m))

pad = eas.spawn_actor_from_class(bpc("BP_EndTrigger"), unreal.Vector(3600, 0, 0))
pad.set_actor_label("ExitPad")
pad.set_folder_path("Gameplay")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
f"placed: rubble={n}, game, rover, {len(FRAGS)} fragments, bot spawn, exit pad"
'''))
