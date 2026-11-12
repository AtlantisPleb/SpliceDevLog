"""Splice phase 1b: lay out and style the three UI widgets (runs inside the editor)."""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from uemcp import py  # noqa: E402

print(py(r'''
def W(wbp, name):
    return unreal.find_object(None, f"/Game/Splice/UI/{wbp}.{wbp}:WidgetTree.{name}")

def text(wbp, name, s, size=20, color=(1, 1, 1, 1), justify=None):
    t = W(wbp, name)
    t.set_editor_property("text", s)
    f = t.get_editor_property("font")
    f.set_editor_property("size", size)
    t.set_editor_property("font", f)
    t.set_editor_property("color_and_opacity", unreal.SlateColor(unreal.LinearColor(*color)))
    if justify:
        t.set_editor_property("justification", justify)
    return t

def canvas(wbp, name, anchors, pos, size, align, auto=False):
    s = W(wbp, name).get_editor_property("slot")
    s.set_anchors(unreal.Anchors(minimum=unreal.Vector2D(*anchors[:2]), maximum=unreal.Vector2D(*anchors[2:])))
    s.set_position(unreal.Vector2D(*pos))
    s.set_size(unreal.Vector2D(*size))
    s.set_alignment(unreal.Vector2D(*align))
    s.set_auto_size(auto)

def pad(wbp, name, l, t, r, b, fill=False):
    s = W(wbp, name).get_editor_property("slot")
    s.set_padding(unreal.Margin(l, t, r, b))
    if fill and hasattr(s, "set_size"):
        s.set_size(unreal.SlateChildSize(1.0, unreal.SlateSizeRule.FILL))

C = unreal.TextJustify.CENTER
# ---- HUD
text("WBP_HUD", "CarryText", "Carrying: nothing", 22, (1, 0.95, 0.8, 1))
canvas("WBP_HUD", "CarryText", (0, 0, 0, 0), (40, 30), (0, 0), (0, 0), auto=True)
text("WBP_HUD", "PromptText", "", 30, (1, 0.85, 0.3, 1), C)
canvas("WBP_HUD", "PromptText", (0.5, 1, 0.5, 1), (0, -120), (0, 0), (0.5, 0.5), auto=True)
text("WBP_HUD", "MessageText", "", 40, (1, 0.35, 0.25, 1), C)
canvas("WBP_HUD", "MessageText", (0.5, 0.3, 0.5, 0.3), (0, 0), (0, 0), (0.5, 0.5), auto=True)

# ---- Edit Bay
canvas("WBP_EditBay", "Panel", (0.5, 0.5, 0.5, 0.5), (0, 0), (1100, 560), (0.5, 0.5))
p = W("WBP_EditBay", "Panel")
p.set_editor_property("brush_color", unreal.LinearColor(0.05, 0.05, 0.07, 0.92))
p.set_editor_property("padding", unreal.Margin(36, 28, 36, 28))
text("WBP_EditBay", "Title", "EDIT BAY - splice the Digger", 34, (1, 0.85, 0.3, 1))
text("WBP_EditBay", "ItemsLabel", "Your parts (click to place):", 20, (0.8, 0.8, 0.8, 1))
pad("WBP_EditBay", "ItemsLabel", 0, 18, 0, 6)
for b, label in [("BtnArm", "Drill Arm"), ("BtnTreads", "Treads"), ("BtnBattery", "Battery"),
                 ("BtnMove", "MOVE card"), ("BtnDrill", "DRILL card")]:
    text("WBP_EditBay", b + "Label", label, 20, (0.05, 0.05, 0.05, 1), C)
    pad("WBP_EditBay", b, 0, 0, 12, 0)
text("WBP_EditBay", "SlotsText", "ARM: -    TREADS: -    BATTERY: -", 24)
pad("WBP_EditBay", "SlotsText", 0, 26, 0, 0)
text("WBP_EditBay", "StripText", "FILM STRIP:  [ SLOT 1: - ]  [ SLOT 2: - ]", 24, (0.6, 0.9, 1.0, 1))
pad("WBP_EditBay", "StripText", 0, 14, 0, 0)
for b, label in [("BtnClear", "Clear Strip"), ("BtnDeploy", "DEPLOY"), ("BtnClose", "Close (E)")]:
    text("WBP_EditBay", b + "Label", label, 22, (0.05, 0.05, 0.05, 1), C)
    pad("WBP_EditBay", b, 0, 0, 16, 0)
pad("WBP_EditBay", "ActionsRow", 0, 30, 0, 0)
text("WBP_EditBay", "StatusText", "", 20, (1, 0.6, 0.4, 1))
pad("WBP_EditBay", "StatusText", 0, 16, 0, 0)

# ---- End screen
canvas("WBP_End", "Backdrop", (0, 0, 1, 1), (0, 0), (0, 0), (0, 0))
e = W("WBP_End", "Backdrop")
e.set_editor_property("brush_color", unreal.LinearColor(0.02, 0.02, 0.03, 0.95))
e.set_editor_property("horizontal_alignment", unreal.HorizontalAlignment.H_ALIGN_CENTER)
e.set_editor_property("vertical_alignment", unreal.VerticalAlignment.V_ALIGN_CENTER)
text("WBP_End", "EndTitle", "SCENE RESTORED", 72, (1, 0.85, 0.3, 1), C)
text("WBP_End", "EndSub", "The Digger cut through. The director's cut lives on.", 24, (0.85, 0.85, 0.85, 1), C)
pad("WBP_End", "EndSub", 0, 12, 0, 40)
text("WBP_End", "BtnRestartLabel", "Restart", 28, (0.05, 0.05, 0.05, 1), C)

out = []
for w in ("WBP_HUD", "WBP_EditBay", "WBP_End"):
    bp = unreal.load_asset(f"/Game/Splice/UI/{w}")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(f"/Game/Splice/UI/{w}")
    out.append(w)
"styled " + ", ".join(out)
'''))
