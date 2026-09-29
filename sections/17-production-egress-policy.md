# 17. Production egress policy

For sensitive server networks, adopt a default-deny policy:

```text
DEFAULT:
    Internet egress = DENY

ALLOW:
    Operating system update repositories
    Explicitly required SaaS APIs
    Approved package repositories
    Required telemetry
    Corporate proxy
    DNS to corporate resolvers

DENY:
    Public inference APIs
    Anonymous proxies
    Consumer VPN endpoints, where feasible
    Tor exit nodes, where appropriate
    Newly registered domains, where feasible
```

Default deny is stronger than maintaining a hostname list alone. A new reseller is simply another outbound HTTPS destination, and that destination is how an ordinary server obtains frontier-model access. The server cannot load Claude, GPT, Gemini, GLM-5.3, or Kimi K3 itself ([section 19](19-open-source-models.md)).

The AI denylist in [section 4](04-domain-denylist.md) is the explicit layer within this model. It will continue to grow, because each new reseller introduces another hostname. A default-deny policy does not need to be updated each time a new service launches at `api.example.ai`; the denylist remains valuable as a record of intent, as protection for networks that cannot adopt default deny, and as a source of high-confidence alerts ([section 15](15-detection.md)).
