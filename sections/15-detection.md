# 15. Detection before enforcement

A production server that contacts an inference API is attempting to use a model it cannot host. Claude, GPT, and Gemini have no local weights, and a GLM-5.3 or Kimi K3 class model requires a GPU cluster ([section 1](01-threat-model.md)). The attempt is the detection signal; the deny is what removes the capability.

## Staged rollout

Deploy the controls in stages:

```text
LOG -> ALERT -> BLOCK
```

rather than moving directly to:

```text
BLOCK EVERYTHING
```

Logging first identifies approved dependencies that need an exception ([section 18](18-explicit-exceptions.md)) before enforcement causes an outage. The Suricata rules in [`rules/suricata/`](../rules/suricata/) raise alerts on TLS SNI, DNS queries, and HTTP Host headers for every catalog hostname, and are suitable for the logging and alerting stages.

## Egress alerts

Alert when workloads that do not normally use AI services query the hostnames in [section 4](04-domain-denylist.md), including:

```text
api.anthropic.com
api.openai.com
api.groq.com
api.together.xyz
api.fireworks.ai
api.mistral.ai
api.cohere.com
generativelanguage.googleapis.com
api.perplexity.ai
api.deepseek.com
api.x.ai
api.cerebras.ai
api.sambanova.ai
openrouter.ai
router.huggingface.co
```

An example of a high-priority event:

```text
prod-postgres-07
   -> api.anthropic.com:443
```

A database server has no legitimate reason to contact a model API. Treat this as a probable compromise until an owner confirms otherwise.

Enrich each alert with:

```text
host
user
process
container
parent process
destination FQDN
destination IP
SNI
bytes sent
bytes received
timestamp
DNS query
```

A first-ever connection to an AI API from a production server by a process such as:

```text
python
node
curl
powershell
unknown binary
```

warrants investigation. Large volumes of bytes sent relative to bytes received also indicate data being submitted to a model, rather than ordinary API use.

## Inbound alerts

On the inbound side, alert when a request's user agent contains `Claude-SearchBot`, `ClaudeBot`, `GPTBot`, `OAI-SearchBot`, `PerplexityBot`, `Bytespider`, or `CCBot`, and the source address is absent from that operator's published feed in [section 13](13-inbound-crawler-addresses.md). Such a request is either a forged crawler identity or an indication that the local feed snapshot needs refreshing (`python tools/refresh_feeds.py`). Operators without a published feed, such as `Bytespider` and `CCBot`, cannot be verified this way and should be assessed by behavior and volume.
