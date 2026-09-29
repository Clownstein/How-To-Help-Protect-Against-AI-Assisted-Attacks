# Squid

ACL files and configuration fragments for Squid 4 and later, as an explicit forward proxy or in intercept mode.

## Files

| File | Generated | Contents |
| --- | --- | --- |
| `ai-inference-domains.txt` | Yes | `dstdomain` list, recommended profile. A leading period matches the host and all subdomains. |
| `ai-inference-domains-full.txt` | Yes | `dstdomain` list, full profile. |
| `ai-inference-domain-regex.txt` | Yes | `dstdom_regex` patterns for Vertex AI regional endpoints added after the review date. |
| `ai-inference-url-regex.txt` | Yes | `url_regex` pattern for the Cloudflare Workers AI inference path. |
| `squid.conf` | No | Explicit-proxy ACLs and `http_access deny` rules. |
| `squid-intercept.conf` | No | `ssl_bump` peek-and-terminate rules for intercepted TLS, using the same lists as SNI matches. |

Squid warns when a `dstdomain` list contains both a domain and one of its subdomains. The generator removes those redundant entries.

## Install

```bash
sudo mkdir -p /etc/squid/ai-inference
sudo cp ai-inference-*.txt squid.conf squid-intercept.conf /etc/squid/ai-inference/
```

Add one line to `/etc/squid/squid.conf`, **before** the first `http_access allow` line:

```text
include /etc/squid/ai-inference/squid.conf
```

For transparent deployments that already have an `https_port ... intercept ssl-bump` listener with a signing certificate, also include `squid-intercept.conf` before any existing `ssl_bump` lines. It peeks at the ClientHello, terminates connections whose SNI matches the lists, and splices everything else without decryption.

Validate and apply:

```bash
sudo squid -k parse
sudo squid -k reconfigure
```

To enforce the full profile, change the `ai_inference_domains` path in `squid.conf` (and `ai_inference_sni` in `squid-intercept.conf`) to `ai-inference-domains-full.txt`.

## Verify

```bash
curl -x http://proxy.example.internal:3128 -sS -o /dev/null -w '%{http_code}\n' https://api.openai.com/v1/models
```

A blocked CONNECT returns `403`, and the access log records `TCP_DENIED/403 ... CONNECT api.openai.com:443`.

## Notes

- `url_regex` matches only requests whose full URL Squid can see: plain HTTP and HTTPS decrypted with `ssl_bump bump`. For CONNECT tunnels that are not decrypted, only the host rules apply.
- The explicit-proxy rules are effective only if workloads cannot reach the Internet directly. Pair them with a default-deny egress firewall that permits outbound TCP 80/443 only from the proxy ([section 5](../../sections/05-proxy-controlled-egress.md)).

## References

- [Squid `acl` directive](https://www.squid-cache.org/Doc/config/acl/)
- [Squid `ssl_bump` directive](https://www.squid-cache.org/Doc/config/ssl_bump/)
- [Squid configuration reference](https://www.squid-cache.org/Doc/config/)
