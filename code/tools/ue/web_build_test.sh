#!/bin/zsh
# Build the Splice web build (Wasm), then run the scripted browser test on both
# renderer tiers. Screenshots land in OUT/deferred and OUT/forward.
#
# usage: tools/ue/web_build_test.sh OUT [--test-only] [FIXTURE]
# FIXTURE is a name from Rovers/Build/Wasm/fixtures.json (default: splice).
set -u
ROOT=${0:A:h:h:h}
ENGINE=${UE_ENGINE:-$HOME/UnrealEngine-5.9/src}
export WASM_EMSDK_ROOT=${WASM_EMSDK_ROOT:-$HOME/emsdk-ue}
OUT=${1:?usage: web_build_test.sh OUT [--test-only]}
STAGE=$ROOT/Rovers/Saved/WasmOut
LOG=$ROOT/Rovers/Saved/wasm-build.log
PY=$ENGINE/Engine/Binaries/ThirdParty/Python3/Mac/bin/python3
FIXTURE=splice
for a in "${@:2}"; do [[ $a != --test-only ]] && FIXTURE=$a; done
mkdir -p "$OUT"

if [[ ${2:-} != --test-only ]]; then
  (cd "$ENGINE" && ./Engine/Build/BatchFiles/RunUAT.sh BuildCookRun \
    -project="$ROOT/Rovers/Rovers.uproject" -platform=Wasm -clientconfig=Development \
    -build -cook -stage -pak -iostore -package -archive -archivedirectory="$STAGE" \
    -nocompileeditor -unattended -utf8output) > "$LOG" 2>&1
  code=$?
  grep -E "BuildCookRun time|BUILD SUCCESSFUL" "$LOG" | tail -2
  # A material that fails on a web tier is replaced by a flat fallback, so say so loudly.
  grep -E "Failed to compile Material" "$LOG" | sort -u | cut -c1-240
  if (( code != 0 )); then
    echo "BUILD FAILED (exit $code): see $LOG"
    exit $code
  fi
fi

fail=0
for tier in deferred forward; do
  (cd "$ENGINE/Engine/Platforms/Wasm/Build/Tools/web" && "$PY" webrun.py run \
    --stage "$STAGE" --project "$ROOT/Rovers/Rovers.uproject" \
    --fixtures "$ROOT/Rovers/Build/Wasm/fixtures.json" --fixture $FIXTURE \
    --query tier=$tier --out "$OUT/$tier") > "$OUT/$tier.log" 2>&1 || fail=1
  echo "$tier: $(tail -1 "$OUT/$tier.log" | cut -c1-200)"
  echo "$tier: tier line: $(grep -m1 -o 'WebGPU tier:.*' "$OUT/$tier/console.log" | cut -c1-160)"
done
exit $fail
