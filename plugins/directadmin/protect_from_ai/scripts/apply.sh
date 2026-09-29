#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
exec perl -I"$ROOT/lib" -MProtectFromAI -e 'ProtectFromAI::apply_pending($ARGV[0])' "$ROOT"
