# Cloudflare Gateway

Domain lists for Cloudflare One (Zero Trust) Gateway DNS and HTTP policies.

## Files

| File | Contents |
| --- | --- |
| `ai-inference-domains.csv` | Recommended profile: core and extended inference destinations. |
| `ai-inference-domains-full.csv` | Full profile: adds candidate destinations. |

## Entry format

- The CSV has the `value,description` header that Cloudflare requires to recognize descriptions.
- Cloudflare hostname lists reject wildcard entries. Tenant-wide families such as Azure OpenAI are therefore listed by their parent domain (`openai.azure.com`) and must be used with the **Domain** selector, which matches the domain and all of its subdomains.
- Hostnames already covered by a parent entry are removed, so the list has no redundant or duplicate values.
- Vertex AI regional endpoints are enumerated.
- The Cloudflare Workers AI path is not included, because a domain list cannot express a path. To block it, add an HTTP policy with TLS inspection: selector **URL Path** matches regex `^/client/v4/accounts/[^/]+/ai/run` and selector **Host** is `api.cloudflare.com`, action **Block**.

The recommended list is within the 1,000-entry limit for Standard plans. The generator warns if a profile grows beyond it.

## Import

1. In the Cloudflare One dashboard, go to **My Team > Lists** (or **Reusable components > Lists**) and select **Upload CSV**.
2. Name the list, for example `AI Inference APIs`, choose list type **Domains**, and upload `ai-inference-domains.csv`.
3. Create a **DNS policy**: selector **Domain**, operator **in list**, value `AI Inference APIs`, action **Block**.
4. If HTTP filtering is enabled, create a matching **HTTP policy** with selector **Domain in list** and action **Block**, so connections that bypass Gateway DNS are still stopped.
5. Place both policies above any allow policies.

Terraform users can load the CSV with `csvdecode(file("ai-inference-domains.csv"))` into a `cloudflare_zero_trust_list` resource.

## References

- [Lists](https://developers.cloudflare.com/cloudflare-one/reusable-components/lists/)
- [DNS policies](https://developers.cloudflare.com/cloudflare-one/traffic-policies/dns-policies/)
- [HTTP policies](https://developers.cloudflare.com/cloudflare-one/traffic-policies/http-policies/)
