# 3. Why a static CIDR list is the wrong control

For most inference APIs, no authoritative, provider-specific static address range exists that is suitable for a long-term denylist.

Inference endpoints are commonly served from CDNs, hyperscaler address space, frequently changing DNS records, or shared cloud infrastructure. Blocking an observed `/24` can therefore block unrelated customers of the same CDN or cloud. The reliable indicator is the **API hostname**, not the address it currently resolves to.

## Provider by provider

**OpenAI.** A DNS lookup of `api.openai.com` on 27 September 2026 returned:

```text
162.159.140.245
172.66.0.243
```

Both addresses are shared CDN space. Treating whichever addresses currently answer DNS as a permanent provider netblock would cause outages for unrelated services as the CDN reallocates them. Separately, OpenAI OpCo, LLC registers [AS401518](https://whois.arin.net/rest/asn/AS401518), which originates `199.47.142.0/23` ([section 2](02-inference-providers.md)). That prefix is OpenAI's own routed space. It is not the address set returned for `api.openai.com`, and it is not one of the crawler feeds. OpenAI publishes separate JSON prefix lists for its **crawlers** (`GPTBot`, `OAI-SearchBot`, `ChatGPT-User`, and `OAI-AdsBot`). Those lists belong on an inbound WAF, as described in [section 13](13-inbound-crawler-addresses.md). ([Overview of OpenAI crawlers](https://developers.openai.com/api/docs/bots))

**Anthropic** publishes a stable inbound range for its API, `160.79.104.0/23` and `2607:6bc0::/48`, and a separate outbound range, `160.79.104.0/21`. ([Anthropic IP addresses](https://platform.claude.com/docs/en/api/ip-addresses)) ARIN organization AP-2440 holds additional allocations, and the routed portions of those allocations are listed in [section 2](02-inference-providers.md). The published inbound range can supplement a hostname block for `api.anthropic.com`. It does not cover Claude Platform on AWS (`aws-external-anthropic.<region>.api.aws`, which resolves to AWS address space) or Claude models served through Amazon Bedrock and Google Vertex AI, so the hostname remains the primary control.

Anthropic's crawler feed at [claude.com/crawling/bots.json](https://claude.com/crawling/bots.json) is a different list: it verifies that a request claiming to be `ClaudeBot`, `Claude-SearchBot`, or `Claude-User` originates from Anthropic. The snapshot taken on 27 September 2026 carries a creation time of `2026-08-18T23:56:36Z`. Anthropic advises that blocking its crawler addresses may not work reliably or persistently, because it can prevent the crawler from reading `robots.txt`. ([Anthropic crawler documentation](https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler))

**Google** states that its default API and service address ranges change frequently. It publishes `goog.json` and `cloud.json`, and documents deriving the Google API and service ranges by subtracting the customer Cloud ranges from the Google-owned ranges. ([Obtain Google IP address ranges](https://support.google.com/a/answer/10026322?hl=en)) The result covers every Google API, not only Gemini ([section 10](10-google-ranges.md)).

**AWS** publishes a continuously maintained `ip-ranges.json`, but states that it does not publish ranges for every service. ([AWS IP address ranges](https://docs.aws.amazon.com/vpc/latest/userguide/aws-ip-ranges.html))

**Microsoft** provides **service tags**, whose prefixes it updates as infrastructure changes, and advises using service tags rather than maintaining static addresses manually. ([Azure service tags overview](https://learn.microsoft.com/en-us/azure/virtual-network/service-tags-overview))

## Recommended approach

Enforce by hostname, using FQDN, SNI, and HTTP Host matching, and use official dynamic feeds where a provider publishes them. Use crawler feeds only for inbound bot verification.

The absence of a stable address range does not weaken the control. A host that cannot resolve or connect to `api.anthropic.com`, `api.openai.com`, or `generativelanguage.googleapis.com` cannot use Claude, GPT, or Gemini. The same applies to resellers hosting GLM-5.3 or Kimi K3: serving those models requires a cluster ([section 19](19-open-source-models.md)), so the reseller's hostname is the capability.
