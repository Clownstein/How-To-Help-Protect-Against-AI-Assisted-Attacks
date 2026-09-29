# robots.txt

`robots.txt` files that ask AI crawlers, AI search indexers, and AI agents not to fetch a site.

## Files

| File | Contents |
| --- | --- |
| `robots.txt` | Recommended. The operator-documented tokens for OpenAI, Anthropic, Perplexity, Amazon, Google, and Apple, plus widely observed AI crawlers (Common Crawl, ByteDance, Meta, Cohere, Mistral AI, Diffbot). |
| `robots-training-only.txt` | Model-training crawlers only: `GPTBot`, `ClaudeBot`, `Amazonbot`, `Google-Extended`, `Applebot-Extended`, `CCBot`, `Bytespider`, `Meta-ExternalAgent`, and `Diffbot`. AI search indexers and user-triggered fetchers remain allowed, which keeps the site visible in AI search results. |
| `robots-full.txt` | The recommended tokens plus the community list maintained by the [ai.robots.txt](https://github.com/ai-robots-txt/ai.robots.txt) project. |

Each file is a single group of `User-agent` lines followed by `Disallow: /`, as defined in RFC 9309.

## Choosing a file

- `Google-Extended` and `Applebot-Extended` are control tokens only. Disallowing them opts out of Gemini and Apple Intelligence training without affecting Google Search or Apple search. Do not add `Googlebot` or `Applebot` unless you intend to leave those search indexes.
- `robots-full.txt` also names `Applebot`, `GoogleOther`, `FacebookBot`, `facebookexternalhit`, and generic scraper tokens such as `Scrapy`. Disallowing `Applebot` removes the site from Apple search, and disallowing `facebookexternalhit` stops link previews on Meta platforms. Review the list before publishing it.
- User-triggered fetchers such as `ChatGPT-User`, `Claude-User`, `Perplexity-User`, and `Amzn-User` act on behalf of a person. Some operators state that these fetchers may not follow `robots.txt` rules intended for automated crawling.

## Install

Copy the chosen file to the web root as `/robots.txt`. If the site already has a `robots.txt`, append the group to it; groups for other user agents are unaffected.

## Limitations

`robots.txt` is a voluntary convention, not an access control. To enforce the policy, use the [nginx configuration](../nginx/), the [Suricata crawler rules](../suricata/), the [address feeds](../ip-feeds/), or the [Cloudflare WAF](../../guides/cloudflare-waf/) or [AWS WAF](../../guides/aws-waf/) guides.

## References

- [RFC 9309: Robots Exclusion Protocol](https://www.rfc-editor.org/rfc/rfc9309.html)
- [Overview of OpenAI crawlers](https://developers.openai.com/api/docs/bots)
- [Anthropic crawler documentation](https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)
- [Perplexity crawlers](https://docs.perplexity.ai/docs/resources/perplexity-crawlers)
- [Amazonbot](https://developer.amazon.com/amazonbot)
- [Google common crawlers](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers)
- [About Applebot](https://support.apple.com/en-us/119829)
