# 18. Approved exceptions

Suppose a development team has a legitimate need to use OpenAI. Do not grant:

```text
entire corporate network -> api.openai.com
```

Instead, route approved use through a single gateway:

```text
AI gateway
      |
      v
api.openai.com
```

and keep the deny in place for everything else:

```text
all other hosts -> api.openai.com = DENY
```

Developers and services then call:

```text
internal-ai-gateway.corp
```

The gateway enforces:

- Approved models
- Quotas and budgets
- Authentication
- Data loss prevention
- Logging
- Prompt filtering
- Project attribution
- API-key isolation

## Restricting both directions

OpenAI supports API IP allowlisting, which restricts an organization's or project's API use to specified source addresses. ([IP allowlisting for the OpenAI API](https://help.openai.com/en/articles/20001201-ip-allowlisting-for-the-openai-api)) This allows the restriction to be enforced in both directions:

```text
Your firewall:
    only the AI gateway -> OpenAI

OpenAI organization:
    only the corporate AI gateway addresses -> your OpenAI project
```

A stolen OpenAI API key then has substantially less value outside your infrastructure.

## Applying the pattern

Apply the same pattern to each provider you intentionally retain from [section 2](02-inference-providers.md): one gateway may reach `api.anthropic.com`, `api.x.ai`, `api.cerebras.ai`, Bedrock, or Azure OpenAI, and every other workload remains on the denylist. Because the exception is narrow, those other workloads do not gain a private Claude or Kimi deployment; they lose the API, and they lack the hardware the weights require ([section 1](01-threat-model.md)).

Product options for the gateway (LiteLLM, Kong AI Gateway, Azure API Management, Google Cloud Agent Gateway, and Amazon Bedrock through VPC endpoints), together with the network rule that allows only the gateway, are described in the [approved AI gateway guide](../guides/approved-ai-gateway/README.md).
