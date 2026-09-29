# CrowdStrike Falcon Firewall Management

Remote address lists for Falcon Firewall Management rules that deny inbound connections from AI crawlers to servers protected by the Falcon sensor.

## Files

| File | Contents |
| --- | --- |
| `crawler-prefixes-ipv4.txt` | Aggregated, collapsed IPv4 prefixes published by OpenAI, Anthropic, Perplexity, and Amazon for their AI crawlers and user-triggered fetchers. |
| `crawler-prefixes-ipv6.txt` | The IPv6 equivalent. It is empty when none of the aggregated feeds publish IPv6 prefixes. |

Each file has one address or CIDR per line and no comments, so it can be pasted into a rule's remote address field or submitted through the API.

## Why only crawler addresses

Falcon Firewall Management rules match IP addresses, ports, protocols, and applications; they do not match DNS names or TLS SNI. AI inference APIs are served from shared CDN and cloud address space, so an address-based egress rule would either miss the endpoint or block unrelated services. The egress controls in this repository are therefore delivered through DNS, proxy, and SNI products, and Falcon is used for the inbound case, where the crawler operators publish authoritative address lists. For egress on Windows endpoints, use [Microsoft Defender for Endpoint](../microsoft-defender/) indicators or a proxy.

## Configure

1. In the Falcon console, go to **Endpoint security > Firewall > Firewall rule groups** and create a rule group for the server platform, for example `Block AI crawlers`.
2. Add an **inbound** rule with action **Block**, protocol **TCP**, local ports `80` and `443` (plus any other published ports), and the contents of `crawler-prefixes-ipv4.txt` as the remote address. Add a second rule for IPv6 when that file is not empty.
3. Attach the rule group to the firewall policy for the host group that serves public web content, and set the policy to **Enforce**.
4. Refresh the lists after each run of `tools/refresh_feeds.py`. For automated updates, use the Falcon Firewall Management API to replace the remote addresses in the rule.

If the combined list exceeds the address limit your console accepts for a single rule, split the file across several rules in the same rule group.

## References

- [Falcon Firewall Management documentation](https://falcon.crowdstrike.com/documentation/page/c0d9d4b9/firewall-management) (requires a Falcon login)
