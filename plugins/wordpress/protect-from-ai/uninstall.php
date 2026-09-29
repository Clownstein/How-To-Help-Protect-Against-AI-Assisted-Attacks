<?php
if (!defined('WP_UNINSTALL_PLUGIN')) {
    exit;
}
delete_option('pfai_settings');
wp_clear_scheduled_hook('pfai_github_update');
