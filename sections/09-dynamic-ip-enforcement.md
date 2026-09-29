# 9. IP-based enforcement where names cannot be matched

Some enforcement points, such as host firewalls, cannot match hostnames. On those, destination addresses can be resolved periodically into an `nftables` set:

```text
table inet egress {
    set ai_ipv4 {
        type ipv4_addr
        flags interval,timeout
        timeout 10m
    }

    set ai_published_ipv4 {
        type ipv4_addr
        flags interval
        elements = { 153.61.192.0/23, 153.61.196.0/23, 153.61.198.0/24, 160.79.104.0/21, 216.73.216.0/22 }
    }

    set ai_published_ipv6 {
        type ipv6_addr
        flags interval
        elements = { 2607:6bc0::/48, 2607:6bc0:11::/48 }
    }

    chain output {
        type filter hook output priority 0; policy accept;

        ip daddr @ai_ipv4 tcp dport 443 reject with tcp reset
        ip daddr @ai_ipv4 udp dport 443 reject
        ip daddr @ai_published_ipv4 reject
        ip6 daddr @ai_published_ipv6 reject
    }
}
```

Resolve the hostnames in [section 4](04-domain-denylist.md) on a schedule and add the results with a timeout, so addresses that a CDN reallocates expire from the set:

```bash
#!/usr/bin/env bash
set -euo pipefail

hosts=(
  api.openai.com
  api.cohere.com
  api.mistral.ai
  api.together.xyz
  api.groq.com
  api.fireworks.ai
  api.perplexity.ai
  api.deepseek.com
  api.x.ai
  api.cerebras.ai
  api.sambanova.ai
  openrouter.ai
  router.huggingface.co
)

for host in "${hosts[@]}"; do
  dig +short A "$host" | grep -E '^[0-9]+(\.[0-9]+){3}$' | while read -r addr; do
    nft add element inet egress ai_ipv4 "{ $addr timeout 10m }"
  done
done
```

Anthropic's routed ranges are held in the separate `ai_published_ipv4` and `ai_published_ipv6` sets above, which have no timeout, so `api.anthropic.com` can be omitted from the resolver loop. The same prefixes are generated as [`rules/ip-feeds/anthropic-network.txt`](../rules/ip-feeds/anthropic-network.txt). `160.79.104.0/21` contains the published inbound API range `160.79.104.0/23`, and `2607:6bc0::/48` is the published IPv6 API range. ([Anthropic IP addresses](https://platform.claude.com/docs/en/api/ip-addresses)) The other entries are Anthropic-registered prefixes that were routed on the review date ([section 2](02-inference-providers.md)). The observation table for the other providers is in that section; on 27 September 2026, `api.openai.com` answered `162.159.140.245` and `172.66.0.243`.

## The shared-address problem

```text
api.example.ai
       |
       v
Cloudflare / Fastly / AWS / Azure
       |
       +---- AI provider
       +---- unrelated customer
       +---- your payment processor
```

A destination-address rule cannot distinguish these services. The 27 September 2026 lookups demonstrate this: OpenAI, Mistral, Groq, Together, Perplexity, xAI, Cerebras, Moonshot, OpenRouter, and several others resolved to shared CDN address space. Rejecting those addresses also rejects other customers on the same anycast front end for as long as the entries remain in the set.

Dynamically resolved address blocking is therefore **supplementary enforcement**, not the primary control. Prefer the FQDN and SNI deny in [section 5](05-proxy-controlled-egress.md). The hostname identifies the model service: Claude, GPT, and Gemini exist only as those services, and GLM-5.3 or Kimi K3 class weights are too large for the host to serve itself ([section 19](19-open-source-models.md)).

Inbound crawler prefixes are a different dataset, published by providers for crawler verification. They are described in [section 13](13-inbound-crawler-addresses.md) and stored under [`data/inbound-bot-ips/`](../data/inbound-bot-ips/). Do not load crawler prefixes into this egress set.
