#!/usr/bin/perl
use strict;
use warnings;
use FindBin;
use lib "$FindBin::Bin/../plugins/shared";
use ProtectFromAI;

my $catalog = ProtectFromAI::load_json("$FindBin::Bin/../plugins/wordpress/protect-from-ai/data/catalog.json");
my $tokens = ProtectFromAI::preset_tokens($catalog, 'full');
my $headers = ProtectFromAI::header_tokens($catalog, $tokens);
die "community token enforced as a header\n" if grep { $_ eq 'Cursor' || $_ eq 'Spider' || $_ eq 'Google-Extended' } @{$headers};
my $recommended = ProtectFromAI::header_tokens($catalog, ProtectFromAI::preset_tokens($catalog, 'recommended'));
my $ua = ProtectFromAI::regex_alternation($recommended);
my $devin_ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36; Devin/1.0; +https://devin.ai';
my $chrome_ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36';
die "Devin user agent was not matched\n" unless $devin_ua =~ /$ua/i;
die "plain Chrome was matched\n" if $chrome_ua =~ /$ua/i;
my $devin_robots = ProtectFromAI::robots_txt(['Devin']);
die "robots.txt used the HTTP prefix\n" if $devin_robots =~ /Mozilla/;
die "robots token missing\n" unless $devin_robots =~ /User-agent: Devin/;
die "GPTBot missing from header enforcement\n" unless grep { $_ eq 'GPTBot' } @{$headers};

my $conf = ProtectFromAI::apache_conf($headers);
die "Apache rule blocks Google-Extended\n" if $conf =~ /Google-Extended/;
die "Apache rule uses a RewriteRule\n" if $conf =~ /RewriteRule/;
die "GPTBot missing\n" unless $conf =~ /GPTBot/;
my $dotted = ProtectFromAI::apache_conf(['quillbot.com']);
die "dot was not escaped for the Apache quoted string\n" unless $dotted =~ /quillbot\\\\\./;

my $empty = ProtectFromAI::robots_txt([]);
die "empty selection disallows everything\n" if $empty =~ /Disallow/;
my $some = ProtectFromAI::robots_txt(['GPTBot']);
die "selected token missing from robots.txt\n" unless $some =~ /User-agent: GPTBot/ && $some =~ /Disallow: \//;

my $kept = ProtectFromAI::known_tokens($catalog, ['GPTBot', 'NotARealBot']);
die "unknown token kept\n" unless @{$kept} == 1;

my $stub = ProtectFromAI::apache_conf([]);
die "empty header list still denies\n" if $stub =~ /Require all denied/;

use File::Path qw(make_path remove_tree);
use File::Temp qw(tempdir);
my $home = tempdir(CLEANUP => 1);
my $public = "$home/domains/example.com/public_html";
make_path($public);
open my $robots, '>:utf8', "$public/robots.txt" or die $!;
print {$robots} "User-agent: *\nDisallow: /admin\n";
close $robots;
my $roots = ProtectFromAI::account_document_roots('not-a-real-user', $home);
die "site directory was not found\n" unless @{$roots} == 1 && $roots->[0] eq $public;
ProtectFromAI::update_robots_file("$public/robots.txt", $home, ['GPTBot']);
ProtectFromAI::update_robots_file("$public/robots.txt", $home, ['GPTBot']);
open my $merged, '<:utf8', "$public/robots.txt" or die $!;
local $/;
my $merged_text = <$merged>;
close $merged;
die "existing robots rule was removed\n" unless $merged_text =~ /Disallow: \/admin/;
die "selected token was not added\n" unless $merged_text =~ /User-agent: GPTBot/;
die "robots block was duplicated\n" unless (() = $merged_text =~ /# BEGIN Protect From AI/g) == 1;
ProtectFromAI::update_robots_file("$public/robots.txt", $home, []);
open my $cleared, '<:utf8', "$public/robots.txt" or die $!;
my $cleared_text = <$cleared>;
close $cleared;
die "token block remained after clearing\n" if $cleared_text =~ /GPTBot/;
die "existing robots rule did not remain\n" unless $cleared_text =~ /Disallow: \/admin/;
my $owned = "$home/domains/example.net/public_html";
make_path($owned);
ProtectFromAI::update_robots_file("$owned/robots.txt", $home, ['GPTBot']);
ProtectFromAI::update_robots_file("$owned/robots.txt", $home, []);
die "empty managed robots.txt was left behind\n" if -e "$owned/robots.txt";

my $stage = "$home/stage";
my $plugin = "$home/plugin";
make_path("$stage/data", "$stage/admin", "$plugin/data");
for my $file ("$stage/data/catalog.json", "$stage/admin/index.html", "$stage/data/settings.json") {
    open my $handle, '>:raw', $file or die $!;
    print {$handle} "new $file\n";
    close $handle;
}
open my $outside, '>:raw', "$home/outside.txt" or die $!;
print {$outside} "outside\n";
close $outside;
my $linked = eval { symlink("$home/outside.txt", "$plugin/data/catalog.json") };
ProtectFromAI::_copy_package($stage, $plugin);
open my $outside_after, '<:raw', "$home/outside.txt" or die $!;
my $outside_text = <$outside_after>;
close $outside_after;
die "update wrote through a symbolic link\n" unless $outside_text eq "outside\n";
die "update left the symbolic link in place\n" if $linked && -l "$plugin/data/catalog.json";
die "update did not install the package file\n" unless -f "$plugin/admin/index.html" && -f "$plugin/data/catalog.json";
die "update overwrote saved settings\n" if -e "$plugin/data/settings.json";
make_path("$stage/data/nested");
open my $nested, '>:raw', "$stage/data/nested/file.txt" or die $!;
close $nested;
die "update wrote below an account-owned directory\n" if eval { ProtectFromAI::_copy_package($stage, $plugin); 1 };
remove_tree($home);

print "panel config ok\n";
