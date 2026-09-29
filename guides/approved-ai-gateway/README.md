# Approved AI gateway

Most organizations cannot deny all AI inference; some teams have legitimate, approved uses. The pattern that preserves the protection in this repository is a single approved path:

1. Deploy one AI gateway that holds the provider credentials, authenticates internal callers, enforces budgets and model allowlists, and logs every request.
2. Allow egress to the approved provider endpoints **only from the gateway**.
3. Deny the provider hostnames from every other workload, using the rule files in [`rules/`](../../rules/).

A compromised server or an unauthorized tool then has no direct route to frontier inference, and the only remaining route requires an identity the gateway recognizes and leaves an audit trail. The reasoning is covered in [section 18](../../sections/18-explicit-exceptions.md).

The gateway products below provide this functionality natively. There is nothing to import from this repository into them; the repository supplies the deny rules for everything else.

## Network policy around the gateway

Place the allow for the gateway above the deny rules, and scope it to the gateway's source addresses and the specific providers it uses. For example, in Squid:

```text
acl ai_gateway src 10.20.0.10/32
acl ai_gateway_providers dstdomain api.anthropic.com api.openai.com
http_access allow ai_gateway ai_gateway_providers
include /etc/squid/ai-inference/squid.conf
```

The equivalent in other products is an allow rule for the gateway's source identity or address, ranked above the rule that references the AI inference list: a Security policy rule in PAN-OS, a URL filtering rule with a location or group criterion in Zscaler, a Real-time Protection policy exception in Netskope, a Gateway policy with a source IP or identity selector in Cloudflare One, or a separate Umbrella policy for the gateway identity.

## Gateway options

### LiteLLM Proxy (self-hosted, open source)

An OpenAI-compatible proxy in front of more than one hundred providers. It issues virtual keys to internal users and teams, enforces per-key budgets, rate limits, and model access lists, and logs requests to your observability stack.

- [LiteLLM Proxy overview](https://docs.litellm.ai/docs/simple_proxy)
- [Virtual keys](https://docs.litellm.ai/docs/proxy/virtual_keys)
- [Budgets and rate limits](https://docs.litellm.ai/docs/proxy/users)
- [Production deployment](https://docs.litellm.ai/docs/proxy/deploy)

### Kong AI Gateway

Kong Gateway plugins that proxy requests to model providers under a single API, with authentication, rate limiting, prompt guarding, and logging from the wider Kong plugin set.

- [Kong AI Gateway](https://developer.konghq.com/ai-gateway/)
- [AI Proxy plugin](https://developer.konghq.com/plugins/ai-proxy/)
- [AI Prompt Guard plugin](https://developer.konghq.com/plugins/ai-prompt-guard/)

### Azure API Management

The GenAI gateway capabilities in API Management front Azure OpenAI and other model endpoints with token-based rate limits (`llm-token-limit`), token metrics, semantic caching, and managed-identity authentication to the backend. Combine it with private endpoints on the Azure OpenAI resource and disable public network access, so the resource is reachable only through API Management.

- [GenAI gateway capabilities in API Management](https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities)
- [Import an Azure OpenAI API](https://learn.microsoft.com/en-us/azure/api-management/azure-openai-api-from-specification)
- [`llm-token-limit` policy](https://learn.microsoft.com/en-us/azure/api-management/azure-openai-token-limit-policy)
- [Azure OpenAI with private endpoints](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/network)

### Google Cloud Agent Gateway and VPC Service Controls

Agent Gateway governs agent and model traffic on Google Cloud. VPC Service Controls places the Vertex AI API inside a service perimeter, so it can be called only from authorized networks and identities, which blocks use of stolen credentials from outside the perimeter.

- [Agent Gateway](https://cloud.google.com/agent-gateway)
- [VPC Service Controls overview](https://docs.cloud.google.com/vpc-service-controls/docs/overview)
- [VPC Service Controls with Vertex AI](https://cloud.google.com/vertex-ai/docs/general/vpc-service-controls)

### Amazon Bedrock through VPC endpoints

Amazon Bedrock is reachable privately through interface VPC endpoints (AWS PrivateLink). An endpoint policy limits which principals and models can be used through the endpoint, and an identity policy or service control policy can deny model invocation that does not arrive through it. With that in place, the public `bedrock-runtime` and `bedrock-mantle` hostnames can stay on the deny lists for all workloads.

An example service control policy statement, to be adapted to your endpoint IDs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyBedrockInvocationOutsideApprovedEndpoint",
      "Effect": "Deny",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": { "aws:SourceVpce": ["<approved-vpc-endpoint-id>"] }
      }
    }
  ]
}
```

The Converse and ConverseStream APIs are authorized through the same `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` actions.

- [Use interface VPC endpoints with Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/vpc-interface-endpoints.html)
- [Protect jobs using a VPC](https://docs.aws.amazon.com/bedrock/latest/userguide/usingVPC.html)
- [Control access to VPC endpoints using endpoint policies](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-access.html)
- [Identity-based policy examples for Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/security_iam_id-based-policy-examples.html)

## Provider-side restrictions

Some providers can also restrict API use to known source addresses, which complements the gateway:

- OpenAI supports [API IP allowlisting](https://help.openai.com/en/articles/20001201-ip-allowlisting-for-the-openai-api) at the organization or project level. Restrict it to the gateway's egress addresses.

## Checklist

- [ ] The gateway is the only workload with an egress allow for the approved providers.
- [ ] Provider API keys exist only in the gateway's secret store, and personal keys are revoked.
- [ ] Every other workload uses the recommended or full deny profile.
- [ ] Gateway logs are forwarded to the SIEM, with alerts on unusual volume or new callers ([section 15](../../sections/15-detection.md)).
- [ ] DNS, proxy-bypass, and ECH controls are in place, so the deny rules cannot be bypassed ([section 7](../../sections/07-prevent-proxy-bypass.md), [section 8](../../sections/08-dns-policy.md)).
