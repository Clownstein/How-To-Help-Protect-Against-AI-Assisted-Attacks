# Microsoft Defender for Endpoint

Custom network indicators that block AI inference destinations on managed endpoints through Network Protection and Microsoft Edge SmartScreen.

## Files

| File | Contents |
| --- | --- |
| `ai-inference-indicators.csv` | Recommended profile. |
| `ai-inference-indicators-full.csv` | Full profile. |

If a profile grows beyond 500 rows, the generator splits it into `-part1.csv`, `-part2.csv`, and so on, because the portal accepts at most 500 indicators per import batch.

## CSV format

The columns follow the Defender indicator import schema: `indicatorType`, `indicatorValue`, `action`, `title`, `description`, `expirationTime`, `severity`, `recommendedActions`, `rbacGroups`, `category`, `mitretechniques`, `GenerateAlert`.

Each row is a `DomainName` indicator with action `Block`, severity `Medium`, alert generation enabled, and no expiration. `rbacGroups` is empty, which applies the indicator to all device groups; fill it in before import to scope the indicators.

Defender domain indicators take fully qualified names and do not document wildcard support. Tenant-wide families are therefore excluded from the CSV:

- `*.openai.azure.com`, `*.cognitiveservices.azure.com`, and `*.services.ai.azure.com` (Azure OpenAI and Foundry resources)
- `*.runpod.ai` and `*.modal.run` (full profile only)

Add indicators for the specific resource names you need to block, for example `contoso-eastus.openai.azure.com`. Vertex AI regional endpoints are enumerated and included.

## Import

1. In the Microsoft Defender portal, go to **Settings > Endpoints > Indicators > IP addresses and URLs/Domains**.
2. Select **Import** and choose `ai-inference-indicators.csv`.
3. Review the import summary. Rows rejected by the portal are listed with the reason.

The same indicators can be submitted through the Defender for Endpoint Import Indicators API (`POST /api/indicators/import`), which accepts up to 500 indicators per request.

## Requirements

- Microsoft Edge enforces the indicators through SmartScreen.
- Other browsers and non-browser processes, including command-line tools, scripts, and SDKs that call inference APIs, require **Network Protection in block mode**.
- For non-Microsoft browsers, Network Protection reads the SNI from the TLS handshake. Disable QUIC and Encrypted Client Hello in those browsers, as the Defender documentation requires, or the destination name is not visible.
- **Custom network indicators** must be turned on under **Settings > Endpoints > Advanced features**.

## References

- [Create indicators for IPs and URLs/domains](https://learn.microsoft.com/en-us/defender-endpoint/indicator-ip-domain)
- [Manage indicators (import format)](https://learn.microsoft.com/en-us/defender-endpoint/indicator-manage)
- [Turn on network protection](https://learn.microsoft.com/en-us/defender-endpoint/enable-network-protection)
