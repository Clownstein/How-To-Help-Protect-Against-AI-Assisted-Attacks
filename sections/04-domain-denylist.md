# 4. Inference-provider domain denylist

Deny the following names from workloads you operate. This is the control that removes Claude, GPT, Gemini, and hosted cluster-scale open-weight models from a system that cannot load the weights itself ([section 1](01-threat-model.md)).

The authoritative list is [`catalog/catalog.json`](../catalog/catalog.json). The generator converts it into ready-to-import files for each product in [`rules/`](../rules/); [rule_implementation.md](../rule_implementation.md) maps products to directories. The lists below explain what the catalog contains and why.

## Core tier

The core tier covers the primary frontier-model APIs:

```text
api.anthropic.com
api.openai.com
generativelanguage.googleapis.com
*.openai.azure.com

bedrock-runtime.<region>.amazonaws.com
bedrock-mantle.<region>.api.aws

api.cohere.com
api.mistral.ai
api.together.xyz
api.groq.com
api.fireworks.ai
```

Bedrock hostnames are enumerated per region from the AWS endpoint tables rather than expressed as a wildcard, because `*.amazonaws.com` and `*.api.aws` carry unrelated AWS services ([section 12](12-amazon-bedrock.md)).

## Extended tier

Add the extended tier where the corresponding service is not an approved business dependency. The `recommended` profile contains the core and extended tiers.

```text
api.perplexity.ai
api.deepseek.com
api.x.ai
api.moonshot.ai
api.moonshot.cn
api.meta.ai
api.cerebras.ai
api.sambanova.ai
openrouter.ai
router.huggingface.co
api.together.ai

*.cognitiveservices.azure.com
*.services.ai.azure.com

aiplatform.googleapis.com
aiplatform.us.rep.googleapis.com
aiplatform.eu.rep.googleapis.com
REGION-aiplatform.googleapis.com
```

Vertex AI regional endpoints take the form `REGION-aiplatform.googleapis.com`, for example `us-central1-aiplatform.googleapis.com`. The region is part of the first label, so the pattern `*.aiplatform.googleapis.com` does not match them. Products that accept regular expressions receive the pattern `(^|\.)[a-z0-9-]+-aiplatform\.googleapis\.com$`; products that accept only literal names receive the regional hostnames enumerated from the catalog's `vertex_regions` list. The multi-region hosts `aiplatform.us.rep.googleapis.com` and `aiplatform.eu.rep.googleapis.com` are listed explicitly.

`api.cloudflare.com` serves the entire Cloudflare API. Where the enforcement point can match URL paths, deny only the Workers AI path:

```text
api.cloudflare.com/client/v4/accounts/*/ai/run
```

A hostname-wide deny of `api.cloudflare.com` also denies DNS, Zero Trust, and Workers administration.

## Candidate tier

These hostnames resolved on 27 September 2026 and are included only in the `full` profile. Confirm each against the vendor's current documentation before enforcement. Details and observed addresses are in [section 2](02-inference-providers.md).

```text
api.replicate.com
api.ai21.com
api.novita.ai
api.deepinfra.com
api.featherless.ai
api.hyperbolic.xyz
inference.baseten.co
api.voyageai.com
api.jina.ai
queue.fal.run
api.stability.ai
api.writer.com
api.upstage.ai
dashscope.aliyuncs.com
dashscope-intl.aliyuncs.com
open.bigmodel.cn
api.minimax.io
api.minimaxi.com
api.siliconflow.com
api.siliconflow.cn
api.friendli.ai
llm.chutes.ai
api.bfl.ai
integrate.api.nvidia.com
inference.api.nscale.com
*.runpod.ai
*.modal.run
```

`*.runpod.ai` and `*.modal.run` also match GPU sandboxes and customer applications. Use them in an allowlist-based egress policy, or narrow them to the specific API hostnames in use.

## Wildcards to avoid

Do not deny the following parent domains:

```text
*.googleapis.com
*.amazonaws.com
*.api.aws
*.azure.com
*.cloudflare.com
*.huggingface.co
*.aliyuncs.com
```

Each carries a large number of unrelated services, and blocking one causes widespread outages. The catalog records the most important of these under `never_block`, and the generator refuses to build if any entry targets one of them.
