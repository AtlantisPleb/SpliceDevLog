"""Splice look pass: flat comic materials, a depth-only ink-line post-process, flat lighting.

Why it is built this way:
- World materials are UNLIT. Each face gets one flat tone from its normal against a fixed
  "sun", and only shadow-side faces get screen-space hatching. No lights are needed, the
  result is identical on every web renderer tier, and it is cheap.
- M_Ink (post-process) reads only scene colour and scene depth, so it compiles on the web
  forward tier, which has no GBuffer. Lines come from the second difference of 1/depth,
  which is zero on any flat surface and spikes at silhouettes and creases.

Usage: python3 tools/ue/splice_look.py
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from uemcp import py  # noqa: E402


def lin(hexstr):
    """sRGB hex -> linear RGB tuple."""
    out = []
    for i in (1, 3, 5):
        c = int(hexstr[i:i + 2], 16) / 255.0
        out.append(round(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4, 4))
    return tuple(out)


# name -> (colour, glow multiplier). Palette: sand, burnt orange, dusty pink, lavender,
# plus the UI board's paper, ink, heat and glow.
PALETTE = {
    "M_MineFloor": ("#DBA594", 1.0),    # dusty pink
    "M_MineWall": ("#F0D2A0", 1.0),     # sand
    "M_MineCeiling": ("#9A8FBF", 1.0),  # lavender
    "M_Rubble": ("#C2552B", 1.0),       # burnt orange
    "M_ZoneMarker": ("#EADBC4", 1.0),   # paper
    "M_Orange": ("#E0683F", 1.0),       # drill arm, Digger body
    "M_Blue": ("#8F86C9", 1.0),         # treads (lavender: blue is reserved for banned tech)
    "M_Green": ("#E3A3AC", 1.0),        # battery (dusty pink)
    "M_White": ("#F3E8D4", 1.0),        # cards
    "M_Gray": ("#D8CCB6", 1.0),         # rover body
    "M_Dark": ("#1E1B18", 1.0),         # ink
    "M_Red": ("#B8431F", 1.6),          # heat
    "M_Pad": ("#4FB3D9", 1.8),          # glow
}

# Party neon: name -> (colour, pulse speed, pulse phase). No blue: blue means banned tech.
NEON = {
    "M_NeonPink": ("#FF2E9A", 5.0, 0.0),
    "M_NeonLime": ("#B6FF3A", 5.0, 2.1),
    "M_NeonAmber": ("#FFB020", 5.0, 4.2),
    "M_NeonViolet": ("#A855F7", 2.0, 1.0),
}

SRC = r'''
PALETTE = __PALETTE__
NEON = __NEON__
HOLO = __HOLO__
MAT_DIR = "/Game/Splice/Materials"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for _ in range(20):
    if not les.is_in_play_in_editor():
        break
    les.editor_request_end_play()
    await asyncio.sleep(0.5)

def get_or_create(name):
    path = f"{MAT_DIR}/{name}"
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    if reg.get_assets_by_package_name(path):
        m = unreal.load_asset(path)
        mel.delete_all_material_expressions(m)
        return m
    return tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())

def custom(m, code, names, out_type, x, y):
    c = mel.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    c.set_editor_property("code", code)
    c.set_editor_property("output_type", out_type)
    ins = []
    for n in names:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        ins.append(ci)
    c.set_editor_property("inputs", ins)
    return c

COMIC = """
float3 L = normalize(float3(-0.45, -0.55, 0.70));
float ndl = dot(normalize(N), L);
float band = ndl > 0.30 ? 1.0 : (ndl > -0.50 ? 0.86 : 0.70);
float3 c = Col * band * Glow;
float sc = max(VS.y / 720.0, 1.0);
float2 p = UV * VS / sc;
float h = step(frac((p.x - p.y) / 9.0), 0.16);
float3 ink = float3(0.012, 0.010, 0.009);
if (ndl <= -0.50) c = lerp(c, ink, h * 0.45);
return c;
"""

def comic(name, rgb, glow):
    m = get_or_create(name)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    col = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -900, 0)
    col.constant = unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0)
    g = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -900, 200)
    g.set_editor_property("r", glow)
    n = mel.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -900, 320)
    uv = mel.create_material_expression(m, unreal.MaterialExpressionScreenPosition, -900, 440)
    vs = mel.create_material_expression(m, unreal.MaterialExpressionViewSize, -900, 560)
    c = custom(m, COMIC, ["Col", "Glow", "N", "UV", "VS"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, 200)
    mel.connect_material_expressions(col, "", c, "Col")
    mel.connect_material_expressions(g, "", c, "Glow")
    mel.connect_material_expressions(n, "", c, "N")
    mel.connect_material_expressions(uv, "", c, "UV")
    mel.connect_material_expressions(vs, "", c, "VS")
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(f"{MAT_DIR}/{name}")

for name, (rgb, glow) in PALETTE.items():
    comic(name, rgb, glow)

# ---- Party neon: an unlit colour that pulses. Each has its own speed and phase, so
# neighbouring lights are out of step.
NEON_CODE = """
float pulse = 0.55 + 0.45 * sin(T * Speed + Phase);
return Col * pulse;
"""
def neon(name, rgb, speed, phase):
    m = get_or_create(name)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    col = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -900, 0)
    col.constant = unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0)
    t = mel.create_material_expression(m, unreal.MaterialExpressionTime, -900, 200)
    sp = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -900, 320)
    sp.set_editor_property("r", speed)
    ph = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -900, 440)
    ph.set_editor_property("r", phase)
    c = custom(m, NEON_CODE, ["Col", "T", "Speed", "Phase"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, 200)
    mel.connect_material_expressions(col, "", c, "Col")
    mel.connect_material_expressions(t, "", c, "T")
    mel.connect_material_expressions(sp, "", c, "Speed")
    mel.connect_material_expressions(ph, "", c, "Phase")
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(f"{MAT_DIR}/{name}")

for name, (rgb, speed, phase) in NEON.items():
    neon(name, rgb, speed, phase)

# ---- M_Hologram: the memory scene. Glow blue with moving scanlines and a flicker.
HOLO_CODE = """
float3 L = normalize(float3(-0.45, -0.55, 0.70));
float band = 0.72 + 0.28 * saturate(dot(normalize(N), L) * 0.5 + 0.5);
float sc = max(VS.y / 720.0, 1.0);
float2 p = UV * VS / sc;
float scan = step(frac(p.y / 5.0 + T * 0.8), 0.55);
float flicker = 0.88 + 0.12 * sin(T * 31.0);
return Col * band * (0.45 + 0.55 * scan) * flicker;
"""
m = get_or_create("M_Hologram")
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
col = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -900, 0)
col.constant = unreal.LinearColor(HOLO[0], HOLO[1], HOLO[2], 1.0)
t = mel.create_material_expression(m, unreal.MaterialExpressionTime, -900, 200)
n = mel.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -900, 320)
uv0 = mel.create_material_expression(m, unreal.MaterialExpressionScreenPosition, -900, 440)
vs0 = mel.create_material_expression(m, unreal.MaterialExpressionViewSize, -900, 560)
c = custom(m, HOLO_CODE, ["Col", "T", "N", "UV", "VS"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, 200)
for src, pin in ((col, "Col"), (t, "T"), (n, "N"), (uv0, "UV"), (vs0, "VS")):
    mel.connect_material_expressions(src, "", c, pin)
mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(m)
unreal.EditorAssetLibrary.save_asset(f"{MAT_DIR}/M_Hologram")

# ---- M_Ink: depth-only contour lines + faint paper grain.
INK = """
float qC = 1.0 / max(DC, 1.0);
float qL = 1.0 / max(DL, 1.0), qR = 1.0 / max(DR, 1.0);
float qU = 1.0 / max(DU, 1.0), qD = 1.0 / max(DD, 1.0);
// Second difference of 1/depth: zero on a flat surface, large at silhouettes and creases.
float lx = abs(qL + qR - 2.0 * qC), ly = abs(qU + qD - 2.0 * qC);
// Reject sampling error: when depth is rendered at a different resolution than the
// screen, a steep flat surface gives a small second difference that is only a fraction
// of its slope. A real edge is at least comparable to the slope.
float rx = lx / (abs(qL - qR) + 1e-9), ry = ly / (abs(qU - qD) + 1e-9);
float ex = smoothstep(T, T * 2.5, lx / qC) * smoothstep(0.30, 0.50, rx);
float ey = smoothstep(T, T * 2.5, ly / qC) * smoothstep(0.30, 0.50, ry);
float nearFade = saturate((60000.0 - DC) / 30000.0);
float edge = max(ex, ey) * nearFade;
float sc = max(VS.y / 720.0, 1.0);
float2 p = UV * VS / sc;
float grain = frac(sin(dot(floor(p), float2(12.9898, 78.233))) * 43758.5453);
float3 ink = float3(0.118, 0.106, 0.094);
// Time of day (MPC_Splice): depth fog first, then lines, then a tint over everything.
float3 outc = lerp(Col, Fog.rgb, Fog.a * saturate(DC / 5000.0));
outc = lerp(outc, ink, edge * 0.92);
// Strongly saturated, bright pixels (banned-tech blue, neon, heat orange) keep their
// colour, so they glow against the dark at night.
float mx = max(outc.r, max(outc.g, outc.b));
float mn = min(outc.r, min(outc.g, outc.b));
float keep = smoothstep(0.62, 0.82, (mx - mn) / max(mx, 1e-3)) * step(0.45, mx);
outc *= lerp(Tint.rgb, float3(1.0, 1.0, 1.0), keep);
outc *= 0.97 + 0.03 * grain;
return saturate(outc);
"""
# MPC_Splice holds the time-of-day look. BP_TimeOfDay writes it at run time.
mpc_path = f"{MAT_DIR}/MPC_Splice"
reg = unreal.AssetRegistryHelpers.get_asset_registry()
if reg.get_assets_by_package_name(mpc_path):
    mpc = unreal.load_asset(mpc_path)
else:
    mpc = tools.create_asset("MPC_Splice", MAT_DIR, unreal.MaterialParameterCollection,
                             unreal.MaterialParameterCollectionFactoryNew())
vps = []
for pname, val in (("Tint", (1.0, 1.0, 1.0, 1.0)), ("Fog", (1.0, 1.0, 1.0, 0.0))):
    vp = unreal.CollectionVectorParameter()
    vp.set_editor_property("parameter_name", pname)
    vp.set_editor_property("default_value", unreal.LinearColor(*val))
    vps.append(vp)
mpc.set_editor_property("vector_parameters", vps)
unreal.EditorAssetLibrary.save_asset(mpc_path)
ink = get_or_create("M_Ink")
ink.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
ink.set_editor_property("blendable_location", unreal.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)
uv = mel.create_material_expression(ink, unreal.MaterialExpressionScreenPosition, -2000, 0)
vs = mel.create_material_expression(ink, unreal.MaterialExpressionViewSize, -2000, 200)
depths = {}
y = -700
for k, (dx, dy) in {"C": (0, 0), "L": (-2.0, 0), "R": (2.0, 0), "U": (0, -2.0), "D": (0, 2.0)}.items():
    off = mel.create_material_expression(ink, unreal.MaterialExpressionConstant2Vector, -1800, y)
    off.set_editor_property("r", dx)
    off.set_editor_property("g", dy)
    div = mel.create_material_expression(ink, unreal.MaterialExpressionDivide, -1600, y)
    mel.connect_material_expressions(off, "", div, "A")
    mel.connect_material_expressions(vs, "", div, "B")
    add = mel.create_material_expression(ink, unreal.MaterialExpressionAdd, -1400, y)
    mel.connect_material_expressions(uv, "", add, "A")
    mel.connect_material_expressions(div, "", add, "B")
    d = mel.create_material_expression(ink, unreal.MaterialExpressionSceneDepth, -1100, y)
    mel.connect_material_expressions(add, "", d, "UVs")
    depths[k] = d
    y += 220
col = mel.create_material_expression(ink, unreal.MaterialExpressionSceneTexture, -1100, -1000)
col.set_editor_property("scene_texture_id", unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
thr = mel.create_material_expression(ink, unreal.MaterialExpressionScalarParameter, -1100, 600)
thr.set_editor_property("parameter_name", "Threshold")
thr.set_editor_property("default_value", __THRESHOLD__)
c = custom(ink, INK, ["Col", "DC", "DL", "DR", "DU", "DD", "UV", "VS", "T", "Tint", "Fog"],
           unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, -200)
for pname in ("Tint", "Fog"):
    cp = mel.create_material_expression(ink, unreal.MaterialExpressionCollectionParameter, -1100, 800)
    cp.set_editor_property("collection", mpc)
    cp.set_editor_property("parameter_name", pname)
    mel.connect_material_expressions(cp, "", c, pname)
mel.connect_material_expressions(col, "Color", c, "Col")
for k in "CLRUD":
    mel.connect_material_expressions(depths[k], "", c, "D" + k)
mel.connect_material_expressions(uv, "", c, "UV")
mel.connect_material_expressions(vs, "", c, "VS")
mel.connect_material_expressions(thr, "", c, "T")
mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(ink)
unreal.EditorAssetLibrary.save_asset(f"{MAT_DIR}/M_Ink")

# ---- Level: swap the post-process, replace the work lamps with flat character lighting.
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if not world.get_path_name().startswith("/Game/Splice/L_Mine"):
    les.load_level("/Game/Splice/L_Mine")
lamps = 0
for a in eas.get_all_level_actors():
    label = a.get_actor_label()
    if isinstance(a, unreal.PointLight) or label in ("KeyLight", "FillLight"):
        eas.destroy_actor(a)
        lamps += 1
    elif label == "PP_Mine":
        wb = unreal.WeightedBlendable()
        wb.set_editor_property("object", ink)
        wb.set_editor_property("weight", 1.0)
        arr = unreal.WeightedBlendables()
        arr.set_editor_property("array", [wb])
        st = a.settings
        st.set_editor_property("weighted_blendables", arr)
        st.set_editor_property("override_auto_exposure_bias", True)
        st.set_editor_property("auto_exposure_bias", __EXPOSURE__)
        st.set_editor_property("override_bloom_intensity", True)
        st.set_editor_property("bloom_intensity", 0.0)
        st.set_editor_property("override_vignette_intensity", True)
        st.set_editor_property("vignette_intensity", 0.0)
        a.set_editor_property("settings", st)
# The world is unlit; these two lights only shade the lit template character.
for label, pitch, yaw, lux in (("KeyLight", -50.0, 50.0, 3.2), ("FillLight", -20.0, 230.0, 1.6)):
    l = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 600),
                                   unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0))
    l.set_actor_label(label)
    l.set_folder_path("Mine/Lights")
    lc = l.get_component_by_class(unreal.DirectionalLightComponent)
    lc.set_mobility(unreal.ComponentMobility.MOVABLE)
    lc.set_editor_property("intensity", lux)
    lc.set_editor_property("cast_shadows", False)
    # Only one directional light can drive forward shading; make the key win outright.
    lc.set_editor_property("forward_shading_priority", 1 if label == "KeyLight" else 0)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
f"look applied: {len(PALETTE)} comic materials, {len(NEON)} neon, M_Hologram, M_Ink, {lamps} old lights removed"
'''

if __name__ == "__main__":
    threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0025
    exposure = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    pal = {k: (lin(v[0]), v[1]) for k, v in PALETTE.items()}
    neon_lin = {k: (lin(v[0]), v[1], v[2]) for k, v in NEON.items()}
    print(py(SRC.replace("__PALETTE__", repr(pal)).replace("__THRESHOLD__", repr(threshold))
             .replace("__NEON__", repr(neon_lin)).replace("__HOLO__", repr(lin("#4FB3D9")))
             .replace("__EXPOSURE__", repr(exposure))))
