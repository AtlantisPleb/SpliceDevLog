"""Splice gray box, steps 2-7, phase 1: assets.

Creates the Blueprint classes (with their components and variables), the
materials, and the three UI widget trees. Graph logic is phase 2
(splice_build_logic.py). Run from a shell with the editor open:

    python3 tools/ue/splice_build_assets.py
"""
import json
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from uemcp import ToolError, py, ref, tool  # noqa: E402

BP = "/Game/Splice/Blueprints"
UI = "/Game/Splice/UI"
BPT = "BlueprintToolsets.BlueprintToolset"
WBT = "UMGEditor.WidgetBlueprintEditorSubsystem"


def exists(path):
    pkg, name = path, path.rsplit("/", 1)[1]
    return str(py(f'''
r = unreal.AssetRegistryHelpers.get_asset_registry()
len(r.get_assets_by_package_name("{pkg}")) > 0
''')).lower() == "true"


def cls(path):
    name = path.rsplit("/", 1)[1]
    return f"{path}.{name}_C"


# ---------------------------------------------------------------- materials
print(py(r'''
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
def material(name, rgb, glow=0.12):
    path = "/Game/Splice/Materials/" + name
    if unreal.load_asset(path) is not None:
        return
    m = tools.create_asset(name, "/Game/Splice/Materials", unreal.Material, unreal.MaterialFactoryNew())
    c = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, 0)
    c.constant = unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0)
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    g = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -200, 200)
    mel.connect_material_expressions(c, "", g, "A")
    g.set_editor_property("const_b", glow)
    mel.connect_material_property(g, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 300)
    r.set_editor_property("r", 0.85)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(path)
material("M_Orange", (0.95, 0.42, 0.08))
material("M_Blue", (0.10, 0.35, 0.90))
material("M_Green", (0.15, 0.75, 0.25))
material("M_White", (0.92, 0.92, 0.90))
material("M_Gray", (0.45, 0.46, 0.48))
material("M_Dark", (0.08, 0.08, 0.09))
material("M_Red", (0.95, 0.08, 0.06), glow=0.6)
material("M_Pad", (0.20, 0.90, 0.55), glow=0.5)
"materials ok"
'''))

# ---------------------------------------------------------------- blueprints
for name in ["BP_SpliceGame", "BP_Rover", "BP_Fragment", "BP_Bot", "BP_Rubble", "BP_EndTrigger"]:
    path = f"{BP}/{name}"
    if exists(path):
        continue
    py(f'''
f = unreal.BlueprintFactory()
f.set_editor_property("parent_class", unreal.Actor)
bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset("{name}", "{BP}", unreal.Blueprint, f)
unreal.EditorAssetLibrary.save_asset("{path}")
''')
    print("created", name)

# Components: (blueprint, name, class, parent or None for root child, mesh, material,
#              relative location, relative scale, collision profile)
COMPONENTS = [
    ("BP_Rover", "Body", "StaticMeshComponent", None, "Cube", "M_Gray", (0, 0, 100), (4, 2, 2), "BlockAll"),
    ("BP_Rover", "Bay", "StaticMeshComponent", None, "Cube", "M_Dark", (0, 101, 110), (2.4, 0.04, 1.1), "NoCollision"),
    ("BP_Fragment", "Mesh", "StaticMeshComponent", None, "Cube", "M_Orange", (0, 0, 0), (0.5, 0.5, 0.5), "OverlapAllDynamic"),
    ("BP_Bot", "Body", "StaticMeshComponent", None, "Cube", "M_Orange", (0, 0, 0), (1, 1, 1), "NoCollision"),
    ("BP_Bot", "Front", "StaticMeshComponent", None, "Cube", "M_Dark", (48, 0, 5), (0.08, 0.8, 0.5), "NoCollision"),
    ("BP_Rubble", "Mesh", "StaticMeshComponent", None, "Cube", None, (0, 0, 0), (1, 1, 1), "BlockAll"),
    ("BP_EndTrigger", "Pad", "StaticMeshComponent", None, "Cube", "M_Pad", (0, 0, 5), (3, 3, 0.1), "OverlapAllDynamic"),
]
print(py("COMPONENTS = " + repr(COMPONENTS) + r'''
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
out = []
for bpn, cname, ccls, parent, mesh, mat, loc, scale, prof in COMPONENTS:
    bp = unreal.load_asset("/Game/Splice/Blueprints/" + bpn)
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    names = {}
    for h in handles:
        o = lib.get_object(lib.get_data(h))
        if o:
            names[o.get_name().replace("_GEN_VARIABLE", "")] = (h, o)
    if cname in names:
        comp = names[cname][1]
    else:
        root = handles[0]
        params = unreal.AddNewSubobjectParams(parent_handle=root, new_class=getattr(unreal, ccls), blueprint_context=bp)
        h, fail = sds.add_new_subobject(params)
        sds.rename_subobject(h, cname)
        comp = lib.get_object(lib.get_data(h))
    if mesh:
        comp.set_editor_property("static_mesh", unreal.load_asset("/Engine/BasicShapes/" + mesh))
    if mat:
        comp.set_editor_property("override_materials", [unreal.load_asset("/Game/Splice/Materials/" + mat)])
    comp.set_editor_property("relative_location", unreal.Vector(*loc))
    comp.set_editor_property("relative_scale3d", unreal.Vector(*scale))
    comp.set_collision_profile_name(prof)
    comp.set_editor_property("generate_overlap_events", prof.startswith("Overlap"))
    out.append(f"{bpn}.{cname}")
for bpn in set(c[0] for c in COMPONENTS):
    bp = unreal.load_asset("/Game/Splice/Blueprints/" + bpn)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset("/Game/Splice/Blueprints/" + bpn)
", ".join(out)
'''))

# ---------------------------------------------------------------- widgets
# Widget trees: (name, class, parent name or None, is_variable)
WIDGETS = {
    "WBP_HUD": [
        ("Root", "CanvasPanel", None, False),
        ("CarryText", "TextBlock", "Root", True),
        ("PromptText", "TextBlock", "Root", True),
        ("MessageText", "TextBlock", "Root", True),
    ],
    "WBP_EditBay": [
        ("Root", "CanvasPanel", None, False),
        ("Panel", "Border", "Root", False),
        ("Rows", "VerticalBox", "Panel", False),
        ("Title", "TextBlock", "Rows", False),
        ("ItemsLabel", "TextBlock", "Rows", False),
        ("ItemsRow", "HorizontalBox", "Rows", False),
        ("BtnArm", "Button", "ItemsRow", True),
        ("BtnTreads", "Button", "ItemsRow", True),
        ("BtnBattery", "Button", "ItemsRow", True),
        ("BtnMove", "Button", "ItemsRow", True),
        ("BtnDrill", "Button", "ItemsRow", True),
        ("SlotsText", "TextBlock", "Rows", True),
        ("StripText", "TextBlock", "Rows", True),
        ("ActionsRow", "HorizontalBox", "Rows", False),
        ("BtnClear", "Button", "ActionsRow", True),
        ("BtnDeploy", "Button", "ActionsRow", True),
        ("BtnClose", "Button", "ActionsRow", True),
        ("StatusText", "TextBlock", "Rows", True),
    ],
    "WBP_End": [
        ("Root", "CanvasPanel", None, False),
        ("Backdrop", "Border", "Root", False),
        ("Rows", "VerticalBox", "Backdrop", False),
        ("EndTitle", "TextBlock", "Rows", False),
        ("EndSub", "TextBlock", "Rows", False),
        ("BtnRestart", "Button", "Rows", True),
    ],
}
BUTTON_LABELS = {"BtnArm": "Drill Arm", "BtnTreads": "Treads", "BtnBattery": "Battery",
                 "BtnMove": "MOVE card", "BtnDrill": "DRILL card", "BtnClear": "Clear Strip",
                 "BtnDeploy": "DEPLOY", "BtnClose": "Close (E)", "BtnRestart": "Restart"}

for wname, tree in WIDGETS.items():
    path = f"{UI}/{wname}"
    if exists(path):
        continue
    py(f'''
f = unreal.WidgetBlueprintFactory()
f.set_editor_property("parent_class", unreal.UserWidget)
unreal.AssetToolsHelpers.get_asset_tools().create_asset("{wname}", "{UI}", unreal.WidgetBlueprint, f)
unreal.EditorAssetLibrary.save_asset("{path}")
''')
    wbp = ref(f"{path}.{wname}")
    made = {}
    for name, wcls, parent, is_var in tree:
        r = tool(f"{WBT}.CreateAndAddWidget", widgetBlueprint=wbp, widgetClass=ref(f"/Script/UMG.{wcls}"),
                 widgetDisplayName=name, parentWidget=made[parent] if parent else None)["returnValue"]
        made[name] = r["Widget"] if "Widget" in r else r.get("widget")
        tool(f"{WBT}.ToggleWidgetAsVariable", widgetBlueprint=wbp, widget=made[name], bIsVariable=is_var)
        if wcls == "Button":
            t = tool(f"{WBT}.CreateAndAddWidget", widgetBlueprint=wbp, widgetClass=ref("/Script/UMG.TextBlock"),
                     widgetDisplayName=name + "Label", parentWidget=made[name])["returnValue"]
            made[name + "Label"] = t["Widget"] if "Widget" in t else t.get("widget")
    print(wname, "tree:", list(made))

print("widgets created")
