<?php
/**
 * Plugin Name: Protect From AI
 * Description: Blocks selected AI crawler user agents, adds matching robots.txt rules, and stops WordPress HTTP API calls to selected inference hosts.
 * Version: 1.0.0
 * Author: Albert Clownstein
 * License: MIT
 * Requires at least: 5.8
 * Requires PHP: 7.2
 * Text Domain: protect-from-ai
 */

if (!defined('ABSPATH')) {
    exit;
}

const PFAI_OPTION = 'pfai_settings';
const PFAI_CREATOR = 'Albert Clownstein';
const PFAI_REPOSITORY = 'Clownstein/How-To-Help-Protect-Against-AI-Assisted-Attacks';
const PFAI_DEFAULT_BRANCH = 'main';

function pfai_catalog() {
    static $catalog = null;
    if ($catalog === null) {
        $path = __DIR__ . '/data/catalog.json';
        $decoded = json_decode((string) file_get_contents($path), true);
        if (!is_array($decoded) || empty($decoded['crawlers']) || empty($decoded['inference'])) {
            $decoded = array('creator' => PFAI_CREATOR, 'reviewed' => '', 'crawlers' => array(), 'inference' => array());
        }
        $catalog = $decoded;
    }
    return $catalog;
}

function pfai_crawler_index() {
    $index = array();
    foreach (pfai_catalog()['crawlers'] as $item) {
        $index[$item['token']] = $item;
    }
    return $index;
}

function pfai_inference_index() {
    $index = array();
    foreach (pfai_catalog()['inference'] as $item) {
        $index[$item['id']] = $item;
    }
    return $index;
}

function pfai_preset_tokens($preset) {
    $tokens = array();
    foreach (pfai_catalog()['crawlers'] as $item) {
        if ($preset === 'training' && $item['purpose'] === 'training') {
            $tokens[] = $item['token'];
        } elseif ($preset === 'recommended' && $item['profile'] === 'recommended') {
            $tokens[] = $item['token'];
        } elseif ($preset === 'full') {
            $tokens[] = $item['token'];
        }
    }
    return $tokens;
}

function pfai_preset_inference($preset) {
    $ids = array();
    foreach (pfai_catalog()['inference'] as $item) {
        if ($preset === 'full' || $item['profile'] === 'recommended') {
            $ids[] = $item['id'];
        }
    }
    return $preset === 'none' ? array() : $ids;
}

function pfai_default_settings() {
    return array(
        'block_ua' => 1,
        'robots' => 1,
        'block_http' => 1,
        'tokens' => pfai_preset_tokens('recommended'),
        'inference' => pfai_preset_inference('recommended'),
    );
}

function pfai_settings() {
    $stored = get_option(PFAI_OPTION);
    if (!is_array($stored)) {
        return pfai_default_settings();
    }
    return array_merge(pfai_default_settings(), $stored);
}

function pfai_sanitize_tokens($requested) {
    $index = pfai_crawler_index();
    $kept = array();
    foreach ((array) $requested as $token) {
        $token = (string) $token;
        if (isset($index[$token]) && !isset($kept[$token])) {
            $kept[$token] = $token;
        }
    }
    return array_values($kept);
}

function pfai_sanitize_inference($requested) {
    $index = pfai_inference_index();
    $kept = array();
    foreach ((array) $requested as $id) {
        $id = (string) $id;
        if (isset($index[$id]) && !isset($kept[$id])) {
            $kept[$id] = $id;
        }
    }
    return array_values($kept);
}

register_activation_hook(__FILE__, function () {
    if (get_option(PFAI_OPTION) === false) {
        add_option(PFAI_OPTION, pfai_default_settings());
    }
});

add_action('admin_menu', function () {
    add_options_page('Protect From AI', 'Protect From AI', 'manage_options', 'protect-from-ai', 'pfai_render_page');
});

add_action('admin_init', function () {
    register_setting('pfai', PFAI_OPTION, array(
        'type' => 'array',
        'sanitize_callback' => 'pfai_sanitize_settings',
        'default' => pfai_default_settings(),
    ));
});

function pfai_sanitize_settings($input) {
    if (!is_array($input)) {
        return pfai_default_settings();
    }
    $preset = isset($input['preset']) ? (string) $input['preset'] : '';
    if ($preset === 'none') {
        $tokens = array();
        $inference = array();
    } elseif (in_array($preset, array('training', 'recommended', 'full'), true)) {
        $tokens = pfai_preset_tokens($preset);
        $inference = $preset === 'training' ? pfai_settings()['inference'] : pfai_preset_inference($preset);
    } else {
        $tokens = pfai_sanitize_tokens(isset($input['tokens']) ? $input['tokens'] : array());
        $inference = pfai_sanitize_inference(isset($input['inference']) ? $input['inference'] : array());
    }
    return array(
        'block_ua' => empty($input['block_ua']) ? 0 : 1,
        'robots' => empty($input['robots']) ? 0 : 1,
        'block_http' => empty($input['block_http']) ? 0 : 1,
        'tokens' => $tokens,
        'inference' => $inference,
    );
}

function pfai_header_tokens($tokens) {
    $index = pfai_crawler_index();
    $header = array();
    $seen = array();
    foreach ($tokens as $token) {
        if (empty($index[$token]['header'])) {
            continue;
        }
        $patterns = isset($index[$token]['header_patterns']) ? $index[$token]['header_patterns'] : array();
        if (!$patterns) {
            $patterns = array($token);
        }
        foreach ($patterns as $pattern) {
            $key = strtolower($pattern);
            if (isset($seen[$key])) {
                continue;
            }
            $seen[$key] = true;
            $header[] = $pattern;
        }
    }
    return $header;
}

function pfai_token_pattern($tokens) {
    $parts = array();
    foreach ($tokens as $token) {
        $parts[] = preg_quote($token, '#');
    }
    if (!$parts) {
        return '';
    }
    return '#(?:' . implode('|', $parts) . ')#i';
}

function pfai_ends_with($value, $suffix) {
    $length = strlen($suffix);
    return $length === 0 || substr($value, -$length) === $suffix;
}

function pfai_host_matches($host, $entry) {
    $host = strtolower($host);
    foreach ($entry['values'] as $value) {
        $value = strtolower($value);
        if ($entry['match'] === 'url_path') {
            $slash = strpos($value, '/');
            $name = $slash === false ? $value : substr($value, 0, $slash);
            if ($host === $name) {
                return $value;
            }
        } elseif ($entry['match'] === 'label_suffix') {
            if (pfai_ends_with($host, $value)) {
                $prefix = substr($host, 0, -strlen($value));
                if ($prefix !== '' && strpos($prefix, '.') === false) {
                    return $value;
                }
            }
        } elseif ($entry['match'] === 'subdomains') {
            if (pfai_ends_with($host, '.' . $value)) {
                return $value;
            }
        } elseif ($entry['match'] === 'host' && $host === $value) {
            return $value;
        }
    }
    return '';
}

function pfai_path_matches($path, $pattern) {
    $slash = strpos($pattern, '/');
    $expected = $slash === false ? '/' : substr($pattern, $slash);
    $parts = explode('*', $expected);
    $regex = '';
    $last = count($parts) - 1;
    foreach ($parts as $index => $part) {
        $regex .= preg_quote($part, '#');
        if ($index !== $last) {
            $regex .= '[^/]+';
        }
    }
    return preg_match('#^' . $regex . '(?:/|$)#', $path === '' ? '/' : $path) === 1;
}

function pfai_robots_block($settings) {
    if (empty($settings['robots']) || empty($settings['tokens'])) {
        return '';
    }
    $lines = array('# Protect From AI', '# Creator: ' . PFAI_CREATOR);
    foreach ($settings['tokens'] as $token) {
        $lines[] = 'User-agent: ' . $token;
    }
    $lines[] = 'Disallow: /';
    $lines[] = '# End Protect From AI';
    return implode("\n", $lines) . "\n";
}

function pfai_request_value($key) {
    if (!isset($_SERVER[$key])) {
        return '';
    }
    return sanitize_text_field(wp_unslash($_SERVER[$key]));
}

add_action('init', function () {
    $settings = pfai_settings();
    if (empty($settings['block_ua'])) {
        return;
    }
    $path = (string) wp_parse_url(pfai_request_value('REQUEST_URI'), PHP_URL_PATH);
    $robots = (string) wp_parse_url(home_url('/robots.txt'), PHP_URL_PATH);
    if ($path === $robots) {
        return;
    }
    $pattern = pfai_token_pattern(pfai_header_tokens($settings['tokens']));
    if ($pattern !== '' && preg_match($pattern, pfai_request_value('HTTP_USER_AGENT'))) {
        wp_die(
            esc_html__('Blocked by Protect From AI.', 'protect-from-ai'),
            '',
            array('response' => 403)
        );
    }
}, 0);

add_filter('robots_txt', function ($output) {
    $block = pfai_robots_block(pfai_settings());
    if ($block === '') {
        return $output;
    }
    return rtrim((string) $output) . "\n\n" . $block;
}, 20);

add_filter('pre_http_request', function ($preempt, $args, $url) {
    $settings = pfai_settings();
    if (!empty($preempt) || empty($settings['block_http'])) {
        return $preempt;
    }
    $host = strtolower((string) wp_parse_url($url, PHP_URL_HOST));
    $path = (string) wp_parse_url($url, PHP_URL_PATH);
    if ($host === '') {
        return $preempt;
    }
    $index = pfai_inference_index();
    foreach ($settings['inference'] as $id) {
        if (!isset($index[$id])) {
            continue;
        }
        $matched = pfai_host_matches($host, $index[$id]);
        if ($matched === '') {
            continue;
        }
        if ($index[$id]['match'] === 'url_path' && !pfai_path_matches($path, $matched)) {
            continue;
        }
        return new WP_Error('pfai_blocked', 'Protect From AI blocked a WordPress HTTP request to ' . $host);
    }
    return $preempt;
}, 10, 3);

add_action('init', function () {
    if (!pfai_github_package()) {
        return;
    }
    if (!wp_next_scheduled('pfai_github_update')) {
        wp_schedule_event(time() + HOUR_IN_SECONDS, 'daily', 'pfai_github_update');
    }
});

add_action('pfai_github_update', 'pfai_apply_github_update');

add_action('admin_init', function () {
    if (!current_user_can('manage_options') || !pfai_github_package()) {
        return;
    }
    if (isset($_POST['pfai_update']) && check_admin_referer('pfai_update')) {
        pfai_apply_github_update();
    }
});

add_action('admin_notices', function () {
    if (!current_user_can('manage_options')) {
        return;
    }
    $remote = pfai_remote_release();
    $local = pfai_github_package();
    if (!$remote || !$local || $remote['version'] === $local['version']) {
        return;
    }
    $url = admin_url('options-general.php?page=protect-from-ai');
    echo '<div class="notice notice-warning"><p>A newer Protect From AI package is on GitHub. ';
    echo '<form method="post" action="' . esc_url($url) . '" style="display:inline">';
    wp_nonce_field('pfai_update');
    echo '<button type="submit" class="button" name="pfai_update" value="1">Install update</button></form></p></div>';
});

function pfai_github_package() {
    $path = __DIR__ . '/data/package.json';
    if (!is_readable($path)) {
        return null;
    }
    $decoded = json_decode((string) file_get_contents($path), true);
    if (!is_array($decoded) || ($decoded['channel'] ?? '') !== 'github' || empty($decoded['version'])) {
        return null;
    }
    return $decoded;
}

function pfai_remote_release() {
    $cached = get_transient('pfai_remote_release');
    if (is_array($cached)) {
        return $cached;
    }
    $response = wp_remote_get(pfai_release_url(), array('timeout' => 20));
    if (is_wp_error($response) || wp_remote_retrieve_response_code($response) !== 200) {
        return null;
    }
    $decoded = json_decode((string) wp_remote_retrieve_body($response), true);
    if (!is_array($decoded) || !is_string($decoded['version'] ?? null) || !preg_match('/\A[0-9a-f]{40}\z/', $decoded['version']) || empty($decoded['wordpress'])) {
        return null;
    }
    if (!pfai_allowed_package_url($decoded['wordpress'])) {
        return null;
    }
    set_transient('pfai_remote_release', $decoded, 12 * HOUR_IN_SECONDS);
    return $decoded;
}

function pfai_release_url() {
    return 'https://github.com/' . PFAI_REPOSITORY . '/releases/download/plugins/release.json';
}

function pfai_allowed_package_url($url) {
    return (bool) preg_match('#\Ahttps://github\.com/Clownstein/How-To-Help-Protect-Against-AI-Assisted-Attacks/releases/download/plugins/[A-Za-z0-9._-]+\.zip\z#', $url);
}

function pfai_apply_github_update() {
    $local = pfai_github_package();
    $remote = pfai_remote_release();
    if (!$local || !$remote || $remote['version'] === $local['version']) {
        return;
    }
    if (!current_user_can('manage_options') && !wp_doing_cron()) {
        return;
    }
    if (!class_exists('ZipArchive') || !pfai_commit_on_default_branch($remote['version'])) {
        return;
    }
    $expected = pfai_github_tree_files($remote['version'], 'plugins/wordpress/protect-from-ai');
    if ($expected === null) {
        return;
    }
    require_once ABSPATH . 'wp-admin/includes/file.php';
    require_once ABSPATH . 'wp-admin/includes/plugin.php';
    require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
    add_filter('http_request_host_is_external', 'pfai_allow_github_hosts', 10, 2);
    $archive = download_url($remote['wordpress'], 120);
    remove_filter('http_request_host_is_external', 'pfai_allow_github_hosts', 10);
    if (is_wp_error($archive)) {
        return;
    }
    if (pfai_package_matches_tree($archive, $expected, $remote['version'])) {
        $upgrader = new Plugin_Upgrader(new Automatic_Upgrader_Skin());
        $upgrader->install($archive, array('overwrite_package' => true));
    }
    wp_delete_file($archive);
    delete_transient('pfai_remote_release');
}

function pfai_github_api($endpoint) {
    $response = wp_remote_get(
        'https://api.github.com/repos/' . PFAI_REPOSITORY . '/' . $endpoint,
        array('timeout' => 20, 'headers' => array('Accept' => 'application/vnd.github+json'))
    );
    if (is_wp_error($response) || wp_remote_retrieve_response_code($response) !== 200) {
        return null;
    }
    $decoded = json_decode((string) wp_remote_retrieve_body($response), true);
    return is_array($decoded) ? $decoded : null;
}

function pfai_commit_on_default_branch($commit) {
    $compare = pfai_github_api('compare/' . $commit . '...' . PFAI_DEFAULT_BRANCH . '?per_page=1');
    return $compare !== null && in_array($compare['status'] ?? '', array('identical', 'ahead'), true);
}

function pfai_is_git_sha($value) {
    return is_string($value) && preg_match('/\A[0-9a-f]{40}\z/', $value) === 1;
}

// Returns relative path => git blob SHA-1 for every file under $prefix in $commit, or null when the tree cannot be trusted.
function pfai_github_tree_files($commit, $prefix) {
    $commit_data = pfai_github_api('git/commits/' . $commit);
    $sha = $commit_data['tree']['sha'] ?? '';
    foreach (explode('/', $prefix) as $segment) {
        if (!pfai_is_git_sha($sha)) {
            return null;
        }
        $tree = pfai_github_api('git/trees/' . $sha);
        $sha = '';
        foreach (($tree['tree'] ?? array()) as $entry) {
            if (($entry['path'] ?? '') === $segment && ($entry['type'] ?? '') === 'tree') {
                $sha = $entry['sha'] ?? '';
                break;
            }
        }
    }
    if (!pfai_is_git_sha($sha)) {
        return null;
    }
    $tree = pfai_github_api('git/trees/' . $sha . '?recursive=1');
    if ($tree === null || !empty($tree['truncated'])) {
        return null;
    }
    $files = array();
    foreach (($tree['tree'] ?? array()) as $entry) {
        $type = $entry['type'] ?? '';
        if ($type === 'tree') {
            continue;
        }
        $path = $entry['path'] ?? '';
        if ($type !== 'blob'
            || !in_array($entry['mode'] ?? '', array('100644', '100755'), true)
            || !is_string($path)
            || !preg_match('#\A[A-Za-z0-9_][A-Za-z0-9._-]*(?:/[A-Za-z0-9_][A-Za-z0-9._-]*)*\z#', $path)
            || !pfai_is_git_sha($entry['sha'] ?? '')) {
            return null;
        }
        $files[$path] = $entry['sha'];
    }
    return $files === array() ? null : $files;
}

function pfai_package_matches_tree($archive, $expected, $version) {
    $zip = new ZipArchive();
    if ($zip->open($archive) !== true) {
        return false;
    }
    $prefix = 'protect-from-ai/';
    $seen = array();
    $package_ok = false;
    $valid = true;
    for ($index = 0; $index < $zip->numFiles; $index++) {
        $name = $zip->getNameIndex($index);
        if (!is_string($name) || strpos($name, $prefix) !== 0) {
            $valid = false;
            break;
        }
        $relative = substr($name, strlen($prefix));
        $data = $zip->getFromIndex($index);
        if ($data === false || isset($seen[$relative])) {
            $valid = false;
            break;
        }
        $seen[$relative] = true;
        if ($relative === 'data/package.json') {
            $decoded = json_decode($data, true);
            $package_ok = is_array($decoded) && count($decoded) === 2
                && ($decoded['version'] ?? '') === $version && ($decoded['channel'] ?? '') === 'github';
            if (!$package_ok) {
                $valid = false;
                break;
            }
            continue;
        }
        if (!isset($expected[$relative]) || sha1('blob ' . strlen($data) . "\0" . $data) !== $expected[$relative]) {
            $valid = false;
            break;
        }
    }
    $zip->close();
    return $valid && $package_ok && count($seen) === count($expected) + 1;
}

function pfai_allow_github_hosts($allowed, $host) {
    if ($allowed || $host === 'github.com' || pfai_ends_with($host, '.githubusercontent.com')) {
        return true;
    }
    return $allowed;
}

function pfai_render_page() {
    if (!current_user_can('manage_options')) {
        return;
    }
    $settings = pfai_settings();
    $selected_tokens = array_fill_keys($settings['tokens'], true);
    $selected_inference = array_fill_keys($settings['inference'], true);
    $catalog = pfai_catalog();
    echo '<div class="wrap"><h1>Protect From AI</h1>';
    echo '<p>Creator: ' . esc_html(PFAI_CREATOR) . '. Catalog reviewed ' . esc_html($catalog['reviewed']) . '. Activating the plugin applies the recommended crawler and inference selections until you save a different choice.</p>';
    echo '<form method="post" action="options.php">';
    settings_fields('pfai');
    echo '<h2>Actions</h2>';
    pfai_checkbox('block_ua', $settings['block_ua'], 'Return 403 for selected tokens that are sent as a User-Agent. Requests for /robots.txt stay allowed.');
    pfai_checkbox('robots', $settings['robots'], 'Add the selected tokens to the robots.txt file WordPress generates. A robots.txt file already stored on disk is not changed.');
    pfai_checkbox('block_http', $settings['block_http'], 'Block WordPress HTTP API requests to the selected inference services. Other programs on the server are not affected.');
    echo '<h2>Presets</h2><p>';
    foreach (array('training' => 'Training crawlers', 'recommended' => 'Recommended', 'full' => 'Full') as $value => $label) {
        echo '<button type="submit" class="button" name="' . esc_attr(PFAI_OPTION) . '[preset]" value="' . esc_attr($value) . '">' . esc_html($label) . '</button> ';
    }
    echo '</p><h2>Crawler tokens</h2>';
    foreach ($catalog['crawlers'] as $item) {
        $note = !empty($item['header']) ? $item['purpose'] : 'robots.txt only';
        $who = $item['operator'] !== '' ? $item['operator'] . ', ' : '';
        $checked = isset($selected_tokens[$item['token']]);
        echo '<label style="display:block"><input type="checkbox" name="' . esc_attr(PFAI_OPTION) . '[tokens][]" value="' . esc_attr($item['token']) . '"' . checked($checked, true, false) . '> ';
        echo esc_html($item['token']) . ' <small>(' . esc_html($who . $note) . ')</small></label>';
    }
    echo '<h2>Inference services</h2><p>These choices apply only to requests WordPress makes with its HTTP API.</p>';
    foreach ($catalog['inference'] as $item) {
        $count = count($item['values']);
        $detail = $count === 1 ? $item['values'][0] : $count . ' hostnames';
        $checked = isset($selected_inference[$item['id']]);
        echo '<label style="display:block"><input type="checkbox" name="' . esc_attr(PFAI_OPTION) . '[inference][]" value="' . esc_attr($item['id']) . '"' . checked($checked, true, false) . '> ';
        echo esc_html($item['provider'] . ' — ' . $item['service']) . ' <small>(' . esc_html($detail) . ', ' . esc_html($item['profile']) . ')</small></label>';
    }
    submit_button('Save this selection');
    echo '</form></div>';
}

function pfai_checkbox($name, $value, $label) {
    echo '<label style="display:block"><input type="checkbox" name="' . esc_attr(PFAI_OPTION) . '[' . esc_attr($name) . ']" value="1"' . checked(!empty($value), true, false) . '> ' . esc_html($label) . '</label>';
}
