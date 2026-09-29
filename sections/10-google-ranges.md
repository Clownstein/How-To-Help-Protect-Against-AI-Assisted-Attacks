# 10. Google address ranges

Google is one provider for which an authoritative, if broad, address set can be constructed programmatically. Google publishes:

```text
https://www.gstatic.com/ipranges/goog.json
https://www.gstatic.com/ipranges/cloud.json
```

and documents that the default Google API and service ranges can be derived as:

```text
GOOGLE_API_RANGES = goog.json - cloud.json
```

Both lists are updated frequently. ([Obtain Google IP address ranges](https://support.google.com/a/answer/10026322?hl=en), [App Engine outbound IP addresses](https://docs.cloud.google.com/appengine/docs/standard/outbound-ip-addresses))

The resulting set covers considerably more than Gemini. A lookup of `generativelanguage.googleapis.com` on 27 September 2026 returned eight addresses in `172.217.112.0/24` through `172.217.119.0/24`, which is general Google front-end space. Blocking by hostname:

```text
block generativelanguage.googleapis.com
```

is therefore safer than:

```text
block every Google API address
```

unless the environment already enforces an allowlist-only egress policy.

## Vertex AI

Vertex AI, including Gemini on Vertex AI, has the same shared-address limitation. Google documents the regional endpoint form `REGION-aiplatform.googleapis.com`, together with the global `aiplatform.googleapis.com` and the multi-region hosts `aiplatform.us.rep.googleapis.com` and `aiplatform.eu.rep.googleapis.com`. Keep the control on these hostnames. Note that the region is part of the first label, so the wildcard `*.aiplatform.googleapis.com` does not match regional endpoints; the rule files use a regular expression or an enumerated regional list instead ([section 4](04-domain-denylist.md)). Blocking `172.217.0.0/16` would block ordinary Google front-end traffic along with Gemini. ([Google API access methods](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/general/googleapi-access-methods))

For approved Vertex AI use, place the API inside a VPC Service Controls perimeter ([approved AI gateway guide](../guides/approved-ai-gateway/README.md)).

## Crawler feeds are not the Gemini API

Google also publishes crawler verification feeds. Snapshots stored in [`data/inbound-bot-ips/`](../data/inbound-bot-ips/) on 27 September 2026:

| Feed | Creation time in file | Prefixes | Purpose |
| --- | --- | --- | --- |
| [googlebot.json](https://developers.google.com/static/search/apis/ipranges/googlebot.json) | `2026-09-25T14:49:23` | 317 | Google Search crawler verification |
| [special-crawlers.json](https://developers.google.com/static/search/apis/ipranges/special-crawlers.json) | `2026-09-25T14:47:24` | 272 | Special-case Google crawlers |
| [user-triggered-fetchers.json](https://developers.google.com/static/search/apis/ipranges/user-triggered-fetchers.json) | `2026-09-25T14:46:16` | 1058 | User-triggered fetchers, including fetches initiated from Google products |
| [user-triggered-fetchers-google.json](https://developers.google.com/static/search/apis/ipranges/user-triggered-fetchers-google.json) | `2026-09-25T14:46:19` | 496 | The Google-initiated subset of the user-triggered fetchers |

`Google-Extended` is a `robots.txt` token that controls whether Google may use fetched content for Gemini grounding and model improvement. It is never sent as a user agent: the fetch itself is made by Googlebot. Blocking the Googlebot feed therefore blocks Google Search, not a Gemini-specific path. For this reason the Google feeds are published individually in [`rules/ip-feeds/`](../rules/ip-feeds/) but excluded from the aggregate crawler lists.
