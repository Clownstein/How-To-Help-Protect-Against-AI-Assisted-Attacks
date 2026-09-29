#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
root=$(pwd)
if [ "$(basename "$root")" != protect_from_ai ]; then
    echo "This plugin was installed as $(basename "$root"), but its menu links need the folder name protect_from_ai. Uninstall it and upload the archive named protect_from_ai.tar.gz without renaming it."
    exit 1
fi
for dir in conf data; do
    if [ -L "$dir" ]; then
        rm -f "$dir"
    fi
done
mkdir -p conf data
chmod 755 admin/index.html user/index.html reseller/index.html
chmod 755 scripts/install.sh scripts/uninstall.sh scripts/update.sh scripts/apply.sh
chmod -R a+rX .
if [ ! -s conf/apache.conf ]; then
    cat > conf/apache.conf <<'EOF'
# Protect From AI
# Creator: Albert Clownstein
# No enforcement until an administrator saves a selection. This file must exist before Apache includes it.
EOF
fi

# The admin page runs as the DirectAdmin admin account, which must be able to save its settings and the Apache rule.
# No other account may write here, because Apache includes conf/apache.conf.
owner=
admins=/usr/local/directadmin/data/admin/admin.list
if [ -f "$admins" ]; then
    owner=$(sed -n '1{s/[[:space:]]//g;p;}' "$admins")
fi
if [ -z "$owner" ] || ! id "$owner" >/dev/null 2>&1; then
    owner=admin
fi
find conf data -type l -exec rm -f {} +
if id "$owner" >/dev/null 2>&1; then
    chown -hR "$owner:$(id -gn "$owner")" conf data
else
    chown -hR root:root conf data
fi
chmod 755 conf data
find conf data -type f -exec chmod 644 {} +
for private in data/settings.json data/csrf.txt; do
    if [ -f "$private" ]; then
        chmod 600 "$private"
    fi
done
if [ -f "$admins" ] && command -v setfacl >/dev/null 2>&1; then
    while IFS= read -r admin; do
        admin=$(printf '%s' "$admin" | tr -d '[:space:]')
        if [ -n "$admin" ] && [ "$admin" != "$owner" ] && id "$admin" >/dev/null 2>&1; then
            setfacl -P -R -m "u:$admin:rwX" conf data
            setfacl -m "d:u:$admin:rwX" conf data
        fi
    done < "$admins"
fi

if [ -d /etc/httpd/conf/extra ]; then
    line="Include $root/conf/apache.conf"
    includes=/etc/httpd/conf/extra/httpd-includes.conf
    touch "$includes"
    if ! grep -qxF "$line" "$includes"; then
        printf '\n%s\n' "$line" >> "$includes"
    fi
fi
if [ -d /etc/cron.d ]; then
    {
        printf '* * * * * root %s\n' "$root/scripts/apply.sh"
        printf '15 13 * * 1 root %s\n' "$root/scripts/update.sh"
    } > /etc/cron.d/protect-from-ai
    chmod 644 /etc/cron.d/protect-from-ai
fi
echo "Protect From AI installed. Creator: Albert Clownstein. Open the plugin in DirectAdmin and choose the tokens to enforce."
