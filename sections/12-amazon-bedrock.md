# 12. Amazon Bedrock

Bedrock provides access to frontier models, including Claude and OpenAI models, without calling `api.anthropic.com` or `api.openai.com`. Those requests must still leave the network, because the weights are not available on the instance. Bedrock is difficult to express as an address range because its API is served from within AWS's very large address space.

## Endpoints

AWS's inference endpoints take the forms:

```text
bedrock-runtime.<region>.amazonaws.com
bedrock-mantle.<region>.api.aws
```

([Endpoints supported by Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/endpoints.html))

Mantle is also the endpoint Inspect uses for OpenAI models hosted on Bedrock (`bedrock-mantle.<region>.api.aws`, under the paths `/openai/v1` and `/v1`). ([Inspect providers](https://inspect.aisi.org.uk/providers.html))

Anthropic's Claude Platform on AWS uses a separate regional endpoint, `aws-external-anthropic.<region>.api.aws`, which also resolves to AWS address space. ([Anthropic IP addresses](https://platform.claude.com/docs/en/api/ip-addresses))

## Why address ranges do not work

AWS publishes its overall range feed:

```text
https://ip-ranges.amazonaws.com/ip-ranges.json
```

but notes that not every AWS service has independently published ranges. ([AWS IP address ranges](https://docs.aws.amazon.com/vpc/latest/userguide/aws-ip-ranges.html)) Blocking broad EC2 or AWS ranges would disrupt a large proportion of Internet services.

## Recommended control

Match on DNS name or SNI. Patterns such as `bedrock-runtime.*.amazonaws.com` have a variable label in the middle of the name, which most DNS filters, RPZ implementations, and URL-list products cannot express. The catalog therefore enumerates every documented regional hostname for the Bedrock Runtime (`bedrock-runtime`), Agents for Amazon Bedrock Runtime (`bedrock-agent-runtime`), and Bedrock Mantle (`bedrock-mantle`) endpoints, and every generated rule file contains that enumeration. Do not deny `*.amazonaws.com` or `*.api.aws`.

The control-plane endpoint `bedrock.<region>.amazonaws.com` is used for model and account management rather than inference, and is not included in the generated lists. Where Bedrock is not an approved dependency, it can be added to your product's local deny list as well.

Where Bedrock is approved, access it through interface VPC endpoints and restrict invocation to those endpoints with endpoint and identity policies ([approved AI gateway guide](../guides/approved-ai-gateway/README.md)). The public hostnames can then remain denied for all workloads.

## Crawlers are a separate dataset

Amazon's **web crawlers** (`Amazonbot`, `Amzn-SearchBot`, and `Amzn-User`) have their own published address lists, described in [section 13](13-inbound-crawler-addresses.md). Those are inbound source addresses, not Bedrock's API.
