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
text("WBP_HUD", "CarryText", "Carrying: nothing", 16, PAPER, MONO_B, None, 40, INK)
canvas("WBP_HUD", "CarryText", (0, 0, 0, 0), (28, 24), (0, 0), (0, 0), auto=True)
text("WBP_HUD", "PromptText", "", 19, PAPER, MONO_B, C, 40, INK)
canvas("WBP_HUD", "PromptText", (0.5, 1, 0.5, 1), (0, -72), (0, 0), (0.5, 0.5), auto=True)
text("WBP_HUD", "MessageText", "", 22, PAPER, MONO_B, C, 40, INK)
canvas("WBP_HUD", "MessageText", (0.5, 0.26, 0.5, 0.26), (0, 0), (0, 0), (0.5, 0.5), auto=True)

# ---- HUD panels from the Game UI board.
GLOW = "#4FB3D9"
canvas("WBP_HUD", "HeartsPanel", (0, 0, 0, 0), (24, 24), (0, 0), (0, 0), auto=True)
panel("WBP_HUD", "HeartsPanel", PAPER, INK, (16, 10, 16, 12))
text("WBP_HUD", "HeartsLabel", "HEARTS", 12, INK, MONO_B, None, 150)
pad("WBP_HUD", "HeartsRow", 0, 6, 0, 0)
for i in (1, 2, 3):
    h = panel("WBP_HUD", f"Heart{i}", HEAT, INK, (0, 0, 0, 0), radius=7.0)
    pad("WBP_HUD", f"Heart{i}", 0, 0, 8, 0)
    sb = W("WBP_HUD", f"Heart{i}Size")
    # The setters also switch the override on; setting the property alone does not.
    sb.set_width_override(40.0)
    sb.set_height_override(30.0)
canvas("WBP_HUD", "CarryText", (0, 0, 0, 0), (28, 124), (0, 0), (0, 0), auto=True)

canvas("WBP_HUD", "PhaseBar", (0.5, 0, 0.5, 0), (0, 24), (0, 0), (0.5, 0), auto=True)
panel("WBP_HUD", "PhaseBar", INK, None, (6, 6, 6, 6), radius=6.0)
for i, word in enumerate(("DAWN", "DAY", "DUSK", "NIGHT")):
    panel("WBP_HUD", f"Phase{i}", PAPER, None, (20, 9, 20, 9), radius=3.0)
    pad("WBP_HUD", f"Phase{i}", 0, 0, 0 if i == 3 else 6, 0)
    text("WBP_HUD", f"Phase{i}Label", word, 13, INK, MONO_B, C, 100)

canvas("WBP_HUD", "HeatPanel", (1, 0, 1, 0), (-24, 24), (380, 132), (1, 0))
panel("WBP_HUD", "HeatPanel", PAPER, INK, (16, 12, 16, 12))
text("WBP_HUD", "HeatText", "HEAT 0 / 100  ·  COOL", 15, HEAT, MONO_B, None, 80)
bar = W("WBP_HUD", "HeatBar")
bst = bar.get_editor_property("widget_style")
bg = box_brush(PAPER, INK, 2.0, 3.0)
bg.set_editor_property("image_size", unreal.DeprecateSlateVector2D(344.0, 18.0))
fill = box_brush(HEAT, None, 0.0, 2.0)
fill.set_editor_property("image_size", unreal.DeprecateSlateVector2D(344.0, 18.0))
bst.set_editor_property("background_image", bg)
bst.set_editor_property("fill_image", fill)
bar.set_editor_property("widget_style", bst)
bar.set_editor_property("fill_color_and_opacity", unreal.LinearColor(1, 1, 1, 1))
bar.set_editor_property("percent", 0.0)
pad("WBP_HUD", "HeatBar", 0, 8, 0, 6)
text("WBP_HUD", "HeatBands", "COOL            WARM           WANTED", 11, INK, MONO, None, 60)
text("WBP_HUD", "HeatNote", "Banned pieces raise it. Cools at the rover.", 10, INK, MONO)
pad("WBP_HUD", "HeatNote", 0, 4, 0, 0)

canvas("WBP_HUD", "ObjectivePanel", (1, 1, 1, 1), (-24, -24), (400, 112), (1, 1))
panel("WBP_HUD", "ObjectivePanel", PAPER, INK, (16, 12, 16, 12))
text("WBP_HUD", "ObjectiveLabel", "OBJECTIVE", 12, INK, MONO_B, None, 150)
text("WBP_HUD", "ObjectiveText", "", 14, INK, MICHROMA, None, 40).set_editor_property("auto_wrap_text", True)
pad("WBP_HUD", "ObjectiveText", 0, 8, 0, 0)

text("WBP_HUD", "HelpText", "[F]  Hit / stun", 14, PAPER, MONO_B, None, 40, INK)
canvas("WBP_HUD", "HelpText", (0, 1, 0, 1), (28, -40), (0, 0), (0, 1), auto=True)

# ---- The memory overlay: a click anywhere skips; the caption sits at the bottom.
canvas("WBP_Memory", "BtnSkip", (0, 0, 1, 1), (0, 0), (0, 0), (0, 0))
skip = W("WBP_Memory", "BtnSkip")
sst = skip.get_editor_property("widget_style")
for state in ("normal", "hovered", "pressed", "disabled"):
    sst.set_editor_property(state, box_brush(INK, None, 0.0, 0.0, alpha=0.0))
skip.set_editor_property("widget_style", sst)
canvas("WBP_Memory", "CaptionPanel", (0.5, 1, 0.5, 1), (0, -90), (0, 0), (0.5, 1), auto=True)
panel("WBP_Memory", "CaptionPanel", "#0F1A24", None, (28, 14, 28, 14), alpha=0.85, radius=6.0)
text("WBP_Memory", "Caption", "", 20, "#CDEFFB", MONO_B, C, 40)
text("WBP_Memory", "SkipHint", "CLICK TO SKIP", 12, "#CDEFFB", MONO, C, 200)
canvas("WBP_Memory", "SkipHint", (0.5, 1, 0.5, 1), (0, -44), (0, 0), (0.5, 1), auto=True)

# ---- Full-screen banners.
for wbp, fill_c, ink_c, tag, title, sub in (
        ("WBP_Sweep", HEAT, "#FFF6EA", "MAX HEAT", "IMPERIAL SWEEP", "Heat hit the limit. Back to the checkpoint outside the mine."),
        ("WBP_TakeTwo", INK, PAPER, "0 HEARTS", "CUT. TAKE TWO.", "Back at the rover with your checkpoint inventory. Banned pieces since then are lost.")):
    canvas(wbp, "Backdrop", (0, 0, 1, 1), (0, 0), (0, 0), (0, 0))
    bd = panel(wbp, "Backdrop", fill_c, None, (0, 0, 0, 0), radius=0.0)
    bd.set_editor_property("horizontal_alignment", unreal.HorizontalAlignment.H_ALIGN_CENTER)
    bd.set_editor_property("vertical_alignment", unreal.VerticalAlignment.V_ALIGN_CENTER)
    text(wbp, "Tag", tag, 14, ink_c, MONO_B, C, 200)
    text(wbp, "Title", title, 40, ink_c, MICHROMA, C, 400)
    pad(wbp, "Title", 0, 14, 0, 14)
    text(wbp, "Sub", sub, 17, ink_c, MONO, C, 40)

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
# Blue means banned tech: DRILL+ and the core get the blue outline.
for b, label in (("BtnDrillPlus", "DRILL+"), ("BtnSpliceCore", "SPLICE CORE")):
    button("WBP_EditBay", b, label, False, 12)
    bw = W("WBP_EditBay", b)
    bs = bw.get_editor_property("widget_style")
    bs.set_editor_property("normal", box_brush(PAPER, "#1F5F80", 3.0, 8.0))
    bs.set_editor_property("hovered", box_brush("#DDF3FB", "#1F5F80", 3.0, 8.0))
    bs.set_editor_property("pressed", box_brush("#B8E4F5", "#1F5F80", 3.0, 8.0))
    bw.set_editor_property("widget_style", bs)
    text("WBP_EditBay", b + "Label", label, 12, "#1F5F80", MICHROMA, C, 200)
    pad("WBP_EditBay", b, 0, 0, 12, 0)
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
for w in ("WBP_HUD", "WBP_EditBay", "WBP_End", "WBP_Sweep", "WBP_TakeTwo", "WBP_Memory"):
    bp = unreal.load_asset(f"/Game/Splice/UI/{w}")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(f"/Game/Splice/UI/{w}")
    out.append(w)
"styled " + ", ".join(out)
'''))
