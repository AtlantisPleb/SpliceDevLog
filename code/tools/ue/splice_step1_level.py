"""Splice gray box, step 1: the L_Mine level (run inside the editor via runpy.sh).

A straight mine about 40 m long along +X, built from cubes:
  entrance (8 m) -> scrap room (10 x 10 m) -> tunnel (14 m, rubble wall) -> exit room (8 m)
Floor top is z = 0. Everything goes under /Game/Splice/.
"""
import unreal

LEVEL = "/Game/Splice/L_Mine"
MAT_DIR = "/Game/Splice/Materials"
T = 20.0  # wall, floor and ceiling thickness (cm)

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")

if les.is_in_play_in_editor():
    les.editor_request_end_play()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)


def material(name, rgb):
    """Plain lit colour, with a little self-glow so nothing is ever pitch black."""
    path = f"{MAT_DIR}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)
    m = tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    c = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, 0)
    c.constant = unreal.LinearColor(*rgb, 1.0)
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    g = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -200, 200)
    mel.connect_material_expressions(c, "", g, "A")
    g.set_editor_property("const_b", 0.12)
    mel.connect_material_property(g, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 300)
    r.set_editor_property("r", 0.9)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(path)
    return m


MATS = {
    "floor": material("M_MineFloor", (0.30, 0.28, 0.26)),
    "wall": material("M_MineWall", (0.50, 0.44, 0.36)),
    "ceiling": material("M_MineCeiling", (0.22, 0.21, 0.20)),
    "rubble": material("M_Rubble", (0.36, 0.20, 0.10)),
    "marker": material("M_ZoneMarker", (0.85, 0.75, 0.20)),
}


def box(label, x0, x1, y0, y1, z0, z1, mat, folder):
    """Axis-aligned cube from min to max corners (cm)."""
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    smc = a.static_mesh_component
    smc.set_static_mesh(CUBE)
    smc.set_material(0, MATS[mat])
    smc.set_collision_profile_name("BlockAll")
    a.set_actor_scale3d(unreal.Vector((x1 - x0) / 100, (y1 - y0) / 100, (z1 - z0) / 100))
    a.set_actor_label(label)
    a.set_folder_path(folder)
    return a


# Segments along +X: (name, x start, x end, half width, height).
SEGMENTS = [
    ("Entrance", 0, 800, 300, 400),
    ("ScrapRoom", 800, 1800, 500, 500),
    ("Tunnel", 1800, 3200, 200, 350),
    ("ExitRoom", 3200, 4000, 400, 400),
]

if not unreal.EditorAssetLibrary.does_asset_exist(LEVEL):
    les.new_level(LEVEL)
else:
    les.load_level(LEVEL)
    for a in eas.get_all_level_actors():
        eas.destroy_actor(a)

for name, x0, x1, hw, h in SEGMENTS:
    f = f"Mine/{name}"
    box(f"{name}_Floor", x0, x1, -hw - T, hw + T, -T, 0, "floor", f)
    box(f"{name}_Ceiling", x0, x1, -hw - T, hw + T, h, h + T, "ceiling", f)
    box(f"{name}_WallL", x0, x1, -hw - T, -hw, 0, h, "wall", f)
    box(f"{name}_WallR", x0, x1, hw, hw + T, 0, h, "wall", f)

# Where two segments meet, fill the step between their widths and heights,
# leaving an opening the size of the smaller one.
for (n0, _, xa, hw0, h0), (n1, xb, _, hw1, h1) in zip(SEGMENTS, SEGMENTS[1:]):
    x = xa
    big_hw, big_h = max(hw0, hw1), max(h0, h1)
    small_hw, small_h = min(hw0, hw1), min(h0, h1)
    xs = (x - T, x) if hw0 > hw1 else (x, x + T)
    f = f"Mine/{n0}_to_{n1}"
    if big_hw > small_hw:
        box(f"{n0}_{n1}_ShoulderL", xs[0], xs[1], -big_hw, -small_hw, 0, big_h, "wall", f)
        box(f"{n0}_{n1}_ShoulderR", xs[0], xs[1], small_hw, big_hw, 0, big_h, "wall", f)
    if big_h > small_h:
        box(f"{n0}_{n1}_Lintel", xs[0], xs[1], -big_hw, big_hw, small_h, big_h, "wall", f)

# End caps.
box("BackWall", -T, 0, -320, 320, 0, 420, "wall", "Mine/Entrance")
box("ExitEndWall", 4000, 4000 + T, -420, 420, 0, 420, "wall", "Mine/ExitRoom")

# Rubble wall fills the tunnel near its far end. Placeholder until BP_Rubble (step 6).
rubble = []
for i, (dy, dz) in enumerate([(y, z) for z in range(0, 350, 70) for y in range(-200, 200, 80)]):
    rubble.append(box(f"Rubble_{i:02d}", 2880 + (i % 3) * 8, 2960 - (i % 2) * 10,
                      dy, dy + 80, dz, dz + 70, "rubble", "Mine/Tunnel/Rubble"))

# Thin floor stripes so each zone is easy to tell apart on screen.
for name, x0, x1, hw, h in SEGMENTS:
    box(f"{name}_Marker", x0 + 20, x0 + 60, -hw + 20, hw - 20, 0, 1, "marker", f"Mine/{name}")

# Player start at the entrance, facing down the mine (+X).
ps = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(250, 0, 100),
                                unreal.Rotator(pitch=0, yaw=0, roll=0))
ps.set_actor_label("PlayerStart")

# Lights: a warm work lamp every ~5 m along the ceiling, no shadows, so it's easy to see.
for i, x in enumerate(range(300, 4000, 500)):
    seg = next(s for s in SEGMENTS if s[1] <= x < s[2])
    l = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, 0, seg[4] - 40))
    l.set_actor_label(f"Lamp_{i:02d}")
    l.set_folder_path("Mine/Lights")
    lc = l.point_light_component
    lc.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    lc.set_editor_property("intensity", 22.0)
    lc.set_editor_property("attenuation_radius", 1400.0)
    lc.set_editor_property("light_color", unreal.Color(255, 226, 190, 255))
    lc.set_editor_property("cast_shadows", False)

# Fixed exposure so the mine never adapts to black.
ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(2000, 0, 200))
ppv.set_actor_label("PP_Mine")
ppv.set_editor_property("unbound", True)
st = ppv.settings
st.set_editor_property("override_auto_exposure_method", True)
st.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
st.set_editor_property("override_auto_exposure_bias", True)
st.set_editor_property("auto_exposure_bias", 0.0)
st.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
st.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
ppv.set_editor_property("settings", st)  # settings is a copy; write it back

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
f"L_Mine built: {len(eas.get_all_level_actors())} actors"
