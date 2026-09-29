# 6. Squid reference configuration

Squid provides an open-source implementation of the egress deny. The complete, tested configuration is in [`rules/squid/`](../rules/squid/); this section explains how it works.

## Lists

The generator produces four list files from the catalog:

| File | Squid ACL type | Content |
| --- | --- | --- |
| `ai-inference-domains.txt` | `dstdomain` | Recommended profile hostnames |
| `ai-inference-domains-full.txt` | `dstdomain` | Full profile, including candidate hostnames |
| `ai-inference-domain-regex.txt` | `dstdom_regex` | Vertex AI regional endpoints (`REGION-aiplatform.googleapis.com`) |
| `ai-inference-url-regex.txt` | `url_regex` | The Cloudflare Workers AI path |

In a `dstdomain` list, a leading dot matches the host and all of its subdomains. Every entry is written with a leading dot, so each API hostname is denied together with any subdomain beneath it, and wildcard entries such as `*.openai.azure.com` become `.openai.azure.com`. An excerpt:

```text
.api.anthropic.com
.api.openai.com
.generativelanguage.googleapis.com
.openai.azure.com
.api.cohere.com
.api.mistral.ai
```

Amazon Bedrock endpoints are enumerated for every region that AWS documents, for example:

```text
.bedrock-runtime.us-east-1.amazonaws.com
.bedrock-runtime.us-east-2.amazonaws.com
.bedrock-runtime.us-west-2.amazonaws.com
.bedrock-mantle.us-east-1.api.aws
.bedrock-mantle.us-east-2.api.aws
.bedrock-mantle.us-west-2.api.aws
```

## Policy

[`rules/squid/squid.conf`](../rules/squid/squid.conf) defines the ACLs and deny rules. Include it before the first `http_access allow` line:

```text
include /etc/squid/ai-inference/squid.conf
```

It applies:

```text
acl ai_inference_domains dstdomain "/etc/squid/ai-inference/ai-inference-domains.txt"
acl ai_inference_domain_regex dstdom_regex -i "/etc/squid/ai-inference/ai-inference-domain-regex.txt"
acl ai_inference_url_regex url_regex -i "/etc/squid/ai-inference/ai-inference-url-regex.txt"

http_access deny ai_inference_domains
http_access deny ai_inference_domain_regex
http_access deny ai_inference_url_regex
```

For transparent interception, [`rules/squid/squid-intercept.conf`](../rules/squid/squid-intercept.conf) peeks at the TLS ClientHello, terminates connections whose SNI matches the lists, and splices all other traffic without decryption.

## Logging

Retain denied requests in the access log:

```text
access_log /var/log/squid/access.log
```

Denied attempts then appear as telemetry:

```text
TCP_DENIED/403 CONNECT api.anthropic.com:443
TCP_DENIED/403 CONNECT api.openai.com:443
```

These events are frequently more valuable than the block itself, because a denied inference request from a server is a strong indicator of compromise or policy violation. Forward them to your SIEM ([section 15](15-detection.md)).
