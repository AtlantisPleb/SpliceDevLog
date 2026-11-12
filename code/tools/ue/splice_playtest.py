"""Automated play-through of the Splice gray box in PIE, driven through the editor.

Each stage runs inside the editor; between stages the editor window is captured
with macOS screencapture (UMG only shows in a real window capture).
Usage: python3 tools/ue/splice_playtest.py OUTDIR
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uemcp import py  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/splice_playtest"
os.makedirs(OUT, exist_ok=True)

PRE = r'''
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
W = ues.get_game_world()
GS = unreal.GameplayStatics
def actor(label_class):
    c = unreal.load_class(None, f"/Game/Splice/Blueprints/{label_class}.{label_class}_C")
    return GS.get_actor_of_class(W, c)
def count(cls_name):
    c = unreal.load_class(None, f"/Game/Splice/Blueprints/{cls_name}.{cls_name}_C")
    return len(GS.get_all_actors_of_class(W, c))
def pawn():
    return GS.get_player_pawn(W, 0)
def go(x, y, z=100.0, yaw=0.0):
    p = pawn()
    p.set_actor_location(unreal.Vector(x, y, z), False, True)
    p.get_controller().set_control_rotation(unreal.Rotator(pitch=-10, yaw=yaw, roll=0))
def state():
    g = actor("BP_SpliceGame")
    return (f"inv={list(g.get_editor_property('Inventory'))} strip={list(g.get_editor_property('Strip'))} "
            f"arm={g.get_editor_property('SlotArm')!r} treads={g.get_editor_property('SlotTreads')!r} "
            f"battery={g.get_editor_property('SlotBattery')!r} near={g.get_editor_property('NearRover')} "
            f"bay={g.get_editor_property('BayOpen')} botRunning={g.get_editor_property('BotRunning')} "
            f"rubble={count('BP_Rubble')} bots={count('BP_Bot')} fragments={count('BP_Fragment')} "
            f"end={g.get_editor_property('EndScreen') is not None}")
def call(name, *args):
    actor("BP_SpliceGame").call_method(name, args=tuple(args))
'''


def stage(title, body, shot=None, wait=0.0):
    src = PRE + body + "\nstate()"
    r = py(src)
    print(f"[{title}] {r}")
    if wait:
        time.sleep(wait)
    if shot:
        subprocess.run(["osascript", "-e", 'tell application "UnrealEditor" to activate'])
        time.sleep(1.2)
        path = os.path.join(OUT, shot + ".png")
        subprocess.run(["screencapture", "-x", path])
        print("   shot:", path)
    return r


# Start PIE.
print(py(r'''
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for _ in range(20):
    if not les.is_in_play_in_editor():
        break
    les.editor_request_end_play()
    await asyncio.sleep(0.5)
await asyncio.sleep(1.0)
les.editor_request_begin_play()
await asyncio.sleep(6.0)
"pie=" + str(les.is_in_play_in_editor())
'''))
stage("start", "await asyncio.sleep(0.5)", shot="01_start")
stage("pickups", r'''
for x, y in [(1100, -300), (1350, 320), (1620, -260), (1500, 380), (1050, 250)]:
    go(x, y)
    await asyncio.sleep(0.6)
go(1000, 0, yaw=180)
await asyncio.sleep(0.5)
''', shot="02_pickups")
stage("at rover", r'''
go(560, 40, yaw=-90)
await asyncio.sleep(1.0)
''', shot="03_rover_prompt")
stage("open bay", r'''
call("ToggleEditBay")
await asyncio.sleep(0.5)
for e in ["ClickArm", "ClickTreads", "ClickBattery", "ClickDrill", "ClickMove"]:
    call(e)
await asyncio.sleep(0.5)
''', shot="04_bay_wrong_order")
stage("deploy wrong", r'''
call("Deploy")
go(2000, 170, 120, yaw=-8)
await asyncio.sleep(2.0)
''', shot="05_drilling_air", wait=0.0)
stage("wrong result", r'''
await asyncio.sleep(4.0)
''', shot="06_bad_cut")
stage("re-cut", r'''
await asyncio.sleep(2.5)
go(560, 40, yaw=-90)
await asyncio.sleep(1.0)
call("ToggleEditBay")
await asyncio.sleep(0.4)
call("ClearStrip")
call("ClickMove")
call("ClickDrill")
await asyncio.sleep(0.5)
''', shot="07_bay_right_order")
stage("deploy right", r'''
call("Deploy")
go(2000, 170, 120, yaw=-8)
await asyncio.sleep(3.2)
''', shot="08_bot_moving")
stage("right result", r'''
await asyncio.sleep(3.5)
''', shot="09_tunnel_clear")
stage("exit", r'''
go(3300, 0, 100, yaw=0)
await asyncio.sleep(0.5)
go(3600, 0, 100, yaw=0)
await asyncio.sleep(1.0)
''', shot="10_scene_restored")
