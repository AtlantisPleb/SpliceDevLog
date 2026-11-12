"""Build the Moebius-style post-process material and attach it to the level's volume.

Runs after tonemapping, so its output is the final screen colour and exposure
can't crush it. Flat colour comes from the GBuffer albedo; shading comes from
scene colour divided by albedo.
"""
import unreal

MAT_DIR = "/Game/Mars/Materials"
MAT_NAME = "M_Moebius"
MAT_PATH = f"{MAT_DIR}/{MAT_NAME}"
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if unreal.EditorAssetLibrary.does_asset_exist(MAT_PATH):
    unreal.EditorAssetLibrary.delete_asset(MAT_PATH)
mat = asset_tools.create_asset(MAT_NAME, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
mat.set_editor_property("blendable_location", unreal.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)


def node(cls, x, y):
    return mel.create_material_expression(mat, cls, x, y)


def scene_tex(tex_id, uv_src, x, y):
    n = node(unreal.MaterialExpressionSceneTexture, x, y)
    n.set_editor_property("scene_texture_id", tex_id)
    mel.connect_material_expressions(uv_src, "", n, "Coordinates")
    return n


uv = node(unreal.MaterialExpressionScreenPosition, -2000, 0)
view_size = node(unreal.MaterialExpressionViewSize, -2000, 200)

# Neighbour samples 1.5 px away, sized from the real viewport.
offsets = {"L": (-1.5, 0.0), "R": (1.5, 0.0), "U": (0.0, -1.5), "D": (0.0, 1.5)}
depth_out, normal_out = {}, {}
y = -600
for k, (dx, dy) in offsets.items():
    off = node(unreal.MaterialExpressionConstant2Vector, -1800, y)
    off.set_editor_property("r", dx)
    off.set_editor_property("g", dy)
    div = node(unreal.MaterialExpressionDivide, -1600, y)
    mel.connect_material_expressions(off, "", div, "A")
    mel.connect_material_expressions(view_size, "", div, "B")
    add = node(unreal.MaterialExpressionAdd, -1400, y)
    mel.connect_material_expressions(uv, "", add, "A")
    mel.connect_material_expressions(div, "", add, "B")
    d = node(unreal.MaterialExpressionSceneDepth, -1100, y)
    mel.connect_material_expressions(add, "", d, "UVs")
    depth_out[k] = d
    normal_out[k] = scene_tex(unreal.SceneTextureId.PPI_WORLD_NORMAL, add, -1100, y + 150)
    y += 320

col = scene_tex(unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0, uv, -1100, -1500)
base = scene_tex(unreal.SceneTextureId.PPI_BASE_COLOR, uv, -1100, -1300)

code = """
float3 c = Col;
float3 bc = max(BC, 0.0);
float isLit = step(0.001, bc.r + bc.g + bc.b);
float lumC = dot(c, float3(0.299, 0.587, 0.114));
float lumB = max(dot(pow(bc, 1.0 / 2.2), float3(0.299, 0.587, 0.114)), 0.03);
float ratio = lumC / lumB;

float3 N = normalize(NL + NR + NU + ND + 1e-4);
float3 Lsun = normalize(float3(-0.542, -0.542, 0.643));
float ndl = saturate(dot(N, Lsun));
float shadow = ratio < 0.38 ? 1.0 : 0.0;
float shade = shadow > 0.5 ? min(ndl, 0.12) : ndl;

float depthEdge = abs(DR - DL) / max(DL + DR, 1e-3) + abs(DD - DU) / max(DD + DU, 1e-3);
float3 nE = abs(NR - NL) + abs(ND - NU);
float normEdge = max(nE.x, max(nE.y, nE.z));
float edgeMask = (depthEdge > 0.04 || (normEdge > 0.6 && isLit > 0.5)) ? 1.0 : 0.0;

float sc = max(VS.y / 720.0, 1.0);
float2 p = UVpx * VS / sc;
float hA = step(frac((p.x - p.y) / 6.0), 0.2);
float hB = step(frac((p.x + p.y) / 6.0), 0.2);
float hC = step(frac(p.y / 4.0), 0.3);
float hatch = 0.0;
if (shade < 0.55) hatch = hA;
if (shade < 0.30) hatch = max(hatch, hB);
if (shade < 0.13) hatch = max(hatch, hC);
hatch *= isLit;
float hi = (ndl > 0.97 && shadow < 0.5) ? isLit : 0.0;

float3 ink = float3(0.16, 0.10, 0.10);
float3 outc = lerp(c, bc, isLit);
outc = lerp(outc, outc * 0.72, isLit * step(shade, 0.13));
outc = lerp(outc, ink, hatch * 0.8);
outc = lerp(outc, float3(1.0, 0.97, 0.90), hi);
outc = lerp(outc, ink, edgeMask);
float grain = frac(sin(dot(floor(p), float2(12.9898, 78.233))) * 43758.5453);
outc *= 0.95 + 0.05 * grain;
return saturate(outc);
"""
cust = node(unreal.MaterialExpressionCustom, -500, -300)
cust.set_editor_property("code", code)
cust.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
names = ["Col", "BC", "DL", "DR", "DU", "DD", "NL", "NR", "NU", "ND", "UVpx", "VS"]
inputs = []
for name in names:
    ci = unreal.CustomInput()
    ci.set_editor_property("input_name", name)
    inputs.append(ci)
cust.set_editor_property("inputs", inputs)

mel.connect_material_expressions(col, "Color", cust, "Col")
mel.connect_material_expressions(base, "Color", cust, "BC")
for k in "LRUD":
    mel.connect_material_expressions(depth_out[k], "", cust, f"D{k}")
    mel.connect_material_expressions(normal_out[k], "Color", cust, f"N{k}")
mel.connect_material_expressions(uv, "", cust, "UVpx")
mel.connect_material_expressions(view_size, "", cust, "VS")
mel.connect_material_property(cust, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

mel.layout_material_expressions(mat)
mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(MAT_PATH)
unreal.log("MARS_PP: material built")

kept = False
for a in eas.get_all_level_actors():
    if not isinstance(a, unreal.PostProcessVolume):
        continue
    if a.get_actor_label() != "PP_Moebius" or kept:
        eas.destroy_actor(a)
        continue
    kept = True
    wb = unreal.WeightedBlendable()
    wb.set_editor_property("object", mat)
    wb.set_editor_property("weight", 1.0)
    arr = unreal.WeightedBlendables()
    arr.set_editor_property("array", [wb])
    # settings returns a copy: modify it, then write it back onto the actor.
    st = a.settings
    st.set_editor_property("weighted_blendables", arr)
    a.set_editor_property("settings", st)
    a.set_editor_property("enabled", True)
    a.set_editor_property("priority", 1000.0)
    a.set_editor_property("blend_weight", 1.0)
    a.set_editor_property("unbound", True)
    unreal.log("MARS_PP: attached to PP_Moebius")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
