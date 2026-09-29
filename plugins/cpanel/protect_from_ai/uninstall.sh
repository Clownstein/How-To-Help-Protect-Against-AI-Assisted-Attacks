#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
if [ -x /usr/local/cpanel/bin/unregister_appconfig ]; then
    /usr/local/cpanel/bin/unregister_appconfig "$ROOT/protect_from_ai.conf" || true
fi
for path in \
    /etc/apache2/conf.d/includes/pre_main_global/protect-from-ai.conf \
    /etc/apache2/conf.d/protect-from-ai.conf \
    /etc/httpd/conf.d/protect-from-ai.conf \
    /usr/local/apache/conf/protect-from-ai.conf \
    /etc/nginx/conf.d/protect-from-ai-map.conf
do
    rm -f "$path"
done
rm -rf /usr/local/cpanel/whostmgr/docroot/cgi/protect_from_ai
rm -f /etc/cron.d/protect-from-ai
reloaded=0
for bin in /usr/local/cpanel/bin/apachectl /usr/sbin/apachectl /usr/local/apache/bin/apachectl /usr/sbin/httpd; do
    if [ -x "$bin" ]; then
        if "$bin" -t; then
            if [ -x /scripts/restartsrv_httpd ]; then
                /scripts/restartsrv_httpd || echo "Apache configtest passed, but the reload failed."
            else
                "$bin" graceful || echo "Apache configtest passed, but the graceful reload failed."
            fi
        else
            echo "Apache configtest failed after removal. Repair the configuration before reloading."
        fi
        reloaded=1
        break
    fi
done
if [ "$reloaded" -eq 0 ]; then
    echo "Reload Apache if it is still serving the removed Protect From AI rule."
fi
echo "Protect From AI was unregistered from WHM. Creator: Albert Clownstein."
