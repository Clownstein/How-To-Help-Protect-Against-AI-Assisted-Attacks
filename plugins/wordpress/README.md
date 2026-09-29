# WordPress

Installable plugin that blocks selected AI crawler user agents, appends the matching `robots.txt` group, and stops WordPress HTTP API calls to the inference services you select.

Creator: Albert Clownstein.

## Install

1. Download `protect-from-ai-wordpress.zip` from the repository's `plugins` release, or zip the `protect-from-ai` directory yourself so the archive contains `protect-from-ai/protect-from-ai.php`.
2. In WordPress, open Plugins, Add Plugin, Upload Plugin, and install that archive.
3. Activate Protect From AI.
4. Open Settings, Protect From AI. Choose Training crawlers, Recommended, or Full, or select individual tokens and inference services, then save.

## What each choice does

- **User-Agent block** returns 403 when the request header contains a selected token that operators send as a user agent. `Google-Extended` and `Applebot-Extended` are saved for `robots.txt` only, because those tokens are never sent as a header. `/robots.txt` is not blocked.
- **robots.txt** adds one `Disallow: /` group to the robots.txt file WordPress generates. A robots.txt file already stored on disk is left unchanged.
- **WordPress HTTP API** blocks `wp_remote_*` and other requests made through WordPress to the selected inference hosts. A program that opens its own connection, outside WordPress, is not affected. Use the firewall and proxy rules in this repository for that traffic.

The token and hostname data is `data/catalog.json`, generated from `catalog/catalog.json`. Regenerate the rule pack and reinstall the plugin when the catalog changes.
