# Netskope

URL lists for a Netskope custom category.

## Files

| File | List type | Contents |
| --- | --- | --- |
| `ai-inference-urls.txt` | Exact | Recommended profile: core and extended inference destinations. |
| `ai-inference-urls-full.txt` | Exact | Full profile: adds candidate destinations. |
| `ai-inference-regex.txt` | Regex | Patterns for Vertex AI regional endpoints (`REGION-aiplatform.googleapis.com`) and the Cloudflare Workers AI path. |

## Entry format

The lists follow the Netskope URL list best practices:

- `api.openai.com` is an exact host.
- `*.openai.azure.com` is a wildcard entry. Netskope requires the asterisk to be the first character followed by a period, and the entry also matches `openai.azure.com` itself.
- Lines starting with `#` are comments and are ignored on upload.
- Regex entries are PCRE without a scheme, as Netskope requires. They cover Vertex regions added after the review date and the `/client/v4/accounts/<id>/ai/run` path, without blocking the rest of `api.cloudflare.com`.

## Import

1. In the Netskope tenant, go to **Policies > Web > URL Lists** and create a list of type **Exact**. Upload `ai-inference-urls.txt`.
2. Create a second list of type **Regex** and upload `ai-inference-regex.txt`. Netskope limits regex entries to 1,000 per tenant; this file uses two.
3. Under **Policies > Profiles > Custom Categories**, create a category such as `AI Inference APIs` that includes both lists.
4. In **Policies > Real-time Protection**, add a policy for the category with action **Block**, placed above policies that allow general web traffic. Include steering for servers and workloads if they send traffic through Netskope.
5. Apply the changes.

The lists can also be managed through the Netskope REST API v2, which accepts the list type (`exact` or `regex`) on upload.

## References

- [URL list best practices](https://docs.netskope.com/en/url-list-best-practices)
- [URL lists](https://docs.netskope.com/en/url-lists)
- [Custom categories](https://docs.netskope.com/en/custom-categories)
