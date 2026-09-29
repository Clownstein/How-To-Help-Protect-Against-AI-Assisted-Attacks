# 16. Detecting API authentication patterns

Where TLS inspection is operated, and where it is appropriate and legally permitted, model API requests carry recognizable indicators.

| Provider | Host | Authentication indicator |
| --- | --- | --- |
| OpenAI | `api.openai.com` | `Authorization: Bearer` ([OpenAI API reference](https://platform.openai.com/docs/api-reference/backward-compatibility)) |
| Google Gemini | `generativelanguage.googleapis.com` | `x-goog-api-key` header ([Gemini API reference](https://ai.google.dev/api)) |
| Anthropic | `api.anthropic.com` | `x-api-key` and `anthropic-version` headers ([Claude API overview](https://platform.claude.com/docs/en/api/overview)) |
| Cohere | `api.cohere.com` | `Authorization: Bearer` ([Check API key](https://docs.cohere.com/v2/reference/check-api-key)) |

OpenAI-compatible services, including Groq, Together AI, Fireworks AI, Cerebras, SambaNova, OpenRouter, DeepSeek, Moonshot, and the Hugging Face router, send the same request shape to their own hosts:

```text
POST /v1/chat/completions
Authorization: Bearer <credential>
```

Cerebras documents `base_url="https://api.cerebras.ai/v1"`, and Hugging Face documents `https://router.huggingface.co/v1/chat/completions`. ([Cerebras OpenAI compatibility](https://inference-docs.cerebras.ai/resources/openai), [Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers/index))

The request path is also a useful indicator on hosts that are not in the catalog. `POST /v1/chat/completions`, `/v1/messages`, or `/v1/responses` to an unfamiliar hostname commonly indicates a new reseller or a self-hosted OpenAI-compatible endpoint.

## Handling credentials

**Never log the credential itself.** Record only its presence:

```text
Authorization header present: yes
x-api-key header present: yes
destination: api.openai.com
path: /v1/chat/completions
```

and not:

```text
Authorization: Bearer sk-...
```

Logging credentials would turn the detection pipeline into a store of live API keys, creating a second incident while investigating the first.
