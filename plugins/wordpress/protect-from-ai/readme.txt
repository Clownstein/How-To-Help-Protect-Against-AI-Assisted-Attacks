=== Protect From AI ===
Contributors: clownstein
Tags: security, robots, crawlers, ai
Requires at least: 5.8
Tested up to: 7.1
Stable tag: 1.0.0
Requires PHP: 7.2
License: MIT
License URI: https://opensource.org/licenses/MIT

Blocks selected AI crawler user agents, adds robots.txt rules, and stops WordPress HTTP API calls to selected inference hosts.

== Description ==

Protect From AI lets a site administrator choose which documented AI crawler tokens to block and which inference services WordPress itself may call.

The user-agent check returns 403 when a request header contains a selected token that the operator sends as a user agent. `Google-Extended` and `Applebot-Extended` are robots.txt tokens only, because those names are never sent as a User-Agent. Requests for the site's robots.txt address are not blocked.

The robots.txt option adds one Disallow group to the robots.txt file WordPress generates. A robots.txt file already stored in the web root is left unchanged.

The HTTP API option blocks requests WordPress makes with `wp_remote_*` and the other WordPress HTTP API functions when the destination is a selected inference service. Programs that open their own connections are not affected.

Creator: Albert Clownstein.

== Installation ==

1. Upload the `protect-from-ai` folder to `/wp-content/plugins/`, or install the zip from the Plugins screen.
2. Activate Protect From AI.
3. Open Settings, Protect From AI.
4. Choose Training crawlers, Recommended, or Full, or select individual tokens and inference services, then save.

Activating the plugin applies the recommended selections until you save a different choice.

== Frequently Asked Questions ==

= Does this stop every program on the server from calling an AI API? =

No. It blocks requests that go through the WordPress HTTP API. Use a firewall, proxy, or DNS rule for other programs.

= Does robots.txt block a client that ignores it? =

No. robots.txt is a request. The user-agent rule is what returns 403.

== Changelog ==

= 1.0.0 =
* Initial release.
