# 11. Azure OpenAI and Microsoft Foundry

Azure OpenAI and Foundry serve the same class of closed models under tenant-specific hostnames. A server that cannot reach `*.openai.azure.com` cannot run GPT locally instead, because the weights are not available to it ([section 1](01-threat-model.md)).

## Service tags

Azure offers a better mechanism than copying observed addresses. Microsoft's network guidance places Azure OpenAI within the Cognitive Services networking infrastructure and identifies the `CognitiveServicesManagement` service tag. ([Configure virtual networks for Foundry Tools](https://learn.microsoft.com/en-us/azure/ai-services/cognitive-services-virtual-networks)) Service tags are backed by managed prefix lists that Microsoft updates as infrastructure changes. ([Azure service tags overview](https://learn.microsoft.com/en-us/azure/virtual-network/service-tags-overview))

No short, static address list specific to Azure OpenAI exists. Service tags change, and they include a large volume of Cognitive Services traffic unrelated to model inference, so they are appropriate for Azure network security groups and Azure Firewall but not as a general denylist.

## Hostname controls

For destination-specific control, deny:

```text
*.openai.azure.com
*.cognitiveservices.azure.com
*.services.ai.azure.com
```

Microsoft uses `*.openai.azure.com` as an example in managed outbound rules. ([Configure a managed virtual network for Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/how-to/managed-virtual-network))

The wildcard covers every tenant resource, including resources created by an adversary with their own subscription, such as:

```text
unapproved-resource.openai.azure.com
external-tenant.openai.azure.com
```

without enumerating Azure tenants.

Inspect's Azure AI Foundry integration requires a caller-supplied base URL (`AZUREAI_OPENAI_BASE_URL` or `AZUREAI_BASE_URL`) and the token audience `https://cognitiveservices.azure.com/.default`. A stolen key used from an unapproved host must still reach the tenant-specific hostname, so the wildcard deny applies even when the resource name is not known in advance. ([Inspect providers](https://inspect.aisi.org.uk/providers.html))

## Approved use

Where Azure OpenAI is an approved dependency, disable public network access on the resource, expose it through private endpoints, and route callers through Azure API Management. The [approved AI gateway guide](../guides/approved-ai-gateway/README.md) describes this configuration. The hostname deny then remains in force for all other workloads.
