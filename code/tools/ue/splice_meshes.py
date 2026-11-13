"""Splice kit meshes: low-poly, flat-shaded shapes the engine's basic shapes lack.

Writes OBJ files to Rovers/SourceArt/Meshes and imports them to /Game/Splice/Meshes.
Every mesh is 100 units across and 100 tall, like the engine's basic shapes.
- Frustums (pivot at the base): SM_Mesa, SM_Cloak, SM_Hat, SM_Drill, SM_Cyl14, SM_Cyl8, SM_Taper
- Facet balls (pivot at the centre): SM_Rock, SM_Dune, SM_Ball

Usage: python3 tools/ue/splice_meshes.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from uemcp import py  # noqa: E402

SRC = os.path.normpath(os.path.join(HERE, "..", "..", "Rovers", "SourceArt", "Meshes"))

# name -> (sides, top radius / base radius)
FRUSTUMS = {"SM_Mesa": (7, 0.33), "SM_Cloak": (10, 0.30), "SM_Hat": (12, 0.25), "SM_Drill": (6, 0.06),
            "SM_Cyl14": (14, 1.0), "SM_Cyl8": (8, 1.0), "SM_Taper": (8, 0.6)}
# name -> (segments round, rings)
BALLS = {"SM_Rock": (8, 5), "SM_Dune": (12, 6), "SM_Ball": (12, 7)}


def write_obj(name, faces):
    """faces: list of vertex lists (counter-clockwise seen from outside), Z up."""
    lines, n = ["o " + name], 1
    for f in faces:
        a, b, c = f[0], f[1], f[2]
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        nx, ny, nz = u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]
        l = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        for p in f:
            lines.append("v %.4f %.4f %.4f" % tuple(p))
        lines.append("vn %.5f %.5f %.5f" % (nx / l, ny / l, nz / l))
        k = (n - 1) // 1
        idx = " ".join("%d//%d" % (n + i, len([x for x in lines if x.startswith("vn")])) for i in range(len(f)))
        lines.append("f " + idx)
        n += len(f)
    with open(os.path.join(SRC, name + ".obj"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


def frustum(sides, top):
    faces = []
    ring = lambda r, z: [(r * math.cos(2 * math.pi * i / sides), r * math.sin(2 * math.pi * i / sides), z) for i in range(sides)]
    b, t = ring(50.0, 0.0), ring(50.0 * top, 100.0)
    for i in range(sides):
        j = (i + 1) % sides
        faces.append([b[i], b[j], t[j], t[i]])
    faces.append(list(reversed(b)))
    faces.append(t)
    return faces


def ball(seg, rings):
    faces = []
    def p(i, k):
        th = math.pi * k / rings
        ph = 2 * math.pi * i / seg
        return (50 * math.sin(th) * math.cos(ph), 50 * math.sin(th) * math.sin(ph), 50 * math.cos(th))
    for k in range(rings):
        for i in range(seg):
            j = (i + 1) % seg
            if k == 0:
                faces.append([p(0, 0), p(i, 1), p(j, 1)])
            elif k == rings - 1:
                faces.append([p(i, k), p(0, rings), p(j, k)])
            else:
                faces.append([p(i, k), p(i, k + 1), p(j, k + 1), p(j, k)])
    return faces


if __name__ == "__main__":
    os.makedirs(SRC, exist_ok=True)
    for name, (sides, top) in FRUSTUMS.items():
        write_obj(name, frustum(sides, top))
    for name, (seg, rings) in BALLS.items():
        write_obj(name, ball(seg, rings))
    names = list(FRUSTUMS) + list(BALLS)
    print(py("SRC = " + repr(SRC) + "\nNAMES = " + repr(names) + r'''
tools = unreal.AssetToolsHelpers.get_asset_tools()
tasks = []
for n in NAMES:
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", f"{SRC}/{n}.obj")
    t.set_editor_property("destination_path", "/Game/Splice/Meshes")
    t.set_editor_property("destination_name", n)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    tasks.append(t)
tools.import_asset_tasks(tasks)
out = []
for n in NAMES:
    m = unreal.load_asset(f"/Game/Splice/Meshes/{n}")
    if m is None:
        out.append(n + "=MISSING")
        continue
    # Collide with the real triangles: these shapes are simple enough.
    bs = m.get_editor_property("body_setup")
    if bs:
        bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    unreal.EditorAssetLibrary.save_asset(f"/Game/Splice/Meshes/{n}")
    b = m.get_bounding_box()
    out.append(f"{n}: min=({b.min.x:.0f},{b.min.y:.0f},{b.min.z:.0f}) max=({b.max.x:.0f},{b.max.y:.0f},{b.max.z:.0f})")
"\n".join(out)
'''))
