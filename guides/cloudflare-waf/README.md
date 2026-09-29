# Cloudflare WAF and bot controls

Cloudflare classifies and blocks AI crawlers natively, so for sites proxied through Cloudflare there is nothing to import for the core control. This guide lists the built-in settings in order of preference and provides one generated custom rule expression for tokens you want to enforce regardless of Cloudflare's classification.

For outbound AI inference control with Cloudflare One, use the Gateway lists in [`rules/cloudflare-gateway`](../../rules/cloudflare-gateway/) instead.

## 1. AI bot policies (all plans)

Cloudflare groups AI traffic into three behaviors:

| Behavior | Meaning |
| --- | --- |
| **Training** | Crawling to train or fine-tune models, including mixed-purpose crawlers used for both training and search. |
| **Search** | Crawling to build search indexes or retrieval (RAG) databases used to answer questions later. |
| **Agent** | Automated activity acting in real time on a person's behalf, such as chat fetchers and browser-use agents. |

To configure:

1. In the Cloudflare dashboard, select the zone and go to **Security > Settings**.
2. Open **Configure AI bot policies**.
3. For each behavior, choose **Block (on all pages)**, **Block on pages with ads**, or **Allow (do not block)**.

Each policy blocks verified bots classified with that behavior, plus unverified bots that Cloudflare detects behaving the same way. On 15 September 2026 Cloudflare changed the defaults for new zones: Training and Agent are blocked on pages that display ads, and Search is allowed. Review the setting on existing zones rather than relying on defaults. The earlier single **Block AI bots** toggle is deprecated in favor of these policies.

## 2. AI Crawl Control (per-crawler decisions)

AI Crawl Control shows every AI crawler that requests the zone, its operator, category, request volume, and the number of `robots.txt` violations, and lets you allow or block each crawler individually.

1. Go to **AI Crawl Control** for the zone.
2. On the **Crawlers** tab, review the activity.
3. In the **Action** column, choose **Allow** or **Block** for each crawler. You can also configure the response returned to blocked crawlers.

Use this to make exceptions to the behavior policies, for example to allow a search crawler that sends referral traffic while blocking the same operator's training crawler.

## 3. Custom rule on verified bot category

For WAF custom rules, Cloudflare exposes the verified bot classification in the `cf.verified_bot_category` field. The legacy category strings for AI traffic are `AI Crawler`, `AI Search`, and `AI Assistant`. A rule that blocks verified AI training crawlers and AI assistants while leaving AI search untouched:

```text
(cf.verified_bot_category in {"AI Crawler" "AI Assistant"})
```

Create it under **Security > WAF > Custom rules**, with action **Block**.

## 4. Custom rule on user-agent tokens (generated)

[`custom-rule-expression.txt`](custom-rule-expression.txt) is generated from the catalog. It matches every crawler token that is sent in the `User-Agent` header, case-insensitively:

```text
(lower(http.user_agent) contains "gptbot")
or (lower(http.user_agent) contains "oai-searchbot")
...
```

This rule applies whether or not Cloudflare has verified the bot, so it also catches clients that impersonate an AI crawler. The generator keeps each expression within Cloudflare's 4,096-character limit. If the token list outgrows one expression, it writes `custom-rule-expression-2.txt` and so on; create one custom rule per file with the same action, since the rules together are the OR of the files.

1. Go to **Security > WAF > Custom rules** and select **Create rule**.
2. Select **Edit expression** and paste the contents of `custom-rule-expression.txt`.
3. Choose action **Block** (or **Managed Challenge** while evaluating), and deploy.

To exempt `robots.txt` so compliant crawlers can still read your directives, wrap the expression:

```text
(<generated expression>) and not (http.request.uri.path eq "/robots.txt")
```

## 5. Managed robots.txt

AI Crawl Control can also publish a managed `robots.txt` that disallows AI training crawlers. If you serve your own file instead, use the variants in [`rules/robots-txt`](../../rules/robots-txt/).

## Verification

- **Security > Events** shows each blocked request with the rule or setting that matched.
- **AI Crawl Control > Crawlers** shows request trends per crawler after a policy change.

## References

- [Block AI bots and AI bot policies](https://developers.cloudflare.com/bots/additional-configurations/block-ai-bots/)
- [Verified bots and categories](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/)
- [AI Crawl Control: manage AI crawlers](https://developers.cloudflare.com/ai-crawl-control/features/manage-ai-crawlers/)
- [AI Crawl Control overview](https://developers.cloudflare.com/ai-crawl-control/)
- [`cf.verified_bot_category` field](https://developers.cloudflare.com/ruleset-engine/rules-language/fields/reference/cf.verified_bot_category/)
- [`http.user_agent` field](https://developers.cloudflare.com/ruleset-engine/rules-language/fields/reference/http.user_agent/)
- [Create a custom rule in the dashboard](https://developers.cloudflare.com/waf/custom-rules/create-dashboard/)
