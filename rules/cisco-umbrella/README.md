# Cisco Umbrella

Destination lists for Umbrella DNS and Secure Internet Gateway (SIG) policies.

## Files

| File | Contents |
| --- | --- |
| `ai-inference-destinations.txt` | Recommended profile: core and extended inference destinations. |
| `ai-inference-destinations-full.txt` | Full profile: adds candidate destinations. |

## Entry format

- One domain per line, with no scheme, path, or comments, as the bulk upload requires.
- An Umbrella destination such as `openai.azure.com` implicitly covers every subdomain, so tenant-wide families are listed by their parent domain and redundant children are removed.
- Vertex AI regional endpoints are enumerated.
- The Cloudflare Workers AI path is not included. Umbrella DNS policies cannot match paths, and blocking `api.cloudflare.com` would block the entire Cloudflare API.

## Import

1. In the Umbrella dashboard, go to **Policies > Policy Components > Destination Lists** and add a list named, for example, `AI Inference APIs`, with **Block** as the default action.
2. Select **Upload** (or **Add in Bulk**) and choose `ai-inference-destinations.txt`.
3. Attach the destination list to the DNS policy, and to the web policy if SIG is in use, for the identities in scope. Include server and network identities, not just roaming users.
4. Save, then confirm with a test lookup of `api.openai.com` from a protected identity; Umbrella should return its block page address.

## References

- [Add destinations in bulk](https://securitydocs.cisco.com/docs/umbrella-dns/olh/146782.dita)
- [Add a web destination list](https://securitydocs.cisco.com/docs/umbrella-sig/olh/151166.dita)
