"""Splice phase 2: write Blueprint graph logic from tools/ue/splice_dsl/*.dsl.

Blueprints call each other (the game spawns the bot, the bot reports back), so
empty stub events are written first, then each full graph, then everything is
compiled. Usage: python3 tools/ue/splice_build_logic.py [BP_Name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from uemcp import ToolError, py, tool  # noqa: E402

B = "/Game/Splice/Blueprints/"
WRITE = "BlueprintToolsets.BlueprintDslToolset.Write"
STUBS = {
    "BP_SpliceGame": """
(event `PickUp` (params (Item :type String)))
(event `SetNearRover` (params (Near :type Boolean)))
(event `BotFinished` (params (Success :type Boolean)))
(event `ShowEnd`)
""",
    "BP_Bot": "(event `Run`)",
}
ORDER = ["BP_Rubble", "BP_SpliceGame", "BP_Bot", "BP_Rover", "BP_Fragment", "BP_EndTrigger"]


def write(bp, dsl):
    r = tool(WRITE, assetPath=B + bp, dsl=dsl, scope="")
    return r


only = sys.argv[1:] or ORDER
for bp, dsl in STUBS.items():
    try:
        write(bp, dsl)
    except ToolError as e:
        if "already" not in str(e):
            print(f"stub {bp}: {e}")

failed = False
for bp in ORDER:
    if bp not in only:
        continue
    dsl = open(os.path.join(HERE, "splice_dsl", bp + ".dsl")).read()
    try:
        r = write(bp, dsl)
        warn = r.get("returnValue", {}) if isinstance(r, dict) else r
        print(f"OK   {bp}")
        w = str(warn)
        if "warn" in w.lower():
            print("     ", w[:600])
    except ToolError as e:
        failed = True
        print(f"FAIL {bp}:\n{str(e)[:3000]}")

print(py(r'''
out = []
for n in ["BP_Rubble", "BP_SpliceGame", "BP_Bot", "BP_Rover", "BP_Fragment", "BP_EndTrigger"]:
    bp = unreal.load_asset("/Game/Splice/Blueprints/" + n)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    st = bp.get_editor_property("status")
    unreal.EditorAssetLibrary.save_asset("/Game/Splice/Blueprints/" + n)
    out.append(f"{n}={st}")
" ".join(out)
'''))
sys.exit(1 if failed else 0)
