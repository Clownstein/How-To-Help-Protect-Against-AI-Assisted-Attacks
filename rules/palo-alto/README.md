# Palo Alto Networks NGFW and Prisma Access

External dynamic lists (EDLs) for PAN-OS firewalls, Panorama, and Prisma Access.

## Files

| File | EDL type | Direction | Contents |
| --- | --- | --- | --- |
| `ai-inference-url-edl.txt` | URL List | Egress | Recommended profile: core and extended inference destinations. |
| `ai-inference-url-edl-full.txt` | URL List | Egress | Full profile: adds candidate destinations. |
| `ai-crawlers-ip-edl.txt` | IP Address List | Inbound | Aggregated, collapsed prefixes published by OpenAI, Anthropic, Perplexity, and Amazon for their AI crawlers and user-triggered fetchers. |

## Entry format

The URL lists follow the PAN-OS URL category exception guidelines:

- `api.openai.com/` matches the host and every path on it. The trailing slash prevents the entry from also matching `api.openai.com.example.net`.
- `*.openai.azure.com/` matches every tenant resource below the domain. The asterisk is a whole-token wildcard, as PAN-OS requires.
- `api.cloudflare.com/client/v4/accounts/*/ai/run` matches only the Cloudflare Workers AI inference path. The rest of the Cloudflare API is not affected. Path matching requires SSL decryption; without decryption, the firewall sees only the SNI and this entry has no effect.
- Vertex AI regional endpoints are enumerated (`us-central1-aiplatform.googleapis.com/` and so on) because a URL-list wildcard cannot express "first label ends with `-aiplatform`".

The IP list contains one prefix per line with no comments.

## Import

1. Host the files on an internal web server that the firewall management plane can reach over HTTPS, or reference the raw file URL from your fork of this repository.
2. In **Objects > External Dynamic Lists**, add a list of type **URL List** with the source URL for `ai-inference-url-edl.txt`. Set the check interval to **Hourly** or **Daily**.
3. Reference the EDL in the **URL Filtering** profile with action **block**, or add it as a URL category match in a Security policy rule with action **Deny**, placed above rules that allow general web access.
4. For inbound crawler control, add a list of type **IP Address List** pointing at `ai-crawlers-ip-edl.txt` and use it as the source address in a deny rule in front of your published applications.
5. Commit, then confirm with `request system external-list show type url name <edl-name>`.

## Notes

- Without SSL decryption, URL filtering on HTTPS uses the SNI and the certificate names; host entries still work, path entries do not.
- Remove any destination your organization has approved before importing, or place an allow rule for the approved gateway above the deny rule.

## References

- [Formatting guidelines for an external dynamic list](https://docs.paloaltonetworks.com/network-security/security-policy/administration/objects/external-dynamic-lists/formatting-guidelines-for-an-external-dynamic-list)
- [Guidelines for URL category exceptions](https://docs.paloaltonetworks.com/advanced-url-filtering/administration/configuring-url-filtering/url-category-exceptions/guidelines-for-url-category-exceptions)
- [Configure the firewall to access an external dynamic list](https://docs.paloaltonetworks.com/network-security/security-policy/administration/objects/external-dynamic-lists/configure-the-firewall-to-access-an-external-dynamic-list)
