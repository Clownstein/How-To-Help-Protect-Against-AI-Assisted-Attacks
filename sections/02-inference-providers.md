# 2. Inference providers and enforceable destinations

The hostnames in this section are the access path to hosted models. Claude, GPT, and Gemini have no published weights, and open-weight models at the scale of GLM-5.3 and Kimi K3 require a GPU cluster that a compromised server does not have ([section 1](01-threat-model.md), [section 19](19-open-source-models.md)). Denying the hostname denies the model. Denying an observed `/24` usually does not, because most APIs are served from shared CDN or cloud address space.

The endpoint names below are documented by the providers or by the UK AI Security Institute's Inspect provider reference, which records the default base URL for each integration. Anthropic documents `https://api.anthropic.com`; the OpenAI API uses `https://api.openai.com/v1`; the Gemini API uses `generativelanguage.googleapis.com`; Groq uses `api.groq.com`; Cohere uses `api.cohere.com`; Mistral uses `api.mistral.ai`; Fireworks uses `api.fireworks.ai/inference/v1`; and Together AI uses `api.together.xyz/v1`. ([Claude API overview](https://platform.claude.com/docs/en/api/overview), [Together AI serverless inference](https://www.together.ai/serverless-inference), [Inspect providers](https://inspect.aisi.org.uk/providers.html))

## Core providers

| Provider | Primary inference destination | Provider-specific address range | Recommended control |
| --- | --- | --- | --- |
| **Anthropic (Claude)** | `api.anthropic.com` | Published: inbound `160.79.104.0/23` and `2607:6bc0::/48` ([Anthropic IP addresses](https://platform.claude.com/docs/en/api/ip-addresses)) | Block by FQDN or SNI; the published range may be used as a supplementary IP control |
| **OpenAI** | `api.openai.com` | `199.47.142.0/23`, originated by AS401518. The API hostname still resolves to shared CDN space. Crawler feeds are a separate inbound list | Block by FQDN or SNI, with the registered prefix as a supplement ([OpenAI registered address space](#openai-registered-address-space)) |
| **Google Gemini** | `generativelanguage.googleapis.com` | No Gemini-specific range | Block by hostname; Google API netblock feeds are optional ([section 10](10-google-ranges.md)) |
| **Microsoft Azure OpenAI and Foundry** | `*.openai.azure.com`, `*.cognitiveservices.azure.com`, `*.services.ai.azure.com` | Azure service tags | Block by FQDN or by the relevant service tag ([section 11](11-azure-openai.md)) |
| **Amazon Bedrock** | `bedrock-runtime.<region>.amazonaws.com`, `bedrock-mantle.<region>.api.aws` | No Bedrock-specific public range | Block by FQDN; AWS ranges are too broad ([section 12](12-amazon-bedrock.md)) |
| **Cohere** | `api.cohere.com` | None documented | Block by FQDN or SNI |
| **Mistral AI** | `api.mistral.ai` | None documented | Block by FQDN or SNI |
| **Together AI** | `api.together.xyz` | None documented | Block by FQDN or SNI |
| **Groq** | `api.groq.com` | None documented | Block by FQDN or SNI |
| **Fireworks AI** | `api.fireworks.ai` | None documented | Block by FQDN or SNI |

### OpenAI registered address space

OpenAI does not publish an API netblock the way it publishes crawler feeds, and a lookup of `api.openai.com` still returns shared CDN addresses. OpenAI OpCo, LLC does hold its own network. ARIN organization [OOL-15](https://whois.arin.net/rest/org/OOL-15) has two ASNs. [AS401518](https://whois.arin.net/rest/asn/AS401518) (OAI-01) originates one prefix. [AS401864](https://whois.arin.net/rest/asn/AS401864) (OPENAI) originated none on the review date.

| Prefix | Registration | Routed by | Use |
| --- | --- | --- | --- |
| `199.47.142.0/23` | ARIN [NET-199-47-142-0-1](https://whois.arin.net/rest/net/NET-199-47-142-0-1), net name OOL-15 | AS401518 | The only routed prefix registered to OpenAI OpCo. [IPinfo](https://ipinfo.io/AS401518/199.47.142.0/23) and [IPGeolocation](https://ipgeolocation.io/browse/asn/AS401518) show the same assignment. |
| `2604:f20::/32` | ARIN [STARGATE-01](https://whois.arin.net/rest/net/NET6-2604-F20-1), registered 6 May 2025 | Not announced | Allocation only. Not included in the generated file. |

The routed prefix is emitted as [`rules/ip-feeds/openai-network.txt`](../rules/ip-feeds/openai-network.txt). It is not part of the aggregate crawler lists. Those lists still come from OpenAI's crawler JSON. Blocking `199.47.142.0/23` does not by itself block `api.openai.com` while that name stays on the CDN. Keep the hostname deny.

### Anthropic's published ranges

Anthropic publishes the addresses on which its services accept connections (IPv4 `160.79.104.0/23`, IPv6 `2607:6bc0::/48`) and a separate outbound range (`160.79.104.0/21`) used when Anthropic connects to external systems, for example through the MCP connector, web search, or web fetch. The addresses `34.162.46.92/32`, `34.162.102.82/32`, `34.162.136.91/32`, `34.162.142.92/32`, and `34.162.183.95/32` are listed as phased out. ([Anthropic IP addresses](https://platform.claude.com/docs/en/api/ip-addresses))

The inbound range is suitable as a supplementary network-layer block for `api.anthropic.com`, but the hostname remains the primary control, for two reasons. First, Claude Platform on AWS is served from `aws-external-anthropic.<region>.api.aws`, which resolves to AWS address space outside the ranges below and is not covered by them. Deny that hostname for each region you need to cover, and do not deny `*.api.aws`, which carries unrelated AWS services. Second, Claude models are also available through Amazon Bedrock and Google Vertex AI, which are covered in [section 12](12-amazon-bedrock.md) and [section 4](04-domain-denylist.md).

The generated inbound crawler lists never include `160.79.104.0/21` or `2607:6bc0::/48`, so crawler blocking does not overlap the API ranges. The catalog guard enforces that ([`catalog/catalog.json`](../catalog/catalog.json), `egress.observed_inference_addresses`).

### Anthropic's routed address space

The API page is not the whole of Anthropic's registrations. ARIN organization [AP-2440](https://whois.arin.net/rest/org/AP-2440) (Anthropic, PBC) holds the allocations below. [AS Rank](https://asrank.caida.org/orgs/b7403dc2df) lists the same organization. The routed portions, checked against [RIPEstat](https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS399358) on 27 September 2026, are emitted as [`rules/ip-feeds/anthropic-network.txt`](../rules/ip-feeds/anthropic-network.txt). That file is an address inventory. It is not part of the aggregate crawler lists, because most of it was not published as crawler source space.

| Prefix | Registration | Routed by | Use |
| --- | --- | --- | --- |
| `160.79.104.0/21` | ARIN [NET-160-79-104-0-1](https://whois.arin.net/rest/net/NET-160-79-104-0-1) | AS399358 announces `160.79.104.0/23` | Allocation and published outbound range. The API inbound range `160.79.104.0/23` is inside it. |
| `2607:6bc0::/48` | Inside ARIN [ANTHROPIC-V6](https://whois.arin.net/rest/net/NET6-2607-6BC0-1) (`2607:6bc0::/32`) | AS399358 | Published API range |
| `2607:6bc0:11::/48` | Inside the same `/32` | AS399358 | Originated by the API ASN. Not named on the API IP page. |
| `216.73.216.0/22` | ARIN [AWS-ANTHROPIC](https://whois.arin.net/rest/net/NET-216-73-216-0-1) | AS16509 (Amazon) | Anthropic address space brought to AWS. [IPinfo](https://ipinfo.io/AS16509/216.73.216.0/22) shows the same net name. Already present in the crawler feed ([section 13](13-inbound-crawler-addresses.md)). |
| `153.61.192.0/23` | Inside ARIN [NET-153-61-0-0-1](https://whois.arin.net/rest/net/NET-153-61-0-0-1) (`153.61.0.0/16`, direct allocation, 17 June 2026) | AS396982 (Google Cloud) | Routed portion of the allocation |
| `153.61.196.0/24` | Same allocation | AS14618 (Amazon) | Routed portion |
| `153.61.197.0/24` | Same allocation | AS16509 (Amazon) | Routed portion |
| `153.61.198.0/24` | Same allocation | AS16509 (Amazon) | Routed portion |

The generator collapses `153.61.196.0/24` and `153.61.197.0/24` into `153.61.196.0/23`. It does not emit `153.61.0.0/16` or `2607:6bc0::/32`, because the rest of those allocations was not announced.

AS399358 is the ASN that originates the API prefixes ([ARIN AS399358](https://whois.arin.net/rest/asn/AS399358), [Hurricane Electric](https://ipv4.bgp.he.net/AS399358)). ARIN also registers AS400243, AS401551, and AS4167 to AP-2440; none of them originated prefixes on the review date. AS60808 is registered to the same organization and originates `209.249.57.0/24` with a valid ROA, but ARIN still assigns that net to Mitel Networks, Inc. under [NET-209-249-57-0-1](https://whois.arin.net/rest/ip/209.249.57.0). That prefix is excluded.

[ANTHR5-ARIN](https://whois.arin.net/rest/poc/ANTHR5-ARIN) is the role contact for that organization (admin, tech, routing, NOC, abuse, and DNS; `arin@anthropic.com`). It is a point of contact, not a network. Its organization links point only at AP-2440, and AP-2440's network list is the four allocations above. No additional Anthropic ranges come from that handle.

### xAI

`api.x.ai` is served from Cloudflare anycast, so the hostname remains the control for the Grok API. X.AI CORP. also has its own ARIN organization, [XAI](https://whois.arin.net/rest/org/XAI). That organization holds one net and one ASN:

| Prefix | Registration | Routed by | Use |
| --- | --- | --- | --- |
| `31.207.0.0/24` | ARIN [NET-31-207-0-0-1](https://whois.arin.net/rest/net/NET-31-207-0-0-1), direct allocation, 23 April 2026 | [AS400297](https://whois.arin.net/rest/asn/AS400297) | The only address space registered to X.AI CORP. |

The generated file is [`rules/ip-feeds/xai-network.txt`](../rules/ip-feeds/xai-network.txt). It is not part of the aggregate crawler lists.

[AS63179](https://www.peeringdb.com/asn/63179) is named XAI and PeeringDB identifies the network as xAI, with `https://x.ai/` as its website. ARIN registers the ASN and its prefixes to Twitter Inc. ([TWITT](https://whois.arin.net/rest/org/TWITT)), not to X.AI CORP. On the review date it announced `69.12.56.0/21` and `192.48.236.0/23` (both named TWITTER-NETWORK) and `209.237.208.0/24`, which sits inside Twitter's allocation `209.237.192.0/19`. Those prefixes are not in the xAI file, because blocking them would block X and Twitter address space.

### Azure OpenAI and Foundry

Azure OpenAI resource endpoints use:

```text
https://<resource-name>.openai.azure.com
```

Microsoft recommends FQDN-based rules such as `*.openai.azure.com` in managed-network configurations. ([Endpoints for Microsoft Foundry Models](https://learn.microsoft.com/en-us/azure/ai-studio/ai-services/concepts/endpoints))

Foundry model deployments also use tenant-specific hosts. Inspect records the managed-identity audience `https://cognitiveservices.azure.com/.default` and deployment base URLs of the form `https://<resource>.azure.com` and `https://<resource>.azure.com/models`. Block the FQDN pattern your tenant uses, in addition to:

```text
*.openai.azure.com
*.cognitiveservices.azure.com
*.services.ai.azure.com
```

([Inspect providers](https://inspect.aisi.org.uk/providers.html))

### Amazon Bedrock

Bedrock inference endpoints are regional, for example:

```text
bedrock-runtime.us-east-1.amazonaws.com
bedrock-runtime.us-west-2.amazonaws.com
bedrock-mantle.us-east-1.api.aws
```

AWS documents the regional structure explicitly. OpenAI models on Bedrock are served from the regional Mantle host, under the paths `/openai/v1` and `/v1`. The complete regional host list used by the rule files is maintained in the catalog. ([Amazon Bedrock endpoints](https://docs.aws.amazon.com/bedrock/latest/userguide/endpoints.html), [Inspect providers](https://inspect.aisi.org.uk/providers.html))

## Additional providers

The default base URLs below are those recorded by Inspect, except for Cerebras and Hugging Face, which are taken from the vendors' own documentation.

| Provider | Documented destination | Provider-specific address range | Control |
| --- | --- | --- | --- |
| **Perplexity** | `api.perplexity.ai` | None. A separate crawler feed exists ([section 13](13-inbound-crawler-addresses.md)) | Block by FQDN or SNI |
| **DeepSeek** | `api.deepseek.com` | None | Block by FQDN or SNI |
| **xAI (Grok)** | `api.x.ai` | `31.207.0.0/24` is registered to X.AI CORP. and is not where `api.x.ai` answers. See [xAI](#xai). | Block by FQDN or SNI |
| **Moonshot (Kimi)** | `api.moonshot.ai` | None | Block by FQDN or SNI |
| **Meta** | `api.meta.ai` | No inference-specific range | Block by FQDN or SNI |
| **Cerebras** | `api.cerebras.ai` | None | Block by FQDN or SNI |
| **SambaNova** | `api.sambanova.ai` | None | Block by FQDN or SNI |
| **OpenRouter** | `openrouter.ai` | None | Block by FQDN or SNI |
| **Hugging Face router** | `router.huggingface.co` | None; served from CloudFront at review time | Block by FQDN or SNI |
| **Cloudflare Workers AI** | `api.cloudflare.com` under `/client/v4/accounts/<id>/ai/run` | None; the hostname serves the entire Cloudflare API | Block the Workers AI path where the proxy can inspect HTTP. A hostname-wide block also denies the rest of the Cloudflare API |

Sources: [Inspect providers](https://inspect.aisi.org.uk/providers.html), [Cerebras OpenAI compatibility](https://inference-docs.cerebras.ai/resources/openai), [Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers/index).

The Hugging Face Inference Providers directory also lists the following hosted backends. Block each vendor's API hostname individually rather than attempting to express the set as a single address range:

Baseten, Cerebras, Cohere, DeepInfra, Fal AI, Featherless AI, Fireworks, Groq, HF Inference, Novita, Nscale, OVHcloud AI Endpoints, Public AI, Replicate, Scaleway, Together, WaveSpeedAI, and Z.ai. ([Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers/index))

## Point-in-time DNS observations, 27 September 2026

The A records below were resolved during research on 27 September 2026. They identify **which CDN or cloud** fronts each API. They are recorded to explain why address-based blocking is unsafe, and they must not be used as a denylist. The generator refuses to emit any crawler prefix that covers them.

Most of these addresses fall within shared anycast space, including Cloudflare's `104.16.0.0/12`, `172.64.0.0/13`, `172.66.0.0/16`, and `162.159.0.0/16`. Blocking those prefixes blocks unrelated sites served by the same CDN. Anthropic is the exception: its API address falls within its own published range.

| Hostname | Observed A records | Interpretation |
| --- | --- | --- |
| `api.anthropic.com` | `160.79.104.10` | Within Anthropic's published inbound range `160.79.104.0/23` |
| `api.openai.com` | `172.66.0.243`, `162.159.140.245` | Shared CDN anycast |
| `api.mistral.ai` | `162.159.142.207`, `172.66.2.203` | Shared CDN anycast |
| `api.together.xyz` | `104.18.43.158`, `172.64.144.98` | Shared CDN anycast |
| `api.groq.com` | `104.18.38.236`, `172.64.149.20` | Shared CDN anycast |
| `api.perplexity.ai` | `104.18.27.48`, `104.18.26.48` | Shared CDN anycast |
| `api.x.ai` | `104.18.19.80`, `104.18.18.80` | Shared CDN anycast |
| `openrouter.ai` | `104.18.2.115`, `104.18.3.115` | Shared CDN anycast |
| `api.cerebras.ai` | `104.18.10.146`, `104.18.11.146` | Shared CDN anycast |
| `api.moonshot.ai` | `104.18.28.136`, `104.18.29.136` | Shared CDN anycast |
| `api.replicate.com` | `104.18.3.60`, `104.18.2.60` | Shared CDN anycast |
| `api.ai21.com` | `104.20.38.76`, `172.66.145.160` | Shared CDN anycast |
| `api.featherless.ai` | `172.67.72.137`, `104.26.6.127`, `104.26.7.127` | Shared CDN anycast |
| `api.hyperbolic.xyz` | `104.18.31.126`, `104.18.30.126` | Shared CDN anycast |
| `api.jina.ai` | `104.26.10.242`, `104.26.11.242`, `172.67.70.54` | Shared CDN anycast |
| `api.stability.ai` | `104.18.34.224`, `172.64.153.32` | Shared CDN anycast |
| `api.writer.com` | `104.20.31.216`, `172.66.167.93` | Shared CDN anycast |
| `api.together.ai` | `104.18.37.81`, `172.64.150.175` | Shared CDN anycast; the documented host is `api.together.xyz` |
| `generativelanguage.googleapis.com` | `172.217.112.4` through `172.217.119.4` | Shared Google front end, not Gemini-specific |
| `api.cohere.com` | `34.96.76.122` | Google Cloud address, shared infrastructure |
| `api.fireworks.ai` | `35.207.52.96` | Google Cloud address |
| `inference.baseten.co` | `35.244.129.243` | Google Cloud address |
| `llm.chutes.ai` | `34.111.142.178` | Google Cloud address |
| `inference.api.nscale.com` | `34.91.100.50` | Google Cloud address |
| `api.deepseek.com` | `3.173.21.63` | AWS CloudFront address |
| `api.sambanova.ai` | `34.235.97.209`, `3.223.245.77` | AWS addresses |
| `router.huggingface.co` | `3.162.103.113`, `.110`, `.127`, `.36` | AWS CloudFront |
| `api.novita.ai` | Six addresses within `44.225.0.0/16`, `44.233.0.0/16`, `44.235.0.0/16`, `44.241.0.0/16`, `52.13.0.0/16`, and `54.68.0.0/16` | AWS |
| `api.upstage.ai` | `52.79.171.164`, `54.117.8.238`, `3.36.7.77` | AWS |
| `api.friendli.ai` | `3.33.246.183`, `15.197.205.95` | AWS Global Accelerator addresses |
| `integrate.api.nvidia.com` | `75.2.113.119`, `99.83.136.103` | AWS Global Accelerator addresses |
| `api.meta.ai` | `31.13.66.4` | Meta edge address, shared with other Meta services |
| `api.minimax.io` | `23.205.106.147`, `.153`, `.168` | Akamai shared address space |
| `api.deepinfra.com` | `38.101.151.13` through `.30` (14 addresses) | Tight cluster, but an observation rather than a published range |
| `api.voyageai.com` | `136.110.181.169` | Single observed address |
| `queue.fal.run` | `35.253.220.11` | Google Cloud address |
| `dashscope.aliyuncs.com` | `8.140.217.18`, `8.152.159.24`, `39.96.198.249`, `39.96.213.166` | Alibaba Cloud (DashScope, Qwen) |
| `open.bigmodel.cn` | `47.253.34.159`, `47.253.242.212` | Alibaba Cloud (Zhipu, Z.ai) |
| `api.siliconflow.com` | `47.85.102.97`, `47.85.105.126`, `47.90.171.203` | Alibaba Cloud |
| `api.bfl.ai` | `150.171.109.72` | Black Forest Labs, single observed address |

`api.lambda.ai` and `api.openrouter.ai` did not resolve during the review; `openrouter.ai` did. `api.nscale.com` returned no A record, while `inference.api.nscale.com` did.

The following related hostnames also resolved on the same date:

| Hostname | Observed A records |
| --- | --- |
| `api.moonshot.cn` | `8.147.223.37` |
| `dashscope-intl.aliyuncs.com` | `47.236.117.191`, `47.236.175.160`, `47.245.114.142` |
| `api.minimaxi.com` | `47.79.117.67` |
| `api.siliconflow.cn` | `47.239.184.63`, `47.239.215.199` |
| `aiplatform.googleapis.com` | `64.233.180.95`, `142.251.163.95`, `142.251.167.95`, `192.178.218.95` |
| `us-central1-aiplatform.googleapis.com` | `172.217.113.4` through `172.217.116.4` |

Google documents `REGION-aiplatform.googleapis.com` as the regional Vertex AI (Gemini Enterprise Agent Platform) endpoint. ([Google API access methods](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/general/googleapi-access-methods)) These addresses are shared Google front ends, with the same limitation as `generativelanguage.googleapis.com`.

The hostnames in the second group (`api.replicate.com`, `api.ai21.com`, `api.novita.ai`, `api.deepinfra.com`, `api.featherless.ai`, `api.hyperbolic.xyz`, `inference.baseten.co`, `api.voyageai.com`, `api.jina.ai`, `queue.fal.run`, `api.stability.ai`, `api.writer.com`, `api.upstage.ai`, `dashscope.aliyuncs.com`, `open.bigmodel.cn`, `api.minimax.io`, `api.siliconflow.com`, `api.friendli.ai`, `llm.chutes.ai`, `api.bfl.ai`, `integrate.api.nvidia.com`, and `inference.api.nscale.com`) resolved on the review date. They are **candidate** entries in the catalog and are included only in the `full` profile. Confirm each hostname against the vendor's current documentation before enforcement, because resellers rename hosts.

## Sources

- [Claude API overview](https://platform.claude.com/docs/en/api/overview)
- [Anthropic IP addresses](https://platform.claude.com/docs/en/api/ip-addresses)
- [Together AI serverless inference](https://www.together.ai/serverless-inference)
- [Inspect providers](https://inspect.aisi.org.uk/providers.html) (September 2026)
- [Cerebras OpenAI compatibility](https://inference-docs.cerebras.ai/resources/openai)
- [Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers/index)
- [Endpoints for Microsoft Foundry Models](https://learn.microsoft.com/en-us/azure/ai-studio/ai-services/concepts/endpoints)
- [Amazon Bedrock endpoints](https://docs.aws.amazon.com/bedrock/latest/userguide/endpoints.html)
- [Anthropic crawler documentation](https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler) (updated 7 April 2026)
