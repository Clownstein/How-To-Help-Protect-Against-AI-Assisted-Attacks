# 8. DNS policy

Where you operate the resolvers, refuse to resolve inference domains. A workload that cannot resolve `api.anthropic.com` or `api.openai.com` cannot reach Claude or GPT, and it has no local copy of those models to use instead ([section 1](01-threat-model.md)).

## Response Policy Zones

Ready-to-load zones for BIND and other RPZ-capable resolvers are in [`rules/bind-rpz/`](../rules/bind-rpz/), and a Pi-hole adlist with installer is in [`rules/pi-hole/`](../rules/pi-hole/). In RPZ, a `CNAME .` record returns NXDOMAIN for the name:

```text
api.anthropic.com                 CNAME .
api.openai.com                    CNAME .
generativelanguage.googleapis.com CNAME .
aiplatform.googleapis.com         CNAME .
api.cohere.com                    CNAME .
api.mistral.ai                    CNAME .
api.together.xyz                  CNAME .
api.groq.com                      CNAME .
api.fireworks.ai                  CNAME .
```

RPZ supports wildcards only as the leftmost label. Tenant-specific Azure hosts are covered with leftmost wildcards:

```text
*.openai.azure.com                CNAME .
*.cognitiveservices.azure.com     CNAME .
*.services.ai.azure.com           CNAME .
```

Patterns with a variable label in the middle, such as `bedrock-runtime.<region>.amazonaws.com`, or a variable part within a label, such as `REGION-aiplatform.googleapis.com`, cannot be expressed as RPZ wildcards. The generated zones therefore list every documented Bedrock and Vertex AI regional hostname explicitly:

```text
bedrock-runtime.us-east-1.amazonaws.com CNAME .
bedrock-mantle.us-east-1.api.aws        CNAME .
us-central1-aiplatform.googleapis.com   CNAME .
```

## Enforcing resolver use

Require endpoints to use your resolvers, and deny unauthorized outbound DNS:

```text
TCP/UDP 53
TCP 853   (DNS over TLS)
UDP 853   (DNS over QUIC)
```

Also control public DNS-over-HTTPS endpoints where feasible, such as `dns.google`, `cloudflare-dns.com`, `dns.quad9.net`, and `one.one.one.one`. A compromised host that can reach a public DoH resolver bypasses your RPZ.

DNS blocking alone can be bypassed with hardcoded addresses or alternative resolvers, so it supplements network-layer enforcement ([section 5](05-proxy-controlled-egress.md), [section 7](07-prevent-proxy-bypass.md)); it does not replace it.
