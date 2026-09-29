# 13. Inbound crawler address feeds

Several operators publish the source addresses of their **web crawlers** so that site owners can verify them. These ranges identify crawlers fetching your sites. They are not the addresses of `api.openai.com`, `api.anthropic.com`, or the other inference APIs in [section 2](02-inference-providers.md).

The feeds below were downloaded on **27 September 2026**. Snapshots are stored in [`data/inbound-bot-ips/`](../data/inbound-bot-ips/), and the per-feed and aggregate block lists generated from them are in [`rules/ip-feeds/`](../rules/ip-feeds/). Refresh the snapshots with `python tools/refresh_feeds.py` before enforcing them; the script rejects a feed that fails to download, fails to parse, or shrinks by more than half, and retains the previous snapshot in that case.

## Verification, not identification by header

A user-agent header is trivially forged:

```text
User-Agent: OAI-SearchBot
```

A request should therefore be treated as a verified crawler only when both the user agent and the source address match:

```text
IF User-Agent claims OAI-SearchBot
AND source address is not in the official OAI-SearchBot feed
THEN block
```

OpenAI recommends allowing requests from its published ranges where you want its bots to reach the site. ([Overview of OpenAI crawlers](https://developers.openai.com/api/docs/bots))

## OpenAI

| Crawler | robots.txt token | Full user agent (version may change) | Feed | Snapshot |
| --- | --- | --- | --- | --- |
| Training | `GPTBot` | `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.4; +https://openai.com/gptbot` | https://openai.com/gptbot.json | `2026-09-22`, 18 prefixes |
| Search | `OAI-SearchBot` | `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36; compatible; OAI-SearchBot/1.4; +https://openai.com/searchbot` | https://openai.com/searchbot.json | `2026-01-02`, 39 prefixes |
| Advertising review | `OAI-AdsBot` | `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; OAI-AdsBot/1.0; +https://openai.com/adsbot` | https://openai.com/adsbot.json | `2026-05-12`, 2 prefixes |
| User-initiated fetch | `ChatGPT-User` | `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot` | https://openai.com/chatgpt-user.json | `2026-09-25`, 230 prefixes |

OAI-SearchBot may append `; robots.txt` to its user agent when fetching `robots.txt`. ChatGPT-User acts on behalf of a person, so `robots.txt` rules may not apply to it. ([Overview of OpenAI crawlers](https://developers.openai.com/api/docs/bots))

Generated lists: [`openai-gptbot.txt`](../rules/ip-feeds/openai-gptbot.txt), [`openai-searchbot.txt`](../rules/ip-feeds/openai-searchbot.txt), [`openai-adsbot.txt`](../rules/ip-feeds/openai-adsbot.txt), [`openai-chatgpt-user.txt`](../rules/ip-feeds/openai-chatgpt-user.txt).

Of the 230 ChatGPT-User prefixes, 229 are `/28` networks. The remaining entry, `9.129.0.0/17` (32,768 addresses), is considerably broader. It is part of the official feed, but a blanket deny of that prefix may affect unrelated services; matching the user agent together with the feed is the more precise control.

## Anthropic

Anthropic's crawler documentation, updated 7 April 2026, names three crawlers and publishes one verification feed for all of them. A request from an address on that list originates from Anthropic. Anthropic advises that blocking those addresses may not work as an opt-out, because the crawler then cannot read `robots.txt`. ([Anthropic crawler documentation](https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler))

| Crawler | robots.txt token | Role |
| --- | --- | --- |
| Training | `ClaudeBot` | Collects web content that may contribute to model training |
| User-initiated fetch | `Claude-User` | Retrieves pages when a person asks Claude to |
| Search | `Claude-SearchBot` | Indexes content to improve search results |

Feed: https://claude.com/crawling/bots.json. The snapshot has creation time `2026-08-18T23:56:36Z` and 26 prefixes, which are not separated by crawler. Generated list: [`anthropic.txt`](../rules/ip-feeds/anthropic.txt).

The feed contains one Anthropic-registered block, `216.73.216.0/22` (ARIN net AWS-ANTHROPIC, announced by Amazon AS16509), along with individual `/32` addresses in Google Cloud and AWS space and small `/28` networks in Azure space, all of which can be reassigned. Match the user-agent token together with this feed when verifying. Further Anthropic registrations that are not in this feed are listed in [section 2](02-inference-providers.md) and in [`rules/ip-feeds/anthropic-network.txt`](../rules/ip-feeds/anthropic-network.txt).

Anthropic publishes no extended browser-style user-agent string for these crawlers; match the product token, such as `Claude-SearchBot`, in `robots.txt` and WAF rules.

The crawler feed is distinct from Anthropic's published API ranges (`160.79.104.0/23`, `2607:6bc0::/48`, and the outbound range `160.79.104.0/21`). The generator excludes any crawler prefix that overlaps those ranges ([section 2](02-inference-providers.md)).

## Perplexity

| Crawler | Feed | Creation time | Prefixes |
| --- | --- | --- | --- |
| `PerplexityBot` | https://www.perplexity.ai/perplexitybot.json | `2025-02-07` | 8 |
| `Perplexity-User` | https://www.perplexity.ai/perplexity-user.json | `2025-10-17` | 4 |

([Perplexity crawlers](https://docs.perplexity.ai/docs/resources/perplexity-crawlers)) Generated lists: [`perplexitybot.txt`](../rules/ip-feeds/perplexitybot.txt), [`perplexity-user.txt`](../rules/ip-feeds/perplexity-user.txt).

These addresses are in AWS space (`3.0.0.0/8`, `18.0.0.0/8`, `44.0.0.0/8`, and `107.20.0.0/16`). Verify the user agent against the feed, and do not block the surrounding AWS prefixes such as `18.97.0.0/16`.

## Amazon

Amazon documents three crawlers, each with its own address page. ([Amazonbot](https://developer.amazon.com/amazonbot))

| Crawler | Example user agent | Address page | Snapshot |
| --- | --- | --- | --- |
| `Amazonbot` | `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Amazonbot/0.1) Chrome/W.X.Y.Z Safari/537.36` | https://developer.amazon.com/amazonbot/ip-addresses/ | 1,292 individual IPv4 addresses |
| `Amzn-SearchBot` | `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Amzn-SearchBot/0.1) Chrome/W.X.Y.Z Safari/537.36` | https://developer.amazon.com/amazonbot/searchbot-ip-addresses/ | 816 individual IPv4 addresses |
| `Amzn-User` | `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Amzn-User/0.1) Chrome/W.X.Y.Z Safari/537.36` | https://developer.amazon.com/amazonbot/live-ip-addresses/ | 1,023 individual IPv4 addresses |

Amazon states that Amazonbot may be used to train Amazon AI models, and that Amzn-SearchBot and Amzn-User are used for search and live retrieval and not for generative model training. Amzn-User may disregard some `robots.txt` rules because a person initiated the request.

The published entries are individual addresses within AWS space. Blocking AWS ranges broadly is a different and far more disruptive action ([section 12](12-amazon-bedrock.md)). Generated lists: [`amazonbot.txt`](../rules/ip-feeds/amazonbot.txt), [`amzn-searchbot.txt`](../rules/ip-feeds/amzn-searchbot.txt), [`amzn-user.txt`](../rules/ip-feeds/amzn-user.txt).

## Apple

Apple publishes https://search.developer.apple.com/applebot.json. The snapshot has creation time `2026-09-15T10:00:00Z` and 24 prefixes, all within Apple's `17.0.0.0/8`. Generated list: [`applebot.txt`](../rules/ip-feeds/applebot.txt).

`Applebot-Extended` is a `robots.txt` token that controls use of content for Apple Intelligence training. It is never sent as a user agent; the fetch is made by Applebot from the same addresses. Blocking this feed therefore also blocks Apple's search crawling, and it is excluded from the aggregate crawler lists.

## Google

See [section 10](10-google-ranges.md). `Google-Extended` is a `robots.txt` token rather than a separate crawler or address list. The verification feeds are `googlebot.json`, `special-crawlers.json`, and the two user-triggered fetcher files published on `developers.google.com`. They are published individually in [`rules/ip-feeds/`](../rules/ip-feeds/) and excluded from the aggregate lists, because blocking them removes a site from Google Search.

## Aggregate lists

[`ai-crawlers-ipv4.txt`](../rules/ip-feeds/ai-crawlers-ipv4.txt) and [`ai-crawlers-ipv6.txt`](../rules/ip-feeds/ai-crawlers-ipv6.txt) combine the OpenAI, Anthropic, Perplexity, and Amazon feeds, collapsed into the minimal set of networks. The Palo Alto Networks crawler EDL, the CrowdStrike prefix lists, and the nginx `geo` map are generated from the same data.

## Crawlers without a published range

Common Crawl (`CCBot`), ByteDance (`Bytespider`), Meta (`Meta-ExternalAgent` and `Meta-ExternalFetcher`), Cohere (`cohere-ai`), and Mistral (`MistralAI-User` and related tokens) appear frequently in crawler logs and in the community `robots.txt` list in [section 14](14-robots-and-user-agents.md). No official address feed comparable to OpenAI's was found for them. Block them by user-agent token at the WAF, recognizing that the header can be forged. Do not construct address ranges for them from observations.

## Sources

- [Overview of OpenAI crawlers](https://developers.openai.com/api/docs/bots)
- [Anthropic crawler documentation](https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler) (7 April 2026)
- [Perplexity crawlers](https://docs.perplexity.ai/docs/resources/perplexity-crawlers)
- [Amazonbot](https://developer.amazon.com/amazonbot)
- https://claude.com/crawling/bots.json
- https://openai.com/gptbot.json
- https://openai.com/searchbot.json
- https://openai.com/adsbot.json
- https://openai.com/chatgpt-user.json
- https://www.perplexity.ai/perplexitybot.json
- https://www.perplexity.ai/perplexity-user.json
- https://search.developer.apple.com/applebot.json
