#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
DEST=/usr/local/cpanel/whostmgr/docroot/cgi/protect_from_ai
install -d "$DEST/lib" "$DEST/data" "$DEST/conf"
install -m 755 "$ROOT/index.cgi" "$DEST/index.cgi"
install -m 755 "$ROOT/update.sh" "$DEST/update.sh"
install -m 644 "$ROOT/lib/ProtectFromAI.pm" "$DEST/lib/ProtectFromAI.pm"
install -m 644 "$ROOT/data/catalog.json" "$DEST/data/catalog.json"
if [ -f "$ROOT/data/package.json" ]; then
    install -m 644 "$ROOT/data/package.json" "$DEST/data/package.json"
fi
if [ ! -x /usr/local/cpanel/bin/register_appconfig ]; then
    echo "WHM registration tool was not found. Run this script on the cPanel server as root." >&2
    exit 1
fi
/usr/local/cpanel/bin/register_appconfig "$ROOT/protect_from_ai.conf"
if [ -d /etc/cron.d ]; then
    printf '15 13 * * 1 root %s\n' "$DEST/update.sh" > /etc/cron.d/protect-from-ai
fi
echo "Protect From AI is registered in WHM. Creator: Albert Clownstein. Open WHM, Plugins, Protect From AI."
