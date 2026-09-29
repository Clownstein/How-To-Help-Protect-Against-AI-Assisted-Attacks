# 19. Open-weight models and the compute constraint

Closed models have no local copy. Open-weight models do, which makes self-hosting the obvious bypass. It is limited, however, by the hardware the adversary actually controls.

## Frontier open-weight models

In September 2026, frontier-class open-weight models require deployment on the scale of a small GPU cluster:

| Model | Scale | Self-hosting requirement |
| --- | --- | --- |
| GLM-5.3 | Approximately 743B total parameters, approximately 39B active | FP8 weights of approximately 743 GB. The vLLM recipe targets eight H200 or eight B200 GPUs. FP8 on H100 hardware requires approximately ten GPUs; AWQ INT4 fits on one eight-GPU H100 node. ([GLM-5.3 GPU cloud guide](https://www.spheron.network/blog/deploy-glm-5-3-gpu-cloud/)) |
| Kimi K3 | Approximately 2.8T total parameters | MXFP4 weights of approximately 1.56 TB. Serving recipes target clusters such as sixteen B200 GPUs. ([Best open source LLMs, September 2026](https://www.thundercompute.com/blog/best-open-source-llms)) |

An adversary who has obtained a credential or a foothold on a Linux server does not have that hardware available. To use GLM-5.3 or Kimi K3, they must rent it or call a service that already hosts the model. GPU rental platforms and API resellers are additional entries on the egress denylist: Together AI, Fireworks AI, Groq, Cerebras, DeepInfra, Novita, and the remainder of the Hugging Face Inference Providers directory (Baseten, Cohere, Fal, Featherless, Nscale, OVHcloud, Public AI, Replicate, Scaleway, WaveSpeed, and Z.ai). ([Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers/index))

## Smaller open-weight models

Smaller models are a genuine option. Distilled and mid-size models, ranging from a few billion to a few tens of billions of parameters, run on a workstation, a single rented GPU, or a CPU at reduced speed. They can draft scripts, explain errors, and assist with routine attack steps. They are not a substitute for Claude, GPT, Gemini, GLM-5.3, or Kimi K3 on difficult problems. Blocking inference APIs does not remove this weaker class of model; it removes the stronger class from every host that cannot provide a GPU cluster of its own.

A compromised GPU server, or a cluster the adversary has already rented, is the exception: if the adversary already operates hardware large enough to load the weights, egress policy does not apply. That is a far smaller set of systems than every host with a Python interpreter.

## Effectiveness by threat

| Threat | Effectiveness of the egress denylist |
| --- | --- |
| Compromised internal host calling OpenAI, Anthropic, or Gemini | **High.** No local copy of those models exists as a fallback. |
| Compromised internal host calling a hosted frontier open-weight model (GLM, Kimi, DeepSeek, or the resellers in [section 4](04-domain-denylist.md)) | **High** for each listed hostname. |
| Compromised host that would require eight H200 or sixteen B200 GPUs to self-host GLM-5.3 or Kimi K3 | **High.** The hardware is absent, so the remaining path is an API. |
| Unauthorized employee submitting data to public model APIs | **High** while the device uses corporate egress. A home network is outside the policy. |
| Malware with a hardcoded cloud AI API | **High** until the operator changes the compiled endpoint to an unlisted provider. |
| External adversary using Claude, GPT, or Gemini from their own computer | **None** for that session. The request never originates in your network; the adversary is a client of the vendor, not a host of the model. |
| Adversary with an existing GPU cluster and the weights | **None.** Inference runs on hardware outside your network. |
| Small local model on a laptop or a single consumer GPU | **Low.** The policy does not observe it, and the model is considerably weaker than the frontier systems above. |
| Botnet or exploit framework that never calls a model | **None.** |
| Inbound request whose user agent merely claims to be `Claude-SearchBot` | **None**, unless the source address is verified against the feed in [section 13](13-inbound-crawler-addresses.md). |

The control provides AI service containment for the systems you operate. On those systems, frontier capability requires an outbound connection, and that connection can be denied.

## Sources

- [GLM-5.3 GPU cloud guide](https://www.spheron.network/blog/deploy-glm-5-3-gpu-cloud/) (August 2026)
- [Best open source LLMs, September 2026](https://www.thundercompute.com/blog/best-open-source-llms)
- [Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers/index)
