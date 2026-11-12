"""Scripted playthrough of vertical slice steps 8-10, in play mode in the editor.

Checks state only (no screenshots): night switch, banned pieces and Heat, raiders and the
catwalk, hearts, out-of-hearts respawn, Heat cooling at the rover, the Imperial Sweep,
and the end pad. Prints PASS or FAIL per check and exits non-zero on any failure.
Usage: python3 tools/ue/splice_playtest_slice.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uemcp import py  # noqa: E402

PRE = r'''
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
W = ues.get_game_world()
GS = unreal.GameplayStatics
def cls(n):
    return unreal.load_class(None, f"/Game/Splice/Blueprints/{n}.{n}_C")
def game():
    return GS.get_actor_of_class(W, cls("BP_SpliceGame"))
def pawn():
    return GS.get_player_pawn(W, 0)
def go(x, y, z=100.0):
    pawn().set_actor_location(unreal.Vector(x, y, z), False, True)
def call(name, *args):
    game().call_method(name, args=tuple(args))
def S():
    g = game()
    raiders = GS.get_all_actors_of_class(W, cls("BP_Raider"))
    frags = [f for f in GS.get_all_actors_of_class(W, cls("BP_Fragment")) if f.get_editor_property("bIsBanned")]
    return dict(
        heat=round(g.get_editor_property("Heat"), 1), hearts=g.get_editor_property("Hearts"),
        banned=g.get_editor_property("BannedCarried"), phase=g.get_editor_property("Phase"),
        objective=str(g.get_editor_property("Objective")), busy=g.get_editor_property("Busy"),
        inv=len(g.get_editor_property("Inventory")), rubble=len(GS.get_all_actors_of_class(W, cls("BP_Rubble"))),
        raiders=len(raiders), chasing=sum(1 for r in raiders if r.get_editor_property("Chasing")),
        banned_hidden=sum(1 for f in frags if f.get_editor_property("hidden")), px=round(pawn().get_actor_location().x),
        end=g.get_editor_property("EndScreen") is not None)
extra = None
'''

FAILS = []


def stage(title, body, checks):
    s = eval(str(py(PRE + body + "\nrepr(dict(S(), extra=extra))")))
    line = " ".join(f"{k}={v}" for k, v in s.items())
    print(f"[{title}] {line}")
    for label, fn in checks:
        ok = bool(fn(s))
        print(f"    {'PASS' if ok else 'FAIL'}  {label}")
        if not ok:
            FAILS.append(f"{title}: {label}")
    return s


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

stage("start", "await asyncio.sleep(0.5)", [
    ("3 hearts, no Heat, phase is Day", lambda s: s["hearts"] == 3 and s["heat"] == 0 and s["phase"] == 1),
    ("5 raiders, none chasing", lambda s: s["raiders"] == 5 and s["chasing"] == 0),
    ("objective set", lambda s: "Digger" in s["objective"]),
])
stage("gray box run", r'''
for x, y in [(1100, -300), (1350, 320), (1620, -260), (1500, 380), (1050, 250)]:
    go(x, y)
    await asyncio.sleep(0.5)
go(560, 40)
await asyncio.sleep(1.0)
call("ToggleEditBay")
await asyncio.sleep(0.3)
for e in ["ClickArm", "ClickTreads", "ClickBattery", "ClickMove", "ClickDrill"]:
    call(e)
call("Deploy")
await asyncio.sleep(7.0)
''', [
    ("rubble cleared by MOVE then DRILL", lambda s: s["rubble"] == 0),
    ("objective moved on", lambda s: "tunnel" in s["objective"].lower()),
])
stage("night switch", r'''
go(3200, 0)
await asyncio.sleep(0.3)
go(3320, 0)
await asyncio.sleep(0.8)
''', [
    ("phase is Night", lambda s: s["phase"] == 3),
    ("objective is the blue glow", lambda s: "blue glow" in s["objective"].lower()),
])
stage("catwalk piece", r'''
go(5500, 825, 420)
await asyncio.sleep(3.0)
''', [
    ("banned piece on the catwalk picked up: Heat 25", lambda s: s["banned"] == 1 and s["heat"] == 25),
    ("no raider chases a player on the catwalk", lambda s: s["chasing"] == 0),
    ("no heart lost on the catwalk", lambda s: s["hearts"] == 3),
])
stage("floor piece", r'''
go(5600, -250)
await asyncio.sleep(0.7)
extra = sum(1 for r in GS.get_all_actors_of_class(W, cls("BP_Raider")) if r.get_editor_property("Chasing"))
''', [
    ("second banned piece: Heat 50", lambda s: s["banned"] == 2 and s["heat"] == 50),
    ("raiders chase on the floor", lambda s: s["extra"] >= 1),
])
stage("raider hits", r'''
import time
t0 = time.time()
for _ in range(30):
    await asyncio.sleep(0.25)
    if game().get_editor_property("Hearts") < 3:
        break
extra = round(time.time() - t0, 1)
''', [("a raider hit cost exactly one heart", lambda s: s["hearts"] == 2)])
stage("out of hearts", r'''
import time
t0 = time.time()
for _ in range(120):
    await asyncio.sleep(0.25)
    if game().get_editor_property("Busy"):
        break
extra = round(time.time() - t0, 1)
await asyncio.sleep(3.5)
''', [
    ("the last two hearts took at least 1.5 s to lose", lambda s: s["extra"] >= 1.5),
    ("back at the checkpoint", lambda s: s["px"] < 600),
    ("hearts restored to 3", lambda s: s["hearts"] == 3),
    ("Heat reset and unsaved banned pieces lost", lambda s: s["heat"] == 0 and s["banned"] == 0),
    ("lost banned pieces are back in the level", lambda s: s["banned_hidden"] == 0),
    ("parts from before the checkpoint kept", lambda s: s["inv"] == 5),
])
stage("heat cools at the rover", r'''
go(560, 40)
await asyncio.sleep(0.8)
call("AddHeat", 50.0)
await asyncio.sleep(2.0)
''', [("Heat fell from 50 by about 5 per second", lambda s: 36 <= s["heat"] <= 44)])
stage("imperial sweep", r'''
go(3600, 0)
await asyncio.sleep(0.5)
call("AddHeat", 100.0)
await asyncio.sleep(0.5)
extra = game().get_editor_property("Busy")
await asyncio.sleep(3.0)
''', [
    ("banner showed (game was busy)", lambda s: s["extra"] is True),
    ("sent back to the checkpoint with Heat reset", lambda s: s["px"] < 600 and s["heat"] == 0),
])
stage("end pad", r'''
go(6500, -250)
await asyncio.sleep(0.4)
go(6820, -250)
await asyncio.sleep(1.0)
''', [("end screen shows", lambda s: s["end"])])

print(py(r'''
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.editor_request_end_play()
"pie ended"
'''))
print("\nRESULT:", "ALL PASS" if not FAILS else f"{len(FAILS)} FAILED")
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
