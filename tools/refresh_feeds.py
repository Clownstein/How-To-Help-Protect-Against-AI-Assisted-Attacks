#!/usr/bin/env python3
"""Download published AI crawler address feeds, validate them, and update the snapshots.

Each feed listed under inbound.feeds in catalog/catalog.json is fetched over HTTPS,
parsed, and validated with the ipaddress module. A snapshot is replaced only when the
new data parses cleanly and has not shrunk below the configured ratio of the previous
snapshot; otherwise the last good snapshot is kept and the failure is reported. After
the snapshots are updated, tools/generate.py runs so every rule file reflects them.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import generate

USER_AGENT = "How-to-help-protect-against-ai-attacks feed refresher (Python urllib)"
TIMEOUT_SECONDS = 60
DEFAULT_MIN_RATIO = 0.5
STATUS_FILE = "refresh-status.json"


def fetch(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json, text/html;q=0.9, */*;q=0.1"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise urllib.error.HTTPError(url, response.status, "unexpected status", response.headers, None)
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset)


def render_snapshot(feed: generate.Feed, payload: str, retrieved: str) -> tuple[str, list[generate.Network]]:
    """Return the snapshot file text and the parsed networks for a downloaded payload."""
    if feed.fmt == "google-json":
        networks = generate.parse_google_json(payload)
        document = json.loads(payload)
        return json.dumps(document, indent=2, ensure_ascii=False) + "\n", networks
    if feed.fmt == "amazon-html":
        ipv4, ipv6 = generate.collapse(generate.parse_amazon_html(payload))
        networks = list(ipv4) + list(ipv6)
        header = [f"# Source: {feed.url}", f"# Retrieved: {retrieved}"]
        return "\n".join(header + [str(net) for net in networks]) + "\n", networks
    raise generate.CatalogError(f"feed {feed.feed_id}: unknown format {feed.fmt}")


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def load_status(path: Path) -> dict:
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def refresh(root: Path, min_ratio: float, only: set[str] | None) -> tuple[dict, list[str]]:
    catalog = generate.load_catalog(root)
    snapshot_dir = root / generate.SNAPSHOT_DIR
    status_path = snapshot_dir / STATUS_FILE
    status = load_status(status_path)
    failures: list[str] = []
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    for feed in generate.feeds(catalog):
        if only and feed.feed_id not in only:
            continue
        record = status.get(feed.feed_id, {})
        record["url"] = feed.url
        record["snapshot"] = feed.snapshot
        record["last_attempt"] = now
        try:
            payload = fetch(feed.url)
            text, networks = render_snapshot(feed, payload, now)
            if not networks:
                raise generate.CatalogError("feed returned no prefixes")
            try:
                previous = generate.load_feed_snapshot(root, feed)
            except (generate.CatalogError, OSError, ValueError):
                previous = None
            before = len(previous) if previous is not None else None
            if before and len(networks) < before * min_ratio:
                raise generate.CatalogError(
                    f"feed shrank from {before} to {len(networks)} prefixes (below ratio {min_ratio}); keeping previous snapshot"
                )
            if previous is not None and {str(net) for net in previous} == {str(net) for net in networks}:
                record.update({"status": "ok", "prefixes": len(networks), "last_success": now, "error": None})
                print(f"unchanged {feed.feed_id:37} {len(networks):5} prefixes")
            else:
                atomic_write(snapshot_dir / feed.snapshot, text)
                record.update({"status": "ok", "prefixes": len(networks), "last_success": now, "error": None})
                print(f"ok      {feed.feed_id:40} {len(networks):5} prefixes")
        except (urllib.error.URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError,
                generate.CatalogError, ValueError, OSError) as error:
            record.update({"status": "failed", "error": str(error)})
            failures.append(feed.feed_id)
            print(f"FAILED  {feed.feed_id:40} {error}", file=sys.stderr)
        status[feed.feed_id] = record

    atomic_write(status_path, json.dumps(dict(sorted(status.items())), indent=2) + "\n")
    return status, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=generate.ROOT, help="repository root (default: this checkout)")
    parser.add_argument("--feed", action="append", dest="feeds", help="refresh only this feed id (repeatable)")
    parser.add_argument("--min-ratio", type=float, default=DEFAULT_MIN_RATIO,
                        help="reject a feed whose prefix count falls below this fraction of the previous snapshot")
    parser.add_argument("--no-generate", action="store_true", help="update snapshots without regenerating rule files")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    try:
        _, failures = refresh(root, args.min_ratio, set(args.feeds) if args.feeds else None)
    except (generate.CatalogError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if not args.no_generate:
        result = generate.main(["--root", str(root)])
        if result != 0:
            return result
    if failures:
        print(f"{len(failures)} feed(s) kept their previous snapshot: {', '.join(failures)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
