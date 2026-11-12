"""Splice UI fonts: import Michroma and IBM Plex Mono (both SIL Open Font License) and
wrap them in Font assets that UMG can use.

The .ttf files and their licences are in Rovers/SourceArt/Fonts. A FontFace on its own
can't be used as a widget font, and the composite-font structs aren't exposed to editor
Python, so the Font assets are filled in with import_text.
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from uemcp import py  # noqa: E402

print(py(r'''
out = []
tools = unreal.AssetToolsHelpers.get_asset_tools()
reg = unreal.AssetRegistryHelpers.get_asset_registry()
D = "/Game/Splice/UI/Fonts"
SRC = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "SourceArt/Fonts/"
for f in ["Michroma-Regular", "IBMPlexMono-Regular", "IBMPlexMono-SemiBold"]:
    if not reg.get_assets_by_package_name(f"{D}/{f}"):
        t = unreal.AssetImportTask()
        t.filename = SRC + f + ".ttf"
        t.destination_path = D
        t.automated = True
        t.save = True
        tools.import_asset_tasks([t])

def entry(tname, face):
    return f"(Name=\"{tname}\",Font=(FontFaceAsset=\"/Script/Engine.FontFace'{D}/{face}.{face}'\"))"

FONTS = {"F_Michroma": [("Regular", "Michroma-Regular")],
         "F_PlexMono": [("Regular", "IBMPlexMono-Regular"), ("Bold", "IBMPlexMono-SemiBold")]}
for name, faces in FONTS.items():
    path = f"{D}/{name}"
    if reg.get_assets_by_package_name(path):
        font = unreal.load_asset(path)
    else:
        font = tools.create_asset(name, D, unreal.Font, unreal.FontFactory())
    font.set_editor_property("font_cache_type", unreal.FontCacheType.RUNTIME)
    cf = unreal.CompositeFont()
    cf.import_text("(DefaultTypeface=(Fonts=(" + ",".join(entry(*f) for f in faces) + ")))")
    font.set_editor_property("composite_font", cf)
    unreal.EditorAssetLibrary.save_asset(path)
    out.append(name)
"fonts: " + ", ".join(out)
'''))
