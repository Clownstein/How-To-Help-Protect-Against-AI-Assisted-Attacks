# 14. robots.txt and user-agent controls

## robots.txt

Crawlers operated by legitimate organizations follow `robots.txt`. A group that disallows the primary AI crawlers:

```text
User-agent: GPTBot
User-agent: OAI-SearchBot
User-agent: ClaudeBot
User-agent: Claude-SearchBot
User-agent: Claude-User
Disallow: /
```

Anthropic states that its crawlers honor `robots.txt`. ([Anthropic crawler documentation](https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)) OpenAI documents its crawler controls, and each token is independent: allowing `OAI-SearchBot` while disallowing `GPTBot` is a supported combination. ([Overview of OpenAI crawlers](https://developers.openai.com/api/docs/bots))

Complete, generated files are in [`rules/robots-txt/`](../rules/robots-txt/): a recommended file, a training-only file that keeps the site visible in AI search, and a full file that adds the community list below.

`robots.txt` is a voluntary convention. It is **not a security boundary**, and a hostile client will disregard it. User-initiated fetchers (`ChatGPT-User`, `Claude-User`, `Perplexity-User`, and `Amzn-User`) may also fetch pages when a training or search token is disallowed, because a person requested the page.

## Operator-documented tokens

To enforce the policy rather than request it, place the token in `robots.txt` **and** in a WAF or web server rule. Where an operator publishes a full user-agent string, match the product token (`Claude-SearchBot`, `GPTBot`), because version numbers in the full string change.

| Token | Operator | Role | Sent in the User-Agent header | Address feed |
| --- | --- | --- | --- | --- |
| `GPTBot` | OpenAI | Training | Yes | [Section 13](13-inbound-crawler-addresses.md) |
| `OAI-SearchBot` | OpenAI | ChatGPT search | Yes | Section 13 |
| `OAI-AdsBot` | OpenAI | Advertising landing-page review | Yes | Section 13 |
| `ChatGPT-User` | OpenAI | User-initiated fetch | Yes | Section 13 |
| `ClaudeBot` | Anthropic | Training | Yes | `bots.json`, shared by the three Anthropic crawlers |
| `Claude-SearchBot` | Anthropic | Search indexing | Yes | Same feed |
| `Claude-User` | Anthropic | User-initiated fetch | Yes | Same feed |
| `PerplexityBot` | Perplexity | Search crawler | Yes | Section 13 |
| `Perplexity-User` | Perplexity | User-initiated fetch | Yes | Section 13 |
| `Amazonbot` | Amazon | Amazon services; may be used for model training | Yes | Section 13 |
| `Amzn-SearchBot` | Amazon | Search, including Alexa | Yes | Section 13 |
| `Amzn-User` | Amazon | User-initiated fetch | Yes | Section 13 |
| `Google-Extended` | Google | Opt-out of Gemini training and grounding | **No**; `robots.txt` only | None; fetches are made by Googlebot ([section 10](10-google-ranges.md)) |
| `Applebot-Extended` | Apple | Opt-out of Apple Intelligence training | **No**; `robots.txt` only | None; fetches are made by Applebot |

`Google-Extended` and `Applebot-Extended` are control tokens. Google and Apple read them from `robots.txt`, but their requests carry the `Googlebot` or `Applebot` user agent. A WAF or web server rule that matches `Google-Extended` or `Applebot-Extended` in the User-Agent header therefore never matches, and the generated nginx, Suricata, Cloudflare, and AWS rules omit them. Blocking `Googlebot` or `Applebot` themselves removes the site from those companies' search indexes.

Cloudflare Radar's AI assistant directory is recorded in the catalog by the `robots.txt` token on each bot page. Header rules use only the distinctive suffix of that page's HTTP user-agent, such as `Devin/` and `+https://devin.ai`, and they do not match the Chrome prefix those agents wrap around the token. Assistants that publish no HTTP user-agent and no robots token are omitted. The recommended preset includes these header matches. The generated files are the full list; this table stays the operator-documented set from section 13.

Representative request headers for the crawlers above:

```text
User-Agent: Claude-SearchBot
User-Agent: ClaudeBot
User-Agent: Claude-User
User-Agent: GPTBot
User-Agent: OAI-SearchBot
User-Agent: ChatGPT-User
User-Agent: PerplexityBot
User-Agent: Perplexity-User
```

## Enforcement at the WAF or web server

A reverse proxy can deny the token on the request itself, which `robots.txt` cannot. The header is still trivially forged, so pair user-agent rules with the address feeds in section 13 when handling traffic that claims to originate from OpenAI, Anthropic, Perplexity, Amazon, or Apple.

Ready-to-use configurations:

- **nginx:** [`rules/nginx/`](../rules/nginx/) provides a `map` on the user agent, a `geo` map built from the published crawler feeds, and a server-level rule that returns 403 when either matches, while still serving `/robots.txt`. An excerpt of the user-agent map:

  ```nginx
  map $http_user_agent $ai_crawler_user_agent {
      default 0;
      "~*(?:GPTBot|OAI-SearchBot|OAI-AdsBot|ChatGPT-User|ClaudeBot|Claude-SearchBot|Claude-User|PerplexityBot|Perplexity-User|Amazonbot|Amzn-SearchBot|Amzn-User|CCBot|Bytespider|Meta-ExternalAgent|Meta-ExternalFetcher|cohere-ai|MistralAI-User|Diffbot)" 1;
  }
  ```

- **Cloudflare:** the [Cloudflare WAF guide](../guides/cloudflare-waf/README.md) covers the built-in AI bot controls and AI Crawl Control, and provides a generated custom-rule expression that matches the tokens case-insensitively, in the form:

  ```text
  (lower(http.user_agent) contains "gptbot")
  or (lower(http.user_agent) contains "claude-searchbot")
  or (lower(http.user_agent) contains "claudebot")
  ```

- **AWS WAF:** the [AWS WAF guide](../guides/aws-waf/README.md) covers the Bot Control managed rule group and provides generated regex patterns for a regex pattern set.
- **Network IDS:** [`rules/suricata/ai-crawlers.rules`](../rules/suricata/ai-crawlers.rules) raises alerts for the same tokens in plaintext HTTP.

## Community token list

The [ai.robots.txt](https://github.com/ai-robots-txt/ai.robots.txt/blob/main/robots.txt) project maintains a single `Disallow: /` block covering a large set of AI crawler and agent tokens. The copy retrieved on 27 September 2026 follows; it is stored in the catalog as `community_robots_tokens` and included in `robots-full.txt`. It is broader than the operator-documented table above and includes SEO and scraping tokens (`SemrushBot-OCOB`, `Scrapy`, and `Diffbot`) alongside AI laboratory crawlers. Review it before publishing it on a public site, because it also names `GoogleOther`, `Applebot`, `Amazonbot`, and `FacebookBot`.

```text
User-agent: AddSearchBot
User-agent: AgentDataBot
User-agent: AgentTimes
User-agent: AI2Bot
User-agent: AI2Bot-DeepResearchEval
User-agent: Ai2Bot-Dolma
User-agent: aiHitBot
User-agent: AIWebIndex
User-agent: amazon-kendra
User-agent: amazon-QBusiness
User-agent: Amazonbot
User-agent: AmazonBuyForMe
User-agent: Amzn-SearchBot
User-agent: Amzn-User
User-agent: Andibot
User-agent: Anomura
User-agent: anthropic-ai
User-agent: ApifyBot
User-agent: ApifyWebsiteContentCrawler
User-agent: Applebot
User-agent: Applebot-Extended
User-agent: Aranet-SearchBot
User-agent: atlassian-bot
User-agent: Awario
User-agent: AzureAI-SearchBot
User-agent: bedrockbot
User-agent: bigsur.ai
User-agent: BixelBot
User-agent: Bravebot
User-agent: Brightbot
User-agent: Brightbot 1.0
User-agent: BuddyBot
User-agent: Bytespider
User-agent: CCBot
User-agent: Channel3Bot
User-agent: ChatGLM-Spider
User-agent: ChatGPT Agent
User-agent: ChatGPT-User
User-agent: Claude-Code
User-agent: Claude-SearchBot
User-agent: Claude-User
User-agent: Claude-Web
User-agent: ClaudeBot
User-agent: Cloudflare-AutoRAG
User-agent: CloudflareBrowserRenderingCrawler
User-agent: CloudVertexBot
User-agent: Code
User-agent: cohere-ai
User-agent: cohere-training-data-crawler
User-agent: Cotoyogi
User-agent: CragCrawler
User-agent: Crawl4AI
User-agent: Crawlspace
User-agent: Cursor
User-agent: Datenbank Crawler
User-agent: DeepSeekBot
User-agent: Devin
User-agent: Diffbot
User-agent: Diffbot-User
User-agent: DoubaoBot
User-agent: DuckAssistBot
User-agent: Echobot Bot
User-agent: EchoboxBot
User-agent: ERNIEBot
User-agent: ExaBot
User-agent: ExaSearchBot
User-agent: FacebookBot
User-agent: facebookexternalhit
User-agent: Factset_spyderbot
User-agent: FirecrawlAgent
User-agent: FriendlyCrawler
User-agent: GeistHaus-PageFetcher
User-agent: Gemini-Deep-Research
User-agent: Google-Agent
User-agent: Google-CloudVertexBot
User-agent: Google-Extended
User-agent: Google-Firebase
User-agent: Google-Gemini-CLI
User-agent: Google-NotebookLM
User-agent: GoogleAgent-Mariner
User-agent: GoogleAgent-URLContext
User-agent: GoogleOther
User-agent: GoogleOther-Image
User-agent: GoogleOther-Video
User-agent: GPTBot
User-agent: HenkBot
User-agent: iAskBot
User-agent: iaskspider
User-agent: iaskspider/2.0
User-agent: ICC-Crawler
User-agent: ImagesiftBot
User-agent: imageSpider
User-agent: img2dataset
User-agent: ISSCyberRiskCrawler
User-agent: kagi-fetcher
User-agent: Kangaroo Bot
User-agent: Kimi-Agent
User-agent: Kimi-SearchBot
User-agent: Kimi-User
User-agent: KimiBot
User-agent: KlaviyoAIBot
User-agent: KunatoCrawler
User-agent: laion-huggingface-processor
User-agent: LAIONDownloader
User-agent: LCC
User-agent: Lightpanda
User-agent: LinerBot
User-agent: Linguee Bot
User-agent: LinkupBot
User-agent: Manus-User
User-agent: meta-externalagent
User-agent: Meta-ExternalAgent
User-agent: meta-externalfetcher
User-agent: Meta-ExternalFetcher
User-agent: meta-webindexer
User-agent: MistralAI-Index
User-agent: MistralAI-Training
User-agent: MistralAI-User
User-agent: MistralAI-User/1.0
User-agent: Mozilla-Tabstack
User-agent: MyCentralAIScraperBot
User-agent: NagetBot
User-agent: netEstate Imprint Crawler
User-agent: newsai
User-agent: NotebookLM
User-agent: NovaAct
User-agent: OAI-AdsBot
User-agent: OAI-SearchBot
User-agent: omgili
User-agent: omgilibot
User-agent: OpenAI
User-agent: opencode
User-agent: Operator
User-agent: PanguBot
User-agent: Panscient
User-agent: panscient.com
User-agent: Perplexity-User
User-agent: PerplexityBot
User-agent: PetalBot
User-agent: PhindBot
User-agent: Poggio-Citations
User-agent: Poseidon Research Crawler
User-agent: qodercli
User-agent: QualifiedBot
User-agent: Querit-SearchBot
User-agent: QueritBot
User-agent: QuillBot
User-agent: quillbot.com
User-agent: QwenBot
User-agent: Reflectionbot
User-agent: SBIntuitionsBot
User-agent: Scrapy
User-agent: SemrushBot-OCOB
User-agent: SemrushBot-SWA
User-agent: Shap-User
User-agent: ShapBot
User-agent: Sidetrade indexer bot
User-agent: Spider
User-agent: TavilyBot
User-agent: Terra Cotta
User-agent: TerraCotta
User-agent: Thinkbot
User-agent: TikTokSpider
User-agent: Timpibot
User-agent: TongyiBot
User-agent: Trae
User-agent: TwinAgent
User-agent: UseAI
User-agent: VelenPublicWebCrawler
User-agent: WARDBot
User-agent: Webzio-Extended
User-agent: webzio-extended
User-agent: wpbot
User-agent: WRTNBot
User-agent: YaK
User-agent: YandexAdditional
User-agent: YandexAdditionalBot
User-agent: YiyanBot
User-agent: YouBot
User-agent: ZanistaBot
Disallow: /
```

Tokens in the list that correspond to organizations that also operate inference APIs:

- `DeepSeekBot`, `QwenBot`, `TongyiBot`, `ERNIEBot`, `DoubaoBot`, `YiyanBot`, `KimiBot`, `Kimi-SearchBot`, `Kimi-User`, and `Kimi-Agent`
- `cohere-ai` and `cohere-training-data-crawler`
- `MistralAI-Index`, `MistralAI-Training`, and `MistralAI-User`
- `Gemini-Deep-Research`, `Google-NotebookLM`, `GoogleAgent-Mariner`, `Google-CloudVertexBot`, `AzureAI-SearchBot`, and `bedrockbot`
- `Cursor`, `Devin`, `Claude-Code`, and `opencode`, which are coding agents rather than conventional crawlers

## Sources

- [Anthropic crawler documentation](https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)
- [Overview of OpenAI crawlers](https://developers.openai.com/api/docs/bots)
- [Amazonbot](https://developer.amazon.com/amazonbot)
- [Google common crawlers](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers)
- [About Applebot](https://support.apple.com/en-us/119829)
- [ai.robots.txt](https://github.com/ai-robots-txt/ai.robots.txt/blob/main/robots.txt)
