#!/bin/zsh
# Render a devlog screenshot from the open Unreal editor, at a fixed camera.
# The editor renders it itself (HighResShot), so it works even when the editor
# isn't the front window.
#
# Usage: tools/devlog/shot.sh ENTRY NAME X Y Z PITCH YAW [WxH]
#   tools/devlog/shot.sh 0001 hero 450 -800 190 -4 119
# Output: docs/devlog/media/ENTRY/NAME.png
# Needs: the editor open with its MCP server on 127.0.0.1:8000.
set -e
ROOT=${0:a:h:h:h}
ENTRY=$1 NAME=$2 X=$3 Y=$4 Z=$5 PITCH=$6 YAW=$7 RES=${8:-1920x1080}
OUT="$ROOT/docs/devlog/media/$ENTRY/$NAME.png"
mkdir -p "${OUT:h}"
TMP=$(mktemp -t devlogshot).py
cat > $TMP <<PY
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.set_level_viewport_camera_info(unreal.Vector($X, $Y, $Z), unreal.Rotator(pitch=$PITCH, yaw=$YAW, roll=0), "")
await asyncio.sleep(1.0)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(w, "HighResShot $RES filename=$OUT")
await asyncio.sleep(2.0)
"ok"
PY
"$ROOT/tools/ue/runpy.sh" $TMP >/dev/null
rm -f $TMP
[ -f "$OUT" ] && echo "$OUT" || { echo "no image written" >&2; exit 1; }
