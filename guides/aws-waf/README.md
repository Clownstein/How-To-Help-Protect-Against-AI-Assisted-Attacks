# AWS WAF

AWS WAF identifies AI bots natively through the Bot Control managed rule group, so for CloudFront distributions, Application Load Balancers, API Gateway REST APIs, and AppSync APIs the core control is a configuration change with nothing to import. This guide describes that configuration and two optional additions built from this repository: IP sets from the published crawler feeds, and a regex pattern set of crawler user-agent tokens.

## 1. Bot Control `CategoryAI` (managed)

The Bot Control rule group (`AWSManagedRulesBotControlRuleSet`, 50 WCU at the Common inspection level) contains the rule `CategoryAI`, which matches artificial intelligence bots. Its default action is **Block**, and it applies to both verified and unverified bots. Matching requests receive the labels `awswaf:managed:aws:bot-control:bot:category:ai` and `awswaf:managed:aws:bot-control:CategoryAI`; verified bots also receive `awswaf:managed:aws:bot-control:bot:verified` and a bot-name label.

Recommended rollout:

1. In the AWS WAF console, open the protection pack (web ACL) and choose **Add rules > Add managed rule groups**.
2. Add **Bot Control** (`AWSManagedRulesBotControlRuleSet`) with inspection level **Common**.
3. Set the rule group to **Override all rule actions to Count** for an initial observation period.
4. Review matches in CloudWatch metrics, sampled requests, or the **AI Activity Dashboard** (available since February 2026), which breaks down AI bot traffic by bot and category.
5. Remove the Count override for `CategoryAI` so its default **Block** action takes effect. Leave overrides in place for other categories you do not intend to block.

To block only some AI bots, keep `CategoryAI` at Count and add a rule after the rule group that blocks requests carrying `awswaf:managed:aws:bot-control:bot:category:ai` together with the specific bot-name labels you choose.

Bot Control is billed per request inspected in addition to standard AWS WAF charges. A scope-down statement (for example, excluding static assets) limits the requests it evaluates.

## 2. IP sets from the published crawler feeds (optional)

The files [`rules/ip-feeds/ai-crawlers-ipv4.txt`](../../rules/ip-feeds/ai-crawlers-ipv4.txt) and [`rules/ip-feeds/ai-crawlers-ipv6.txt`](../../rules/ip-feeds/ai-crawlers-ipv6.txt) contain the collapsed prefixes that OpenAI, Anthropic, Perplexity, and Amazon publish for their AI crawlers and user-triggered fetchers. AWS WAF IP sets hold a single address family, so create one set per file.

```bash
aws wafv2 create-ip-set --name ai-crawlers-ipv4 --scope REGIONAL --region us-east-1 \
    --ip-address-version IPV4 --addresses file://<(jq -R . rules/ip-feeds/ai-crawlers-ipv4.txt | jq -s .)
```

For CloudFront, use `--scope CLOUDFRONT --region us-east-1`. Individual addresses must be written as `/32`, which the generated files already do. An IP set holds up to 10,000 addresses by default; check the line count of each file against the quota for your account.

To refresh an existing set after running `tools/refresh_feeds.py`:

```bash
lock=$(aws wafv2 get-ip-set --name ai-crawlers-ipv4 --scope REGIONAL --id <id> --query LockToken --output text)
aws wafv2 update-ip-set --name ai-crawlers-ipv4 --scope REGIONAL --id <id> --lock-token "$lock" \
    --addresses file://<(jq -R . rules/ip-feeds/ai-crawlers-ipv4.txt | jq -s .)
```

Reference the sets in a rule with an **IP set match** statement (OR the IPv4 and IPv6 sets) and action **Block**. This catches crawlers from those operators even when they send a generic browser user agent.

## 3. Regex pattern set of user-agent tokens (optional)

[`user-agent-regex-patterns.txt`](user-agent-regex-patterns.txt) is generated from the catalog. Each line is a lowercase alternation of crawler tokens, sized to stay within the AWS WAF limits of 200 characters per pattern and 10 patterns per set.

```bash
aws wafv2 create-regex-pattern-set --name ai-crawler-user-agents --scope REGIONAL --region us-east-1 \
    --regular-expression-list "$(jq -R '{RegexString: .}' guides/aws-waf/user-agent-regex-patterns.txt | jq -s -c .)"
```

Use it in a **Regex pattern set match** statement that inspects the `User-Agent` single header with the text transformation **LOWERCASE**, and action **Block**. The patterns are lowercase, so the transformation is required. If the token list outgrows one set, the generator writes `user-agent-regex-patterns-2.txt` and so on; create one pattern set per file and OR the match statements in the rule.

User-agent matching is spoofable in both directions. Combine it with `CategoryAI`, which verifies bots, and with the IP sets.

## Verification

- CloudWatch metrics for each rule show allowed, blocked, and counted requests.
- The AI Activity Dashboard in the AWS WAF console shows AI bot traffic by bot and category.
- Sampled requests show the labels applied to each request.

## References

- [AWS WAF Bot Control](https://docs.aws.amazon.com/waf/latest/developerguide/waf-bot-control.html)
- [Bot Control rule group reference](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html)
- [Adding the Bot Control rule group to a web ACL](https://docs.aws.amazon.com/waf/latest/developerguide/waf-bot-control-rg-using.html)
- [AI Activity Dashboard announcement](https://aws.amazon.com/about-aws/whats-new/2026/02/aws-waf-ai-activity-dashboard/)
- [Managing IP sets](https://docs.aws.amazon.com/waf/latest/developerguide/waf-ip-set-managing.html)
- [IP set match rule statement](https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-ipset-match.html)
- [Managing regex pattern sets](https://docs.aws.amazon.com/waf/latest/developerguide/waf-regex-pattern-set-managing.html)
- [Regex pattern set match rule statement](https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-regex-pattern-set-match.html)
- [AWS WAF quotas](https://docs.aws.amazon.com/waf/latest/developerguide/limits.html)
