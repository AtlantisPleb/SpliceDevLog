"""Shared editor-side helpers for the Splice build scripts.

PRELUDE is Python source that runs inside the editor (prepend it to a script sent with
uemcp.py). It gives:
- cel(rgb), glow(rgb, strength): material instances of M_Cel / M_Glow for a display-space
  colour (0..1 sRGB, the same numbers the Aethyr world uses), created on first use;
- A(x, y, z): a point in Aethyr coordinates (metres; x right, y up, z back) as a UE vector
  (cm; X forward = -z, Y right = x, Z up = y);
- kit pieces that spawn static mesh actors from Aethyr-style calls: block, box, tube,
  ball, ellipsoid, limb.
"""

PRELUDE = r'''
import math
MAT_DIR = "/Game/Splice/Materials"
INST_DIR = "/Game/Splice/Materials/Inst"
_tools = unreal.AssetToolsHelpers.get_asset_tools()
_reg = unreal.AssetRegistryHelpers.get_asset_registry()
_mel = unreal.MaterialEditingLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

def to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

_inst = {}
def _instance(prefix, parent, rgb, strength=None):
    r, g, b = [max(0.0, min(1.0, v)) for v in rgb]
    name = "%s_%02X%02X%02X" % (prefix, round(r * 255), round(g * 255), round(b * 255))
    if strength is not None:
        name += "_%d" % round(strength * 10)
    if name in _inst:
        return _inst[name]
    path = f"{INST_DIR}/{name}"
    if _reg.get_assets_by_package_name(path):
        mi = unreal.load_asset(path)
    else:
        mi = _tools.create_asset(name, INST_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    _mel.set_material_instance_parent(mi, unreal.load_asset(f"{MAT_DIR}/{parent}"))
    _mel.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(to_lin(r), to_lin(g), to_lin(b), 1.0))
    if strength is not None:
        _mel.set_material_instance_scalar_parameter_value(mi, "Strength", strength)
    unreal.EditorAssetLibrary.save_asset(path)
    _inst[name] = mi
    return mi

def cel(rgb):
    return _instance("C", "M_Cel", rgb)
def glow(rgb, strength=2.2):
    return _instance("G", "M_Glow", rgb, strength)
def named(name):
    return unreal.load_asset(f"{MAT_DIR}/{name}")

SHAPES = {n: unreal.load_asset("/Engine/BasicShapes/" + n) for n in ("Cube", "Cylinder", "Sphere", "Cone", "Plane")}
for _n in ("Mesa", "Cloak", "Hat", "Drill", "Cyl14", "Cyl8", "Taper", "Rock", "Dune", "Ball"):
    SHAPES[_n] = unreal.load_asset("/Game/Splice/Meshes/SM_" + _n)

def A(x, y, z):
    return unreal.Vector(-z * 100.0, x * 100.0, y * 100.0)
def ayaw(yaw):
    """Aethyr yaw (radians, 0 faces +z, turning toward +x) as UE yaw in degrees."""
    return 180.0 - math.degrees(yaw)

N_ACT = [0]
FOLDER = ["World"]
def _spawn(shape, m, loc, rot, scale, label, collide):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
    smc = a.static_mesh_component
    smc.set_static_mesh(SHAPES[shape])
    smc.set_material(0, m)
    smc.set_collision_profile_name("BlockAll" if collide else "NoCollision")
    smc.set_editor_property("cast_shadow", False)
    a.set_actor_scale3d(scale)
    N_ACT[0] += 1
    a.set_actor_label(f"W_{label}_{N_ACT[0]}")
    a.set_folder_path(FOLDER[0])
    return a

R0 = unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0)
def block(m, cx, y0, cz, hx, h, hz, label="block", collide=True):
    """An upright box: centre (cx, cz), base at y0, half sizes hx and hz, height h (metres)."""
    return _spawn("Cube", m, A(cx, y0 + h / 2, cz), R0, unreal.Vector(hz * 2, hx * 2, h), label, collide)
def box(m, x, y, z, hx, hy, hz, yaw=0.0, label="box", collide=False):
    """A box centred at (x, y, z) with half sizes, turned by an Aethyr yaw."""
    return _spawn("Cube", m, A(x, y, z), unreal.Rotator(pitch=0.0, yaw=ayaw(yaw), roll=0.0),
                  unreal.Vector(hz * 2, hx * 2, hy * 2), label, collide)
def tube(m, x, y, z, h, r, shape="Cyl8", rz=None, label="tube", collide=False):
    """An upright tube from its base: height h, radius r (rz for an oval)."""
    return _spawn(shape, m, A(x, y, z), R0, unreal.Vector((rz or r) * 2, r * 2, h), label, collide)
def ball(m, x, y, z, r, label="ball", shape="Ball"):
    return _spawn(shape, m, A(x, y, z), R0, unreal.Vector(r * 2, r * 2, r * 2), label, False)
def ellipsoid(m, x, y, z, rx, ry, rz, yaw=0.0, shape="Rock", label="rock", collide=False):
    return _spawn(shape, m, A(x, y, z), unreal.Rotator(pitch=0.0, yaw=math.degrees(yaw), roll=0.0),
                  unreal.Vector(rz * 2, rx * 2, ry * 2), label, collide)
def limb(m, a, b, r, shape="Cyl8", label="limb"):
    """A tube from point a to point b (Aethyr coordinates), radius r."""
    va, vb = A(*a), A(*b)
    d = vb - va
    length = d.length()
    rot = unreal.MathLibrary.make_rot_from_z(d)
    return _spawn(shape, m, va, rot, unreal.Vector(r * 2, r * 2, length / 100.0), label, False)

def kit_rand(k):
    v = math.sin(k * 127.1 + 311.7) * 43758.5453
    return v - math.floor(v)

async def stop_pie():
    for _ in range(20):
        if not les.is_in_play_in_editor():
            break
        les.editor_request_end_play()
        await asyncio.sleep(0.5)
'''
