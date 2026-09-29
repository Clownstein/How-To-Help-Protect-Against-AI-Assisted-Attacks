# BIND and RPZ-capable resolvers

A DNS response policy zone (RPZ) that returns NXDOMAIN for AI inference destinations. RPZ is supported by BIND 9, Knot Resolver, PowerDNS Recursor, Unbound (1.10 and later), and many commercial DNS firewalls.

## Files

| File | Generated | Contents |
| --- | --- | --- |
| `ai-inference.rpz` | Yes | Recommended profile. |
| `ai-inference-full.rpz` | Yes | Full profile. |
| `named.conf.snippet` | No | `response-policy` and `zone` statements for BIND 9. |

## Zone format

- Each exact host has two records: `api.openai.com CNAME .` for the name itself and `*.api.openai.com CNAME .` for its subdomains. `CNAME .` is the RPZ action for NXDOMAIN.
- Tenant-wide families have a wildcard record only, for example `*.openai.azure.com CNAME .`.
- Vertex AI regional endpoints are enumerated, because RPZ wildcards replace whole labels only.
- Owner names are relative to the zone origin, so the same file loads under any RPZ zone name.
- The SOA serial is derived from the catalog `reviewed` date (`YYYYMMDD01`), so secondaries pick up a new version whenever the catalog changes.

## Install on BIND 9

```bash
sudo cp ai-inference.rpz /etc/bind/ai-inference.rpz
sudo named-checkzone ai-inference.rpz /etc/bind/ai-inference.rpz
```

Merge `named.conf.snippet` into `named.conf`: add the `response-policy` statement to the existing `options` block, and the `zone` statement at the top level. Then:

```bash
sudo named-checkconf
sudo rndc reload
```

## Verify

```bash
dig @127.0.0.1 api.openai.com A +short     # no answer, status NXDOMAIN
dig @127.0.0.1 api.openai.com A | grep status
```

With `log yes`, BIND writes an `rpz` category log line for each rewrite, which also provides a detection signal ([section 15](../../sections/15-detection.md)).

## Notes

- RPZ affects only clients that use this resolver. Block outbound DNS (TCP/UDP 53) and DNS over TLS (TCP 853) to other resolvers, and block or control known DNS-over-HTTPS endpoints ([section 8](../../sections/08-dns-policy.md)).
- An NXDOMAIN answer does not stop a client that already knows an address. Combine RPZ with proxy or SNI enforcement.

## References

- [BIND 9 response policy zones](https://bind9.readthedocs.io/en/latest/reference.html#response-policy-zones)
