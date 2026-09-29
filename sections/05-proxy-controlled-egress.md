# 5. Recommended architecture: proxy-controlled egress

The strongest architecture routes all outbound traffic through a controlled egress point:

```text
Application hosts
       |
       X  direct Internet access on port 443
       |
       v
 Egress proxy or firewall
       |
       +---- business-approved destinations
       |
       X---- AI inference domains
       |
       v
    Internet
```

Route ordinary workloads through an explicit or transparent egress gateway, and deny direct outbound connections at the network layer ([section 7](07-prevent-proxy-bypass.md)).

Enforce policy on:

- DNS name
- TLS Server Name Indication (SNI)
- HTTP Host header, where visible
- Destination category
- Destination IP address, as a secondary signal only

Matching on names avoids tracking CDN addresses. The domain list is described in [section 4](04-domain-denylist.md), and ready-to-import files for Squid, Palo Alto Networks, Zscaler, Netskope, Cloudflare Gateway, Cisco Umbrella, F5 BIG-IP, and Microsoft Defender for Endpoint are in [`rules/`](../rules/). A host behind this policy has no hosted frontier model to call, and it lacks the GPUs to serve one locally.
