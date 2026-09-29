"""Tests for tools/generate.py and tools/refresh_feeds.py.

Run from the repository root:

    python -m unittest discover -s tests -v

The tests are offline. They use the committed catalog and crawler snapshots.
"""

from __future__ import annotations

import copy
import csv
import io
import ipaddress
import json
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import generate  # noqa: E402
import refresh_feeds  # noqa: E402

try:
    import tkinter
except ImportError:
    tkinter = None


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def data_lines(relative: str, comment: str = "#") -> list[str]:
    return [line for line in read(relative).splitlines() if line.strip() and not line.startswith(comment)]


def is_covered(name: str, entries: set[str]) -> bool:
    labels = name.split(".")
    return any(".".join(labels[index:]) in entries for index in range(0, len(labels) - 1))


IP_LITERAL_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?(?![\w.])")
EGRESS_DIRECTORIES = (
    "palo-alto", "zscaler", "netskope", "cloudflare-gateway", "cisco-umbrella", "squid",
    "f5", "bind-rpz", "pi-hole", "microsoft-defender",
)


class CatalogFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = generate.load_catalog(ROOT)
        cls.outputs = generate.build_outputs(ROOT)
        cls.profiles = {profile: generate.destinations(cls.catalog, profile) for profile in generate.PROFILES}
        cls.names = {profile: generate.list_names(cls.catalog, dests) for profile, dests in cls.profiles.items()}


class TestGeneration(CatalogFixture):
    def test_committed_files_are_current(self) -> None:
        self.assertEqual(generate.stale_outputs(ROOT, self.outputs), [], "run python tools/generate.py")

    def test_generation_is_deterministic(self) -> None:
        self.assertEqual(generate.build_outputs(ROOT), self.outputs)

    def test_check_mode_reports_success(self) -> None:
        with mock.patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(generate.main(["--check"]), 0)

    def test_every_output_ends_with_newline_and_has_no_trailing_whitespace(self) -> None:
        for relative, content in self.outputs.items():
            if not content:
                continue
            self.assertTrue(content.endswith("\n"), relative)
            for number, line in enumerate(content.splitlines(), start=1):
                self.assertEqual(line, line.rstrip(), f"{relative}:{number} has trailing whitespace")

    def test_full_profile_is_superset_of_recommended(self) -> None:
        recommended = {item.name for item in self.names["recommended"]}
        full = {item.name for item in self.names["full"]}
        self.assertTrue(recommended < full)
        candidates = {entry["value"] for entry in self.catalog["egress"]["entries"] if entry["tier"] == "candidate"}
        self.assertFalse(recommended & candidates)
        self.assertTrue(candidates <= full)

    def test_vertex_regions_are_enumerated(self) -> None:
        names = {item.name for item in self.names["recommended"]}
        for region in self.catalog["egress"]["vertex_regions"]["regions"]:
            self.assertIn(f"{region}-aiplatform.googleapis.com", names)

    def test_bedrock_hosts_are_present(self) -> None:
        names = {item.name for item in self.names["recommended"]}
        for service in self.catalog["egress"]["bedrock"]["services"]:
            for host in service["hosts"]:
                self.assertIn(host, names)


class TestCatalogCoverage(CatalogFixture):
    def assert_names(self, profile: str, relative: str, render, comment: str = "#") -> None:
        entries = set(data_lines(relative, comment))
        for item in self.names[profile]:
            self.assertIn(render(item), entries, f"{item.name} missing from {relative}")

    def assert_names_covered(self, profile: str, relative: str, transform=lambda line: line, comment: str = "#") -> None:
        entries = {transform(line) for line in data_lines(relative, comment)}
        for item in self.names[profile]:
            self.assertTrue(is_covered(item.name, entries), f"{item.name} not covered by {relative}")

    def test_palo_alto(self) -> None:
        for profile in generate.PROFILES:
            relative = f"rules/palo-alto/ai-inference-url-edl{generate.profile_suffix(profile)}.txt"
            self.assert_names(profile, relative, lambda item: ("*." if item.subdomains else "") + item.name + "/")
            self.assertIn("api.cloudflare.com/client/v4/accounts/*/ai/run", data_lines(relative))

    def test_zscaler(self) -> None:
        for profile in generate.PROFILES:
            relative = f"rules/zscaler/ai-inference-urls{generate.profile_suffix(profile)}.txt"
            self.assert_names(profile, relative, lambda item: ("." if item.subdomains else "") + item.name)

    def test_netskope(self) -> None:
        for profile in generate.PROFILES:
            relative = f"rules/netskope/ai-inference-urls{generate.profile_suffix(profile)}.txt"
            self.assert_names(profile, relative, lambda item: ("*." if item.subdomains else "") + item.name)

    def test_cloudflare_gateway(self) -> None:
        for profile in generate.PROFILES:
            relative = f"rules/cloudflare-gateway/ai-inference-domains{generate.profile_suffix(profile)}.csv"
            rows = list(csv.reader(io.StringIO(read(relative))))
            self.assertEqual(rows[0], ["value", "description"])
            values = [row[0] for row in rows[1:]]
            self.assertEqual(len(values), len(set(values)), "duplicate entries are rejected by Cloudflare")
            self.assertLessEqual(len(values), generate.CLOUDFLARE_GATEWAY_STANDARD_LIMIT)
            for item in self.names[profile]:
                self.assertTrue(is_covered(item.name, set(values)), item.name)

    def test_cisco_umbrella(self) -> None:
        for profile in generate.PROFILES:
            self.assert_names_covered(profile, f"rules/cisco-umbrella/ai-inference-destinations{generate.profile_suffix(profile)}.txt")

    def test_squid(self) -> None:
        for profile in generate.PROFILES:
            relative = f"rules/squid/ai-inference-domains{generate.profile_suffix(profile)}.txt"
            lines = data_lines(relative)
            self.assertTrue(all(line.startswith(".") for line in lines))
            stripped = {line[1:] for line in lines}
            for line in stripped:
                labels = line.split(".")
                parents = {".".join(labels[i:]) for i in range(1, len(labels) - 1)}
                self.assertFalse(parents & stripped, f"{line} is redundant; Squid warns about overlapping dstdomain entries")
            self.assert_names_covered(profile, relative, lambda value: value[1:])

    def test_pi_hole(self) -> None:
        for profile in generate.PROFILES:
            suffix = generate.profile_suffix(profile)
            self.assert_names_covered(profile, f"rules/pi-hole/ai-inference-domains{suffix}.txt")
            self.assert_names_covered(
                profile, f"rules/pi-hole/ai-inference-adlist{suffix}.txt",
                lambda value: value[2:-1] if value.startswith("||") and value.endswith("^") else value, comment="!",
            )

    def test_bind_rpz(self) -> None:
        for profile in generate.PROFILES:
            records = set(data_lines(f"rules/bind-rpz/ai-inference{generate.profile_suffix(profile)}.rpz", ";"))
            for item in self.names[profile]:
                self.assertIn(f"*.{item.name} CNAME .", records)
                if not item.subdomains:
                    self.assertIn(f"{item.name} CNAME .", records)

    def test_f5_datagroups(self) -> None:
        for profile in generate.PROFILES:
            groups = parse_tmsh_datagroups(read(f"rules/f5/ai-inference-datagroups{generate.profile_suffix(profile)}.tmsh"))
            self.assertEqual(
                set(groups), {"ai_inference_hosts", "ai_inference_suffixes", "ai_inference_label_suffixes", "ai_inference_url_paths"}
            )
            for item in self.names[profile]:
                if item.subdomains:
                    self.assertIn("." + item.name, groups["ai_inference_suffixes"])
                else:
                    self.assertIn(item.name, groups["ai_inference_hosts"])
            self.assertIn("-aiplatform.googleapis.com", groups["ai_inference_label_suffixes"])
            self.assertIn("api.cloudflare.com/client/v4/accounts/*/ai/run", groups["ai_inference_url_paths"])

    def test_microsoft_defender(self) -> None:
        for profile in generate.PROFILES:
            files = sorted((ROOT / "rules/microsoft-defender").glob(f"ai-inference-indicators{generate.profile_suffix(profile)}*.csv"))
            files = [path for path in files if profile == "full" or "-full" not in path.name]
            rows = []
            for path in files:
                parsed = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8"))))
                self.assertEqual(parsed[0], generate.DEFENDER_COLUMNS)
                self.assertLessEqual(len(parsed) - 1, generate.DEFENDER_BATCH_LIMIT)
                rows.extend(parsed[1:])
            values = {row[1] for row in rows}
            for row in rows:
                self.assertEqual(row[0], "DomainName")
                self.assertEqual(row[2], "Block")
                self.assertNotIn("*", row[1])
                self.assertTrue(row[3] and row[4], "title and description are required")
            for item in self.names[profile]:
                if item.subdomains:
                    self.assertNotIn(item.name, values)
                else:
                    self.assertIn(item.name, values)

    def test_suricata_covers_every_destination(self) -> None:
        for profile, dests in self.profiles.items():
            text = read(f"rules/suricata/ai-inference{generate.profile_suffix(profile)}.rules")
            for dest in dests:
                if dest.match == "url_path":
                    self.assertIn(f"HTTP path {dest.provider} {dest.value}", text)
                    continue
                for kind in ("TLS SNI", "DNS query", "HTTP Host"):
                    self.assertIn(f'"AI-INFERENCE {kind} {generate.suricata_msg(dest.provider)} {dest.value}"', text)


def parse_tmsh_datagroups(text: str) -> dict[str, dict[str, str]]:
    groups: dict[str, dict[str, str]] = {}
    current = None
    key = None
    for line in text.splitlines():
        header = re.match(r"^ltm data-group internal (\S+) \{$", line)
        if header:
            current = header.group(1)
            groups[current] = {}
            continue
        record = re.match(r'^\s+"([^"]+)" \{$', line)
        if record and current:
            key = record.group(1)
            continue
        data = re.match(r'^\s+data "([^"]*)"$', line)
        if data and current and key:
            groups[current][key] = data.group(1)
            key = None
    return groups


class TestWildcardHandling(CatalogFixture):
    def test_no_asterisk_where_unsupported(self) -> None:
        for relative in (
            "rules/zscaler/ai-inference-urls-full.txt",
            "rules/cloudflare-gateway/ai-inference-domains-full.csv",
            "rules/cisco-umbrella/ai-inference-destinations-full.txt",
            "rules/pi-hole/ai-inference-domains-full.txt",
            "rules/squid/ai-inference-domains-full.txt",
        ):
            for line in data_lines(relative):
                self.assertNotIn("*", line, relative)

    def test_netskope_wildcards_are_leading_only(self) -> None:
        for line in data_lines("rules/netskope/ai-inference-urls-full.txt"):
            if "*" in line:
                self.assertTrue(line.startswith("*.") and line.count("*") == 1, line)

    def test_palo_alto_wildcards_are_whole_tokens(self) -> None:
        for line in data_lines("rules/palo-alto/ai-inference-url-edl-full.txt"):
            for token in re.split(r"[./?&=;+]", line):
                if "*" in token:
                    self.assertEqual(token, "*", line)

    def test_never_block_domains_are_absent(self) -> None:
        never_block = set(self.catalog["egress"]["never_block"])
        for item in self.names["full"]:
            self.assertNotIn(item.name, never_block)
        for relative, content in self.outputs.items():
            if relative.startswith(tuple(f"rules/{name}/" for name in EGRESS_DIRECTORIES)):
                for domain in never_block:
                    for form in (domain, "." + domain, "*." + domain, "||" + domain + "^", domain + "/", "*." + domain + "/"):
                        self.assertNotIn("\n" + form + "\n", "\n" + content, f"{form} found in {relative}")

    def test_label_suffix_regexes(self) -> None:
        should_match = ["us-central1-aiplatform.googleapis.com", "newregion9-aiplatform.googleapis.com"]
        should_not = ["aiplatform.googleapis.com", "googleapis.com", "us-central1-aiplatform.googleapis.com.example.net"]
        for relative in ("rules/pi-hole/ai-inference-regex.txt", "rules/squid/ai-inference-domain-regex.txt"):
            patterns = [re.compile(line, re.IGNORECASE) for line in data_lines(relative)]
            self.assertTrue(patterns, relative)
            for name in should_match:
                self.assertTrue(any(p.search(name) for p in patterns), f"{relative} should match {name}")
            for name in should_not:
                self.assertFalse(any(p.search(name) for p in patterns), f"{relative} should not match {name}")

    def test_url_path_regexes(self) -> None:
        squid = [re.compile(line, re.IGNORECASE) for line in data_lines("rules/squid/ai-inference-url-regex.txt")]
        netskope = [re.compile(line) for line in data_lines("rules/netskope/ai-inference-regex.txt")]
        blocked = "api.cloudflare.com/client/v4/accounts/0123abcd/ai/run/@cf/meta/llama-3.1-8b-instruct"
        allowed = ["api.cloudflare.com/client/v4/zones", "api.cloudflare.com/client/v4/accounts/0123abcd/workers/scripts"]
        self.assertTrue(any(p.search("https://" + blocked) for p in squid))
        self.assertTrue(any(p.search(blocked) for p in netskope))
        self.assertTrue(any(p.search("europe-west4-aiplatform.googleapis.com/v1/projects") for p in netskope))
        for url in allowed:
            self.assertFalse(any(p.search("https://" + url) for p in squid), url)
            self.assertFalse(any(p.search(url) for p in netskope), url)

    def test_suricata_pcre_semantics(self) -> None:
        cases = {
            generate.Destination("api.openai.com", "host", "core", "p", "s", "x"): (
                ["api.openai.com", "API.OPENAI.COM", "eu.api.openai.com"], ["xapi.openai.com", "api.openai.com.example.net"]),
            generate.Destination("openai.azure.com", "subdomains", "core", "p", "s", "x"): (
                ["contoso.openai.azure.com"], ["openai.azure.com.example.net", "notopenai.azure.com"]),
            generate.Destination("-aiplatform.googleapis.com", "label_suffix", "core", "p", "s", "x"): (
                ["us-central1-aiplatform.googleapis.com"], ["aiplatform.googleapis.com", "-aiplatform.googleapis.com.example.net"]),
        }
        for dest, (matches, misses) in cases.items():
            content, pcre = generate.suricata_match(dest)
            pattern = re.compile(pcre.replace("\\/", "/"), re.IGNORECASE)
            for name in matches:
                self.assertIn(content.lower(), name.lower())
                self.assertTrue(pattern.search(name), f"{pcre} should match {name}")
            for name in misses:
                self.assertFalse(pattern.search(name) and content.lower() in name.lower(), f"{pcre} should not match {name}")


class TestSharedAddressGuard(CatalogFixture):
    def test_egress_files_contain_no_addresses(self) -> None:
        for relative, content in self.outputs.items():
            if "ai-inference" in Path(relative).name:
                self.assertIsNone(IP_LITERAL_RE.search(content), f"{relative} contains an IP literal")

    def test_no_output_contains_observed_inference_address(self) -> None:
        guard = self.catalog["egress"]["observed_inference_addresses"]
        addresses = [ipaddress.ip_address(value) for value in guard["addresses"]]
        shared = [ipaddress.ip_network(value) for value in guard["shared_prefixes"]]
        for relative, content in self.outputs.items():
            if relative == "rules/ip-feeds/anthropic-network.txt":
                continue
            for literal in IP_LITERAL_RE.findall(content):
                network = ipaddress.ip_network(literal, strict=False)
                for address in addresses:
                    self.assertNotIn(address, network, f"{relative}: {network} covers inference address {address}")
                for prefix in shared:
                    if prefix.version != network.version:
                        continue
                    self.assertFalse(network == prefix or network.supernet_of(prefix), f"{relative}: {network} covers {prefix}")

    def test_guard_drops_covering_prefixes(self) -> None:
        networks = [
            ipaddress.ip_network("160.79.104.0/24"),
            ipaddress.ip_network("104.16.0.0/12"),
            ipaddress.ip_network("104.0.0.0/8"),
            ipaddress.ip_network("198.51.100.0/24"),
            ipaddress.ip_network("2607:6bc0::/32"),
            ipaddress.ip_network("2001:db8::/32"),
        ]
        with mock.patch("sys.stderr", new_callable=io.StringIO):
            kept = generate.guard_networks(self.catalog, networks, "test")
        self.assertEqual(kept, [ipaddress.ip_network("198.51.100.0/24"), ipaddress.ip_network("2001:db8::/32")])


class TestSuricataSids(CatalogFixture):
    SID_RE = re.compile(r"\bsid:(\d+);")

    def sids(self, relative: str) -> list[int]:
        return [int(value) for value in self.SID_RE.findall(read(relative))]

    def test_sids_are_unique_within_each_deployment(self) -> None:
        for suffix in ("", "-full"):
            sids = self.sids(f"rules/suricata/ai-inference{suffix}.rules") + self.sids("rules/suricata/ai-crawlers.rules")
            self.assertEqual(len(sids), len(set(sids)), f"duplicate SIDs with ai-inference{suffix}.rules")

    def test_sids_are_within_declared_ranges(self) -> None:
        bases = self.catalog["suricata"]["sid_base"]
        text = read("rules/suricata/ai-inference-full.rules")
        for rule in (line for line in text.splitlines() if line.startswith("alert ")):
            sid = int(self.SID_RE.search(rule).group(1))
            base = bases["tls_sni"] if " TLS SNI " in rule else bases["dns_query"] if " DNS query " in rule else bases["http_host"]
            self.assertTrue(base < sid <= base + generate.SID_SPACE, rule)
        for sid in self.sids("rules/suricata/ai-crawlers.rules"):
            base = bases["http_user_agent"]
            self.assertTrue(base < sid <= base + generate.SID_SPACE)

    def test_same_destination_keeps_sid_across_profiles(self) -> None:
        def by_msg(relative: str) -> dict[str, int]:
            result = {}
            for rule in read(relative).splitlines():
                if rule.startswith("alert "):
                    result[re.search(r'msg:"([^"]+)"', rule).group(1)] = int(self.SID_RE.search(rule).group(1))
            return result

        recommended = by_msg("rules/suricata/ai-inference.rules")
        full = by_msg("rules/suricata/ai-inference-full.rules")
        for msg, sid in recommended.items():
            self.assertEqual(full[msg], sid, msg)

    def test_adding_an_entry_does_not_renumber_existing_rules(self) -> None:
        before = generate.suricata_sid_map(self.catalog)
        changed = copy.deepcopy(self.catalog)
        changed["egress"]["entries"].insert(0, {
            "value": "api.example-inference.test", "match": "host", "tier": "core",
            "provider": "Example", "service": "Example API", "source": "https://example.test",
        })
        after = generate.suricata_sid_map(changed)
        moved = [key for key, sid in before.items() if after[key] != sid]
        self.assertLessEqual(len(moved), 1, "only a hash collision with the new entry may move an existing SID")

    def test_rule_structure(self) -> None:
        for relative in ("rules/suricata/ai-inference-full.rules", "rules/suricata/ai-crawlers.rules"):
            for rule in read(relative).splitlines():
                if not rule or rule.startswith("#"):
                    continue
                self.assertRegex(rule, r"^alert (tls|dns|http) \S+ \S+ -> \S+ \S+ \(.*;\)$")
                self.assertEqual(rule.count('"') % 2, 0, rule)
                for keyword in ("msg:", "sid:", "rev:", "classtype:"):
                    self.assertIn(keyword, rule)


class TestInboundOutputs(CatalogFixture):
    def test_robots_files(self) -> None:
        agents = generate.user_agents(self.catalog)
        recommended = data_lines("rules/robots-txt/robots.txt")
        training = data_lines("rules/robots-txt/robots-training-only.txt")
        full = data_lines("rules/robots-txt/robots-full.txt")
        for lines in (recommended, training, full):
            self.assertEqual(lines[-1], "Disallow: /")
            self.assertTrue(all(line.startswith("User-agent: ") for line in lines[:-1]))
        self.assertEqual({line[12:] for line in recommended[:-1]}, {agent.token for agent in agents})
        self.assertEqual({line[12:] for line in training[:-1]}, {agent.token for agent in agents if agent.purpose == "training"})
        community = set(self.catalog["inbound"]["community_robots_tokens"]["tokens"])
        self.assertTrue(community <= {line[12:] for line in full[:-1]})
        recommended_text = read("rules/robots-txt/robots.txt")
        full_text = read("rules/robots-txt/robots-full.txt")
        self.assertIn("User-agent: Devin\n", recommended_text)
        self.assertNotIn("Mozilla", recommended_text)
        self.assertEqual(full_text.count("User-agent: Devin\n"), 1)

    def test_nginx_user_agent_pattern(self) -> None:
        text = read("rules/nginx/ai-crawlers-http.conf")
        pattern = re.search(r'"~\*(\(\?:[^"]+\))" 1;', text).group(1)
        compiled = re.compile(pattern, re.IGNORECASE)
        self.assertTrue(compiled.search("Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.2; +https://openai.com/gptbot"))
        self.assertTrue(compiled.search("Mozilla/5.0 (compatible; Claude-SearchBot/1.0; +Claude-SearchBot@anthropic.com)"))
        self.assertFalse(compiled.search("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36"))
        devin = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36; Devin/1.0; +https://devin.ai"
        chrome = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        self.assertTrue(compiled.search(devin))
        self.assertFalse(compiled.search(chrome))
        self.assertNotIn("Google-Extended", pattern, "robots.txt-only tokens are never sent as a User-Agent")
        self.assertNotIn("Applebot-Extended", pattern)

    def test_nginx_geo_matches_aggregate(self) -> None:
        text = read("rules/nginx/ai-crawlers-http.conf")
        geo = re.findall(r"^    (\S+/\d+) 1;$", text, re.MULTILINE)
        aggregate = data_lines("rules/ip-feeds/ai-crawlers-ipv4.txt") + data_lines("rules/ip-feeds/ai-crawlers-ipv6.txt")
        self.assertEqual(geo, aggregate)

    def test_ip_feed_files_are_valid_and_collapsed(self) -> None:
        for relative in sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "rules/ip-feeds").glob("*.txt")):
            networks = [ipaddress.ip_network(line, strict=True) for line in data_lines(relative)]
            for version in (4, 6):
                family = [net for net in networks if net.version == version]
                self.assertEqual(family, list(ipaddress.collapse_addresses(family)), f"{relative} is not collapsed")

    def test_aggregate_contains_only_aggregated_feeds(self) -> None:
        feed_data = generate.load_feed_data(ROOT, self.catalog)
        expected_v4, expected_v6 = generate.aggregate_networks(feed_data)
        self.assertEqual(data_lines("rules/ip-feeds/ai-crawlers-ipv4.txt"), [str(net) for net in expected_v4])
        self.assertEqual(data_lines("rules/ip-feeds/ai-crawlers-ipv6.txt"), [str(net) for net in expected_v6])
        self.assertEqual(data_lines("rules/crowdstrike/crawler-prefixes-ipv4.txt"), [str(net) for net in expected_v4])
        googlebot = next(item for item in feed_data if item.feed.feed_id == "googlebot")
        aggregate = set(expected_v4)
        for net in googlebot.ipv4:
            self.assertFalse(any(net.subnet_of(agg) for agg in aggregate if agg.version == 4), f"{net} leaked into aggregate")

    def test_anthropic_network_file(self) -> None:
        listed = [ipaddress.ip_network(line) for line in data_lines("rules/ip-feeds/anthropic-network.txt")]
        required = [
            "153.61.192.0/23",
            "153.61.196.0/23",
            "153.61.198.0/24",
            "160.79.104.0/21",
            "216.73.216.0/22",
            "2607:6bc0::/48",
            "2607:6bc0:11::/48",
        ]
        self.assertEqual([str(net) for net in listed], required)
        body = {str(net) for net in listed}
        text = read("rules/ip-feeds/anthropic-network.txt")
        for excluded in ("153.61.0.0/16", "2607:6bc0::/32", "209.249.57.0/24"):
            self.assertNotIn(excluded, body)
        self.assertIn("Mitel Networks", text)
        aggregate = set(data_lines("rules/ip-feeds/ai-crawlers-ipv4.txt"))
        self.assertNotIn("160.79.104.0/21", aggregate)
        self.assertNotIn("153.61.192.0/23", aggregate)
        self.assertIn("216.73.216.0/22", aggregate)

    def test_xai_network_file(self) -> None:
        listed = data_lines("rules/ip-feeds/xai-network.txt")
        self.assertEqual(listed, ["31.207.0.0/24"])
        text = read("rules/ip-feeds/xai-network.txt")
        self.assertIn("Twitter Inc.", text)
        for excluded in ("69.12.56.0/21", "192.48.236.0/23", "209.237.192.0/19"):
            self.assertNotIn(excluded, listed)
        aggregate = set(data_lines("rules/ip-feeds/ai-crawlers-ipv4.txt"))
        self.assertNotIn("31.207.0.0/24", aggregate)

    def test_openai_network_file(self) -> None:
        listed = data_lines("rules/ip-feeds/openai-network.txt")
        self.assertEqual(listed, ["199.47.142.0/23"])
        text = read("rules/ip-feeds/openai-network.txt")
        self.assertIn("2604:f20::/32", text)
        self.assertNotIn("2604:f20::/32", listed)
        aggregate = set(data_lines("rules/ip-feeds/ai-crawlers-ipv4.txt"))
        self.assertNotIn("199.47.142.0/23", aggregate)

    def test_plugin_catalog(self) -> None:
        paths = [
            "plugins/wordpress/protect-from-ai/data/catalog.json",
            "plugins/directadmin/protect_from_ai/data/catalog.json",
            "plugins/cpanel/protect_from_ai/data/catalog.json",
        ]
        payloads = [json.loads(read(path)) for path in paths]
        self.assertEqual(payloads[0], payloads[1])
        self.assertEqual(payloads[0], payloads[2])
        payload = payloads[0]
        self.assertEqual(payload["creator"], "Albert Clownstein")
        crawlers = {item["token"]: item for item in payload["crawlers"]}
        self.assertTrue(crawlers["GPTBot"]["header"])
        self.assertFalse(crawlers["Google-Extended"]["header"])
        self.assertFalse(crawlers["Applebot-Extended"]["header"])
        self.assertTrue(all(item["header"] is False for item in payload["crawlers"] if item["purpose"] == "community"))
        self.assertFalse(crawlers["Cursor"]["header"])
        self.assertEqual(crawlers["CCBot"]["profile"], "recommended")
        self.assertEqual(crawlers["Devin"]["profile"], "recommended")
        self.assertEqual(crawlers["Devin"]["header_patterns"], ["Devin/", "+https://devin.ai"])
        self.assertTrue(crawlers["Devin"]["header"])
        self.assertIn("Bytespider", crawlers)
        services = {item["id"]: item for item in payload["inference"]}
        openai = services["OpenAI:OpenAI API:host"]
        self.assertEqual(openai["values"], ["api.openai.com"])
        self.assertEqual(openai["profile"], "recommended")
        replicate = next(item for item in payload["inference"] if item["values"] == ["api.replicate.com"])
        self.assertEqual(replicate["profile"], "full")
        bedrock = next(item for item in payload["inference"] if "Bedrock Runtime" in item["service"] and item["match"] == "host")
        self.assertIn("bedrock-runtime.us-east-1.amazonaws.com", bedrock["values"])
        self.assertNotIn("bedrock-runtime.us-west-1.amazonaws.com", bedrock["values"])
        shared = (ROOT / "plugins/shared/ProtectFromAI.pm").read_bytes()
        self.assertEqual((ROOT / "plugins/directadmin/protect_from_ai/lib/ProtectFromAI.pm").read_bytes(), shared)
        self.assertEqual((ROOT / "plugins/cpanel/protect_from_ai/lib/ProtectFromAI.pm").read_bytes(), shared)

    def test_cloudflare_expression(self) -> None:
        parts = sorted((ROOT / "guides/cloudflare-waf").glob("custom-rule-expression*.txt"))
        text = "\n".join(path.read_text(encoding="utf-8").strip() for path in parts)
        for path in parts:
            self.assertLessEqual(len(path.read_text(encoding="utf-8").strip()), generate.CLOUDFLARE_EXPRESSION_LIMIT)
        for token in generate.header_tokens(self.catalog):
            self.assertIn(f'(lower(http.user_agent) contains "{token.lower()}")', text)

    def test_aws_waf_regex_patterns(self) -> None:
        parts = sorted((ROOT / "guides/aws-waf").glob("user-agent-regex-patterns*.txt"))
        patterns = []
        for path in parts:
            lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line != ""]
            self.assertLessEqual(len(lines), generate.AWS_WAF_REGEX_PER_SET)
            patterns.extend(lines)
        for pattern in patterns:
            self.assertLessEqual(len(pattern), generate.AWS_WAF_REGEX_MAX_LENGTH)
            self.assertEqual(pattern, pattern.lower(), "patterns assume a LOWERCASE text transformation")
        combined = [re.compile(pattern) for pattern in patterns]
        for token in generate.header_tokens(self.catalog):
            self.assertTrue(any(p.search(f"mozilla/5.0 (compatible; {token.lower()}/1.0)") for p in combined), token)


class TestParsersAndValidation(unittest.TestCase):
    def test_google_json_parser(self) -> None:
        payload = json.dumps({"creationTime": "x", "prefixes": [{"ipv4Prefix": "192.0.2.0/24"}, {"ipv6Prefix": "2001:db8::/32"}]})
        self.assertEqual(
            generate.parse_google_json(payload),
            [ipaddress.ip_network("192.0.2.0/24"), ipaddress.ip_network("2001:db8::/32")],
        )

    def test_google_json_rejects_host_bits(self) -> None:
        with self.assertRaises(generate.CatalogError):
            generate.parse_google_json(json.dumps({"prefixes": [{"ipv4Prefix": "192.0.2.1/24"}]}))

    def test_amazon_html_parser(self) -> None:
        page = '<script>var d = {"prefixes":[{"ip_prefix":"198.51.100.7/32"},{"ipv4Prefix":"203.0.113.0/24"}]};</script>'
        self.assertEqual(
            generate.parse_amazon_html(page),
            [ipaddress.ip_network("198.51.100.7/32"), ipaddress.ip_network("203.0.113.0/24")],
        )
        with self.assertRaises(generate.CatalogError):
            generate.parse_amazon_html("<html>no data</html>")

    def test_catalog_rejects_invalid_entries(self) -> None:
        base = generate.load_catalog(ROOT)
        bad_values = [
            {"value": "amazonaws.com", "match": "subdomains"},
            {"value": "bad_host.example", "match": "host"},
            {"value": "api.openai.com", "match": "host"},
            {"value": "api.example.test", "match": "regex"},
        ]
        for bad in bad_values:
            catalog = copy.deepcopy(base)
            catalog["egress"]["entries"].append({
                "tier": "core", "provider": "Test", "service": "Test", "source": "https://example.test", **bad,
            })
            with self.assertRaises(generate.CatalogError, msg=str(bad)):
                generate.validate_catalog(catalog)


class TestRefreshFeeds(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / "catalog", self.temp / "catalog")
        shutil.copytree(ROOT / "data", self.temp / "data")
        self.catalog = generate.load_catalog(self.temp)
        self.feed = next(feed for feed in generate.feeds(self.catalog) if feed.feed_id == "openai-gptbot")
        self.snapshot = self.temp / generate.SNAPSHOT_DIR / self.feed.snapshot
        self.original = self.snapshot.read_text(encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp, ignore_errors=True)

    def run_refresh(self, fetch) -> tuple[dict, list[str]]:
        with mock.patch.object(refresh_feeds, "fetch", side_effect=fetch), \
                mock.patch("sys.stdout", new_callable=io.StringIO), mock.patch("sys.stderr", new_callable=io.StringIO):
            return refresh_feeds.refresh(self.temp, refresh_feeds.DEFAULT_MIN_RATIO, {self.feed.feed_id})

    def test_failed_download_keeps_previous_snapshot(self) -> None:
        def fail(url: str) -> str:
            raise refresh_feeds.urllib.error.URLError("offline")

        status, failures = self.run_refresh(fail)
        self.assertEqual(failures, [self.feed.feed_id])
        self.assertEqual(status[self.feed.feed_id]["status"], "failed")
        self.assertEqual(self.snapshot.read_text(encoding="utf-8"), self.original)

    def test_malformed_feed_keeps_previous_snapshot(self) -> None:
        _, failures = self.run_refresh(lambda url: '{"prefixes": [{"ipv4Prefix": "not-an-address"}]}')
        self.assertEqual(failures, [self.feed.feed_id])
        self.assertEqual(self.snapshot.read_text(encoding="utf-8"), self.original)

    def test_shrunken_feed_keeps_previous_snapshot(self) -> None:
        _, failures = self.run_refresh(lambda url: json.dumps({"prefixes": [{"ipv4Prefix": "192.0.2.0/24"}]}))
        self.assertEqual(failures, [self.feed.feed_id])
        self.assertEqual(self.snapshot.read_text(encoding="utf-8"), self.original)

    def test_valid_feed_replaces_snapshot(self) -> None:
        document = json.loads(self.original)
        document["prefixes"].append({"ipv4Prefix": "192.0.2.0/24"})
        status, failures = self.run_refresh(lambda url: json.dumps(document))
        self.assertEqual(failures, [])
        self.assertEqual(status[self.feed.feed_id]["status"], "ok")
        networks = generate.load_feed_snapshot(self.temp, self.feed)
        self.assertIn(ipaddress.ip_network("192.0.2.0/24"), networks)

    def test_unchanged_prefixes_do_not_rewrite_snapshot(self) -> None:
        before = self.snapshot.read_bytes()
        status, failures = self.run_refresh(lambda url: self.original)
        self.assertEqual(failures, [])
        self.assertEqual(status[self.feed.feed_id]["status"], "ok")
        self.assertEqual(self.snapshot.read_bytes(), before)

    def test_amazon_snapshot_rendering(self) -> None:
        feed = next(feed for feed in generate.feeds(self.catalog) if feed.fmt == "amazon-html")
        text, networks = refresh_feeds.render_snapshot(feed, '{"ipv4Prefix": "198.51.100.8/32"}{"ipv4Prefix": "198.51.100.9/32"}', "2026-01-01T00:00:00Z")
        self.assertEqual(networks, [ipaddress.ip_network("198.51.100.8/31")])
        self.assertEqual(generate.parse_prefix_lines(text), networks)


def client_hello(server_name: str) -> bytes:
    context = ssl.create_default_context()
    incoming, outgoing = ssl.MemoryBIO(), ssl.MemoryBIO()
    connection = context.wrap_bio(incoming, outgoing, server_hostname=server_name)
    try:
        connection.do_handshake()
    except ssl.SSLWantReadError:
        pass
    return outgoing.read()


TCL_STUBS = r"""
namespace eval TCP {}
namespace eval SSL {}
namespace eval HTTP {}
namespace eval IP {}
array set ::handlers {}
proc when {event args} { set ::handlers($event) [lindex $args end] }
proc call {name args} { uplevel 1 [list $name {*}$args] }
proc log {args} {}
proc event {args} {}
proc reject {} { set ::result reject }
proc IP::client_addr {} { return 192.0.2.10 }
proc TCP::collect {args} { set ::result collect }
proc TCP::release {} { set ::result release }
proc TCP::payload {} { return $::payload }
proc SSL::extensions {args} {
    if {[lindex $args 0] eq "exists"} { return [info exists ::sni_extension] }
    return $::sni_extension
}
proc HTTP::method {} { return $::http_method }
proc HTTP::uri {} { return $::http_uri }
proc HTTP::host {} { return $::http_host }
proc HTTP::path {} { return $::http_path }
proc HTTP::respond {code args} { set ::result "respond $code" }
proc class {op args} {
    if {$op eq "names"} { return [dict keys $::groups([lindex $args 0])] }
    if {[lindex $args 0] eq "--"} { set args [lrange $args 1 end] }
    lassign $args value operator group
    foreach key [dict keys $::groups($group)] {
        if {$operator eq "equals" && $value eq $key} { return 1 }
        if {$operator eq "ends_with" && [string match "*$key" $value]} { return 1 }
    }
    return 0
}
"""


@unittest.skipIf(tkinter is None, "tkinter (Tcl) is not available")
class TestF5IRules(unittest.TestCase):
    """Executes the generated iRule logic in a Tcl interpreter with BIG-IP commands stubbed."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.groups = parse_tmsh_datagroups(read("rules/f5/ai-inference-datagroups.tmsh"))

    def interpreter(self, irule: str):
        tcl = tkinter.Tcl()
        tcl.eval(TCL_STUBS)
        for name, records in self.groups.items():
            tcl.call("set", f"::groups({name})", tcl.call("dict", "create", *[item for key in records for item in (key, "")]))
        tcl.eval(read(irule))
        return tcl

    def run_event(self, tcl, event: str) -> str:
        tcl.eval("set ::result allow")
        tcl.eval(f"uplevel #0 $::handlers({event})")
        return tcl.eval("set ::result")

    def test_host_matching(self) -> None:
        tcl = self.interpreter("rules/f5/ai-inference.irule")
        blocked = ["api.openai.com", "API.OpenAI.com.", "contoso.openai.azure.com", "us-central1-aiplatform.googleapis.com",
                   "newregion9-aiplatform.googleapis.com", "bedrock-runtime.us-east-1.amazonaws.com"]
        allowed = ["example.com", "aiplatform.googleapis.com.example.net", "storage.googleapis.com", "openai.azure.com.example.net",
                   "-aiplatform.googleapis.com", "s3.us-east-1.amazonaws.com"]
        for host in blocked:
            self.assertEqual(tcl.call("ai_inference_host_blocked", host), 1, host)
        for host in allowed:
            self.assertEqual(tcl.call("ai_inference_host_blocked", host), 0, host)

    def test_http_request_event(self) -> None:
        tcl = self.interpreter("rules/f5/ai-inference.irule")
        cases = [
            ("CONNECT", "api.anthropic.com:443", "", "", "respond 403"),
            ("CONNECT", "example.com:443", "", "", "allow"),
            ("GET", "/client/v4/accounts/abc/ai/run/@cf/meta/llama", "api.cloudflare.com", "/client/v4/accounts/abc/ai/run/@cf/meta/llama", "respond 403"),
            ("GET", "/client/v4/zones", "api.cloudflare.com", "/client/v4/zones", "allow"),
            ("POST", "/v1/messages", "api.anthropic.com", "/v1/messages", "respond 403"),
        ]
        for method, uri, host, path, expected in cases:
            tcl.call("set", "::http_method", method)
            tcl.call("set", "::http_uri", uri)
            tcl.call("set", "::http_host", host)
            tcl.call("set", "::http_path", path)
            self.assertEqual(self.run_event(tcl, "HTTP_REQUEST"), expected, (method, uri, host))

    def test_clientssl_clienthello_event(self) -> None:
        tcl = self.interpreter("rules/f5/ai-inference.irule")
        for name, expected in (("api.openai.com", "reject"), ("example.com", "allow")):
            encoded = name.encode("ascii")
            extension = (b"\x00\x00" + (len(encoded) + 5).to_bytes(2, "big") + (len(encoded) + 3).to_bytes(2, "big")
                         + b"\x00" + len(encoded).to_bytes(2, "big") + encoded)
            tcl.call("set", "::sni_extension", extension)
            self.assertEqual(self.run_event(tcl, "CLIENTSSL_CLIENTHELLO"), expected, name)

    def test_passthrough_parses_real_client_hello(self) -> None:
        tcl = self.interpreter("rules/f5/ai-inference-sni-passthrough.irule")
        for name, expected in (("api.openai.com", "reject"), ("us-east5-aiplatform.googleapis.com", "reject"),
                               ("contoso.openai.azure.com", "reject"), ("example.com", "release")):
            tcl.call("set", "::payload", client_hello(name))
            self.run_event(tcl, "CLIENT_ACCEPTED")
            self.assertEqual(self.run_event(tcl, "CLIENT_DATA"), expected, name)

    def test_passthrough_releases_non_tls(self) -> None:
        tcl = self.interpreter("rules/f5/ai-inference-sni-passthrough.irule")
        tcl.call("set", "::payload", b"GET / HTTP/1.1\r\nHost: api.openai.com\r\n\r\n")
        self.run_event(tcl, "CLIENT_ACCEPTED")
        self.assertEqual(self.run_event(tcl, "CLIENT_DATA"), "release")


class TestPluginPackages(unittest.TestCase):
    def test_archives_have_update_metadata(self) -> None:
        destination = ROOT / "dist-test"
        shutil.rmtree(destination, ignore_errors=True)
        subprocess.run(
            [sys.executable, "tools/package_plugins.py", "--dist", str(destination), "--version", "abc123"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        release = json.loads((destination / "release.json").read_text(encoding="utf-8"))
        self.assertEqual(release["version"], "abc123")
        self.assertTrue(release["wordpress"].endswith("/protect-from-ai-wordpress.zip"))
        self.assertTrue(release["directadmin"].endswith("/protect_from_ai.tar.gz"))
        self.assertTrue(release["cpanel"].endswith("/protect-from-ai-cpanel.tar.gz"))
        wordpress = zipfile.ZipFile(destination / "protect-from-ai-wordpress.zip")
        self.assertIn("protect-from-ai/protect-from-ai.php", wordpress.namelist())
        self.assertEqual(
            json.loads(wordpress.read("protect-from-ai/data/package.json"))["channel"],
            "github",
        )
        directadmin = tarfile.open(destination / "protect_from_ai.tar.gz", "r:gz")
        names = directadmin.getnames()
        self.assertIn("plugin.conf", names)
        self.assertIn("scripts/update.sh", names)
        self.assertIn("hooks/user_txt.html", names)
        self.assertIn("hooks/reseller_txt.html", names)
        self.assertIn("user/index.html", names)
        self.assertIn("reseller/index.html", names)
        self.assertEqual(directadmin.getmember("scripts/apply.sh").mode, 0o755)
        self.assertEqual(directadmin.getmember("user/index.html").mode, 0o755)
        cpanel = tarfile.open(destination / "protect-from-ai-cpanel.tar.gz", "r:gz")
        self.assertIn("install.sh", cpanel.getnames())
        self.assertIn("update.sh", cpanel.getnames())
        shutil.rmtree(destination, ignore_errors=True)


class TestPluginBehavior(unittest.TestCase):
    def test_panel_configuration_rules(self) -> None:
        self.run_interpreter("perl", "perl:5.40-slim", ["perl", "tests/check_panel.pl"])

    def test_wordpress_host_matching(self) -> None:
        self.run_interpreter("php", "php:8.3-cli", ["php", "tests/check_wordpress.php"])

    def run_interpreter(self, binary: str, image: str, command: list[str]) -> None:
        local = shutil.which(binary)
        if local:
            completed = subprocess.run([local, *command[1:]], cwd=ROOT, capture_output=True, text=True, timeout=60)
        elif shutil.which("docker"):
            completed = subprocess.run(
                ["docker", "run", "--rm", "-v", f"{ROOT}:/src", "-w", "/src", image, *command],
                cwd=ROOT, capture_output=True, text=True, timeout=180,
            )
        else:
            self.fail(f"{binary} or docker is required to verify plugin behavior")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
