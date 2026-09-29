# nginx

Returns `403 Forbidden` to AI crawlers, identified by either their `User-Agent` token or a source address in the operators' published crawler feeds, while still serving `/robots.txt`.

## Files

| File | Include in | Contents |
| --- | --- | --- |
| `ai-crawlers-http.conf` | `http { }` | A `map` of crawler user-agent tokens, a `geo` block with the aggregated crawler prefixes, and a `map` that combines them into `$ai_crawler_block`. |
| `ai-crawlers-server.conf` | each `server { }` | Returns 403 when `$ai_crawler_block` is set. |

## How the decision is made

- `$ai_crawler_user_agent` is `1` when the `User-Agent` header contains any header-sent token from the catalog, matched case-insensitively.
- `$ai_crawler_address` is `1` when `$remote_addr` falls inside a prefix published by OpenAI, Anthropic, Perplexity, or Amazon for their AI crawlers and user-triggered fetchers.
- `$ai_crawler_block` is `1` when either variable is set, except for requests to `/robots.txt`. Crawlers that honor `robots.txt` can still read the disallow rules.

Matching the address as well as the header catches crawlers that send a generic browser user agent from a published crawler address. Matching the header as well as the address catches crawlers whose operators publish no address feed.

## Install

```bash
sudo mkdir -p /etc/nginx/ai-crawlers
sudo cp ai-crawlers-http.conf ai-crawlers-server.conf /etc/nginx/ai-crawlers/
```

In `nginx.conf`, inside `http { }`:

```nginx
include /etc/nginx/ai-crawlers/ai-crawlers-http.conf;
```

In each `server { }` block to protect:

```nginx
include /etc/nginx/ai-crawlers/ai-crawlers-server.conf;
```

Validate and apply:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Verify

```bash
curl -s -o /dev/null -w '%{http_code}\n' -A 'Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)' https://www.example.com/
curl -s -o /dev/null -w '%{http_code}\n' -A 'Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)' https://www.example.com/robots.txt
```

The first request returns `403`, and the second returns `200`.

## Notes

- Behind a CDN, load balancer, or reverse proxy, `$remote_addr` is the proxy. Configure `ngx_http_realip_module` (`set_real_ip_from` and `real_ip_header`) so the `geo` block sees the client address.
- The `geo` block is regenerated from the published feeds by `tools/refresh_feeds.py`. Redeploy `ai-crawlers-http.conf` after each refresh.

## References

- [`ngx_http_map_module`](https://nginx.org/en/docs/http/ngx_http_map_module.html)
- [`ngx_http_geo_module`](https://nginx.org/en/docs/http/ngx_http_geo_module.html)
- [`ngx_http_realip_module`](https://nginx.org/en/docs/http/ngx_http_realip_module.html)
