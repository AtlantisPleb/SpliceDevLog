"""Scripted playthrough of the whole Splice run, in play mode in the editor.

Checks game state only (no screenshots), from the first pickup to SCENE RESTORED:
the Digger waking and following, a wrong cut and a right cut, the night switch, passive
raiders, a fight, the blue piece, battery cells, Imperial robots and Heat, the catwalk,
out-of-hearts respawn, the stash crate, the boss wall and DRILL+, the boss, the core and
the memory ending. Prints PASS or FAIL per check; exits non-zero on any failure.
Usage: python3 tools/ue/splice_playtest_slice.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uemcp import py  # noqa: E402

PRE = r'''
import time
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
W = ues.get_game_world()
GS = unreal.GameplayStatics
def cls(n):
    return unreal.load_class(None, f"/Game/Splice/Blueprints/{n}.{n}_C")
def all_of(n):
    return GS.get_all_actors_of_class(W, cls(n))
def game():
    return GS.get_actor_of_class(W, cls("BP_SpliceGame"))
def pawn():
    return GS.get_player_pawn(W, 0)
def go(x, y, z=100.0):
    pawn().set_actor_location(unreal.Vector(x, y, z), False, True)
def call(name, *args):
    game().call_method(name, args=tuple(args))
def dist(a, b):
    return (a.get_actor_location() - b.get_actor_location()).length()
async def wait_bot(limit=40.0):
    """Wait until the Digger has finished its job and is following again."""
    t0 = time.time()
    await asyncio.sleep(0.5)
    while time.time() - t0 < limit and game().get_editor_property("BotRunning"):
        await asyncio.sleep(0.25)
    await asyncio.sleep(0.3)
def S():
    g = game()
    bots = all_of("BP_Bot")
    npcs = list(all_of("BP_Raider")) + list(all_of("BP_Imperial"))
    blue = [f for f in all_of("BP_Fragment") if f.get_editor_property("bIsBanned")]
    boss = GS.get_actor_of_class(W, cls("BP_Boss"))
    return dict(
        heat=round(g.get_editor_property("Heat"), 1), hearts=g.get_editor_property("Hearts"),
        phase=g.get_editor_property("Phase"), objective=str(g.get_editor_property("Objective")),
        busy=g.get_editor_property("Busy"), inv=[str(i) for i in g.get_editor_property("Inventory")],
        cells=g.get_editor_property("Cells"), parts=g.get_editor_property("Parts"),
        rubble=len(all_of("BP_Rubble")), wall=len(all_of("BP_BossWall")),
        raiders=len(all_of("BP_Raider")), imperials=len(all_of("BP_Imperial")),
        chasing=sum(1 for n in npcs if n.get_editor_property("Chasing")),
        bots=len(bots), bot_mode=bots[0].get_editor_property("Mode") if bots else -1,
        bot_dist=round(dist(bots[0], pawn())) if bots else -1,
        blue_hidden=sum(1 for f in blue if f.get_editor_property("hidden")),
        near_crate=g.get_editor_property("NearCrate"),
        boss_dead=boss.get_editor_property("Dead") if boss else None,
        memory=g.get_editor_property("MemoryPlaying"),
        px=round(pawn().get_actor_location().x), end=g.get_editor_property("EndScreen") is not None)
extra = None
'''

FAILS = []
N = [0]


def stage(title, body, checks):
    s = eval(str(py(PRE + body + "\nrepr(dict(S(), extra=extra))")))
    keys = ("heat", "hearts", "phase", "cells", "parts", "rubble", "wall", "raiders", "chasing", "bot_mode", "bot_dist", "px", "extra")
    print(f"[{title}] " + " ".join(f"{k}={s[k]}" for k in keys))
    for label, fn in checks:
        N[0] += 1
        try:
            ok = bool(fn(s))
        except Exception as e:  # a check that can't run is a failure
            ok = False
            label += f"  ({e})"
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
    ("no Digger yet", lambda s: s["bots"] == 0),
    ("12 raiders and 3 Imperial robots, none chasing", lambda s: s["raiders"] == 12 and s["imperials"] == 3 and s["chasing"] == 0),
    ("player is the cylinder (mannequin hidden)", lambda s: s["extra"] is None),
])
stage("splice the Digger", r'''
for x, y in [(1100, -300), (1350, 320), (1620, -260), (1500, 380), (1050, 250)]:
    go(x, y)
    await asyncio.sleep(0.5)
go(560, 40)
await asyncio.sleep(1.0)
call("ToggleEditBay")
await asyncio.sleep(0.3)
for e in ["ClickArm", "ClickTreads", "ClickBattery"]:
    call(e)
await asyncio.sleep(0.5)
''', [
    ("all 5 parts picked up", lambda s: len(s["inv"]) == 5),
    ("the Digger woke when its 3 parts were placed", lambda s: s["bots"] == 1 and s["bot_mode"] == 0),
])
stage("wrong cut", r'''
call("ClickDrill")
call("ClickMove")
call("Deploy")
await asyncio.sleep(1.2)
extra = all_of("BP_Bot")[0].get_editor_property("Mode")
await wait_bot()
''', [
    ("the Digger drove off to the job (it left follow mode)", lambda s: s["extra"] in (1, 2)),
    ("DRILL then MOVE leaves the rubble", lambda s: s["rubble"] == 25),
    ("the Digger went back to following", lambda s: s["bot_mode"] == 0),
])
stage("right cut", r'''
go(560, 40)
await asyncio.sleep(1.0)
call("ToggleEditBay")
await asyncio.sleep(0.3)
call("ClearStrip")
call("ClickMove")
call("ClickDrill")
call("Deploy")
await wait_bot()
''', [
    ("MOVE then DRILL clears the rubble", lambda s: s["rubble"] == 0),
    ("objective moved on", lambda s: "tunnel" in s["objective"].lower()),
])
stage("the Digger follows", r'''
go(2600, 0)
await asyncio.sleep(3.0)
''', [("the Digger is beside the player after a long move", lambda s: 0 <= s["bot_dist"] < 260)])
stage("night switch", r'''
go(3200, 0)
await asyncio.sleep(0.3)
go(3320, 0)
await asyncio.sleep(0.8)
''', [
    ("phase is Night", lambda s: s["phase"] == 3),
    ("objective is the blue glow", lambda s: "blue glow" in s["objective"].lower()),
])
stage("raiders are passive", r'''
go(4890, -300)
await asyncio.sleep(2.5)
''', [
    ("standing next to a dancing raider: nobody chases", lambda s: s["chasing"] == 0),
    ("no heart lost", lambda s: s["hearts"] == 3),
])
stage("fight a raider", r'''
call("Attack")
await asyncio.sleep(0.3)
extra = sum(1 for r in all_of("BP_Raider") if r.get_editor_property("Provoked"))
await asyncio.sleep(0.4)
call("Attack")
await asyncio.sleep(0.5)
''', [
    ("the first hit provoked exactly one raider", lambda s: s["extra"] == 1),
    ("two hits beat it: one raider fewer", lambda s: s["raiders"] == 11),
    ("it dropped a robot part into the inventory", lambda s: s["parts"] == 1),
    ("winning a fight raised Heat by 15", lambda s: s["heat"] == 15),
])
stage("find the blue piece", r'''
blue = [f for f in all_of("BP_Fragment") if f.get_editor_property("bIsBanned")][0]
loc = blue.get_actor_location()
spots = [(4420, 1720), (6040, 1720), (6000, -1720)]
extra = any(abs(loc.x - x) < 5 and abs(loc.y - y) < 5 for x, y in spots)
go(loc.x - 120, loc.y)
await asyncio.sleep(0.3)
go(loc.x, loc.y)
await asyncio.sleep(0.8)
''', [
    ("there is one blue piece, at one of its three spots", lambda s: s["extra"] is True),
    ("DRILL+ is in the inventory", lambda s: "DRILL+" in s["inv"]),
    ("Heat rose by 25", lambda s: s["heat"] == 40),
    ("objective points to the stash crate", lambda s: "stash crate" in s["objective"].lower()),
])
stage("battery cell", r'''
go(4460, -1620)
await asyncio.sleep(0.3)
go(4460, -1500)
await asyncio.sleep(0.6)
''', [("a battery cell was picked up", lambda s: s["cells"] == 1)])
stage("Imperial robot hunts a hot player", r'''
imp = [i for i in all_of("BP_Imperial")][0]
l = imp.get_actor_location()
go(l.x - 200, l.y)
await asyncio.sleep(1.0)
extra = sum(1 for i in all_of("BP_Imperial") if i.get_editor_property("Chasing"))
''', [("at Heat 40 an Imperial robot nearby gives chase", lambda s: s["extra"] >= 1)])
stage("catwalk is safe", r'''
go(5200, 825, 420)
await asyncio.sleep(2.5)
''', [
    ("nobody chases a player on the catwalk", lambda s: s["chasing"] == 0),
    ("the catwalk cell was picked up", lambda s: s["cells"] == 2),
])
stage("out of hearts", r'''
for _ in range(4):
    if game().get_editor_property("Busy"):
        break
    call("DamagePlayer")
    await asyncio.sleep(1.15)
extra = game().get_editor_property("Busy")
await asyncio.sleep(3.2)
''', [
    ("the take-two banner showed", lambda s: s["extra"] is True),
    ("back at the checkpoint with 3 hearts and no Heat", lambda s: s["px"] < 700 and s["hearts"] == 3 and s["heat"] == 0),
    ("the unsaved DRILL+ was lost and is back in the level", lambda s: "DRILL+" not in s["inv"] and s["blue_hidden"] == 0),
    ("parts saved at the rover were kept", lambda s: len(s["inv"]) == 5),
])
stage("get DRILL+ again and reach the crate", r'''
blue = [f for f in all_of("BP_Fragment") if f.get_editor_property("bIsBanned")][0]
loc = blue.get_actor_location()
go(loc.x - 120, loc.y)
await asyncio.sleep(0.3)
go(loc.x, loc.y)
await asyncio.sleep(0.6)
go(7300, -150)
await asyncio.sleep(1.5)
''', [
    ("DRILL+ picked up again", lambda s: "DRILL+" in s["inv"]),
    ("the stash crate knows the player is near", lambda s: s["near_crate"] is True),
    ("the Digger followed all the way", lambda s: 0 <= s["bot_dist"] < 260),
])
stage("plain DRILL can't break the boss wall", r'''
h = game().get_editor_property("Heat")
await asyncio.sleep(1.0)
extra = game().get_editor_property("Heat") < h
call("ToggleEditBay")
await asyncio.sleep(0.3)
call("ClearStrip")
call("ClickMove")
call("ClickDrill")
call("Deploy")
await wait_bot()
''', [
    ("Heat cools at the stash crate", lambda s: s["extra"] is True),
    ("the wall is still there", lambda s: s["wall"] == 1),
])
stage("DRILL+ breaks it", r'''
call("ToggleEditBay")
await asyncio.sleep(0.3)
call("ClearStrip")
call("ClickMove")
call("ClickDrillPlus")
call("Deploy")
await wait_bot()
''', [
    ("the wall is gone", lambda s: s["wall"] == 0),
    ("objective is to stun the boss", lambda s: "stun" in s["objective"].lower()),
])
stage("boss", r'''
go(8120, 0)
await asyncio.sleep(0.8)
boss = GS.get_actor_of_class(W, cls("BP_Boss"))
extra = boss.get_editor_property("Active")
for x, y in ((8120, 0), (8400, -290), (8400, 290)):
    go(x, y)
    await asyncio.sleep(0.55)
    call("Attack")
    await asyncio.sleep(0.2)
await asyncio.sleep(0.5)
''', [
    ("the boss woke once its wall was down", lambda s: s["extra"] is True),
    ("three stuns powered it down", lambda s: s["boss_dead"] is True),
])
stage("core", r'''
go(8040, 150)
await asyncio.sleep(0.3)
go(8040, 0)
await asyncio.sleep(0.8)
''', [("the banned core is in the inventory", lambda s: "Banned core" in s["inv"])])
stage("memory", r'''
go(7300, -150)
await asyncio.sleep(1.2)
call("ToggleEditBay")
await asyncio.sleep(0.3)
call("SpliceCore")
await asyncio.sleep(2.0)
pc = GS.get_player_controller(W, 0)
target = pc.get_view_target()
mem = game().get_editor_property("MemoryWidget")
extra = (target.get_class().get_name(), game().get_editor_property("MemoryPlaying"), mem is not None)
''', [
    ("the camera cut to the memory scene", lambda s: s["extra"][0] == "BP_MemoryCam_C"),
    ("the memory is playing with its overlay", lambda s: s["extra"][1] is True and s["extra"][2] is True),
])
stage("ending", r'''
await asyncio.sleep(15.0)
''', [
    ("after three captions the memory ended by itself", lambda s: s["memory"] is False),
    ("SCENE RESTORED shows", lambda s: s["end"]),
])

print(py(r'''
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.editor_request_end_play()
"pie ended"
'''))
print(f"\nRESULT: {N[0] - len(FAILS)} of {N[0]} checks pass")
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
