# F5 BIG-IP

Internal data groups and iRules that deny AI inference destinations on BIG-IP forward-proxy, SSL Orchestrator, and outbound forwarding virtual servers.

## Files

| File | Generated | Contents |
| --- | --- | --- |
| `ai-inference-datagroups.tmsh` | Yes | Recommended profile. Four `ltm data-group internal` objects: exact hosts, domain suffixes, label suffixes, and host/path entries. |
| `ai-inference-datagroups-full.tmsh` | Yes | Full profile. The same four data groups with candidate destinations added. |
| `ai-inference.irule` | Yes | For virtual servers with an HTTP profile (explicit proxy) and, when TLS is inspected, a client SSL profile. Checks the SNI in `CLIENTSSL_CLIENTHELLO`, then the CONNECT target or `Host` header and the request path in `HTTP_REQUEST`. |
| `ai-inference-sni-passthrough.irule` | Yes | For standard TCP virtual servers that forward TLS without decryption. Collects the first TLS record, parses the ClientHello `server_name` extension, and rejects matching connections. |

Both iRules share the same matching procedures, driven entirely by the data groups:

- `ai_inference_hosts` is an exact match (`class match ... equals`).
- `ai_inference_suffixes` is a subdomain match (`class match ... ends_with`), with keys such as `.openai.azure.com`.
- `ai_inference_label_suffixes` matches names whose first label ends with the key, such as `us-central1-aiplatform.googleapis.com` for `-aiplatform.googleapis.com`.
- `ai_inference_url_paths` matches a host plus a path pattern in which `*` is a wildcard. It is evaluated only when the HTTP request is visible.

## Install

1. Copy the files to the BIG-IP, for example to `/var/tmp/`.
2. Load the data groups. Loading again later replaces the records with the current catalog:

   ```bash
   tmsh load sys config merge file /var/tmp/ai-inference-datagroups.tmsh
   ```

3. Create the iRules in **Local Traffic > iRules** by pasting the file contents, or with tmsh:

   ```bash
   tmsh create ltm rule ai_inference_egress "$(cat /var/tmp/ai-inference.irule)"
   tmsh create ltm rule ai_inference_sni_passthrough "$(cat /var/tmp/ai-inference-sni-passthrough.irule)"
   ```

4. Attach `ai_inference_egress` to the explicit-proxy or SSL Orchestrator virtual server, or `ai_inference_sni_passthrough` to the outbound TCP forwarding virtual server. Do not attach both to the same virtual server.
5. Save the configuration with `tmsh save sys config`.

Blocked requests are logged to `local0.notice`, for example `AI inference TLS blocked: client=10.0.0.5 sni=api.openai.com`.

## Notes

- The passthrough iRule inspects only the first TLS record. A ClientHello split across several records, or one protected by Encrypted Client Hello, is released without a decision. Disable ECH in managed browsers and pair the iRule with DNS controls.
- An HTTP profile is required for `HTTP_REQUEST`, and a client SSL profile for `CLIENTSSL_CLIENTHELLO`. Events for profiles that are not attached do not fire.

## References

- [`class` command](https://clouddocs.f5.com/api/irules/class.html)
- [`SSL::extensions`](https://clouddocs.f5.com/api/irules/SSL__extensions.html)
- [`CLIENTSSL_CLIENTHELLO` event](https://clouddocs.f5.com/api/irules/CLIENTSSL_CLIENTHELLO.html)
- [`TCP::collect`](https://clouddocs.f5.com/api/irules/TCP__collect.html)
- [`ltm data-group internal` (tmsh reference)](https://clouddocs.f5.com/cli/tmsh-reference/latest/modules/ltm/ltm_data-group_internal.html)
