<?php
define('ABSPATH', __DIR__);

function add_action() {}
function add_filter() {}
function register_activation_hook() {}

require dirname(__DIR__) . '/plugins/wordpress/protect-from-ai/protect-from-ai.php';

function assert_same($expected, $actual, $message) {
    if ($expected !== $actual) {
        fwrite(STDERR, $message . " expected " . var_export($expected, true) . " got " . var_export($actual, true) . "\n");
        exit(1);
    }
}

$host = array('match' => 'host', 'values' => array('api.openai.com'));
assert_same('api.openai.com', pfai_host_matches('api.openai.com', $host), 'exact host');
assert_same('', pfai_host_matches('evil.api.openai.com', $host), 'host must not match a subdomain');

$sub = array('match' => 'subdomains', 'values' => array('openai.azure.com'));
assert_same('openai.azure.com', pfai_host_matches('contoso.openai.azure.com', $sub), 'subdomain');
assert_same('', pfai_host_matches('openai.azure.com', $sub), 'apex is not a subdomain');

$suffix = array('match' => 'label_suffix', 'values' => array('-aiplatform.googleapis.com'));
assert_same('-aiplatform.googleapis.com', pfai_host_matches('us-central1-aiplatform.googleapis.com', $suffix), 'regional vertex host');
assert_same('', pfai_host_matches('foo.bar-aiplatform.googleapis.com', $suffix), 'label suffix is one label');

$path = array('match' => 'url_path', 'values' => array('api.cloudflare.com/client/v4/accounts/*/ai/run'));
assert_same('api.cloudflare.com/client/v4/accounts/*/ai/run', pfai_host_matches('api.cloudflare.com', $path), 'path host');
assert_same(true, pfai_path_matches('/client/v4/accounts/abc/ai/run', 'api.cloudflare.com/client/v4/accounts/*/ai/run'), 'workers path');
assert_same(false, pfai_path_matches('/client/v4/zones/abc', 'api.cloudflare.com/client/v4/accounts/*/ai/run'), 'other cloudflare path');

$pattern = pfai_token_pattern(array('GPTBot', 'Google-Extended'));
assert_same(1, preg_match($pattern, 'Mozilla/5.0 compatible; GPTBot/1.2'), 'header token matches');
assert_same(1, preg_match($pattern, 'Google-Extended'), 'caller supplied the token; the catalog filter is separate');

$devin = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36; Devin/1.0; +https://devin.ai';
$chrome = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36';
$assistant = pfai_token_pattern(pfai_header_tokens(array('Devin')));
assert_same(1, preg_match($assistant, $devin), 'Devin suffix matches');
assert_same(0, preg_match($assistant, $chrome), 'Chrome prefix does not match');
$robots = pfai_robots_block(array('robots' => 1, 'tokens' => array('Devin')));
if (strpos($robots, 'User-agent: Devin') === false || strpos($robots, 'Mozilla') !== false) {
    fwrite(STDERR, "robots block did not keep the robots token\n");
    exit(1);
}

echo "wordpress match ok\n";
