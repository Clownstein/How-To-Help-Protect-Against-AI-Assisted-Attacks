# Suricata

Detection and prevention rules for Suricata 7 and later: egress rules for AI inference destinations and inbound rules for AI crawler user agents.

## Files

| File | Direction | Contents |
| --- | --- | --- |
| `ai-inference.rules` | Egress | Recommended profile. One TLS SNI rule, one DNS query rule, and one HTTP Host rule per destination, plus an HTTP rule for the Cloudflare Workers AI path. |
| `ai-inference-full.rules` | Egress | Full profile. Same structure with candidate destinations added. |
| `ai-crawlers.rules` | Inbound | One HTTP user-agent rule per crawler token that is sent in the `User-Agent` header. |

## Rule design

Each egress destination produces three rules:

| Buffer | SID range | Matches |
| --- | --- | --- |
| `tls.sni` | 9100001 to 9199999 | TLS ClientHello server name |
| `dns.query` | 9200001 to 9299999 | DNS query name |
| `http.host` | 9300001 to 9399999 | HTTP Host header (plaintext HTTP, or decrypted traffic) |

Inbound crawler rules use 9400001 to 9499999.

A literal `content` match with `fast_pattern` selects candidate traffic, and an anchored `pcre` confirms the match:

- Exact hosts match the name and its subdomains: `/(?:^|\.)api\.openai\.com$/i`.
- Tenant-wide families match subdomains only: `/\.openai\.azure\.com$/i`.
- Vertex AI regional endpoints match any first label ending in `-aiplatform`: `/[a-z0-9-]-aiplatform\.googleapis\.com$/i`.

SIDs are derived from a stable hash of each catalog entry, so adding destinations does not renumber existing rules. The recommended and full files use the same SID for the same destination, so load only one of them.

All rules use `alert` with `classtype:policy-violation`. Every egress message starts with `AI-INFERENCE` and every crawler message with `AI-CRAWLER`, so they are easy to select for drop conversion and to search in EVE JSON output.

## Install with suricata-update

```bash
sudo mkdir -p /etc/suricata/rules/local
sudo cp ai-inference.rules ai-crawlers.rules /etc/suricata/rules/local/
sudo suricata-update --local /etc/suricata/rules/local/ai-inference.rules \
                     --local /etc/suricata/rules/local/ai-crawlers.rules
sudo suricata -T -c /etc/suricata/suricata.yaml
sudo systemctl reload suricata    # or: suricatasc -c reload-rules
```

To block in IPS mode (NFQUEUE or AF_PACKET inline), add this line to `/etc/suricata/drop.conf` and run `suricata-update` again:

```text
re:AI-INFERENCE
```

Without `suricata-update`, add the files to `rule-files:` in `suricata.yaml` instead.

## Notes

- `$HOME_NET` must describe your internal networks for the egress rules, and your published services for the inbound rules.
- TLS SNI rules cannot see names protected by Encrypted Client Hello. The DNS rules still fire when clients use a resolver whose traffic Suricata observes.
- User-agent rules detect self-identified crawlers only. Use the address feeds in [`../ip-feeds`](../ip-feeds/) to identify traffic that uses a real crawler address, regardless of the header it sends.

## References

- [TLS keywords](https://docs.suricata.io/en/latest/rules/tls-keywords.html)
- [DNS keywords](https://docs.suricata.io/en/latest/rules/dns-keywords.html)
- [HTTP keywords](https://docs.suricata.io/en/latest/rules/http-keywords.html)
- [Rule management with suricata-update](https://docs.suricata.io/en/latest/rule-management/suricata-update.html)
