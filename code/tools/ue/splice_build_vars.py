"""Splice phase 1c: Blueprint member variables."""
import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from uemcp import ToolError, ref, tool  # noqa: E402

BPT = "BlueprintToolsets.BlueprintToolset"
B = "/Game/Splice/Blueprints/"
def bp(n): return ref(f"{B}{n}.{n}")
def cls(p): n = p.rsplit("/", 1)[1]; return ref(f"{p}.{n}_C")

PLAIN = [  # (blueprint, name, type, array?, instance editable?)
    ("BP_SpliceGame", "Inventory", "string", True, False),
    ("BP_SpliceGame", "Strip", "string", True, False),
    ("BP_SpliceGame", "SlotArm", "string", False, False),
    ("BP_SpliceGame", "SlotTreads", "string", False, False),
    ("BP_SpliceGame", "SlotBattery", "string", False, False),
    ("BP_SpliceGame", "NearRover", "bool", False, False),
    ("BP_SpliceGame", "BayOpen", "bool", False, False),
    ("BP_SpliceGame", "BotRunning", "bool", False, False),
    ("BP_Fragment", "ItemName", "string", False, True),
    ("BP_Bot", "Cards", "string", True, False),
    ("BP_Rover", "WasNear", "bool", False, False),
]
OBJ = [  # (blueprint, name, class path, instance editable?)
    ("BP_SpliceGame", "HUD", "/Game/Splice/UI/WBP_HUD", False),
    ("BP_SpliceGame", "EditBay", "/Game/Splice/UI/WBP_EditBay", False),
    ("BP_SpliceGame", "EndScreen", "/Game/Splice/UI/WBP_End", False),
    ("BP_SpliceGame", "BotSpawn", "/Script/Engine.Actor", True),
    ("BP_SpliceGame", "Bot", "/Game/Splice/Blueprints/BP_Bot", False),
    ("BP_Bot", "Game", "/Game/Splice/Blueprints/BP_SpliceGame", False),
]
for b, n, t, arr, ie in PLAIN:
    try:
        tool(f"{BPT}.AddVariable", blueprint=bp(b), name=n, typeName=t, options={"containerType": "Array"} if arr else {})
    except ToolError as e:
        print("skip", b, n, str(e)[:120])
    if ie:
        tool(f"{BPT}.SetVariableInstanceEditable", blueprint=bp(b), variableName=n, bInstanceEditable=True)
for b, n, c, ie in OBJ:
    oc = ref(c) if c.startswith("/Script") else cls(c)
    try:
        tool(f"{BPT}.AddObjectVariable", blueprint=bp(b), name=n, objectClass=oc)
    except ToolError as e:
        print("skip", b, n, str(e)[:120])
    if ie:
        tool(f"{BPT}.SetVariableInstanceEditable", blueprint=bp(b), variableName=n, bInstanceEditable=True)
print("vars done")
