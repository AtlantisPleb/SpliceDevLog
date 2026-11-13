"""Splice look pass: soft cel shading with coloured light pools, glow, sky, thin ink lines.

It matches the Aethyr world's picture (docs/design/aethyr-gap-analysis.md):
- M_Cel (master, UNLIT): one tone per face from a sun direction, a soft shadow-side tint,
  up to eight coloured point lights, and distance haze. All of it comes from MPC_Splice,
  so no engine lights are needed and both web renderer tiers draw the same picture.
  Colour maths is done in display space, so the numbers are the ones you see on screen.
- M_Glow (master, UNLIT): a colour brighter than white, which the bloom turns into a halo.
- M_Sky: a gradient dome with drifting clouds.
- M_Shadow: a soft dark blob that sits under characters and vehicles.
- M_Ink (post-process): thin contour lines from scene depth only (no GBuffer, so it
  compiles on the web forward tier).
- The named palette materials (M_Dark, M_Red, ...) that Blueprints swap at run time.

Usage: python3 tools/ue/splice_look.py [ink threshold] [exposure bias]
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from splice_common import PRELUDE  # noqa: E402
from uemcp import py  # noqa: E402

# Named materials (display-space colour, glow strength or None for cel).
PALETTE = {
    "M_MineFloor": ((0.90, 0.68, 0.48), None), "M_MineWall": ((0.84, 0.46, 0.32), None),
    "M_MineCeiling": ((0.62, 0.42, 0.56), None), "M_Rubble": ((0.56, 0.36, 0.28), None),
    "M_ZoneMarker": ((0.918, 0.859, 0.769), None), "M_Orange": ((0.722, 0.263, 0.122), None),
    "M_Blue": ((0.22, 0.34, 0.56), None), "M_Green": ((0.93, 0.88, 0.76), None),
    "M_White": ((0.93, 0.88, 0.76), None), "M_Gray": ((0.45, 0.45, 0.50), None),
    "M_Dark": ((0.118, 0.106, 0.094), None), "M_Red": ((1.0, 0.36, 0.14), 2.2),
    "M_Pad": ((0.310, 0.702, 0.851), 2.2),
}
# Party neon: name -> (colour, pulse speed, pulse phase).
NEON = {
    "M_NeonPink": ((1.0, 0.36, 0.62), 7.5, 0.0), "M_NeonLime": ((0.36, 0.86, 0.96), 7.5, 2.1),
    "M_NeonAmber": ((1.0, 0.72, 0.30), 7.5, 4.2), "M_NeonViolet": ((0.42, 0.26, 0.66), 2.0, 1.0),
}
# MPC_Splice vectors and their defaults (day).
MPC = [("Tint", (1, 1, 1, 1)), ("Fog", (1, 1, 1, 0)),
       ("Sun", (-0.60, -0.45, 0.66, 0)), ("Ambient", (1.13, 1.12, 1.10, 1)), ("Shade", (0.80, 0.70, 0.78, 1)),
       ("Haze", (0.80, 0.74, 0.86, 0.55)), ("SkyTop", (0.56, 0.70, 0.90, 1)), ("SkyHorizon", (0.95, 0.90, 0.86, 1)),
       ("Cloud", (1, 1, 1, 0.8))]
for i in range(8):
    MPC.append((f"L{i}P", (0, 0, -100000, 1)))
    MPC.append((f"L{i}C", (0, 0, 0, 0)))

SRC = PRELUDE + r'''
PALETTE = __PALETTE__
NEON = __NEON__
MPC = __MPC__
await stop_pie()
mel = _mel

def get_or_create(name):
    path = f"{MAT_DIR}/{name}"
    if _reg.get_assets_by_package_name(path):
        m = unreal.load_asset(path)
        mel.delete_all_material_expressions(m)
        return m
    return _tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())

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

# ---- MPC_Splice
mpc_path = f"{MAT_DIR}/MPC_Splice"
if _reg.get_assets_by_package_name(mpc_path):
    mpc = unreal.load_asset(mpc_path)
else:
    mpc = _tools.create_asset("MPC_Splice", MAT_DIR, unreal.MaterialParameterCollection,
                              unreal.MaterialParameterCollectionFactoryNew())
have = {str(v.get_editor_property("parameter_name")): v for v in mpc.get_editor_property("vector_parameters")}
vps = []
for pname, val in MPC:
    vp = have.get(pname) or unreal.CollectionVectorParameter()
    vp.set_editor_property("parameter_name", pname)
    vp.set_editor_property("default_value", unreal.LinearColor(*val))
    vps.append(vp)
mpc.set_editor_property("vector_parameters", vps)
unreal.EditorAssetLibrary.save_asset(mpc_path)

def mpc_in(m, c, pname, pin, y):
    cp = mel.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -1400, y)
    cp.set_editor_property("collection", mpc)
    cp.set_editor_property("parameter_name", pname)
    mel.connect_material_expressions(cp, "", c, pin)

# ---- M_Cel
LIGHT = "".join(f"""
{{ float3 d = L{i}P.xyz - P; float dist = length(d); float a = saturate(1.0 - dist / max(L{i}P.w, 1.0)); a *= a;
  float nl = saturate(dot(n, d / max(dist, 1.0)) * 0.6 + 0.4);
  s += (s0 * 0.85 + 0.12) * L{i}C.rgb * (L{i}C.a * a * nl); }}""" for i in range(8))
CEL = """
float3 n = normalize(N);
float3 s0 = pow(max(Col, 0.0), 1.0 / 2.2);
float ndl = dot(n, normalize(Sun.xyz));
float lit = smoothstep(-0.15, 0.30, ndl);
float3 s = s0 * Ambient.rgb * lerp(Shade.rgb, float3(1.0, 1.0, 1.0), lit);
// a touch brighter on faces that look up, so floors and wall tops separate from walls
s *= 1.0 + 0.05 * saturate(n.z);
""" + LIGHT + """
float dcam = length(P - Cam);
s = lerp(s, Haze.rgb, Haze.a * saturate((dcam - 2500.0) / 26000.0));
return pow(saturate(s), 2.2);
"""
CEL_INS = ["Col", "N", "P", "Cam", "Sun", "Ambient", "Shade", "Haze"] + [f"L{i}{k}" for i in range(8) for k in "PC"]

def cel_graph(m, colour_expr):
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    n = mel.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -1400, 100)
    p = mel.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1400, 200)
    cam = mel.create_material_expression(m, unreal.MaterialExpressionCameraPositionWS, -1400, 300)
    c = custom(m, CEL, CEL_INS, unreal.CustomMaterialOutputType.CMOT_FLOAT3, -700, 200)
    mel.connect_material_expressions(colour_expr, "", c, "Col")
    mel.connect_material_expressions(n, "", c, "N")
    mel.connect_material_expressions(p, "", c, "P")
    mel.connect_material_expressions(cam, "", c, "Cam")
    y = 400
    for pin in CEL_INS[4:]:
        mpc_in(m, c, pin, pin, y)
        y += 90
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

def colour_param(m, default):
    v = mel.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -1400, 0)
    v.set_editor_property("parameter_name", "Color")
    v.set_editor_property("default_value", unreal.LinearColor(*default, 1.0))
    return v
def colour_const(m, rgb):
    v = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -1400, 0)
    v.constant = unreal.LinearColor(to_lin(rgb[0]), to_lin(rgb[1]), to_lin(rgb[2]), 1.0)
    return v

def finish(m, name):
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(f"{MAT_DIR}/{name}")

m = get_or_create("M_Cel")
cel_graph(m, colour_param(m, (0.8, 0.8, 0.8)))
finish(m, "M_Cel")

# ---- M_Glow: colour * strength, straight out. Bloom makes the halo.
def glow_graph(m, colour_expr, strength_expr):
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -700, 0)
    mel.connect_material_expressions(colour_expr, "", mul, "A")
    mel.connect_material_expressions(strength_expr, "", mul, "B")
    mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
m = get_or_create("M_Glow")
sp = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -1400, 200)
sp.set_editor_property("parameter_name", "Strength")
sp.set_editor_property("default_value", 2.2)
glow_graph(m, colour_param(m, (0.1, 0.45, 0.7)), sp)
finish(m, "M_Glow")

for name, (rgb, strength) in PALETTE.items():
    m = get_or_create(name)
    if strength is None:
        cel_graph(m, colour_const(m, rgb))
    else:
        k = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -1400, 200)
        k.set_editor_property("r", strength)
        glow_graph(m, colour_const(m, rgb), k)
    finish(m, name)

# ---- Party neon: a glow that pulses on the beat.
NEON_CODE = """
float pulse = 0.65 + 0.35 * abs(sin(T * Speed * 0.5 + Phase));
return Col * pulse * 2.0;
"""
for name, (rgb, speed, phase) in NEON.items():
    m = get_or_create(name)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    col = colour_const(m, rgb)
    t = mel.create_material_expression(m, unreal.MaterialExpressionTime, -900, 200)
    spd = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -900, 320)
    spd.set_editor_property("r", speed)
    ph = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -900, 440)
    ph.set_editor_property("r", phase)
    c = custom(m, NEON_CODE, ["Col", "T", "Speed", "Phase"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, 200)
    for src, pin in ((col, "Col"), (t, "T"), (spd, "Speed"), (ph, "Phase")):
        mel.connect_material_expressions(src, "", c, pin)
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    finish(m, name)

# ---- M_Tile: a dance-floor tile that steps through three colours on the beat. Offset (0, 1, 2)
# puts neighbouring tiles out of step, as (i + i / 5 + step) % 3 does in the Aethyr world.
TILE_CODE = """
float k = fmod(Offset + floor(T * 1.9), 3.0);
float3 c = k < 0.5 ? float3(0.80, 0.22, 0.52) : (k < 1.5 ? float3(0.20, 0.60, 0.74) : float3(0.42, 0.26, 0.66));
return pow(c, 2.2) * 1.7;
"""
m = get_or_create("M_Tile")
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
t = mel.create_material_expression(m, unreal.MaterialExpressionTime, -900, 200)
off = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, 320)
off.set_editor_property("parameter_name", "Offset")
c = custom(m, TILE_CODE, ["T", "Offset"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, 200)
mel.connect_material_expressions(t, "", c, "T")
mel.connect_material_expressions(off, "", c, "Offset")
mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_Tile")
for i in range(3):
    path = f"{MAT_DIR}/MI_Tile{i}"
    if _reg.get_assets_by_package_name(path):
        mi = unreal.load_asset(path)
    else:
        mi = _tools.create_asset(f"MI_Tile{i}", MAT_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, m)
    mel.set_material_instance_scalar_parameter_value(mi, "Offset", float(i))
    unreal.EditorAssetLibrary.save_asset(path)

# ---- M_Hologram: the memory scene. Glow blue with a soft face tone.
HOLO_CODE = """
float3 L = normalize(float3(-0.45, -0.55, 0.70));
float band = 0.55 + 0.45 * saturate(dot(normalize(N), L) * 0.5 + 0.5);
float flicker = 0.92 + 0.08 * sin(T * 31.0);
return Col * band * flicker * 1.5;
"""
m = get_or_create("M_Hologram")
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
col = colour_const(m, (0.310, 0.702, 0.851))
t = mel.create_material_expression(m, unreal.MaterialExpressionTime, -900, 200)
n = mel.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -900, 320)
c = custom(m, HOLO_CODE, ["Col", "T", "N"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, 200)
for src, pin in ((col, "Col"), (t, "T"), (n, "N")):
    mel.connect_material_expressions(src, "", c, pin)
mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_Hologram")

# ---- M_Sky: gradient by view height, with drifting clouds.
SKY = """
float3 d = normalize(P - Cam);
float h = saturate(d.z * 1.4 + 0.04);
float3 s = lerp(SkyHorizon.rgb, SkyTop.rgb, pow(h, 0.55));
float band = saturate(1.0 - abs(d.z - 0.16) * 5.0);
s = lerp(s, Cloud.rgb, saturate(Cl * 1.3 - 0.15) * Cloud.a * band);
return pow(saturate(s), 2.2);
"""
m = get_or_create("M_Sky")
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property("two_sided", True)
p = mel.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1400, 200)
cam = mel.create_material_expression(m, unreal.MaterialExpressionCameraPositionWS, -1400, 300)
# Cloud UVs: the view direction spread flat, drifting slowly.
UVC = """
float3 d = normalize(P - Cam);
float a = atan2(d.y, d.x) / 6.2832;
return float2(a * 3.0 + T * 0.004, d.z * 2.2);
"""
t = mel.create_material_expression(m, unreal.MaterialExpressionTime, -1400, 400)
uvc = custom(m, UVC, ["P", "Cam", "T"], unreal.CustomMaterialOutputType.CMOT_FLOAT2, -1100, 0)
mel.connect_material_expressions(p, "", uvc, "P")
mel.connect_material_expressions(cam, "", uvc, "Cam")
mel.connect_material_expressions(t, "", uvc, "T")
tex = mel.create_material_expression(m, unreal.MaterialExpressionTextureSample, -900, 0)
tex.set_editor_property("texture", unreal.load_asset("/Engine/EngineSky/T_Sky_Clouds_M"))
mel.connect_material_expressions(uvc, "", tex, "UVs")
c = custom(m, SKY, ["P", "Cam", "Cl", "SkyTop", "SkyHorizon", "Cloud"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, 200)
mel.connect_material_expressions(p, "", c, "P")
mel.connect_material_expressions(cam, "", c, "Cam")
mel.connect_material_expressions(tex, "R", c, "Cl")
y = 500
for pin in ("SkyTop", "SkyHorizon", "Cloud"):
    mpc_in(m, c, pin, pin, y)
    y += 90
mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(m, "M_Sky")

# ---- M_Shadow: a soft blob on a plane.
m = get_or_create("M_Shadow")
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
uv = mel.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -900, 0)
c = custom(m, "return 0.30 * smoothstep(0.5, 0.28, length(UV - 0.5));", ["UV"], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -500, 0)
mel.connect_material_expressions(uv, "", c, "UV")
k = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -500, -200)
k.constant = unreal.LinearColor(0.03, 0.01, 0.04, 1.0)
mel.connect_material_property(k, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.connect_material_property(c, "", unreal.MaterialProperty.MP_OPACITY)
finish(m, "M_Shadow")

# ---- M_Ink: thin depth-only contour lines.
INK = """
float qC = 1.0 / max(DC, 1.0);
float qL = 1.0 / max(DL, 1.0), qR = 1.0 / max(DR, 1.0);
float qU = 1.0 / max(DU, 1.0), qD = 1.0 / max(DD, 1.0);
// Second difference of 1/depth: zero on a flat surface, large at silhouettes and creases.
float lx = abs(qL + qR - 2.0 * qC), ly = abs(qU + qD - 2.0 * qC);
// A steep flat surface gives a small second difference that is only a fraction of its
// slope (sampling error); a real edge is at least comparable to the slope.
float rx = lx / (abs(qL - qR) + 1e-9), ry = ly / (abs(qU - qD) + 1e-9);
float ex = smoothstep(T, T * 2.5, lx / qC) * smoothstep(0.30, 0.50, rx);
float ey = smoothstep(T, T * 2.5, ly / qC) * smoothstep(0.30, 0.50, ry);
float nearFade = saturate((30000.0 - DC) / 20000.0);
float edge = max(ex, ey) * nearFade;
// The line is a darker, slightly violet version of what is under it, not black.
float3 lineCol = Col * float3(0.30, 0.24, 0.34);
float3 outc = lerp(Col, lineCol, edge * 0.85);
outc *= Tint.rgb;
return saturate(outc);
"""
ink = get_or_create("M_Ink")
ink.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
ink.set_editor_property("blendable_location", unreal.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)
uv = mel.create_material_expression(ink, unreal.MaterialExpressionScreenPosition, -2000, 0)
vs = mel.create_material_expression(ink, unreal.MaterialExpressionViewSize, -2000, 200)
depths = {}
y = -700
for k, (dx, dy) in {"C": (0, 0), "L": (-1.0, 0), "R": (1.0, 0), "U": (0, -1.0), "D": (0, 1.0)}.items():
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
c = custom(ink, INK, ["Col", "DC", "DL", "DR", "DU", "DD", "T", "Tint"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, -200)
mpc_in(ink, c, "Tint", "Tint", 800)
mel.connect_material_expressions(col, "Color", c, "Col")
for k in "CLRUD":
    mel.connect_material_expressions(depths[k], "", c, "D" + k)
mel.connect_material_expressions(thr, "", c, "T")
mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
finish(ink, "M_Ink")

# ---- Level: post-process settings. The picture is drawn by the materials, so the tone
# curve is off and exposure is fixed; bloom only catches what is brighter than white.
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if not world.get_path_name().startswith("/Game/Splice/L_Mine"):
    les.load_level("/Game/Splice/L_Mine")
done = []
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "PP_Mine":
        wb = unreal.WeightedBlendable()
        wb.set_editor_property("object", ink)
        wb.set_editor_property("weight", 1.0)
        arr = unreal.WeightedBlendables()
        arr.set_editor_property("array", [wb])
        st = a.settings
        st.set_editor_property("weighted_blendables", arr)
        for prop, val in (("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL),
                          ("auto_exposure_bias", __EXPOSURE__),
                          ("auto_exposure_apply_physical_camera_exposure", False),
                          ("bloom_intensity", 0.9), ("bloom_threshold", 1.0),
                          ("vignette_intensity", 0.0), ("tone_curve_amount", 0.0), ("expand_gamut", 0.0),
                          ("film_grain_intensity", 0.0), ("scene_fringe_intensity", 0.0)):
            try:
                st.set_editor_property("override_" + prop, True)
                st.set_editor_property(prop, val)
                done.append(prop)
            except Exception as e:
                done.append("!" + prop)
        a.set_editor_property("settings", st)
        a.set_editor_property("unbound", True)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
f"look applied: M_Cel, M_Glow, M_Sky, M_Shadow, M_Ink, {len(PALETTE)} named, {len(NEON)} neon; post: {' '.join(done)}"
'''

if __name__ == "__main__":
    threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0025
    exposure = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    print(py(SRC.replace("__PALETTE__", repr(PALETTE)).replace("__NEON__", repr(NEON)).replace("__MPC__", repr(MPC))
             .replace("__THRESHOLD__", repr(threshold)).replace("__EXPOSURE__", repr(exposure))))
