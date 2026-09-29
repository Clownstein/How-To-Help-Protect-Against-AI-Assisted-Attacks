# DirectAdmin

Plugin for the admin, reseller, and user levels. The admin page installs a web-server rule for the AI crawler tokens you select. The reseller and user pages write those tokens into robots.txt on the sites owned by the logged-in account.

Creator: Albert Clownstein.

## Install

In DirectAdmin, open **Admin Level**, **Plugin Manager**, and upload `protect_from_ai.tar.gz` from the repository's `plugins` release. Do not rename the file: DirectAdmin installs the plugin into a folder named after the archive, and the plugin's menu links only work from `plugins/protect_from_ai`. DirectAdmin only accepts a `.tar.gz` plugin archive. The archive root contains `plugin.conf`, the menu hooks, and the icons. Those hooks place **Protect From AI** in Extra Features for admin, reseller, and user. After the upload, `scripts/install.sh` runs. Open the plugin from Extra Features, choose a preset or individual tokens, and save. Plugin Manager is where the plugin is enabled or disabled. DirectAdmin runs the admin page as the admin account, not root, so an admin save writes `conf/apache.conf` and a root cron job (`scripts/apply.sh`, every minute) runs the Apache configtest and graceful reload. A failed configtest restores the previous rule, and the result is shown on the admin page. `install.sh` gives `conf/` and `data/` to the first account in `admin.list`, plus an ACL for other admins when `setfacl` is available, because Apache includes that file and no other account may write it. A user or reseller save adds the selected tokens to `robots.txt` under each of that account's site directories, inside a Protect From AI block, and leaves the rest of the file in place.

To install from a shell on the DirectAdmin server, as root:

```sh
mkdir -p /usr/local/directadmin/plugins
cp -a protect_from_ai /usr/local/directadmin/plugins/protect_from_ai
sh /usr/local/directadmin/plugins/protect_from_ai/scripts/install.sh
```

DirectAdmin's plugin manager can upload the same directory as a tarball; `scripts/install.sh` runs after upload. Open the plugin as admin, choose a preset or individual tokens, and save.

When nginx is present, this plugin does not install a server block. The Apache rule is the enforcement. On DirectAdmin, include the plugin only where CustomBuild includes `httpd-includes.conf`.

`Google-Extended` and `Applebot-Extended` can be selected for `robots.txt`. They are omitted from the User-Agent rule because those tokens are never sent as a header. Community-list tokens are written to `robots.txt` only, for the same reason the rest of this repository does not match them in request headers. A user or reseller save writes that selection into each site's `robots.txt`. The admin save also writes `conf/robots.txt`, which the web server does not publish. `/robots.txt` itself is not blocked.

Nginx snippets in `conf/` are not loaded. A reverse proxy that forwards the original User-Agent to Apache is covered by the Apache rule. A server that serves sites with nginx alone needs the firewall and proxy rules in this repository, not this plugin.

## Remove

```sh
sh /usr/local/directadmin/plugins/protect_from_ai/scripts/uninstall.sh
rm -rf /usr/local/directadmin/plugins/protect_from_ai
```

Reload the web server after removal. robots.txt files already written under user accounts stay until that account saves with the robots.txt box cleared. These rules cover crawlers fetching hosted sites. Outbound inference blocking stays with the firewall, proxy, and DNS files in this repository.
