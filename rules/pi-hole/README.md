# Pi-hole v6

DNS blocking for AI inference destinations on Pi-hole v6, either as a subscribed adlist or as locally managed wildcard and regex entries.

## Files

| File | Generated | Contents |
| --- | --- | --- |
| `ai-inference-adlist.txt` | Yes | Recommended profile as an ABP-style adlist (`||api.openai.com^`). Each entry blocks the domain and all of its subdomains. |
| `ai-inference-adlist-full.txt` | Yes | Full profile as an adlist. |
| `ai-inference-domains.txt` | Yes | Recommended profile as plain domains for `pihole --wild`. |
| `ai-inference-domains-full.txt` | Yes | Full profile as plain domains. |
| `ai-inference-regex.txt` | Yes | POSIX extended regular expressions for `pihole --regex`, covering Vertex AI regional endpoints added after the review date. |
| `install.sh` | No | Adds the wildcard domains and regex filters through the `pihole` CLI, then reloads the lists. |

## Option A: subscribe to the adlist

1. Host `ai-inference-adlist.txt` where Pi-hole can fetch it, or use the raw file URL from your fork of this repository.
2. In the Pi-hole web interface, go to **Lists**, add the URL, and assign it to the groups in scope.
3. Run `pihole -g` to update gravity.

Adlists are refreshed on Pi-hole's weekly gravity schedule, so catalog updates arrive without manual steps. Regex filters cannot be delivered through an adlist; use option B for those, or add the single line in `ai-inference-regex.txt` under **Domains > Regex filter**.

## Option B: install locally

```bash
chmod +x install.sh
sudo ./install.sh            # recommended profile
sudo ./install.sh full       # full profile
```

The script reads the domain and regex files, skips comments and blank lines, and calls `pihole --wild` and `pihole --regex`. Running it again is safe, because Pi-hole ignores entries that already exist.

## Verify

```bash
pihole -q api.openai.com
dig @<pihole-address> api.openai.com +short    # returns 0.0.0.0 with the default blocking mode
```

## Notes

- Pi-hole blocks only clients that use it for DNS. Block other outbound DNS, DNS over TLS, and known DNS-over-HTTPS resolvers at the firewall ([section 8](../../sections/08-dns-policy.md)).
- The Cloudflare Workers AI path cannot be expressed in DNS and is not included.

## References

- [The `pihole` command](https://docs.pi-hole.net/main/pihole-command/)
- [Regex blocking](https://docs.pi-hole.net/regex/overview/)
- [Allowlist and denylist editing](https://docs.pi-hole.net/guides/misc/allowlist-denylist/)
