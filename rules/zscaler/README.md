# Zscaler Internet Access

URL lists for a ZIA custom URL category.

## Files

| File | Contents |
| --- | --- |
| `ai-inference-urls.txt` | Recommended profile: core and extended inference destinations. |
| `ai-inference-urls-full.txt` | Full profile: adds candidate destinations. |

## Entry format

The lists follow the ZIA URL format guidelines:

- `api.openai.com` matches that host and every path on it, and no other host.
- `.openai.azure.com` uses the leading-period wildcard, which matches the domain and subdomains up to five levels deep. Zscaler does not accept `*.` wildcards.
- Vertex AI regional endpoints are enumerated, because ZIA wildcards apply only to the left of a full label.
- The Cloudflare Workers AI path entry is omitted because ZIA treats `*` inside a URL as a literal character. Where that path must be blocked, use a URL filtering rule with SSL inspection, or an approved gateway.

Entries are lowercase ASCII with no scheme, as required.

## Import

1. In the Zscaler Admin Console, go to **Administration > URL Categories** and add a custom category named, for example, `AI Inference APIs`.
2. Paste the contents of `ai-inference-urls.txt` into **Custom URLs**, or upload the file with the Bulk URL Upload tool.
3. In **Policy > URL & Cloud App Control**, add a rule for the custom category with action **Block**, ranked above rules that allow general browsing. Apply it to the users, groups, and locations in scope, including server and workload locations.
4. Enable SSL inspection for the category if you want path-level logging.
5. Save and activate the configuration.

## References

- [URL format guidelines](https://help.zscaler.com/zia/url-format-guidelines)
- [Configuring custom URL categories](https://help.zscaler.com/zia/configuring-custom-url-categories)
- [About the Bulk URL Upload tool](https://help.zscaler.com/zia/about-bulk-url-upload-tool)
