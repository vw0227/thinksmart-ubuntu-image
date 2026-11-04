#!/bin/sh
# Optional, version-guarded source patch. No credentials or service changes.
set -eu
here=$(CDPATH='' cd -- "$(dirname "$0")" && pwd)
hub=${1:?usage: sh extras/hub/apply.sh /path/to/xiaozhi-hub-server}
expected=a6e9a8300025b5a2efd75dd4d6a37f36c55dab79
[ "$(git -C "$hub" rev-parse HEAD)" = "$expected" ] || {
    echo "Gateway version differs; review/rebase rather than overwriting"; exit 1;
}
if git -C "$hub" apply --reverse --check "$here/voice-weather.patch" 2>/dev/null; then
    echo "Patch already applied; no changes"
    exit 0
fi
git -C "$hub" diff --quiet -- main/xiaozhi-server/core/providers/llm/openai/openai.py \
    main/xiaozhi-server/core/providers/tts/edge.py main/xiaozhi-server/plugins_func/functions/get_weather.py
git -C "$hub" diff --cached --quiet -- main/xiaozhi-server/core/providers/llm/openai/openai.py \
    main/xiaozhi-server/core/providers/tts/edge.py main/xiaozhi-server/plugins_func/functions/get_weather.py
git -C "$hub" apply --check "$here/voice-weather.patch"
git -C "$hub" apply "$here/voice-weather.patch"
echo "Source patch applied; private configuration and running services unchanged."
