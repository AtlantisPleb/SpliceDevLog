"""Splice vertical slice, steps 8-10, phase 1: assets.

Creates, if missing:
- BP_Tuning (a data asset class) and DA_Tuning (the one place for every tuning number);
- BP_TimeOfDay, BP_PhaseTrigger, BP_Raider, BP_Checkpoint, with components and variables;
- new variables on BP_SpliceGame and BP_Fragment;
- the HUD panels from the Game UI board, and the two full-screen banners.

Graph logic is written by splice_build_logic.py; styling by splice_build_layout.py.
Usage: python3 tools/ue/splice_slice_assets.py
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from uemcp import ToolError, py, ref, tool  # noqa: E402

BP = "/Game/Splice/Blueprints"
DATA = "/Game/Splice/Data"
UI = "/Game/Splice/UI"
BPT = "BlueprintToolsets.BlueprintToolset"
WBT = "UMGEditor.WidgetBlueprintEditorSubsystem"

# Every tuning number: (name, type, value). Distances are in cm, times in seconds.
TUNING = [
    # Heat and hearts
    ("HeatPerBannedPiece", "float", 25.0),
    ("HeatPerFight", "float", 15.0),
    ("MaxHeat", "float", 100.0),
    ("HeatCoolRate", "float", 5.0),
    ("MaxHearts", "int", 3),
    ("SweepBannerTime", "float", 2.0),
    # Raiders and Imperial robots
    ("NoticeRange", "float", 500.0),
    ("RaiderSpeed", "float", 260.0),
    ("RaiderWanderSpeed", "float", 90.0),
    ("RaiderHitRange", "float", 110.0),
    ("RaiderHitCooldown", "float", 1.0),
    ("RaiderGiveUpDistance", "float", 1500.0),
    ("RaiderHP", "int", 2),
    ("ImperialHP", "int", 3),
    ("ImperialNoticeRange", "float", 800.0),
    ("ImperialSpeed", "float", 300.0),
    ("ImperialPatrolSpeed", "float", 140.0),
    ("CatwalkSafeHeight", "float", 150.0),
    # The player's F: hit or stun
    ("AttackRange", "float", 200.0),
    ("AttackCooldown", "float", 0.4),
    ("StunDuration", "float", 1.0),
    # The Digger
    ("DiggerFollowSpeed", "float", 700.0),
    ("DiggerTravelSpeed", "float", 600.0),
    ("DiggerSnapDistance", "float", 1500.0),
    ("DiggerCardInterval", "float", 2.4),
    ("DiggerStopShort", "float", 190.0),
    ("DiggerMaxMove", "float", 500.0),
    ("DiggerDrillReach", "float", 260.0),
    # Rover and stash crate
    ("RoverRange", "float", 450.0),
    ("CrateRange", "float", 350.0),
    # Boss and ending
    ("BossSweepTime", "float", 4.0),
    ("BossWakeRange", "float", 1100.0),
    ("BossSweepRange", "float", 420.0),
    ("BossStunReach", "float", 230.0),
    ("MemoryCaptionTime", "float", 5.0),
]


def exists(path):
    return str(py(f'''
r = unreal.AssetRegistryHelpers.get_asset_registry()
len(r.get_assets_by_package_name("{path}")) > 0
''')).lower() == "true"


def bp(path):
    return ref(f"{path}.{path.rsplit('/', 1)[1]}")


def cls(path):
    return ref(f"{path}.{path.rsplit('/', 1)[1]}_C")


def add_var(bpath, name, type_name, array=False, editable=False):
    try:
        tool(f"{BPT}.AddVariable", blueprint=bp(bpath), name=name, typeName=type_name,
             options={"containerType": "Array"} if array else {})
    except ToolError as e:
        if "exist" not in str(e).lower():
            print("  var", bpath.rsplit("/", 1)[1], name, "->", str(e)[:160])
    if editable:
        tool(f"{BPT}.SetVariableInstanceEditable", blueprint=bp(bpath), variableName=name, bInstanceEditable=True)


def add_obj_var(bpath, name, class_ref, editable=False, array=False):
    try:
        tool(f"{BPT}.AddObjectVariable", blueprint=bp(bpath), name=name, objectClass=class_ref,
             options={"containerType": "Array"} if array else {})
    except ToolError as e:
        if "exist" not in str(e).lower():
            print("  var", bpath.rsplit("/", 1)[1], name, "->", str(e)[:160])
    if editable:
        tool(f"{BPT}.SetVariableInstanceEditable", blueprint=bp(bpath), variableName=name, bInstanceEditable=True)


# ---------------------------------------------------------------- blueprint classes
NEW_BPS = [(f"{DATA}/BP_Tuning", "PrimaryDataAsset"), (f"{BP}/BP_TimeOfDay", "Actor"),
           (f"{BP}/BP_PhaseTrigger", "Actor"), (f"{BP}/BP_Raider", "Actor"), (f"{BP}/BP_Checkpoint", "Actor"),
           (f"{BP}/BP_Imperial", "Actor"), (f"{BP}/BP_StashCrate", "Actor"), (f"{BP}/BP_BossWall", "Actor"),
           (f"{BP}/BP_Boss", "Actor"), (f"{BP}/BP_BannedCore", "Actor"), (f"{BP}/BP_Spinner", "Actor"),
           (f"{BP}/BP_MemoryCam", "Actor")]
for path, parent in NEW_BPS:
    if exists(path):
        continue
    d, n = path.rsplit("/", 1)
    py(f'''
f = unreal.BlueprintFactory()
f.set_editor_property("parent_class", unreal.{parent})
unreal.AssetToolsHelpers.get_asset_tools().create_asset("{n}", "{d}", unreal.Blueprint, f)
unreal.EditorAssetLibrary.save_asset("{path}")
''')
    print("created", n)

# ---------------------------------------------------------------- variables
for name, t, _ in TUNING:
    add_var(f"{DATA}/BP_Tuning", name, t)
G = f"{BP}/BP_SpliceGame"
ACTOR = ref("/Script/Engine.Actor")
for name, t, arr in [("Heat", "float", False), ("Hearts", "int", False), ("BannedCarried", "int", False),
                     ("BannedSaved", "int", False), ("SavedInventory", "string", True), ("Busy", "bool", False),
                     ("Phase", "int", False), ("Objective", "string", False), ("LastDamage", "float", False),
                     ("NearCrate", "bool", False), ("DeployAtCrate", "bool", False), ("Cells", "int", False),
                     ("Parts", "int", False), ("LastAttack", "float", False), ("MemoryPlaying", "bool", False),
                     ("HitDone", "bool", False)]:
    add_var(G, name, t, arr)
add_var(G, "MemoryCaptions", "string", array=True, editable=True)
print(py(f'''
bp = unreal.load_asset("{DATA}/BP_Tuning")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset("{DATA}/BP_Tuning")
"BP_Tuning compiled"
'''))
add_obj_var(G, "Tuning", cls(f"{DATA}/BP_Tuning"), editable=True)
add_obj_var(G, "RespawnPoint", ACTOR, editable=True)
add_obj_var(G, "BossSite", ACTOR, editable=True)
add_obj_var(G, "MemoryCam", cls(f"{BP}/BP_MemoryCam"), editable=True)
F = f"{BP}/BP_Fragment"
add_var(F, "bIsBanned", "bool", editable=True)
add_var(F, "bIsBattery", "bool", editable=True)
add_var(F, "Taken", "bool")
add_var(F, "Banked", "bool")
add_obj_var(F, "Spots", ACTOR, editable=True, array=True)
for npc in (f"{BP}/BP_Raider", f"{BP}/BP_Imperial"):
    for name, t in [("Home", "Vector"), ("Target", "Vector"), ("Chasing", "bool"), ("LastHit", "float"),
                    ("Provoked", "bool"), ("StunnedUntil", "float"), ("RouteIndex", "int"), ("DancePhase", "float")]:
        add_var(npc, name, t)
    add_var(npc, "HP", "int", editable=True)
    add_var(npc, "bImperial", "bool", editable=True)
    add_var(npc, "DropName", "string", editable=True)
    add_obj_var(npc, "Game", cls(G))
    add_obj_var(npc, "Route", ACTOR, editable=True, array=True)
BOT = f"{BP}/BP_Bot"
add_var(BOT, "Mode", "int")
add_var(BOT, "GoalWall", "bool")
add_obj_var(BOT, "Site", ACTOR)
add_obj_var(BOT, "Obstacle", ACTOR)
BOSS = f"{BP}/BP_Boss"
for name, t in [("Active", "bool"), ("Dead", "bool"), ("Raised", "bool"), ("Stun1", "bool"), ("Stun2", "bool"),
                ("Stun3", "bool"), ("NextSweep", "float"), ("SpinUntil", "float")]:
    add_var(BOSS, name, t)
add_obj_var(BOSS, "Game", cls(G))
add_var(f"{BP}/BP_StashCrate", "WasNear", "bool")
SP = f"{BP}/BP_Spinner"
add_var(SP, "Home", "Vector")
for name in ("Rate", "RollRate", "Bob"):
    add_var(SP, name, "float", editable=True)
add_var(f"{BP}/BP_MemoryCam", "Active", "bool")
add_var(f"{BP}/BP_MemoryCam", "Speed", "float", editable=True)
P = f"{BP}/BP_PhaseTrigger"
add_var(P, "PhaseIndex", "int", editable=True)
add_var(P, "Objective", "string", editable=True)
add_var(P, "Used", "bool")
T = f"{BP}/BP_TimeOfDay"
for phase in ("Dawn", "Day", "Dusk", "Night"):
    add_var(T, phase + "Tint", "LinearColor", editable=True)
    add_var(T, phase + "Fog", "LinearColor", editable=True)
print("variables done")

# ---------------------------------------------------------------- components + defaults + data asset
# (blueprint, name, basic shape, material, relative location, relative scale, collision, hidden in game)
PLAYER_BP = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter"
COMPONENTS = [
    ("BP_Raider", "Body", "Cylinder", "M_Dark", (0, 0, 0), (0.7, 0.7, 1.5), "NoCollision", False),
    ("BP_Raider", "Head", "Sphere", "M_Dark", (0, 0, 95), (0.6, 0.6, 0.6), "NoCollision", False),
    ("BP_Raider", "Eye", "Cube", "M_Red", (0, 0, 98), (0.66, 0.66, 0.08), "NoCollision", False),
    ("BP_Imperial", "Body", "Cube", "M_White", (0, 0, 0), (0.7, 0.7, 1.7), "NoCollision", False),
    ("BP_Imperial", "Head", "Cube", "M_Dark", (0, 0, 102), (0.8, 0.8, 0.32), "NoCollision", False),
    ("BP_Imperial", "Eye", "Cube", "M_Red", (38, 0, 102), (0.1, 0.62, 0.12), "NoCollision", False),
    ("BP_Checkpoint", "Post", "Cylinder", "M_Pad", (0, 0, 0), (0.14, 0.14, 2.0), "NoCollision", False),
    ("BP_Checkpoint", "Cap", "Sphere", "M_Pad", (0, 0, 115), (0.36, 0.36, 0.36), "NoCollision", False),
    ("BP_PhaseTrigger", "Box", "Cube", "M_Pad", (0, 0, 0), (1, 1, 1), "OverlapAllDynamic", True),
    ("BP_StashCrate", "Box", "Cube", "M_Gray", (0, 0, 0), (1.2, 0.8, 0.8), "BlockAll", False),
    ("BP_StashCrate", "Lid", "Cube", "M_Pad", (0, 0, 43), (1.24, 0.84, 0.06), "NoCollision", False),
    ("BP_BossWall", "Wall", "Cube", "M_Dark", (0, 0, 0), (1, 1, 1), "BlockAll", False),
    ("BP_Boss", "Body", "Cube", "M_Dark", (0, 0, 0), (3, 3, 4), "NoCollision", False),
    ("BP_Boss", "Band", "Cube", "M_Pad", (0, 0, 60), (3.06, 3.06, 0.3), "NoCollision", False),
    ("BP_Boss", "Head", "Cube", "M_Dark", (0, 0, 240), (1.6, 1.6, 0.8), "NoCollision", False),
    ("BP_Boss", "Eye", "Cube", "M_Pad", (-82, 0, 240), (0.06, 1.2, 0.25), "NoCollision", False),
    ("BP_Boss", "Arm", "Cube", "M_Dark", (0, 0, -60), (8, 0.5, 0.5), "NoCollision", False),
    ("BP_Boss", "WP1", "Sphere", "M_Pad", (-200, 0, -100), (0.7, 0.7, 0.7), "NoCollision", False),
    ("BP_Boss", "WP2", "Sphere", "M_Pad", (0, -200, -100), (0.7, 0.7, 0.7), "NoCollision", False),
    ("BP_Boss", "WP3", "Sphere", "M_Pad", (0, 200, -100), (0.7, 0.7, 0.7), "NoCollision", False),
    ("BP_BannedCore", "Mesh", "Sphere", "M_Pad", (0, 0, 0), (0.7, 0.7, 0.7), "OverlapAllDynamic", False),
    ("BP_Spinner", "Mesh", "Cube", "M_Pad", (0, 0, 0), (1, 1, 1), "NoCollision", False),
    ("BP_MemoryCam", "Camera", "CAMERA", None, (0, 0, 0), (1, 1, 1), None, False),
    # The player: a cylinder with a head, an orange visor (so you can see which way it
    # faces) and a pack. The template mannequin is hidden.
    (PLAYER_BP, "CylBody", "Cylinder", "M_White", (0, 0, -22), (0.7, 0.7, 1.48), "NoCollision", False),
    (PLAYER_BP, "CylHead", "Sphere", "M_White", (0, 0, 74), (0.62, 0.62, 0.62), "NoCollision", False),
    (PLAYER_BP, "CylVisor", "Cube", "M_Orange", (22, 0, 78), (0.3, 0.5, 0.14), "NoCollision", False),
    (PLAYER_BP, "CylPack", "Cube", "M_Dark", (-34, 0, 0), (0.25, 0.5, 0.6), "NoCollision", False),
]
# Time-of-day presets: tint multiplies the picture; fog alpha is its strength.
PRESETS = {
    "DawnTint": (1.00, 0.86, 0.88, 1.0), "DawnFog": (0.85, 0.50, 0.52, 0.22),
    "DayTint": (1.00, 1.00, 1.00, 1.0), "DayFog": (1.00, 1.00, 1.00, 0.0),
    "DuskTint": (1.00, 0.78, 0.62, 1.0), "DuskFog": (0.75, 0.33, 0.14, 0.28),
    "NightTint": (0.46, 0.44, 0.70, 1.0), "NightFog": (0.035, 0.025, 0.07, 0.50),
}
print(py("PLAYER_BP = " + repr(PLAYER_BP) + "\nCOMPONENTS = " + repr(COMPONENTS) + "\nPRESETS = " + repr(PRESETS) + "\nTUNING = " + repr(TUNING) + r'''
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
out = []
def bp_path(bpn):
    return bpn if bpn.startswith("/") else "/Game/Splice/Blueprints/" + bpn

for bpn, cname, shape, mat, loc, scale, prof, hidden in COMPONENTS:
    bp = unreal.load_asset(bp_path(bpn))
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    names = {}
    for h in handles:
        o = lib.get_object(lib.get_data(h))
        if o:
            names[o.get_name().replace("_GEN_VARIABLE", "")] = o
    if cname in names:
        comp = names[cname]
    else:
        ccls = unreal.CameraComponent if shape == "CAMERA" else unreal.StaticMeshComponent
        params = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=ccls, blueprint_context=bp)
        h, fail = sds.add_new_subobject(params)
        sds.rename_subobject(h, cname)
        comp = lib.get_object(lib.get_data(h))
    comp.set_editor_property("relative_location", unreal.Vector(*loc))
    if shape != "CAMERA":
        comp.set_editor_property("static_mesh", unreal.load_asset("/Engine/BasicShapes/" + shape))
        comp.set_editor_property("override_materials", [unreal.load_asset("/Game/Splice/Materials/" + mat)])
        comp.set_editor_property("relative_scale3d", unreal.Vector(*scale))
        comp.set_collision_profile_name(prof)
        comp.set_editor_property("generate_overlap_events", prof.startswith("Overlap"))
        comp.set_editor_property("hidden_in_game", hidden)
        comp.set_editor_property("cast_shadow", False)
    out.append(f"{bpn.rsplit('/', 1)[-1]}.{cname}")

# Hide the template mannequin on the player character.
pbp = unreal.load_asset(PLAYER_BP)
for h in sds.k2_gather_subobject_data_for_blueprint(pbp):
    o = lib.get_object(lib.get_data(h))
    if o and isinstance(o, unreal.SkeletalMeshComponent):
        o.set_editor_property("visible", False)
        o.set_editor_property("hidden_in_game", True)
        out.append("player mannequin hidden: " + o.get_name())
unreal.BlueprintEditorLibrary.compile_blueprint(pbp)
unreal.EditorAssetLibrary.save_asset(PLAYER_BP)

for bpn in ["BP_Raider", "BP_Imperial", "BP_Checkpoint", "BP_PhaseTrigger", "BP_TimeOfDay", "BP_Fragment", "BP_Bot", "BP_StashCrate", "BP_BossWall", "BP_Boss", "BP_BannedCore", "BP_Spinner", "BP_MemoryCam", "BP_SpliceGame"]:
    bp = unreal.load_asset("/Game/Splice/Blueprints/" + bpn)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    if bpn == "BP_TimeOfDay":
        cdo = unreal.get_default_object(bp.generated_class())
        for k, v in PRESETS.items():
            cdo.set_editor_property(k, unreal.LinearColor(*v))
    unreal.EditorAssetLibrary.save_asset("/Game/Splice/Blueprints/" + bpn)

# DA_Tuning: one instance of BP_Tuning that holds the numbers.
reg = unreal.AssetRegistryHelpers.get_asset_registry()
tcls = unreal.load_asset("/Game/Splice/Data/BP_Tuning").generated_class()
if reg.get_assets_by_package_name("/Game/Splice/Data/DA_Tuning"):
    da = unreal.load_asset("/Game/Splice/Data/DA_Tuning")
else:
    f = unreal.DataAssetFactory()
    f.set_editor_property("data_asset_class", tcls)
    da = unreal.AssetToolsHelpers.get_asset_tools().create_asset("DA_Tuning", "/Game/Splice/Data", None, f)
for name, t, value in TUNING:
    da.set_editor_property(name, value)
unreal.EditorAssetLibrary.save_asset("/Game/Splice/Data/DA_Tuning")
out.append(f"DA_Tuning: {len(TUNING)} numbers set")
"\n".join(out)
'''))

# ---------------------------------------------------------------- widgets
# (name, class, parent, is_variable). Existing widgets are skipped.
HUD_ADD = [
    ("HeartsPanel", "Border", "Root", False),
    ("HeartsCol", "VerticalBox", "HeartsPanel", False),
    ("HeartsLabel", "TextBlock", "HeartsCol", False),
    ("HeartsRow", "HorizontalBox", "HeartsCol", False),
    ("Heart1", "Border", "HeartsRow", True), ("Heart1Size", "SizeBox", "Heart1", False),
    ("Heart2", "Border", "HeartsRow", True), ("Heart2Size", "SizeBox", "Heart2", False),
    ("Heart3", "Border", "HeartsRow", True), ("Heart3Size", "SizeBox", "Heart3", False),
    ("PhaseBar", "Border", "Root", False),
    ("PhaseRow", "HorizontalBox", "PhaseBar", False),
    ("Phase0", "Border", "PhaseRow", True), ("Phase0Label", "TextBlock", "Phase0", False),
    ("Phase1", "Border", "PhaseRow", True), ("Phase1Label", "TextBlock", "Phase1", False),
    ("Phase2", "Border", "PhaseRow", True), ("Phase2Label", "TextBlock", "Phase2", False),
    ("Phase3", "Border", "PhaseRow", True), ("Phase3Label", "TextBlock", "Phase3", False),
    ("HeatPanel", "Border", "Root", False),
    ("HeatCol", "VerticalBox", "HeatPanel", False),
    ("HeatText", "TextBlock", "HeatCol", True),
    ("HeatBar", "ProgressBar", "HeatCol", True),
    ("HeatBands", "TextBlock", "HeatCol", False),
    ("HeatNote", "TextBlock", "HeatCol", False),
    ("ObjectivePanel", "Border", "Root", False),
    ("ObjectiveCol", "VerticalBox", "ObjectivePanel", False),
    ("ObjectiveLabel", "TextBlock", "ObjectiveCol", False),
    ("ObjectiveText", "TextBlock", "ObjectiveCol", True),
    ("HelpText", "TextBlock", "Root", False),
]
BAY_ADD = [
    ("BtnDrillPlus", "Button", "ItemsRow", True),
    ("BtnSpliceCore", "Button", "ActionsRow", True),
]
MEMORY = [
    ("Root", "CanvasPanel", None, False),
    ("BtnSkip", "Button", "Root", True),
    ("CaptionPanel", "Border", "Root", False),
    ("Caption", "TextBlock", "CaptionPanel", True),
    ("SkipHint", "TextBlock", "Root", False),
]
BANNER = [
    ("Root", "CanvasPanel", None, False),
    ("Backdrop", "Border", "Root", False),
    ("Rows", "VerticalBox", "Backdrop", False),
    ("Tag", "TextBlock", "Rows", False),
    ("Title", "TextBlock", "Rows", False),
    ("Sub", "TextBlock", "Rows", False),
]


def build_tree(wname, tree):
    path = f"{UI}/{wname}"
    if not exists(path):
        py(f'''
f = unreal.WidgetBlueprintFactory()
f.set_editor_property("parent_class", unreal.UserWidget)
unreal.AssetToolsHelpers.get_asset_tools().create_asset("{wname}", "{UI}", unreal.WidgetBlueprint, f)
unreal.EditorAssetLibrary.save_asset("{path}")
''')
    wbp = ref(f"{path}.{wname}")
    have = set(str(py(f'''
bp = unreal.load_asset("{path}")
",".join(w.get_name() for w in unreal.find_object(None, "{path}.{wname}:WidgetTree").get_editor_property("all_widgets")) if False else ""
''')).split(","))
    made = 0
    for name, wcls, parent, is_var in tree:
        found = str(py(f'unreal.find_object(None, "{path}.{wname}:WidgetTree.{name}") is not None')).lower() == "true"
        if found:
            continue
        parent_ref = ref(f"{path}.{wname}:WidgetTree.{parent}") if parent else None
        r = tool(f"{WBT}.CreateAndAddWidget", widgetBlueprint=wbp, widgetClass=ref(f"/Script/UMG.{wcls}"),
                 widgetDisplayName=name, parentWidget=parent_ref)["returnValue"]
        w = r["Widget"] if "Widget" in r else r.get("widget")
        tool(f"{WBT}.ToggleWidgetAsVariable", widgetBlueprint=wbp, widget=w, bIsVariable=is_var)
        if wcls == "Button" and name != "BtnSkip":
            tool(f"{WBT}.CreateAndAddWidget", widgetBlueprint=wbp, widgetClass=ref("/Script/UMG.TextBlock"),
                 widgetDisplayName=name + "Label", parentWidget=w)
        made += 1
    print(f"{wname}: {made} widgets added")


build_tree("WBP_HUD", HUD_ADD)
build_tree("WBP_Sweep", BANNER)
build_tree("WBP_TakeTwo", BANNER)
build_tree("WBP_EditBay", BAY_ADD)
build_tree("WBP_Memory", MEMORY)
print(py('''
out = []
for w in ("WBP_HUD", "WBP_Sweep", "WBP_TakeTwo", "WBP_EditBay", "WBP_Memory"):
    bp = unreal.load_asset("/Game/Splice/UI/" + w)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset("/Game/Splice/UI/" + w)
    out.append(w)
"compiled " + ", ".join(out)
'''))
# The game keeps a reference to the memory overlay; the widget class has to exist first.
add_obj_var(G, "MemoryWidget", cls(f"{UI}/WBP_Memory"))
print(py(f'''
bp = unreal.load_asset("{G}")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset("{G}")
"BP_SpliceGame compiled"
'''))
