"""Splice kits: the parts of every character, vehicle and prop Blueprint.

The part lists are the Aethyr world's kits (aethyr/kit/machines.coax, land.coax), the same
sizes and colours, built from static mesh components. Kit coordinates are Aethyr's local
frame in metres (x right, y up, z forward); a component's place is UE local centimetres
(X forward, Y right, Z up). Every actor's origin is on the ground, except the player,
whose origin is the capsule centre.

Run after splice_slice_assets.py and splice_meshes.py.
Usage: python3 tools/ue/splice_kits.py
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from splice_common import PRELUDE  # noqa: E402
from uemcp import py  # noqa: E402

PAPER, INK, HEAT, GLOW, GLOW_INK = (0.918, 0.859, 0.769), (0.118, 0.106, 0.094), (0.722, 0.263, 0.122), (0.310, 0.702, 0.851), (0.122, 0.373, 0.502)
CREAM, AMBER, PINK, CYAN = (0.93, 0.88, 0.76), (1.0, 0.72, 0.30), (1.0, 0.36, 0.62), (0.36, 0.86, 0.96)
PLAYER_BP = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter"


def cel(c):
    return ("cel", c)


def glow(c, k=2.2):
    return ("glow", c, k)


class Kit:
    """Collects parts. s scales the kit; lift raises it (cm), for the player's capsule."""

    def __init__(self, s=1.0, lift=0.0):
        self.s, self.lift, self.parts = s, lift, []

    def p(self, x, y, z):
        s = self.s
        return (z * s * 100, x * s * 100, y * s * 100 + self.lift)

    def add(self, name, shape, mat, loc, scale, parent=None, direction=None, collide="NoCollision", rot=None):
        self.parts.append(dict(name=name, shape=shape, mat=mat, loc=loc, scale=scale, parent=parent,
                               dir=direction, collide=collide, rot=rot))

    def group(self, name):
        self.parts.append(dict(name=name, shape="SCENE", mat=None, loc=(0, 0, 0), scale=(1, 1, 1), parent=None,
                               dir=None, collide=None, rot=None))

    def box(self, name, mat, x, y, z, hx, hy, hz, **kw):
        s = self.s
        self.add(name, "Cube", mat, self.p(x, y, z), (hz * 2 * s, hx * 2 * s, hy * 2 * s), **kw)

    def tube(self, name, mat, x, y, z, h, r, shape="Cyl8", rz=None, **kw):
        s = self.s
        self.add(name, shape, mat, self.p(x, y, z), ((rz or r) * 2 * s, r * 2 * s, h * s), **kw)

    def ball(self, name, mat, x, y, z, r, shape="Ball", **kw):
        s = self.s
        self.add(name, shape, mat, self.p(x, y, z), (r * 2 * s,) * 3, **kw)

    def egg(self, name, mat, x, y, z, rx, ry, rz, **kw):
        s = self.s
        self.add(name, "Ball", mat, self.p(x, y, z), (rz * 2 * s, rx * 2 * s, ry * 2 * s), **kw)

    def limb(self, name, mat, a, b, r, shape="Cyl8", **kw):
        s = self.s
        pa, pb = self.p(*a), self.p(*b)
        d = tuple(pb[i] - pa[i] for i in range(3))
        length = sum(v * v for v in d) ** 0.5
        self.add(name, shape, mat, pa, (r * 2 * s, r * 2 * s, length / 100.0), direction=d, **kw)

    def shadow(self, r):
        self.add("Shadow", "Plane", ("named", "M_Shadow"), (0, 0, 3 + self.lift), (r * 2 * self.s, r * 2 * self.s, 1))


def figure(k, cloak, skin, dark, hat, eye=None):
    """kit_figure: a cloaked figure with a pack and a wide hat."""
    k.tube("LegL", cel(dark), -0.16, 0.05, 0, 0.8, 0.10)
    k.tube("LegR", cel(dark), 0.16, 0.05, 0, 0.8, 0.10)
    k.box("Pack", cel(dark), 0, 1.15, -0.3, 0.22, 0.26, 0.12)
    k.tube("Body", cel(cloak), 0, 0.7, 0, 0.85, 0.46, shape="Cloak", rz=0.36)
    k.ball("Head", cel(skin), 0, 1.66, 0, 0.17)
    k.tube("Hat", cel(hat), 0, 1.76, 0, 0.16, 0.40, shape="Hat")
    if eye:
        k.box("Eye", eye, 0, 1.9 / 1.15, 0.19 / 1.15, 0.12 / 1.15, 0.03 / 1.15, 0.02 / 1.15)
    k.shadow(0.55)


def robot(k, body, band, eye, dark):
    """kit_robot: the boxy Imperial robot, 3.3 m at scale 1."""
    k.box("LegL", cel(dark), -0.28, 0.42, 0, 0.14, 0.42, 0.14)
    k.box("LegR", cel(dark), 0.28, 0.42, 0, 0.14, 0.42, 0.14)
    k.box("Hips", cel(dark), 0, 1.02, 0, 0.42, 0.14, 0.32)
    k.box("FootL", cel(body), -0.28, 0.07, 0.06, 0.20, 0.07, 0.26)
    k.box("FootR", cel(body), 0.28, 0.07, 0.06, 0.20, 0.07, 0.26)
    k.box("Body", cel(body), 0, 1.55, 0, 0.50, 0.45, 0.36)
    k.box("Head", cel(body), 0, 2.30, 0, 0.36, 0.30, 0.32)
    k.box("Band", glow(band, 1.0), 0, 1.2, 0, 0.52, 0.07, 0.37)
    k.ball("AntennaTip", glow(band, 1.0), 0.14, 3.2, 0, 0.08)
    k.box("Visor", cel(dark), 0, 2.33, 0.33, 0.28, 0.10, 0.02)
    k.tube("Antenna", cel(dark), 0.14, 2.62, 0, 0.55, 0.03)
    k.ball("Chest", eye, 0, 1.6, 0.42, 0.11)
    k.box("Eye", eye, 0, 2.33, 0.345, 0.20, 0.03, 0.012)
    k.limb("ArmL", cel(body), (-0.62, 1.9, 0), (-0.80, 1.22, 0.10), 0.10)
    k.limb("ArmR", cel(body), (0.62, 1.9, 0), (0.80, 1.0, 0.10), 0.10)
    k.ball("HandR", cel(body), 0.80, 1.0, 0.10, 0.14)
    k.shadow(0.8)


def rover(k, body=CREAM, cab=(0.76, 0.34, 0.20), wheel=INK, hull_name="Body", collide="NoCollision"):
    """kit_rover with the roof crate the game adds."""
    k.box(hull_name, cel(body), 0, 0.9, 0, 0.85, 0.4, 1.6, collide=collide)
    k.box("Cab", glow(cab, 1.0), 0, 1.55, 0.7, 0.7, 0.3, 0.6)
    for i in range(4):
        sx = -1.0 if i % 2 == 0 else 1.0
        sz = -1.1 if i < 2 else 1.1
        k.limb(f"Wheel{i}", cel(wheel), (sx * 0.8, 0.45, sz), (sx * 1.1, 0.45, sz), 0.45, shape="Cyl14")
    k.tube("Mast", cel(wheel), -0.5, 1.3, -1.2, 1.2, 0.04)
    # the game's roof crate: box(kit_at(f, 0, 2.9, -0.9), 1.1, 0.5, 1.3) at rover scale 1.5
    s = k.s
    k.box("RoofCrate", cel((0.70, 0.52, 0.36)), 0, 2.9 / s, -0.9 / s, 1.1 / s, 0.5 / s, 1.3 / s)
    k.add("Shadow", "Plane", ("named", "M_Shadow"), (60, 60, 3), (5.5, 4.2, 1))


def digger(k, body=CREAM, dark=INK, accent=HEAT, light=AMBER):
    """kit_digger: body, head and visor; treads, drill arm and battery are groups to show or hide."""
    for g in ("ArmGroup", "TreadsGroup", "BatteryGroup", "BlocksGroup"):
        k.group(g)
    k.box("Body", cel(body), 0, 0.95, 0, 0.62, 0.42, 0.8)
    k.box("Head", cel(body), 0, 1.52, 0.25, 0.4, 0.2, 0.4)
    k.box("Visor", cel(dark), 0, 1.55, 0.66, 0.3, 0.09, 0.02)
    for side, sx in (("L", -1.0), ("R", 1.0)):
        k.box(f"Tread{side}", cel(dark), sx * 0.8, 0.3, 0, 0.2, 0.3, 1.0, parent="TreadsGroup")
        k.limb(f"TreadF{side}", cel(dark), (sx * 0.6, 0.3, 0.95), (sx * 1.0, 0.3, 0.95), 0.3, shape="Cyl14", parent="TreadsGroup")
        k.limb(f"TreadB{side}", cel(dark), (sx * 0.6, 0.3, -0.95), (sx * 1.0, 0.3, -0.95), 0.3, shape="Cyl14", parent="TreadsGroup")
    k.box("Blocks", cel(dark), 0, 0.3, 0, 0.5, 0.25, 0.6, parent="BlocksGroup")
    k.limb("Arm", glow(accent, 1.0), (0, 1.0, 0.7), (0, 0.95, 1.35), 0.22, parent="ArmGroup")
    k.limb("Drill", cel(body), (0, 0.95, 1.35), (0, 0.9, 2.3), 0.34, shape="Drill", parent="ArmGroup")
    k.box("Battery", glow(light), 0, 1.25, -0.55, 0.34, 0.3, 0.2, parent="BatteryGroup")
    k.box("EyeStrip", glow(light), 0, 1.55, 0.675, 0.2, 0.03, 0.012, parent="BatteryGroup")
    k.shadow(1.3)


def mech(k, shell=(0.22, 0.34, 0.56), accent=GLOW, dark=(0.12, 0.14, 0.24), lens=GLOW):
    """kit_mech: the banned bot. Its arm hangs from a pivot the Blueprint turns."""
    k.egg("Body", cel(shell), 0, 3.0, 0, 1.3, 1.5, 1.15)
    k.ball("ShoulderL", cel(shell), -1.35, 2.9, 0, 0.55)
    k.ball("ShoulderR", cel(shell), 1.35, 2.9, 0, 0.55)
    k.limb("ArmL", cel(shell), (-1.5, 2.7, 0), (-1.8, 0.9, 0.3), 0.42)
    k.limb("ArmR", cel(shell), (1.5, 2.7, 0), (1.8, 0.9, 0.3), 0.42)
    k.box("FistL", cel(shell), -1.8, 0.45, 0.35, 0.5, 0.45, 0.6)
    k.box("FistR", cel(shell), 1.8, 0.45, 0.35, 0.5, 0.45, 0.6)
    k.limb("LegL", cel(dark), (-0.6, 1.7, 0), (-0.7, 0.2, 0.1), 0.40)
    k.limb("LegR", cel(dark), (0.6, 1.7, 0), (0.7, 0.2, 0.1), 0.40)
    k.box("Head", cel(dark), 0, 3.7, 1.0, 0.75, 0.32, 0.12)
    k.box("Band", glow(accent, 1.6), -1.0, 2.2, 0.85, 0.18, 0.35, 0.05)
    k.box("Band2", glow(accent, 1.6), 1.0, 2.2, 0.85, 0.18, 0.35, 0.05)
    k.box("Knuckle1", glow(accent, 1.6), -1.8, 0.75, 0.97, 0.3, 0.06, 0.03)
    k.box("Knuckle2", glow(accent, 1.6), 1.8, 0.75, 0.97, 0.3, 0.06, 0.03)
    k.ball("Eye", glow(lens), 0.3, 3.7, 1.12, 0.13)
    k.add("Shadow", "Plane", ("named", "M_Shadow"), (0, 0, 3), (7, 7, 1))


def crate(k, wood, band, light, w, collide="NoCollision"):
    """kit_crate."""
    k.box("Box", cel(wood), 0, w * 0.4, 0, w * 0.6, w * 0.4, w * 0.45, collide=collide)
    k.box("BandL", cel(band), -w * 0.35, w * 0.4, 0, w * 0.06, w * 0.42, w * 0.47)
    k.box("BandR", cel(band), w * 0.35, w * 0.4, 0, w * 0.06, w * 0.42, w * 0.47)
    k.box("Lid", glow(light), 0, w * 0.82, 0, w * 0.12, w * 0.03, w * 0.12)


KITS = {}

# The player: an orange cylinder with a cream cap and an ink visor band (Aethyr g_live).
k = Kit(lift=-90.0)
k.tube("CylBody", cel((0.76, 0.34, 0.20)), 0, 0, 0, 1.6, 0.42, shape="Cyl14")
k.box("CylVisor", cel(INK), 0, 1.25, 0.36, 0.3, 0.1, 0.08)
k.tube("CylHead", cel((0.93, 0.86, 0.70)), 0, 1.6, 0, 0.08, 0.46, shape="Cyl14")
k.shadow(0.6)
KITS[PLAYER_BP] = (k.parts, ["CylPack"])

# Raider: dark cloak and hat, a pink visor that the Blueprint turns red in a fight.
k = Kit(1.15)
figure(k, (0.16, 0.12, 0.18), (0.16, 0.12, 0.18), (0.10, 0.08, 0.12), (0.30, 0.14, 0.20), eye=glow(PINK))
KITS["BP_Raider"] = (k.parts, [])

# Imperial robot: white plates, an orange band, a pale eye that turns red once it has seen you.
k = Kit(0.8)
robot(k, (0.92, 0.93, 0.96), HEAT, glow((0.95, 0.95, 1.0), 1.4), (0.20, 0.20, 0.28))
KITS["BP_Imperial"] = (k.parts, [])

k = Kit(0.85)
digger(k)
KITS["BP_Bot"] = (k.parts, ["Front"])

# The banned bot. Arm pivot at the top of the body; the Blueprint yaws it to sweep.
km = Kit(1.25)
mech(km)
parts = km.parts
parts.append(dict(name="ArmPivot", shape="SCENE", mat=None, loc=(0, 0, 340), scale=(1, 1, 1), parent=None, dir=None, collide=None, rot=None))
parts.append(dict(name="SweepArm", shape="Cyl8", mat=cel((0.22, 0.34, 0.56)), loc=(0, 0, 0), scale=(1.0, 1.0, 6.6), parent="ArmPivot",
                  dir=(620, 0, -230), collide="NoCollision", rot=None))
parts.append(dict(name="ArmFist", shape="Ball", mat=cel((0.22, 0.34, 0.56)), loc=(620, 0, -230), scale=(1.2, 1.2, 1.2), parent="ArmPivot",
                  dir=None, collide="NoCollision", rot=None))
import math  # noqa: E402
for i, a in enumerate((0.0, 2.2, -2.2)):
    parts.append(dict(name=f"WP{i + 1}", shape="Ball", mat=glow(GLOW), loc=(math.cos(a) * 270, math.sin(a) * 270, 150),
                      scale=(0.72, 0.72, 0.72), parent=None, dir=None, collide="NoCollision", rot=None))
KITS["BP_Boss"] = (parts, ["Arm"])

k = Kit(1.5)
rover(k, collide="BlockAll")
KITS["BP_Rover"] = (k.parts, ["Bay"])
k = Kit(1.5)
rover(k)
KITS["BP_RailRover"] = (k.parts, [])

k = Kit()
crate(k, (0.70, 0.52, 0.36), INK, GLOW, 1.5, collide="BlockAll")
KITS["BP_StashCrate"] = (k.parts, [])

k = Kit()
k.tube("Post", cel(CREAM), 0, 0, 0, 3.2, 0.12)
k.ball("Cap", glow(AMBER), 0, 3.4, 0, 0.3)
KITS["BP_Checkpoint"] = (k.parts, [])

# The boss wall: a slab (the actor's scale gives its size) with three blue seams on the near face.
parts = [dict(name="Wall", shape="Cube", mat=cel((0.34, 0.26, 0.40)), loc=(0, 0, 0), scale=(1, 1, 1), parent=None, dir=None,
              collide="BlockAll", rot=None)]
for i in range(3):
    parts.append(dict(name=f"Seam{i + 1}", shape="Cube", mat=glow(GLOW), loc=(-51, (-2.4 + 2.4 * i) / 8 * 100, ((2.2 + 1.6 * i) - 4.5) / 9 * 100),
                      scale=(0.02, 0.14 / 8, 4.8 / 9), parent=None, dir=None, collide="NoCollision", rot=None))
KITS["BP_BossWall"] = (parts, [])

# A light beam from the truss: wide at the floor (the actor's origin), a point at the lamp.
KITS["BP_Beam"] = ([dict(name="Mesh", shape="Drill", mat=glow(PINK, 1.6), loc=(0, 0, 0), scale=(0.6, 0.6, 6.0), parent=None,
                         dir=None, collide="NoCollision", rot=(-90.0, 0.0, 0.0))], [])

SRC = PRELUDE + r'''
KITS = __KITS__
PLAYER_BP = __PLAYER__
await stop_pie()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
out = []

def material(spec):
    if spec[0] == "cel":
        return cel(spec[1])
    if spec[0] == "glow":
        return glow(spec[1], spec[2])
    return named(spec[1])

for bpn, (parts, drop) in KITS.items():
    path = bpn if bpn.startswith("/") else "/Game/Splice/Blueprints/" + bpn
    bp = unreal.load_asset(path)
    def gather():
        hs = sds.k2_gather_subobject_data_for_blueprint(bp)
        byname = {}
        for h in hs:
            o = lib.get_object(lib.get_data(h))
            if o:
                byname[o.get_name().replace("_GEN_VARIABLE", "")] = (h, o)
        return hs, byname
    hs, byname = gather()
    root = hs[0]
    for p in parts:
        name = p["name"]
        if name in byname:
            h, comp = byname[name]
        else:
            ccls = unreal.SceneComponent if p["shape"] == "SCENE" else unreal.StaticMeshComponent
            parent_h = byname[p["parent"]][0] if p["parent"] else root
            params = unreal.AddNewSubobjectParams(parent_handle=parent_h, new_class=ccls, blueprint_context=bp)
            h, fail = sds.add_new_subobject(params)
            sds.rename_subobject(h, name)
            comp = lib.get_object(lib.get_data(h))
            byname[name] = (h, comp)
        comp.set_editor_property("relative_location", unreal.Vector(*p["loc"]))
        if p["shape"] == "SCENE":
            continue
        rot = unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0)
        if p["dir"]:
            rot = unreal.MathLibrary.make_rot_from_z(unreal.Vector(*p["dir"]))
        elif p["rot"]:
            rot = unreal.Rotator(pitch=p["rot"][0], yaw=p["rot"][1], roll=p["rot"][2])
        comp.set_editor_property("relative_rotation", rot)
        comp.set_editor_property("relative_scale3d", unreal.Vector(*p["scale"]))
        comp.set_editor_property("static_mesh", SHAPES[p["shape"]])
        comp.set_editor_property("override_materials", [material(p["mat"])])
        comp.set_collision_profile_name(p["collide"])
        comp.set_editor_property("generate_overlap_events", False)
        comp.set_editor_property("cast_shadow", False)
        comp.set_editor_property("hidden_in_game", False)
        comp.set_editor_property("visible", True)
    # Parts the kit no longer has: shrink and hide them (deleting can break graph references).
    for name in drop:
        if name in byname:
            comp = byname[name][1]
            comp.set_editor_property("relative_scale3d", unreal.Vector(0.001, 0.001, 0.001))
            comp.set_editor_property("hidden_in_game", True)
            comp.set_editor_property("visible", False)
            comp.set_collision_profile_name("NoCollision")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(path)
    out.append(f"{bpn.rsplit('/', 1)[-1]}: {len(parts)} parts")

# The player's camera: Aethyr's chase view. 6.5 m behind and about 4 m up, aimed 3 m ahead.
pbp = unreal.load_asset(PLAYER_BP)
for h in sds.k2_gather_subobject_data_for_blueprint(pbp):
    o = lib.get_object(lib.get_data(h))
    if isinstance(o, unreal.SpringArmComponent):
        o.set_editor_property("target_arm_length", 670.0)
        o.set_editor_property("relative_location", unreal.Vector(0, 0, 140))
        o.set_editor_property("probe_size", 14.0)
        o.set_editor_property("enable_camera_lag", True)
        o.set_editor_property("camera_lag_speed", 12.0)
    elif isinstance(o, unreal.CameraComponent):
        o.set_editor_property("field_of_view", 70.0)
    elif isinstance(o, unreal.CharacterMovementComponent):
        o.set_editor_property("max_walk_speed", 560.0)
    elif isinstance(o, unreal.CapsuleComponent):
        o.set_editor_property("capsule_radius", 42.0)
unreal.BlueprintEditorLibrary.compile_blueprint(pbp)
unreal.EditorAssetLibrary.save_asset(PLAYER_BP)
"\n".join(out)
'''

if __name__ == "__main__":
    print(py(SRC.replace("__KITS__", repr(KITS)).replace("__PLAYER__", repr(PLAYER_BP))))
