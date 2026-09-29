#!/usr/bin/env bash
# Install the AI inference deny rules into Pi-hole v6 using the pihole command-line interface.
#
# Usage: sudo ./install.sh [recommended|full]
#
# Each domain in ai-inference-domains.txt (or ai-inference-domains-full.txt) is added with
# "pihole --wild", which blocks the domain and every subdomain. Each filter in
# ai-inference-regex.txt is added with "pihole --regex". Running the script again is safe:
# Pi-hole skips entries that already exist.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
profile="${1:-recommended}"

case "$profile" in
    recommended) domain_file="$here/ai-inference-domains.txt" ;;
    full) domain_file="$here/ai-inference-domains-full.txt" ;;
    *)
        echo "usage: $0 [recommended|full]" >&2
        exit 2
        ;;
esac
regex_file="$here/ai-inference-regex.txt"

if ! command -v pihole >/dev/null 2>&1; then
    echo "error: the pihole command was not found; run this script on the Pi-hole host" >&2
    exit 1
fi

for file in "$domain_file" "$regex_file"; do
    if [[ ! -r "$file" ]]; then
        echo "error: cannot read $file" >&2
        exit 1
    fi
done

read_entries() {
    grep -Ev '^[[:space:]]*(#|$)' "$1" | tr -d '\r'
}

mapfile -t domains < <(read_entries "$domain_file")
mapfile -t regexes < <(read_entries "$regex_file")

if (( ${#domains[@]} > 0 )); then
    echo "Adding ${#domains[@]} wildcard domain entries from $(basename "$domain_file")"
    pihole --wild "${domains[@]}"
fi

if (( ${#regexes[@]} > 0 )); then
    echo "Adding ${#regexes[@]} regex filters from $(basename "$regex_file")"
    pihole --regex "${regexes[@]}"
fi

pihole reloadlists
echo "Done. Verify with: pihole -q api.openai.com"
