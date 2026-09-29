#!/usr/bin/perl
use strict;
use warnings;
use FindBin;
use lib "$FindBin::Bin/lib";
use ProtectFromAI;

my $user = $ENV{REMOTE_USER} // '';
if ($user ne 'root') {
    print "Content-Type: text/plain; charset=utf-8\r\n\r\nThis plugin is available only to the root WHM session.\n";
    exit;
}
ProtectFromAI::handle(root => $FindBin::Bin);
