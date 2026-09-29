# Crawler address feeds

Validated, collapsed prefix lists derived from the address feeds that AI crawler operators publish. Use them to block crawlers at a firewall, load balancer, or WAF, and to verify that a request claiming a crawler user agent really comes from that operator.

## Files

| File | Source | Aggregated |
| --- | --- | --- |
| `openai-gptbot.txt` | [openai.com/gptbot.json](https://openai.com/gptbot.json) | Yes |
| `openai-searchbot.txt` | [openai.com/searchbot.json](https://openai.com/searchbot.json) | Yes |
| `openai-adsbot.txt` | [openai.com/adsbot.json](https://openai.com/adsbot.json) | Yes |
| `openai-chatgpt-user.txt` | [openai.com/chatgpt-user.json](https://openai.com/chatgpt-user.json) | Yes |
| `anthropic.txt` | [claude.com/crawling/bots.json](https://claude.com/crawling/bots.json), shared by `ClaudeBot`, `Claude-SearchBot`, and `Claude-User` | Yes |
| `perplexitybot.txt` | [perplexity.ai/perplexitybot.json](https://www.perplexity.ai/perplexitybot.json) | Yes |
| `perplexity-user.txt` | [perplexity.ai/perplexity-user.json](https://www.perplexity.ai/perplexity-user.json) | Yes |
| `amazonbot.txt` | [Amazonbot IP addresses](https://developer.amazon.com/amazonbot/ip-addresses/) | Yes |
| `amzn-searchbot.txt` | [Amzn-SearchBot IP addresses](https://developer.amazon.com/amazonbot/searchbot-ip-addresses/) | Yes |
| `amzn-user.txt` | [Amzn-User IP addresses](https://developer.amazon.com/amazonbot/live-ip-addresses/) | Yes |
| `applebot.txt` | [search.developer.apple.com/applebot.json](https://search.developer.apple.com/applebot.json) | No, verification only |
| `googlebot.txt` | [Googlebot ranges](https://developers.google.com/static/search/apis/ipranges/googlebot.json) | No, verification only |
| `google-special-crawlers.txt` | [Special-case crawler ranges](https://developers.google.com/static/search/apis/ipranges/special-crawlers.json) | No, verification only |
| `google-user-triggered-fetchers.txt` | [User-triggered fetcher ranges](https://developers.google.com/static/search/apis/ipranges/user-triggered-fetchers.json) | No, verification only |
| `google-user-triggered-fetchers-google.txt` | [Google-owned user-triggered fetcher ranges](https://developers.google.com/static/search/apis/ipranges/user-triggered-fetchers-google.json) | No, verification only |
| `ai-crawlers-ipv4.txt` | Union of the aggregated IPv4 feeds, collapsed | |
| `ai-crawlers-ipv6.txt` | Union of the aggregated IPv6 feeds, collapsed | |
| `openai-network.txt` | `199.47.142.0/23`, the routed prefix registered to OpenAI OpCo, LLC (AS401518). Not the crawler feed and not the CDN addresses for `api.openai.com`. See [section 2](../../sections/02-inference-providers.md). | No |
| `anthropic-network.txt` | Address space registered to Anthropic, PBC and routed on the review date. Not a crawler feed and not included in the aggregates. See [section 2](../../sections/02-inference-providers.md). | No |
| `xai-network.txt` | `31.207.0.0/24`, the only net registered to X.AI CORP. Not a crawler feed. Twitter-registered prefixes announced by AS63179 are omitted. See [section 2](../../sections/02-inference-providers.md). | No |

Every crawler-feed file has one prefix per line with no comments, IPv4 first and then IPv6. `anthropic-network.txt`, `openai-network.txt`, and `xai-network.txt` have a comment header and are generated from the catalog's provider inventories rather than from a crawler snapshot. Add `anthropic-network.txt` to an address policy when you want to cover Anthropic-registered ranges beyond the published crawler feed, including the API allocation. Add `openai-network.txt` for the routed prefix registered to OpenAI OpCo. Add `xai-network.txt` for the one net registered to X.AI CORP. Do not substitute `anthropic-network.txt` for `anthropic.txt` when the task is verifying `ClaudeBot`, `Claude-SearchBot`, or `Claude-User`: that decision still uses the feed Anthropic publishes for its crawlers. Do not substitute `openai-network.txt` for the OpenAI crawler files when the task is verifying `GPTBot` or `OAI-SearchBot`.

## Aggregated and verification-only feeds

The aggregate files include only feeds whose addresses serve AI crawling or AI user-triggered fetching. Googlebot and Applebot also index for Google Search and Apple search, and Google's special-case and user-triggered ranges serve many non-AI products. Blocking them removes the site from those services, so their lists are published for verification only: use them to confirm that a request claiming to be `Googlebot` or `Applebot` really comes from Google or Apple, not as a block list. Google's and Apple's AI training opt-outs are the `Google-Extended` and `Applebot-Extended` tokens in [`robots.txt`](../robots-txt/).

## Validation

`tools/refresh_feeds.py` downloads each feed over HTTPS and parses every prefix with Python's `ipaddress` module. A feed is rejected and its previous snapshot is kept if it fails to parse, contains no prefixes, or shrinks below half of the previous prefix count. `tools/generate.py` then collapses adjacent and overlapping prefixes, and removes any prefix that would cover an address in the catalog's list of shared inference front ends, so crawler blocking can never interfere with the name-based egress rules. The status of each feed's last refresh is recorded in [`data/inbound-bot-ips/refresh-status.json`](../../data/inbound-bot-ips/refresh-status.json).

## Using the lists

- **AWS WAF IP sets** take IPv4 and IPv6 in separate sets; use `ai-crawlers-ipv4.txt` and `ai-crawlers-ipv6.txt`. See [the AWS WAF guide](../../guides/aws-waf/).
- **Palo Alto Networks** reads the combined list from [`../palo-alto/ai-crawlers-ip-edl.txt`](../palo-alto/).
- **CrowdStrike Falcon** uses [`../crowdstrike`](../crowdstrike/).
- **nginx** embeds the aggregate in [`../nginx/ai-crawlers-http.conf`](../nginx/).
- **Other firewalls and WAFs** can reference the raw file URL as an external list, or import it as an address group.
