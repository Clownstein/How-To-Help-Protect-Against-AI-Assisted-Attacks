# How to Help Protect Against AI Assisted Attacks

An open-source rule pack and reference guide for restricting access to hosted AI inference from systems you operate, and for controlling AI crawlers that reach systems you publish.

## Why hosted inference is the control point

The most capable models are not available to run locally. Claude, GPT, and Gemini have no published weights and are reachable only through their providers' APIs. The strongest open-weight models, such as GLM-5.3 and Kimi K3, require a multi-GPU cluster (for example, eight H100-class accelerators) to serve at useful speed. A compromised server, a CI runner, or an unmanaged workstation does not have that hardware.

An attacker who wants frontier-grade model assistance from inside your environment therefore depends on reaching a hosted inference endpoint: a first-party API, a cloud platform such as Amazon Bedrock or Vertex AI, or a third-party host that serves open-weight models. Denying those destinations by name removes that capability and leaves only the small models that fit on the local hardware. The reasoning is covered in detail in [section 1](sections/01-threat-model.md) and [section 19](sections/19-open-source-models.md).

Inference endpoints sit on shared CDN and cloud address space. Blocking by IP address either misses the endpoint or blocks unrelated services, so every egress rule in this repository matches DNS names, TLS SNI, or HTTP host and path. Addresses are used only for inbound crawler verification, where the operators publish authoritative feeds.

## Repository layout


| Path                                               | Contents                                                                                                                                                                                                                                                       |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `[catalog/catalog.json](catalog/catalog.json)`     | The single source of truth: inference destinations with tier, provider, and source; enumerated Amazon Bedrock and Vertex AI regional hosts; crawler user-agent tokens; crawler address feeds; and a guard list of shared addresses that must never be blocked. |
| `[rules/](rules/)`                                 | Importable rule files, one directory per product. Every file except the per-directory `README.md`, the Squid and BIND configuration fragments, and the Pi-hole installer is generated from the catalog.                                                        |
| `[guides/](guides/)`                               | Configuration guides for services whose protection is built in and has nothing to import: Cloudflare WAF, AWS WAF, and approved AI gateways.                                                                                                                   |
| `[tools/generate.py](tools/generate.py)`           | Offline, deterministic generator for every file under `rules/` and the generated files under `guides/`.                                                                                                                                                        |
| `[tools/refresh_feeds.py](tools/refresh_feeds.py)` | Downloads the published crawler address feeds, validates them, updates the snapshots in `data/inbound-bot-ips/`, and regenerates the rules.                                                                                                                    |
| `[tests/test_generate.py](tests/test_generate.py)` | Unit tests for catalog coverage, wildcard handling, the shared-address guard, and Suricata SID uniqueness.                                                                                                                                                     |
| `[sections/](sections/)`                           | The reference guide, sections 1 through 20. Start at `[info.md](info.md)`.                                                                                                                                                                                     |
| `[plugins/](plugins/)`                             | Installable plugins for WordPress, DirectAdmin, and WHM/cPanel. Each one lets an administrator choose which crawler tokens to enforce. The WordPress plugin can also block WordPress HTTP API calls to selected inference services.                            |
| `[rule_implementation.md](rule_implementation.md)` | Maps each defender product to its rule directory, import method, and matching behavior.                                                                                                                                                                        |




## Supported products



### Egress: deny hosted inference from your network


| Product                                   | Directory                                               | What you import                             |
| ----------------------------------------- | ------------------------------------------------------- | ------------------------------------------- |
| Palo Alto Networks NGFW and Prisma Access | `[rules/palo-alto](rules/palo-alto/)`                   | URL external dynamic list                   |
| Zscaler Internet Access                   | `[rules/zscaler](rules/zscaler/)`                       | Custom URL category list                    |
| Netskope                                  | `[rules/netskope](rules/netskope/)`                     | Exact and regex URL lists                   |
| Cloudflare Gateway                        | `[rules/cloudflare-gateway](rules/cloudflare-gateway/)` | Domain list CSV                             |
| Cisco Umbrella                            | `[rules/cisco-umbrella](rules/cisco-umbrella/)`         | Destination list                            |
| Squid                                     | `[rules/squid](rules/squid/)`                           | ACL files and configuration fragments       |
| F5 BIG-IP                                 | `[rules/f5](rules/f5/)`                                 | Data groups and iRules                      |
| BIND and other RPZ-capable resolvers      | `[rules/bind-rpz](rules/bind-rpz/)`                     | Response policy zone                        |
| Pi-hole v6                                | `[rules/pi-hole](rules/pi-hole/)`                       | Adlist, wildcard domains, and regex filters |
| Microsoft Defender for Endpoint           | `[rules/microsoft-defender](rules/microsoft-defender/)` | Indicator import CSV                        |
| Suricata                                  | `[rules/suricata](rules/suricata/)`                     | TLS SNI, DNS, and HTTP rules                |




### Inbound: control AI crawlers reaching your sites


| Product                     | Directory                                         | What you import                                                                                       |
| --------------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Any web server              | `[rules/robots-txt](rules/robots-txt/)`           | `robots.txt` variants                                                                                 |
| nginx                       | `[rules/nginx](rules/nginx/)`                     | `map` and `geo` configuration                                                                         |
| Suricata                    | `[rules/suricata](rules/suricata/)`               | HTTP user-agent rules                                                                                 |
| CrowdStrike Falcon Firewall | `[rules/crowdstrike](rules/crowdstrike/)`         | Remote address lists                                                                                  |
| Palo Alto Networks          | `[rules/palo-alto](rules/palo-alto/)`             | IP external dynamic list                                                                              |
| Any firewall or WAF         | `[rules/ip-feeds](rules/ip-feeds/)`               | Per-operator and aggregate prefix lists, plus `anthropic-network.txt` for Anthropic-registered ranges |
| Cloudflare WAF              | `[guides/cloudflare-waf](guides/cloudflare-waf/)` | Built-in controls plus a custom rule expression                                                       |
| AWS WAF                     | `[guides/aws-waf](guides/aws-waf/)`               | Bot Control `CategoryAI` plus optional IP sets and regex pattern sets                                 |


Organizations that permit some AI use should route it through a single approved gateway and deny the provider hostnames everywhere else. See `[guides/approved-ai-gateway](guides/approved-ai-gateway/)`.

## Profiles

Every egress list is produced in two profiles.

- **Recommended** (`*.txt`, `*.csv`, `*.rpz`, `*.rules`, `*.tmsh` without a suffix) contains the `core` and `extended` tiers: provider-documented endpoints for first-party model APIs, the major cloud AI platforms, and the principal hosted open-weight providers and aggregators.
- **Full** (files ending in `-full`) adds the `candidate` tier: hostnames that resolved on the review date and appear in vendor quickstarts or provider directories, but that should be confirmed against current vendor documentation before enforcement.

Before enforcing either profile, remove any provider your organization has approved, or route that provider through the approved gateway described above.

## Keeping the rules current

```bash
python tools/refresh_feeds.py      # download crawler feeds, validate, regenerate
python tools/generate.py           # regenerate after editing catalog/catalog.json
python tools/generate.py --check   # exit 1 if committed files are out of date
python -m unittest discover -s tests -v
```

All tools use only the Python 3.10+ standard library. `generate.py` never touches the network. `refresh_feeds.py` keeps the last good snapshot when a download fails, parses incorrectly, or shrinks below half of the previous prefix count, and it records the result for each feed in `data/inbound-bot-ips/refresh-status.json`.

## Limitations

- Name-based controls depend on visibility of the destination name. Encrypted Client Hello, DNS over HTTPS to an uncontrolled resolver, and direct-to-IP connections can bypass SNI and DNS controls. [Section 7](sections/07-prevent-proxy-bypass.md) and [section 8](sections/08-dns-policy.md) describe the complementary controls.
- Cloud AI platforms use tenant-specific hostnames (for example, `<resource>.openai.azure.com`). Products that cannot express a subdomain wildcard need the tenant names your organization actually uses.
- `robots.txt` and user-agent matching are advisory and trivially spoofed. Pair them with the published address feeds when you need enforcement.
- The catalog reflects the review date recorded in `catalog/catalog.json`. Providers add endpoints and regions; contributions that keep it current are welcome.



## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Created by Albert Clownstein. Released under the [MIT License](LICENSE).