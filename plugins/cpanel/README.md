# WHM / cPanel

WHM plugin that installs the same web-server rule as the DirectAdmin plugin, for the AI crawler tokens you select.

Creator: Albert Clownstein.

## Install

Download `protect-from-ai-cpanel.tar.gz` from the repository's `plugins` release. The archive has no top-level folder, so unpack it into an empty directory. On the cPanel server, as root, from that directory:

```sh
sh install.sh
```

Then open WHM, Plugins, Protect From AI. Choose Training crawlers, Recommended, Full, or individual tokens, and save. The plugin registers with WHM's app registry and writes `protect-from-ai.conf` into cPanel's pre-main Apache include when that directory exists. It reloads Apache only after `apachectl -t` succeeds. `/robots.txt` is not blocked. `conf/robots.txt` is written for you to copy onto a site that does not already have one; it is not published by the web server.

`Google-Extended`, `Applebot-Extended`, and the community token list can be included in that `robots.txt` file. They are left out of the User-Agent rule.

## Remove

```sh
sh uninstall.sh
```

Reload Apache if the plugin reports that it could not reload the service. Outbound connections to inference APIs are outside this plugin; use the firewall, proxy, and DNS rules in this repository for those.
