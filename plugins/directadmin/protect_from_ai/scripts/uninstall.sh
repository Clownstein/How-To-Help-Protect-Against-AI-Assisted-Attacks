#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
for path in \
    /etc/apache2/conf.d/includes/pre_main_global/protect-from-ai.conf \
    /etc/apache2/conf.d/protect-from-ai.conf \
    /etc/httpd/conf.d/protect-from-ai.conf \
    /usr/local/apache/conf/protect-from-ai.conf \
    /etc/nginx/conf.d/protect-from-ai-map.conf
do
    rm -f "$path"
done
includes=/etc/httpd/conf/extra/httpd-includes.conf
if [ -f "$includes" ]; then
    grep -vxF "Include $root/conf/apache.conf" "$includes" > "$includes.tmp" || true
    mv "$includes.tmp" "$includes"
fi
rm -f /etc/cron.d/protect-from-ai
rm -rf /var/lib/protect-from-ai
echo "Protect From AI removed its web-server configuration. Creator: Albert Clownstein."
