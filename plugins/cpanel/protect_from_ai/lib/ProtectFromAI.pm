package ProtectFromAI;

use strict;
use warnings;
use Cwd qw(realpath);
use Fcntl qw(O_WRONLY O_CREAT O_EXCL O_NOFOLLOW);
use File::Find ();
use File::Path qw(make_path);
use File::Spec;
use File::Temp qw(tempdir);
use JSON::PP ();

our $VERSION = '1.0.0';
our $CREATOR = 'Albert Clownstein';
our $REPOSITORY = 'Clownstein/How-To-Help-Protect-Against-AI-Assisted-Attacks';
our $DEFAULT_BRANCH = 'main';
our %EXECUTABLE = map { $_ => 1 } qw(
    admin/index.html user/index.html reseller/index.html
    scripts/install.sh scripts/uninstall.sh scripts/update.sh scripts/apply.sh
    install.sh uninstall.sh update.sh index.cgi
);

sub load_json {
    my ($path) = @_;
    open my $handle, '<:utf8', $path or die "Cannot read $path: $!\n";
    local $/;
    my $text = <$handle>;
    close $handle;
    return JSON::PP->new->utf8(0)->decode($text);
}

sub save_json {
    my ($path, $data) = @_;
    my $encoded = JSON::PP->new->utf8(1)->canonical->pretty->encode($data);
    open my $handle, '>:raw', $path or die "Cannot write $path: $!\n";
    print {$handle} $encoded;
    close $handle;
}

sub read_stdin_body {
    my $length = $ENV{CONTENT_LENGTH} || 0;
    return '' if $length <= 0 || $length > 1_000_000;
    my $body = '';
    my $remaining = $length;
    while ($remaining > 0) {
        my $chunk;
        my $got = read STDIN, $chunk, $remaining;
        last unless $got;
        $body .= $chunk;
        $remaining -= $got;
    }
    return $body;
}

sub parse_form {
    my ($text) = @_;
    my %multi;
    for my $pair (split /[&;]/, $text // '') {
        next if $pair eq '';
        my ($key, $value) = split /=/, $pair, 2;
        $value = '' unless defined $value;
        for ($key, $value) {
            tr/+/ /;
            s/%([0-9A-Fa-f]{2})/chr hex $1/eg;
        }
        push @{ $multi{$key} }, $value;
    }
    return \%multi;
}

sub h {
    my ($text) = @_;
    $text = '' unless defined $text;
    $text =~ s/&/&amp;/g;
    $text =~ s/</&lt;/g;
    $text =~ s/>/&gt;/g;
    $text =~ s/"/&quot;/g;
    return $text;
}

sub catalog_tokens {
    my ($catalog) = @_;
    return map { $_->{token} } @{ $catalog->{crawlers} };
}

sub token_by_name {
    my ($catalog) = @_;
    my %by;
    for my $item (@{ $catalog->{crawlers} }) {
        $by{ $item->{token} } = $item;
    }
    return \%by;
}

sub preset_tokens {
    my ($catalog, $preset) = @_;
    my @tokens;
    for my $item (@{ $catalog->{crawlers} }) {
        if ($preset eq 'training') {
            push @tokens, $item->{token} if $item->{purpose} eq 'training';
        }
        elsif ($preset eq 'recommended') {
            push @tokens, $item->{token} if $item->{profile} eq 'recommended';
        }
        elsif ($preset eq 'full') {
            push @tokens, $item->{token};
        }
    }
    return \@tokens;
}

sub known_tokens {
    my ($catalog, $requested) = @_;
    my $by = token_by_name($catalog);
    my @kept;
    my %seen;
    for my $token (@{$requested}) {
        next if $seen{$token}++;
        next unless $by->{$token};
        die "Token contains a character the web-server expression cannot quote safely: $token\n" if $token =~ /[#\n\r]/;
        push @kept, $token;
    }
    return \@kept;
}

sub header_tokens {
    my ($catalog, $tokens) = @_;
    my $by = token_by_name($catalog);
    my @patterns;
    my %seen;
    for my $token (@{$tokens}) {
        my $item = $by->{$token} or next;
        next unless $item->{header};
        my $extra = $item->{header_patterns};
        my @item_patterns = ($extra && @{$extra}) ? @{$extra} : ($token);
        for my $pattern (@item_patterns) {
            next if $seen{lc $pattern}++;
            push @patterns, $pattern;
        }
    }
    return \@patterns;
}

sub regex_alternation {
    my ($tokens) = @_;
    return '' unless @{$tokens};
    my @escaped = map { quotemeta($_) } @{$tokens};
    return '(?:' . join('|', @escaped) . ')';
}

sub apache_pattern {
    my ($tokens) = @_;
    my $pattern = regex_alternation($tokens);
    # Apache evaluates the <If> argument as a quoted string, which consumes one layer of backslashes.
    $pattern =~ s/\\/\\\\/g;
    return $pattern;
}

sub robots_txt {
    my ($tokens) = @_;
    my @lines = (
        '# Protect From AI',
        "# Creator: $CREATOR",
        '# Copy this file into a site that does not already have robots.txt. It is advisory.',
    );
    if (!@{$tokens}) {
        push @lines, '# No tokens are selected, so this file does not disallow anything.', '';
        return join "\n", @lines;
    }
    push @lines, map { "User-agent: $_" } @{$tokens};
    push @lines, 'Disallow: /', '';
    return join "\n", @lines;
}

sub apache_conf {
    my ($header_tokens) = @_;
    my @lines = (
        '# Protect From AI',
        "# Creator: $CREATOR",
        '# Managed by the Protect From AI plugin. Do not edit by hand.',
    );
    if (@{$header_tokens}) {
        my $pattern = apache_pattern($header_tokens);
        push @lines, (
            '<IfModule mod_authz_core.c>',
            qq{    <If "%{REQUEST_URI} != '/robots.txt' && %{HTTP_USER_AGENT} =~ m#$pattern#i">},
            '        Require all denied',
            '    </If>',
            '</IfModule>',
        );
    }
    push @lines, '';
    return join "\n", @lines;
}

sub nginx_map {
    my ($header_tokens) = @_;
    my $pattern = regex_alternation($header_tokens);
    my @lines = (
        '# Protect From AI',
        "# Creator: $CREATOR",
        '# Include from the http {} context.',
        'map $http_user_agent $protect_from_ai_ua {',
        '    default 0;',
    );
    push @lines, qq{    "~*$pattern" 1;} if $pattern ne '';
    push @lines, '}', '';
    return join "\n", @lines;
}

sub nginx_server {
    return join "\n", (
        '# Protect From AI',
        "# Creator: $CREATOR",
        '# Include inside each server {} block. Requires $protect_from_ai_ua from the http map.',
        'if ($protect_from_ai_ua) {',
        '    set $protect_from_ai_block A;',
        '}',
        'if ($uri = /robots.txt) {',
        '    set $protect_from_ai_block "${protect_from_ai_block}B";',
        '}',
        'if ($protect_from_ai_block = A) {',
        '    return 403;',
        '}',
        '',
    );
}

sub write_file {
    my ($path, $content) = @_;
    my $handle;
    if (!open $handle, '>:utf8', $path) {
        # A root-owned file in a writable directory cannot be truncated. Replacing it requires removing it first.
        unlink $path or die "Cannot write $path: $!\n";
        open $handle, '>:utf8', $path or die "Cannot write $path: $!\n";
    }
    print {$handle} $content;
    close $handle;
}

sub append_unique_line {
    my ($path, $line) = @_;
    my $current = '';
    if (-f $path) {
        open my $in, '<:utf8', $path or die "Cannot read $path: $!\n";
        local $/;
        $current = <$in> // '';
        close $in;
        return 0 if index($current, $line) >= 0;
    }
    open my $out, '>>:utf8', $path or die "Cannot append to $path: $!\n";
    print {$out} ($current =~ /\n\z/ || $current eq '' ? '' : "\n"), $line, "\n";
    close $out;
    return 1;
}

sub reload_web_servers {
    my @testers = (
        '/usr/sbin/apachectl',
        '/usr/local/apache/bin/apachectl',
        '/usr/local/cpanel/bin/apachectl',
        '/usr/sbin/httpd',
    );
    my $tester;
    for my $bin (@testers) {
        if (-x $bin) {
            $tester = $bin;
            last;
        }
    }
    if (!$tester) {
        return 'no Apache configtest command was found; the configuration was saved and was not loaded';
    }
    if (system($tester, '-t') != 0) {
        return "$tester configtest failed; the new configuration was not loaded";
    }
    if (-x '/scripts/restartsrv_httpd') {
        my $status = system('/scripts/restartsrv_httpd');
        return $status == 0 ? '/scripts/restartsrv_httpd' : '/scripts/restartsrv_httpd failed';
    }
    my $reload = system($tester, 'graceful');
    return $reload == 0 ? "$tester graceful" : "$tester graceful failed";
}

sub apply_configuration {
    my (%args) = @_;
    my $root = $args{root};
    my $catalog = load_json("$root/data/catalog.json");
    my $form = $args{form};
    my $preset = $form->{preset}[0] // '';
    my $requested = $preset eq '' ? ($form->{token} // []) : preset_tokens($catalog, $preset);
    $requested = [] if $preset eq 'none';
    my $tokens = known_tokens($catalog, $requested);
    my $headers = header_tokens($catalog, $tokens);
    my $block_ua = $form->{block_ua}[0] ? 1 : 0;
    my $robots = $form->{robots}[0] ? 1 : 0;
    my $scope = $args{scope} // 'admin';
    my $store = $args{store} // ($scope eq 'user' ? user_store($args{home}) : "$root/data");
    ensure_directory($store);
    my $settings = {
        block_ua => $scope eq 'user' ? 0 : $block_ua,
        robots   => $robots,
        tokens   => $tokens,
    };
    save_json("$store/settings.json", $settings);
    chmod 0600, "$store/settings.json" if $scope eq 'user' && -o "$store/settings.json";
    if ($scope eq 'user') {
        my $written = apply_account_robots(
            username => $args{username} // '',
            home     => $args{home},
            tokens   => $robots ? $tokens : [],
        );
        return ($settings, $written, 'updated robots.txt for this account', $catalog);
    }

    my $conf_dir = "$root/conf";
    mkdir $conf_dir unless -d $conf_dir;
    my $robots_path = "$conf_dir/robots.txt";
    write_file($robots_path, $robots ? robots_txt($tokens) : robots_txt([]));
    my $apache = apache_conf($block_ua ? $headers : []);
    write_file("$conf_dir/apache.conf", $apache);
    write_file("$conf_dir/nginx-map.conf", nginx_map($block_ua ? $headers : []));
    write_file("$conf_dir/nginx-server.conf", nginx_server());

    my @installed = ("$conf_dir/apache.conf");
    my %previous;
    my $wrote_system = 0;
    for my $directory (qw(
        /etc/apache2/conf.d/includes/pre_main_global
        /etc/apache2/conf.d
        /etc/httpd/conf.d
        /usr/local/apache/conf
    )) {
        next unless -d $directory && -w $directory;
        my $path = "$directory/protect-from-ai.conf";
        $previous{$path} = read_optional($path);
        write_file($path, $apache);
        push @installed, $path;
        $wrote_system = 1;
        last;
    }
    my $da_includes = '/etc/httpd/conf/extra/httpd-includes.conf';
    if (-d '/etc/httpd/conf/extra' && -w $da_includes && -f "$conf_dir/apache.conf") {
        append_unique_line($da_includes, "Include $conf_dir/apache.conf");
        push @installed, $da_includes;
    }
    my $reload;
    if ($wrote_system || $> == 0) {
        $reload = reload_web_servers();
    }
    elsif (-f "$root/plugin.conf") {
        $reload = 'Apache loads the saved rule within one minute, after a configtest';
    }
    else {
        $reload = 'saved the plugin configuration; no Apache directory was writable, so nothing was loaded';
    }
    if ($reload =~ /configtest failed/) {
        for my $path (keys %previous) {
            if (defined $previous{$path}) {
                write_file($path, $previous{$path});
            }
            elsif (-f $path) {
                unlink $path;
            }
        }
        die "$reload\n";
    }
    return ($settings, \@installed, $reload, $catalog);
}

our $STATE_DIR = '/var/lib/protect-from-ai';

sub apply_pending {
    my ($root) = @_;
    die "apply_pending must run as root.\n" unless $> == 0;
    my $conf = "$root/conf/apache.conf";
    return 0 if -l $conf || !-f $conf;
    make_path($STATE_DIR, { mode => 0755 }) unless -d $STATE_DIR;
    die "$STATE_DIR must be a root-owned directory.\n" if -l $STATE_DIR || (stat $STATE_DIR)[4] != 0;
    my $applied = "$STATE_DIR/apache.conf.applied";
    my $status = "$STATE_DIR/status.txt";
    my $current = read_optional($conf) // '';
    my $previous = read_optional($applied);
    return 0 if defined $previous && $previous eq $current;
    my $result = reload_web_servers();
    my $stamp = gmtime() . ' UTC';
    if ($result =~ /configtest failed/) {
        my ($owner, $group) = (stat "$root/conf")[4, 5];
        unlink $conf or die "Cannot remove $conf: $!\n";
        sysopen my $handle, $conf, O_WRONLY | O_CREAT | O_EXCL, 0644 or die "Cannot write $conf: $!\n";
        binmode $handle, ':utf8';
        print {$handle} (defined $previous ? $previous : apache_conf([]));
        close $handle;
        chown $owner, $group, $conf;
        write_file($status, "$stamp: $result. The previous rule was restored.\n");
    }
    else {
        write_file($applied, $current);
        write_file($status, "$stamp: $result.\n");
    }
    chmod 0644, $applied, $status;
    return 0;
}

sub read_optional {
    my ($path) = @_;
    return undef unless -f $path;
    open my $handle, '<:utf8', $path or die "Cannot read $path: $!\n";
    local $/;
    my $content = <$handle>;
    close $handle;
    return $content;
}

sub path_under {
    my ($path, $root) = @_;
    my $real_root = eval { realpath($root) };
    my $real_path = eval { realpath($path) };
    return 0 unless defined $real_root && $real_root ne '' && defined $real_path && $real_path ne '';
    $real_root =~ s{[\\/]+\z}{};
    $real_path =~ s{[\\/]+\z}{};
    if ($^O eq 'MSWin32') {
        $real_root = lc $real_root;
        $real_path = lc $real_path;
    }
    return 1 if $real_path eq $real_root;
    my $separator = $real_root =~ m{\\} ? '\\' : '/';
    return index($real_path, $real_root . $separator) == 0;
}

sub user_store {
    my ($home) = @_;
    die "This account does not have a home directory, so its settings cannot be saved.\n"
        unless defined $home && $home =~ m{\A/} && $home !~ m{(?:^|/)[.][.](?:/|\z)};
    return "$home/.protect-from-ai";
}

sub ensure_directory {
    my ($directory) = @_;
    return if -d $directory;
    mkdir $directory, 0700 or die "Cannot create $directory: $!\n";
}

sub account_document_roots {
    my ($username, $home) = @_;
    return [] unless defined $home && $home ne '' && -d "$home/domains";
    opendir my $directory, "$home/domains" or die "Cannot read $home/domains: $!\n";
    my @domains = grep { /\A[A-Za-z0-9][A-Za-z0-9.-]*\z/ } readdir $directory;
    closedir $directory;
    my @roots;
    my %seen;
    for my $domain (@domains) {
        for my $kind (qw(public_html private_html)) {
            my $dir = "$home/domains/$domain/$kind";
            next unless -d $dir && path_under($dir, $home);
            my $real = realpath($dir);
            next unless defined $real && !$seen{$real}++;
            push @roots, $dir;
        }
        my $public = "$home/domains/$domain/public_html";
        for my $folder (subdomain_folders($username, $domain)) {
            my $dir = "$public/$folder";
            next unless -d $dir && path_under($dir, $home);
            my $real = realpath($dir);
            next unless defined $real && !$seen{$real}++;
            push @roots, $dir;
        }
    }
    return \@roots;
}

sub subdomain_folders {
    my ($username, $domain) = @_;
    return () unless defined $username && $username =~ /\A[A-Za-z0-9][A-Za-z0-9_-]*\z/;
    return () unless $domain =~ /\A[A-Za-z0-9][A-Za-z0-9.-]*\z/;
    my $path = "/usr/local/directadmin/data/users/$username/domains/$domain.subdomains";
    return () unless -f $path;
    open my $handle, '<', $path or return ();
    my @folders;
    while (my $line = <$handle>) {
        $line =~ s/\s+\z//;
        $line =~ s/\A\s+//;
        next if $line eq '' || $line eq 'www';
        my $folder = $line;
        if ($line =~ /\A(.+)\.\Q$domain\E\z/) {
            ($folder) = split /\./, $1, 2;
        }
        next unless $folder =~ /\A[A-Za-z0-9_-]+\z/;
        push @folders, $folder;
    }
    close $handle;
    return @folders;
}

sub robots_managed_block {
    my ($tokens) = @_;
    return '' unless @{$tokens};
    my @lines = (
        '# BEGIN Protect From AI',
        "# Creator: $CREATOR",
        (map { "User-agent: $_" } @{$tokens}),
        'Disallow: /',
        '# END Protect From AI',
    );
    return join("\n", @lines) . "\n";
}

sub merge_robots_text {
    my ($existing, $tokens) = @_;
    $existing = '' unless defined $existing;
    $existing =~ s/\r\n/\n/g;
    $existing =~ s/\r/\n/g;
    $existing =~ s/(?:^|\n)# BEGIN Protect From AI\n.*?# END Protect From AI\n?//s;
    $existing =~ s/\A\n+//;
    $existing =~ s/\s+\z//;
    $existing .= "\n" if $existing ne '';
    my $block = robots_managed_block($tokens);
    return undef if $block eq '' && $existing eq '';
    return $existing if $block eq '';
    return $existing eq '' ? $block : $existing . "\n" . $block;
}

sub update_robots_file {
    my ($path, $home, $tokens) = @_;
    my (undef, $parent) = File::Spec->splitpath($path);
    die "$parent is outside this account.\n" unless path_under($parent, $home);
    if (-l $path || (-e $path && !-f $path)) {
        die "$path is not a regular robots.txt file inside this account.\n" unless -l $path && -f $path && path_under($path, $home);
    }
    elsif (-f $path) {
        die "$path is outside this account.\n" unless path_under($path, $home);
    }
    my $existing = '';
    if (-f $path) {
        open my $handle, '<:utf8', $path or die "Cannot read $path: $!\n";
        local $/;
        $existing = <$handle> // '';
        close $handle;
    }
    elsif (!-d $parent) {
        die "Cannot find the site directory for $path\n";
    }
    else {
        return undef unless @{$tokens};
    }
    my $next = merge_robots_text($existing, $tokens);
    if (!defined $next) {
        unlink $path or die "Cannot remove $path: $!\n" if -f $path;
        return 'removed';
    }
    write_file($path, $next);
    return 'updated';
}

sub apply_account_robots {
    my (%args) = @_;
    my $roots = account_document_roots($args{username}, $args{home});
    if (!@{$roots}) {
        return ['no site directories were found for this account'];
    }
    my @notes;
    for my $root (@{$roots}) {
        my $path = "$root/robots.txt";
        my $result = eval { update_robots_file($path, $args{home}, $args{tokens}) };
        if ($@) {
            my $error = $@;
            $error =~ s/\s+\z//;
            push @notes, "$error";
            next;
        }
        push @notes, "$path $result" if defined $result;
    }
    return \@notes;
}

sub ensure_csrf {
    my ($directory) = @_;
    ensure_directory($directory);
    my $path = "$directory/csrf.txt";
    unless (-s $path) {
        open my $random, '<:raw', '/dev/urandom' or die "Cannot read random data: $!\n";
        my $bytes = '';
        read $random, $bytes, 16 or die "Cannot read random data: $!\n";
        close $random;
        open my $out, '>:raw', $path or die "Cannot write $path: $!\n";
        print {$out} unpack('H*', $bytes);
        close $out;
        chmod 0600, $path if -o $path;
    }
    open my $in, '<:raw', $path or die "Cannot read $path: $!\n";
    local $/;
    my $token = <$in> // '';
    close $in;
    $token =~ s/\s+//g;
    die "The form token file is invalid.\n" unless $token =~ /^[0-9a-f]{32}$/;
    return $token;
}

sub page {
    my (%args) = @_;
    my $root = $args{root};
    my $scope = $args{scope} // 'admin';
    my $store = $args{store} // ($scope eq 'user' ? user_store($args{home}) : "$root/data");
    my $catalog = load_json("$root/data/catalog.json");
    my $settings_path = "$store/settings.json";
    my $settings = -f $settings_path
        ? load_json($settings_path)
        : { tokens => preset_tokens($catalog, 'recommended'), block_ua => $scope eq 'user' ? 0 : 1, robots => 1 };
    my %selected = map { $_ => 1 } @{ $settings->{tokens} // [] };
    my $notice = $args{notice} // '';
    my $installed = $args{installed} // [];
    my $reload = $args{reload} // '';

    my $html = '';
    if ($args{embedded}) {
        $html = '<div style="max-width:60rem;line-height:1.45"><style>fieldset{margin:1rem 0}label{display:block}</style>';
    }
    else {
        $html = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Protect From AI</title>';
        $html .= '<style>body{font-family:sans-serif;max-width:60rem;margin:2rem auto;line-height:1.45}fieldset{margin:1rem 0}label{display:block}</style></head><body>';
    }
    $html .= '<h1>Protect From AI</h1><p>Creator: ' . h($CREATOR) . '. Catalog reviewed ' . h($catalog->{reviewed}) . '.</p>';
    $html .= '<p>' . h($notice) . '</p>' if $notice ne '';
    if (@{$installed}) {
        if ($scope eq 'user') {
            $html .= '<p>Site files: ' . h(join('; ', @{$installed})) . '.</p>';
        }
        else {
            $html .= '<p>Apache configuration: ' . h(join('; ', @{$installed})) . '. Reload: ' . h($reload) . '.</p>';
        }
    }
    if ($scope ne 'user' && -f "$root/plugin.conf" && -f "$STATE_DIR/status.txt") {
        my $applied = read_optional("$STATE_DIR/status.txt") // '';
        $applied =~ s/\s+\z//;
        $html .= '<p>Last Apache apply: ' . h($applied) . '</p>' if $applied ne '';
    }
    my $csrf = ensure_csrf($store);
    $html .= '<form method="post"><input type="hidden" name="csrf" value="' . h($csrf) . '"><fieldset><legend>Actions</legend>';
    if ($scope eq 'user') {
        $html .= '<label><input type="checkbox" name="robots" value="1"' . ($settings->{robots} ? ' checked' : '') . '> Add the selected tokens to robots.txt on each site under this account. Rules outside the Protect From AI block are left in place. Clearing this box removes that block. User-Agent blocking is set by the server administrator.</label>';
    }
    else {
        $html .= '<label><input type="checkbox" name="block_ua" value="1"' . ($settings->{block_ua} ? ' checked' : '') . '> Return 403 for selected tokens that are sent as a User-Agent. Requests for /robots.txt stay allowed. Tokens marked robots.txt only are not matched in the header.</label>';
        $html .= '<label><input type="checkbox" name="robots" value="1"' . ($settings->{robots} ? ' checked' : '') . '> Write conf/robots.txt for the selected tokens. Copy it onto a site that does not already have a robots.txt file. The web server does not publish it.</label>';
    }
    $html .= '</fieldset><fieldset><legend>Presets</legend>';
    $html .= '<button type="submit" name="preset" value="training">Training crawlers only</button> ';
    $html .= '<button type="submit" name="preset" value="recommended">Recommended</button> ';
    $html .= '<button type="submit" name="preset" value="full">Full, including the community list</button> ';
    $html .= '<button type="submit" name="preset" value="none">Clear the token list</button>';
    $html .= '</fieldset><fieldset><legend>Tokens</legend>';
    for my $item (@{ $catalog->{crawlers} }) {
        my $note = $item->{header} ? $item->{purpose} : 'robots.txt only';
        my $who = $item->{operator} ? $item->{operator} . ', ' : '';
        $html .= '<label><input type="checkbox" name="token" value="' . h($item->{token}) . '"' . ($selected{ $item->{token} } ? ' checked' : '') . '> ';
        $html .= h($item->{token}) . ' <small>(' . h($who . $note) . ')</small></label>';
    }
    $html .= '</fieldset><button type="submit">Save this selection</button></form>';
    if ($scope eq 'user') {
        $html .= '<p>These robots.txt rules are advisory. They cover crawlers that fetch this account\'s sites. They do not block outbound connections to inference APIs, and they do not return 403.</p>';
    }
    else {
        $html .= '<p>Nginx snippets are written to conf/nginx-map.conf and conf/nginx-server.conf and are not loaded. A map on its own does not return 403. Apache, or a reverse proxy that forwards the original User-Agent to Apache, is what this plugin installs. These controls cover crawlers that fetch sites on this server. They do not block outbound connections to inference APIs.</p>';
    }
    $html .= $args{embedded} ? '</div>' : '</body></html>';
    return $html;
}

sub handle {
    my (%args) = @_;
    my $scope = $args{scope} // 'admin';
    my $store = $scope eq 'user' ? user_store($args{home}) : "$args{root}/data";
    my $page_args = {
        root     => $args{root},
        embedded => $args{embedded},
        scope    => $scope,
        store    => $store,
        home     => $args{home},
    };
    my $posted = $ENV{POST} // '';
    my $method = $ENV{REQUEST_METHOD} || ($posted ne '' ? 'POST' : 'GET');
    my $form = {};
    if ($method eq 'POST') {
        $form = parse_form($posted ne '' ? $posted : read_stdin_body());
    }
    my ($notice, $installed, $reload) = ('', [], '');
    print "Content-Type: text/html; charset=utf-8\r\n\r\n" unless $args{embedded};
    if ($method eq 'POST') {
        my $expected = eval { ensure_csrf($store) };
        my $got = $form->{csrf}[0] // '';
        if ($@ || $got eq '' || $got ne $expected) {
            print page(%{$page_args}, notice => 'The form token did not match. Reload the page and save again.');
            return;
        }
        my $result = eval {
            [apply_configuration(
                root     => $args{root},
                form     => $form,
                scope    => $scope,
                store    => $store,
                home     => $args{home},
                username => $args{username} // '',
            )]
        };
        if ($@) {
            print page(%{$page_args}, notice => "The configuration was not saved: $@");
            return;
        }
        my (undef, $paths, $reload_text) = @{$result};
        $notice = 'Configuration saved.';
        $installed = $paths;
        $reload = $reload_text;
    }
    print page(%{$page_args}, notice => $notice, installed => $installed, reload => $reload);
}

sub github_release_url {
    return "https://github.com/$REPOSITORY/releases/download/plugins/release.json";
}

# Installed files come from the git tree of a commit on the default branch, never from a release archive,
# so a replaced release asset cannot put anything on the server that is not in the repository history.
sub update_from_github {
    my ($root) = @_;
    my $package_path = "$root/data/package.json";
    return 0 unless -f $package_path;
    my $package = load_json($package_path);
    return 0 unless ($package->{channel} // '') eq 'github';
    die "Run the update as root.\n" unless $> == 0;
    my $local = $package->{version} // '';
    my $tmp = tempdir('protect-from-ai-update-XXXXXX', TMPDIR => 1, CLEANUP => 1);
    my $release_path = "$tmp/release.json";
    _download(github_release_url(), $release_path);
    my $release = load_json($release_path);
    my $remote = $release->{version} // '';
    die "The release description does not name a commit.\n" unless $remote =~ /\A[0-9a-f]{40}\z/;
    if ($remote eq $local) {
        print "Protect From AI is current ($local).\n";
        return 0;
    }
    _require_default_branch_commit($remote, $tmp);
    my $kind = -f "$root/plugin.conf" ? 'directadmin' : 'cpanel';
    my $prefix = "plugins/$kind/protect_from_ai";
    my $stage = "$tmp/stage";
    mkdir $stage, 0700 or die "Cannot create $stage: $!\n";
    for my $file (@{ _github_tree_files($remote, $prefix, $tmp) }) {
        my ($relative, $git_mode) = @{$file};
        next if $relative eq 'data/package.json';
        my @parts = split m{/}, $relative;
        make_path(File::Spec->catdir($stage, @parts[0 .. $#parts - 1])) if @parts > 1;
        my $to = File::Spec->catfile($stage, @parts);
        _download("https://raw.githubusercontent.com/$REPOSITORY/$remote/$prefix/$relative", $to);
        chmod(($git_mode eq '100755' || $EXECUTABLE{$relative}) ? 0755 : 0644, $to);
    }
    make_path("$stage/data");
    save_json("$stage/data/package.json", { version => $remote, channel => 'github' });
    chmod 0644, "$stage/data/package.json";
    my $install;
    if ($kind eq 'directadmin') {
        _copy_package($stage, $root);
        $install = "$root/scripts/install.sh";
    }
    else {
        $install = "$stage/install.sh";
    }
    die "The update has no install script.\n" unless -f $install;
    system('sh', $install) == 0 or die "The updated plugin did not finish installing.\n";
    print "Protect From AI updated to $remote.\n";
    return 0;
}

sub _require_default_branch_commit {
    my ($commit, $tmp) = @_;
    my $status = _github_json("compare/$commit...$DEFAULT_BRANCH?per_page=1", $tmp)->{status} // '';
    die "Release commit $commit is not on the $DEFAULT_BRANCH branch; the update was not applied.\n"
        unless $status eq 'identical' || $status eq 'ahead';
}

sub _github_tree_files {
    my ($commit, $prefix, $tmp) = @_;
    my $sha = _github_json("git/commits/$commit", $tmp)->{tree}{sha} // '';
    for my $segment (split m{/}, $prefix) {
        die "The commit tree could not be read.\n" unless $sha =~ /\A[0-9a-f]{40}\z/;
        my ($entry) = grep { ($_->{path} // '') eq $segment && ($_->{type} // '') eq 'tree' }
            @{ _github_json("git/trees/$sha", $tmp)->{tree} // [] };
        die "$prefix is missing from commit $commit.\n" unless $entry;
        $sha = $entry->{sha} // '';
    }
    die "The commit tree could not be read.\n" unless $sha =~ /\A[0-9a-f]{40}\z/;
    my $tree = _github_json("git/trees/$sha?recursive=1", $tmp);
    die "The plugin tree in commit $commit is too large to read.\n" if $tree->{truncated};
    my @files;
    for my $entry (@{ $tree->{tree} // [] }) {
        my $type = $entry->{type} // '';
        next if $type eq 'tree';
        my $path = $entry->{path} // '';
        my $mode = $entry->{mode} // '';
        die "Commit $commit has an unexpected $type entry at $path.\n" unless $type eq 'blob';
        die "Commit $commit has an unsafe path: $path\n"
            unless $path =~ m{\A[A-Za-z0-9_][A-Za-z0-9._-]*(?:/[A-Za-z0-9_][A-Za-z0-9._-]*)*\z};
        die "Commit $commit stores $path with mode $mode.\n" unless $mode eq '100644' || $mode eq '100755';
        push @files, [$path, $mode];
    }
    die "Commit $commit has no plugin files under $prefix.\n" unless @files;
    return [sort { $a->[0] cmp $b->[0] } @files];
}

my $github_response = 0;

sub _github_json {
    my ($endpoint, $tmp) = @_;
    $github_response++;
    my $path = "$tmp/github-$github_response.json";
    _download("https://api.github.com/repos/$REPOSITORY/$endpoint", $path, 1);
    my $data = load_json($path);
    die "GitHub returned an unexpected answer for $endpoint.\n" unless ref $data eq 'HASH';
    return $data;
}

sub _download {
    my ($url, $destination, $api) = @_;
    my @headers = $api ? ('--header', 'Accept: application/vnd.github+json') : ();
    system(
        'curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '120',
        '--globoff', '--proto', '=https', '--proto-redir', '=https', @headers,
        '--output', $destination, $url,
    ) == 0 or die "Could not download $url\n";
}

sub _copy_package {
    my ($stage, $root) = @_;
    my $skip = {
        'data/settings.json' => 1,
        'data/csrf.txt' => 1,
        'conf/apache.conf' => 1,
    };
    my @files;
    File::Find::find(sub {
        return unless -f $_;
        my $relative = File::Spec->abs2rel($File::Find::name, $stage);
        $relative =~ s{\\}{/}g;
        return if $skip->{$relative};
        push @files, $relative;
    }, $stage);
    for my $directory (qw(data conf)) {
        die "$root/$directory is a symbolic link; the update was not applied.\n" if -l "$root/$directory";
    }
    for my $relative (sort @files) {
        my @parts = split m{/}, $relative;
        # data/ and conf/ belong to the DirectAdmin admin account, so root never walks into subdirectories there.
        die "The package places $relative below an account-owned directory; the update was not applied.\n"
            if @parts > 2 && ($parts[0] eq 'data' || $parts[0] eq 'conf');
        my $directory = $root;
        for my $part (@parts[0 .. $#parts - 1]) {
            $directory = File::Spec->catdir($directory, $part);
            die "$directory is a symbolic link; the update was not applied.\n" if -l $directory;
            if (!-d $directory) {
                mkdir $directory, 0755 or die "Cannot create $directory: $!\n";
            }
        }
        my $from = File::Spec->catfile($stage, @parts);
        my $to = File::Spec->catfile($directory, $parts[-1]);
        die "$to is a directory; the update was not applied.\n" if -d $to && !-l $to;
        if (-l $to || -e $to) {
            unlink $to or die "Could not replace $relative: $!\n";
        }
        my $mode = ((stat $from)[2] // 0644) & 0777;
        open my $in, '<:raw', $from or die "Cannot read $from: $!\n";
        my $data = do { local $/; <$in> } // '';
        close $in;
        sysopen my $out, $to, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600
            or die "Could not write $relative: $!\n";
        binmode $out;
        print {$out} $data or die "Could not write $relative: $!\n";
        chmod $mode, $out or die "Could not set the mode of $relative: $!\n";
        close $out or die "Could not write $relative: $!\n";
    }
}

1;
