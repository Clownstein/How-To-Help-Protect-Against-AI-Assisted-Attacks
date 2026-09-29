# 1. Threat model

This control denies workloads in your environment access to AI inference services. That denial is the practical constraint on an adversary who wants frontier-model assistance from a system you operate.

## Closed models require the vendor's API

Claude, GPT, and Gemini are closed models. Their weights are not published, so they cannot be run on a workstation, a laptop, or a single rented virtual machine. Every use of these models is a request to the vendor, or to a reseller in front of the vendor: `api.anthropic.com`, `api.openai.com`, `generativelanguage.googleapis.com`, and the other endpoints in [section 4](04-domain-denylist.md). A host that cannot open that connection cannot use those models, and it has no local fallback of equivalent capability.

## Frontier open-weight models require a cluster

Open-weight models can be downloaded, but those that approach the closed frontier are cluster workloads. As of September 2026:

- **GLM-5.3** has approximately 743 billion parameters. The FP8 checkpoint is approximately 743 GB and is sized for eight H200 or eight B200 GPUs. FP8 serving on H100 hardware requires approximately ten GPUs, and a 4-bit community quantization still requires on the order of one eight-GPU H100 node. ([GLM-5.3 GPU cloud guide](https://www.spheron.network/blog/deploy-glm-5-3-gpu-cloud/))
- **Kimi K3** has approximately 2.8 trillion parameters. The native weights are approximately 1.56 TB, and published serving configurations target clusters such as sixteen B200 GPUs. ([Best open source LLMs, September 2026](https://www.thundercompute.com/blog/best-open-source-llms))

An adversary without that hardware cannot move from a hosted frontier model to a local equivalent on a compromised host. Their realistic options are a public inference API, a smaller model that fits on the hardware available, or no model. The egress denylist removes the first option; [section 19](19-open-source-models.md) addresses the second.

## The loop this control interrupts

```text
compromised server
      |
      | prompt and collected data
      v
api.anthropic.com, api.openai.com, and other inference endpoints
      |
      | model output and instructions
      v
compromised server
      |
      | next exploitation, enumeration, or exfiltration step
      v
your environment
```

When the server cannot reach an inference provider, an agent built on Claude, GPT, Gemini, or a hosted frontier open-weight model loses the component performing its reasoning.

Outbound restriction interferes with:

- Malware that generates commands dynamically through a model.
- Agents that repeatedly query a model for their next action.
- Exfiltration of data into an external model API.
- Unauthorized users or applications submitting confidential material to public models.
- Agent frameworks that use OpenAI-compatible APIs.
- Browser-based and cloud-agent workflows that call those APIs from within the environment.
- Use of stolen API keys from within the environment.

## Scope boundary

The loop above exists only when the caller is inside a network you control. An adversary operating from their own connection can use Claude, ChatGPT, or Gemini directly and pay for API access with their own account. That traffic flows from their provider to the vendor and never crosses your network, so your egress policy does not observe it. The adversary then sends ordinary traffic to your services. Egress restrictions do not affect that session, and the adversary does not need to host a model to conduct it.

Inbound blocking of vendor addresses has the same limitation. Traffic that reaches your services originates from the adversary's own servers, residential proxies, or compromised hosts, not from the vendor's API addresses.

The egress control addresses the common case for automated misuse: a compromised host, malware, an internal agent, or an employee device on your network must reach a provider, and frontier capability is concentrated in providers that are no longer reachable. Few adversaries have eight or sixteen datacenter GPUs available as an alternative.

Inbound crawler controls, such as user-agent rules for `Claude-SearchBot` and the address feeds in [section 13](13-inbound-crawler-addresses.md), address a separate question: which automated clients may fetch your websites. They do not interrupt the loop above.

## Sources

- [GLM-5.3 GPU cloud guide](https://www.spheron.network/blog/deploy-glm-5-3-gpu-cloud/) (August 2026)
- [Best open source LLMs, September 2026](https://www.thundercompute.com/blog/best-open-source-llms)
