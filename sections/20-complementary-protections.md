# 20. Complementary protections

Egress denial protects the systems you operate from being used as a platform for model-driven activity. The application itself still depends on conventional controls:

- WAF rules, including the user-agent matches in [section 14](14-robots-and-user-agents.md)
- Rate limiting
- Per-account and per-session quotas
- Bot management
- Behavioral anomaly detection
- Authentication and multi-factor authentication
- API authorization
- Challenges, where appropriate
- Request-size limits
- Server-side request forgery (SSRF) protection
- Input validation
- Network segmentation
- Least privilege
- Endpoint detection and response (EDR)
- Secret management
- Data loss prevention
- Egress restrictions
- Canary credentials and tokens
- Comprehensive logging

These controls address the request that arrives at the application. Egress denial prevents a host you operate from calling Claude, GPT, Gemini, or a hosted GLM-5.3 or Kimi K3 deployment ([section 1](01-threat-model.md)). It does not inspect an exploit that an external adversary developed with their own vendor account, on a network you do not route, and then delivered as ordinary HTTP. A small open-weight model running on a single GPU is a third case: the policy never observes it, and it is weaker than the systems the denylist covers ([section 19](19-open-source-models.md)). WAF, authentication, and rate-limiting controls are what meet that inbound request.

## Reference architecture

```text
                         INTERNET
                            |
                +-----------+-----------+
                |                       |
             inbound                  outbound
                |                       |
                v                       v
        +---------------+       +---------------+
        | CDN / WAF     |       | Egress FW /   |
        | bot defense   |       | secure proxy  |
        | UA + published|       +-------+-------+
        | crawler feeds |               |
        +---------------+         DNS/FQDN/SNI
                |                 AI API denylist
                |                       |
                v                       v
        +---------------+       +---------------+
        | application   |------>| approved      |
        | environment   |       | destinations  |
        +-------+-------+       +---------------+
                |
                +------> EDR and process telemetry
                |
                +------> DNS logs
                |
                +------> SIEM
                              |
                              v
                    alert on attempted
                    inference access
```

The control that removes frontier models from ordinary servers is an egress enforcement point that filters by **FQDN and TLS destination**. Provider address feeds are for the crawlers that publish them. An unexpected production workload calling a public inference API is a security signal because that call is the model: the host cannot run Claude, GPT, Gemini, or a cluster-scale open-weight model itself.

The published feeds worth loading and refreshing are the crawler feeds and address pages in [section 13](13-inbound-crawler-addresses.md): OpenAI, Anthropic, Perplexity, Amazon, Apple, and Google's crawler verification files. Anthropic also publishes an API range. OpenAI OpCo registers `199.47.142.0/23` on AS401518, which is not the CDN address that currently answers `api.openai.com`. In each case the hostname remains the primary control.

Hostname-based enforcement remains effective through DNS rotation, CDN changes, and cloud address reassignment, all of which cause static AI-provider address lists to become inaccurate within weeks.
