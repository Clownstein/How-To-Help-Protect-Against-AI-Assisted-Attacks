# Contributing

Contributions that keep the catalog accurate are the most valuable kind: new inference endpoints, retired hostnames, new Bedrock or Vertex AI regions, new crawler tokens, and corrections to product import formats.

## Ground rules

1. **Edit the catalog, not the rule files.** Every file under `rules/` except the per-directory `README.md`, `rules/squid/squid.conf`, `rules/squid/squid-intercept.conf`, `rules/bind-rpz/named.conf.snippet`, and `rules/pi-hole/install.sh` is generated. Hand edits are overwritten and fail the `--check` step.
2. **Cite a source.** Each egress entry needs a `source` that documents the hostname: the provider's API reference, quickstart, or SDK default, or a recognized provider directory. DNS resolution alone qualifies an entry only for the `candidate` tier.
3. **Names, not addresses, for egress.** Do not add IP addresses or CIDR ranges for inference providers. Their endpoints share CDN and cloud address space with unrelated services. If you resolve a new hostname, add its addresses to `egress.observed_inference_addresses.addresses` so the guard keeps them out of every generated list.
4. **Never add a broad parent domain.** Entries such as `googleapis.com`, `amazonaws.com`, `azure.com`, `cloudflare.com`, and `huggingface.co` are rejected by the generator through the `never_block` list.
5. **Standard library only.** The tools must run on a clean Python 3.10+ installation.

## Catalog fields

| Field | Meaning |
| --- | --- |
| `value` | The hostname, parent domain, label suffix, or `host/path`. |
| `match` | `host` (exact name), `subdomains` (any name below `value`), `label_suffix` (first label ends with `value`, enumerated from `vertex_regions` for list products), or `url_path` (`host/path`, `*` matches one path segment). |
| `tier` | `core`, `extended`, or `candidate`. |
| `provider`, `service` | Human-readable names used in descriptions, Defender titles, and Suricata messages. |
| `source` | URL, or repository path for entries sourced from the point-in-time observations in section 2. |

Amazon Bedrock hosts are listed explicitly under `egress.bedrock.services`, taken from the AWS endpoint tables. Vertex AI regions are listed under `egress.vertex_regions`.

Crawler feeds live under `inbound.feeds`. Set `aggregate` to `true` only for feeds whose addresses serve AI crawling or AI user-triggered fetching exclusively; general search crawlers such as Googlebot and Applebot are included for verification and are not aggregated into block lists.

## Workflow

```bash
# 1. Edit catalog/catalog.json. Update "reviewed" to today's date when you change egress entries,
#    because the BIND RPZ serial is derived from it.
# 2. Regenerate.
python tools/generate.py
# 3. Optionally refresh the crawler feeds.
python tools/refresh_feeds.py
# 4. Run the checks.
python tools/generate.py --check
python -m unittest discover -s tests -v
```

Commit the catalog change and the regenerated files together.

## Suricata SIDs

Egress rules use SID ranges derived from `suricata.sid_base` plus a stable hash of each entry, so adding or reordering entries does not renumber existing rules. If you change the logic of an existing rule, increment `suricata.rev`.

## Reporting a problem with a product format

If a vendor rejects a generated file, open an issue with the product version, the error text, and the offending line. Include a link to the vendor documentation that describes the accepted format.
