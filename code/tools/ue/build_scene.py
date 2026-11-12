"""Build the Mars robot level in the Rovers project (UE 5.9 editor Python)."""
import math
import random
import unreal

LEVEL_PATH = "/Game/Mars/L_MarsRobot"
MAT_DIR = "/Game/Mars/Materials"
SHOT_DIR = "/Users/christopherdavid/games/cakbag/Rovers/Shots"

random.seed(7)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def make_material(name, rgb, unlit=False):
    """Lit material with a constant base colour, no specular sheen, fully rough.
    The post-process reads this albedo back as the flat colour. Unlit is for the sky."""
    path = f"{MAT_DIR}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = asset_tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    col.constant = unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0)
    if unlit:
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        mat.set_editor_property("two_sided", True)
        mel.connect_material_property(col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    else:
        mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
        spec = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 200)
        spec.set_editor_property("r", 0.0)
        mel.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)
        rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 300)
        rough.set_editor_property("r", 1.0)
        mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.layout_material_expressions(mat)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    return mat


MATS = {
    "ground": make_material("M_Ground", (0.82, 0.42, 0.28)),
    "rock": make_material("M_Rock", (0.52, 0.24, 0.20)),
    "mountain": make_material("M_Mountain", (0.72, 0.52, 0.58)),
    "sky": make_material("M_Sky", (0.98, 0.62, 0.48), unlit=True),
    "cream": make_material("M_Cream", (0.96, 0.90, 0.78)),
    "teal": make_material("M_Teal", (0.20, 0.58, 0.66)),
    "visor": make_material("M_Visor", (0.08, 0.14, 0.20)),
    "red": make_material("M_Red", (0.90, 0.26, 0.20)),
    "dark": make_material("M_Dark", (0.16, 0.12, 0.12)),
}

CUBE = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
SPHERE = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere")
CYLINDER = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")
CONE = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cone")


def spawn(mesh, mat, loc, rot=(0, 0, 0), scale=(1, 1, 1), label=None, parent=None):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator(*rot))
    a.static_mesh_component.set_static_mesh(mesh)
    a.static_mesh_component.set_material(0, MATS[mat])
    a.set_actor_scale3d(unreal.Vector(*scale))
    if label:
        a.set_actor_label(label)
    if parent:
        a.attach_to_actor(parent, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, False)
    return a


def build():
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        unreal.EditorAssetLibrary.delete_asset(LEVEL_PATH)
    les.new_level(LEVEL_PATH)

    # Ground: a thick slab with a few dunes, and a far mountain ridge.
    ground = spawn(CUBE, "ground", (0, 0, -50), scale=(440, 440, 1), label="Ground")
    ground.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    # Sky dome: a big unlit sphere around everything. No collision, no shadow.
    sky_dome = spawn(SPHERE, "sky", (0, 0, 0), scale=(400, 400, 400), label="SkyDome")
    sky_dome.static_mesh_component.set_collision_profile_name("NoCollision")
    sky_dome.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    sky_dome.static_mesh_component.set_cast_shadow(False)
    for i in range(14):
        x = random.uniform(-3000, 3000)
        y = random.uniform(-3000, 3000)
        if abs(x) < 900 and abs(y) < 900:
            continue
        spawn(SPHERE, "ground", (x, y, -120), scale=(random.uniform(8, 16), random.uniform(8, 16), 2.2),
              label=f"Dune_{i}")
    for i in range(3):
        spawn(CONE, "mountain", (-2600 + i * 1100, 3200, 600), scale=(14, 14, 10), label=f"Mountain_{i}")

    # Rocks around the robot, kept off the centre.
    for i in range(18):
        ang = random.uniform(0, math.tau)
        dist = random.uniform(380, 1400)
        x, y = math.cos(ang) * dist, math.sin(ang) * dist
        s = random.uniform(0.6, 2.0)
        spawn(SPHERE, "rock", (x, y, 20 * s), rot=(random.uniform(0, 90), random.uniform(0, 90), 0),
              scale=(s * 1.3, s, s * 0.8), label=f"Rock_{i}")

    # The robot. Root is at the origin; the body is built from primitives.
    root = spawn(CUBE, "dark", (0, 0, 0), scale=(0.01, 0.01, 0.01), label="Robot_Root")
    for side in (-1, 1):
        spawn(CYLINDER, "dark", (0, side * 52, 36), rot=(90, 0, 0), scale=(0.72, 0.72, 0.22),
              label=f"Wheel_{side}", parent=root)
    spawn(CUBE, "red", (0, 0, 60), scale=(1.1, 0.85, 0.42), label="Chassis", parent=root)
    spawn(CYLINDER, "cream", (0, 0, 150), scale=(1.5, 1.5, 1.7), label="Body", parent=root)
    spawn(CYLINDER, "red", (0, 0, 60), scale=(1.56, 1.56, 0.12), label="Body_Band", parent=root)
    spawn(SPHERE, "teal", (0, 0, 255), scale=(1.45, 1.25, 1.12), label="Head", parent=root)
    spawn(CUBE, "visor", (0, -90, 258), scale=(1.3, 0.12, 0.6), label="Visor", parent=root)
    spawn(CYLINDER, "cream", (0, 0, 305), scale=(0.08, 0.08, 1.0), label="Antenna", parent=root)
    spawn(SPHERE, "red", (0, 0, 395), scale=(0.22, 0.22, 0.22), label="Antenna_Tip", parent=root)
    spawn(SPHERE, "teal", (0, -80, 165), scale=(0.42, 0.22, 0.42), label="Chest_Light", parent=root)
    # Left arm hangs down; right arm is raised in a wave.
    spawn(CYLINDER, "cream", (-120, 0, 160), rot=(0, 0, 28), scale=(0.22, 0.22, 1.25), label="Arm_L", parent=root)
    spawn(SPHERE, "cream", (-182, 0, 80), scale=(0.3, 0.3, 0.3), label="Hand_L", parent=root)
    spawn(CYLINDER, "cream", (120, 0, 190), rot=(0, 0, -62), scale=(0.22, 0.22, 1.2), label="Arm_R", parent=root)
    spawn(SPHERE, "cream", (190, 0, 290), scale=(0.3, 0.3, 0.3), label="Hand_R", parent=root)

    # Player start beside the robot, on the ground (ground top is z=0).
    ps = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(-900, -900, 150), unreal.Rotator(pitch=0, yaw=45, roll=0))
    ps.set_actor_label("PlayerStart")

    # Lights: one sun lighting the robot's front. Note unreal.Rotator's positional
    # order is (roll, pitch, yaw), so always pass keywords. Sky light kept low.
    sun = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 800), unreal.Rotator(pitch=-40, yaw=45, roll=0))
    sun.set_actor_label("Sun")
    # With fixed exposure (EV100 0, below), ~3.5 lux on a sun-facing surface
    # renders at about its albedo. That keeps the post-process shading ratio near 1.
    sun.light_component.set_editor_property("intensity", 3.5)
    sun.light_component.set_editor_property("light_color", unreal.Color(255, 244, 230, 255))
    sky = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 500), unreal.Rotator(0, 0, 0))
    sky.set_actor_label("SkyLight")
    sky.light_component.set_editor_property("intensity", 0.6)

    # Post-process volume, unbound, with the look settings below.
    ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    ppv.set_actor_label("PP_Moebius")
    ppv.set_editor_property("unbound", True)
    s = ppv.settings
    s.set_editor_property("override_auto_exposure_method", True)
    # Fixed manual exposure: no adaptation, so colours stay put.
    s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    s.set_editor_property("override_auto_exposure_bias", True)
    s.set_editor_property("auto_exposure_bias", 0.0)
    try:
        s.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
        s.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
    except Exception as e:  # property name differs between versions
        unreal.log_warning(f"MARS_BUILD: physical camera exposure not set: {e}")
    # Lumen off for this look: it made the scene near-black.
    s.set_editor_property("override_dynamic_global_illumination_method", True)
    s.set_editor_property("dynamic_global_illumination_method", unreal.DynamicGlobalIlluminationMethod.NONE)
    s.set_editor_property("override_reflection_method", True)
    s.set_editor_property("reflection_method", unreal.ReflectionMethod.NONE)
    s.set_editor_property("override_bloom_intensity", True)
    s.set_editor_property("bloom_intensity", 0.0)
    s.set_editor_property("override_ambient_occlusion_intensity", True)
    s.set_editor_property("ambient_occlusion_intensity", 0.0)
    s.set_editor_property("override_vignette_intensity", True)
    s.set_editor_property("vignette_intensity", 0.0)
    s.set_editor_property("override_motion_blur_amount", True)
    s.set_editor_property("motion_blur_amount", 0.0)

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("MARS_BUILD: level built")


if __name__ == "__main__":
    build()
