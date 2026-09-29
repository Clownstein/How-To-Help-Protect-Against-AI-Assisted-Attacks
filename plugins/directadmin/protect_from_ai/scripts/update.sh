#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
if [ -f "$HERE/plugin.conf" ] || [ -f "$HERE/protect_from_ai.conf" ]; then
    ROOT=$HERE
else
    ROOT=$(CDPATH= cd -- "$HERE/.." && pwd)
fi
exec perl -I"$ROOT/lib" -MProtectFromAI -e 'ProtectFromAI::update_from_github($ARGV[0])' "$ROOT"
