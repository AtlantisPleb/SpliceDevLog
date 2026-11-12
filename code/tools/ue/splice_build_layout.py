"""Splice UI style pass: lay out and style the three widgets to Kiki's Game UI board.

Paper panels with ink borders, Michroma for titles and buttons, IBM Plex Mono for
labels. Orange means danger; blue is reserved for banned tech. Runs inside the editor.
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from uemcp import py  # noqa: E402

print(py(r'''
def lin(h, a=1.0):
    v = []
    for i in (1, 3, 5):
        c = int(h[i:i + 2], 16) / 255.0
        v.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return unreal.LinearColor(v[0], v[1], v[2], a)

PAPER, SHADE, INK, HEAT, HEAT_HI = "#EADBC4", "#DCC9AC", "#1E1B18", "#B8431F", "#E0683F"
F = "/Game/Splice/UI/Fonts/"
# Font assets (F_*) wrap the imported faces; see splice_build_fonts.py.
MICHROMA = (unreal.load_asset(F + "F_Michroma"), "Regular")
MONO = (unreal.load_asset(F + "F_PlexMono"), "Regular")
MONO_B = (unreal.load_asset(F + "F_PlexMono"), "Bold")

def W(wbp, name):
    return unreal.find_object(None, f"/Game/Splice/UI/{wbp}.{wbp}:WidgetTree.{name}")

def text(wbp, name, s, size, color, face=None, justify=None, spacing=0, outline=None):
    t = W(wbp, name)
    if s is not None:
        t.set_editor_property("text", s)
    f = t.get_editor_property("font")
    font, typeface = face or MONO
    f.set_editor_property("font_object", font)
    f.set_editor_property("typeface_font_name", typeface)
    f.set_editor_property("size", size)
    f.set_editor_property("letter_spacing", spacing)
    o = f.get_editor_property("outline_settings")
    o.set_editor_property("outline_size", 3 if outline else 0)
    if outline:
        o.set_editor_property("outline_color", lin(outline))
    f.set_editor_property("outline_settings", o)
    t.set_editor_property("font", f)
    t.set_editor_property("color_and_opacity", unreal.SlateColor(lin(color)))
    if justify:
        t.set_editor_property("justification", justify)
    return t

def box_brush(fill, border=None, width=3.0, radius=10.0, alpha=1.0):
    b = unreal.SlateBrush()
    b.set_editor_property("draw_as", unreal.SlateBrushDrawType.ROUNDED_BOX)
    b.set_editor_property("tint_color", unreal.SlateColor(lin(fill, alpha)))
    o = unreal.SlateBrushOutlineSettings()
    o.set_editor_property("corner_radii", unreal.Vector4(radius, radius, radius, radius))
    o.set_editor_property("rounding_type", unreal.SlateBrushRoundingType.FIXED_RADIUS)
    o.set_editor_property("color", unreal.SlateColor(lin(border or fill, 1.0 if border else alpha)))
    o.set_editor_property("width", width if border else 0.0)
    b.set_editor_property("outline_settings", o)
    return b

def panel(wbp, name, fill, border=None, padding=(18, 12, 18, 12), alpha=1.0, radius=10.0):
    p = W(wbp, name)
    p.set_editor_property("background", box_brush(fill, border, 3.0, radius, alpha))
    p.set_editor_property("brush_color", unreal.LinearColor(1, 1, 1, 1))
    p.set_editor_property("padding", unreal.Margin(*padding))
    return p

def button(wbp, name, label, primary, size=13):
    b = W(wbp, name)
    st = b.get_editor_property("widget_style")
    if primary:
        st.set_editor_property("normal", box_brush(INK, INK, 3.0, 8.0))
        st.set_editor_property("hovered", box_brush("#3A332C", INK, 3.0, 8.0))
        st.set_editor_property("pressed", box_brush(HEAT, INK, 3.0, 8.0))
        st.set_editor_property("disabled", box_brush("#9C8F7C", "#9C8F7C", 3.0, 8.0))
    else:
        st.set_editor_property("normal", box_brush(PAPER, INK, 3.0, 8.0))
        st.set_editor_property("hovered", box_brush("#F6ECDB", INK, 3.0, 8.0))
        st.set_editor_property("pressed", box_brush(SHADE, INK, 3.0, 8.0))
        st.set_editor_property("disabled", box_brush(SHADE, "#9C8F7C", 3.0, 8.0))
    st.set_editor_property("normal_padding", unreal.Margin(20, 12, 20, 12))
    st.set_editor_property("pressed_padding", unreal.Margin(20, 13, 20, 11))
    b.set_editor_property("widget_style", st)
    b.set_editor_property("color_and_opacity", unreal.LinearColor(1, 1, 1, 1))
    b.set_editor_property("background_color", unreal.LinearColor(1, 1, 1, 1))
    text(wbp, name + "Label", label, size, PAPER if primary else INK, MICHROMA, C, 200)

def canvas(wbp, name, anchors, pos, size, align, auto=False):
    s = W(wbp, name).get_editor_property("slot")
    s.set_anchors(unreal.Anchors(minimum=unreal.Vector2D(*anchors[:2]), maximum=unreal.Vector2D(*anchors[2:])))
    s.set_position(unreal.Vector2D(*pos))
    s.set_size(unreal.Vector2D(*size))
    s.set_alignment(unreal.Vector2D(*align))
    s.set_auto_size(auto)

def pad(wbp, name, l, t, r, b):
    W(wbp, name).get_editor_property("slot").set_padding(unreal.Margin(l, t, r, b))

C = unreal.TextJustify.CENTER

# ---- HUD: lettering sits straight on the 3D view, so it is paper with an ink outline.
text("WBP_HUD", "CarryText", "Carrying: nothing", 15, PAPER, MONO_B, None, 40, INK)
canvas("WBP_HUD", "CarryText", (0, 0, 0, 0), (28, 24), (0, 0), (0, 0), auto=True)
text("WBP_HUD", "PromptText", "", 19, PAPER, MONO_B, C, 40, INK)
canvas("WBP_HUD", "PromptText", (0.5, 1, 0.5, 1), (0, -72), (0, 0), (0.5, 0.5), auto=True)
text("WBP_HUD", "MessageText", "", 22, PAPER, MONO_B, C, 40, INK)
canvas("WBP_HUD", "MessageText", (0.5, 0.26, 0.5, 0.26), (0, 0), (0, 0), (0.5, 0.5), auto=True)

# ---- Edit bay: a paper desk with an ink frame.
canvas("WBP_EditBay", "Panel", (0.5, 0.5, 0.5, 0.5), (0, 0), (1120, 560), (0.5, 0.5))
panel("WBP_EditBay", "Panel", PAPER, INK, (40, 30, 40, 30), radius=14.0)
text("WBP_EditBay", "Title", "EDIT BAY  ·  DIGGER", 24, INK, MICHROMA, None, 300)
text("WBP_EditBay", "ItemsLabel", "PARTS AND CARDS  ·  click to place", 13, INK, MONO, None, 100)
pad("WBP_EditBay", "ItemsLabel", 0, 22, 0, 10)
for b, label in [("BtnArm", "DRILL ARM"), ("BtnTreads", "TREADS"), ("BtnBattery", "BATTERY"),
                 ("BtnMove", "MOVE"), ("BtnDrill", "DRILL")]:
    button("WBP_EditBay", b, label, False, 12)
    pad("WBP_EditBay", b, 0, 0, 12, 0)
text("WBP_EditBay", "SlotsText", "ARM: -    TREADS: -    BATTERY: -", 17, INK, MONO_B)
pad("WBP_EditBay", "SlotsText", 0, 30, 0, 0)
text("WBP_EditBay", "StripText", "FILM STRIP:  (empty)", 17, INK, MONO_B).set_editor_property("auto_wrap_text", True)
pad("WBP_EditBay", "StripText", 0, 14, 0, 0)
button("WBP_EditBay", "BtnClear", "CLEAR STRIP", False)
button("WBP_EditBay", "BtnDeploy", "DEPLOY", True)
button("WBP_EditBay", "BtnClose", "EXIT [TAB]", False)
for b in ("BtnClear", "BtnDeploy", "BtnClose"):
    pad("WBP_EditBay", b, 0, 0, 14, 0)
pad("WBP_EditBay", "ActionsRow", 0, 34, 0, 0)
text("WBP_EditBay", "StatusText", "", 14, HEAT, MONO_B)
pad("WBP_EditBay", "StatusText", 0, 18, 0, 0)

# ---- End screen: full-screen ink.
canvas("WBP_End", "Backdrop", (0, 0, 1, 1), (0, 0), (0, 0), (0, 0))
e = panel("WBP_End", "Backdrop", INK, None, (0, 0, 0, 0), alpha=0.97, radius=0.0)
e.set_editor_property("horizontal_alignment", unreal.HorizontalAlignment.H_ALIGN_CENTER)
e.set_editor_property("vertical_alignment", unreal.VerticalAlignment.V_ALIGN_CENTER)
text("WBP_End", "EndTitle", "SCENE RESTORED", 44, PAPER, MICHROMA, C, 400)
text("WBP_End", "EndSub", "Director's Cut  ·  the Digger cut through", 15, PAPER, MONO, C, 60)
pad("WBP_End", "EndSub", 0, 16, 0, 44)
button("WBP_End", "BtnRestart", "RESTART", False, 14)

out = []
for w in ("WBP_HUD", "WBP_EditBay", "WBP_End"):
    bp = unreal.load_asset(f"/Game/Splice/UI/{w}")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(f"/Game/Splice/UI/{w}")
    out.append(w)
"styled " + ", ".join(out)
'''))
