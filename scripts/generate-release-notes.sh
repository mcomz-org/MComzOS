#!/usr/bin/env bash
# Generate GitHub Release notes for an MComzOS version tag.
#
# Usage:  generate-release-notes.sh <tag> <owner/repo>
# Writes: Markdown on stdout
#
# Groups the commits since the previous tag into Fixes / Features / CI / Docs
# buckets based on conventional-commit prefixes, and appends the asset list
# plus a "Full Changelog" link. Requires full git history (fetch-depth: 0).

set -euo pipefail

TAG="${1:?tag required, e.g. v0.0.2-pre-alpha.8}"
REPO="${2:?owner/repo required, e.g. mcomz-org/MComzOS}"

# Previous tag — the one reachable from HEAD~1 (so this works whether we're
# running on the tag commit itself or on a descendant).
PREV=$(git describe --tags --abbrev=0 "${TAG}^" 2>/dev/null || true)

if [ -n "$PREV" ]; then
  RANGE="$PREV..$TAG"
  COMPARE="https://github.com/$REPO/compare/$PREV...$TAG"
else
  # First release — walk the whole history.
  RANGE="$TAG"
  COMPARE=""
fi

# Pull commit subjects for the range; skip merge commits.
commits=$(git log --no-merges --pretty=format:'%s' "$RANGE")

bucket_fix=""
bucket_feat=""
bucket_ci=""
bucket_docs=""
bucket_other=""

while IFS= read -r subject; do
  [ -z "$subject" ] && continue
  case "$subject" in
    fix*)          bucket_fix+="- ${subject}"$'\n' ;;
    feat*)         bucket_feat+="- ${subject}"$'\n' ;;
    chore\(ci*|ci*) bucket_ci+="- ${subject}"$'\n' ;;
    docs*)         bucket_docs+="- ${subject}"$'\n' ;;
    *)             bucket_other+="- ${subject}"$'\n' ;;
  esac
done <<< "$commits"

cat <<HEADER
## MComzOS $TAG

Off-grid emergency communications hub — master image for Raspberry Pi 4/5 (ARM64) and x86_64 PCs running Debian 12 Bookworm.

HEADER

if [ -n "$bucket_fix" ];   then printf '### Fixes\n%s\n' "$bucket_fix"; fi
if [ -n "$bucket_feat" ];  then printf '### Features\n%s\n' "$bucket_feat"; fi
if [ -n "$bucket_docs" ];  then printf '### Documentation\n%s\n' "$bucket_docs"; fi
if [ -n "$bucket_ci" ];    then printf '### CI & build\n%s\n' "$bucket_ci"; fi
if [ -n "$bucket_other" ]; then printf '### Other changes\n%s\n' "$bucket_other"; fi

cat <<FOOTER
### Downloads

| File | Target | How to use |
|---|---|---|
| \`mcomzos-rpi.img.xz\` | Raspberry Pi 4 / 5 (ARM64) | Flash with Raspberry Pi Imager or \`xzcat … \| sudo dd of=/dev/sdX bs=4M\` |
| \`mcomzos-x86_64.img.xz\` | x86_64 PC (UEFI) | Flash to a USB stick with \`xzcat … \| sudo dd of=/dev/sdX bs=4M\` |
| \`mcomzos-rpi-imager.json\` | Raspberry Pi Imager | Paste the raw URL into Imager → *Choose OS* → *Use custom* |

### First boot

1. On boot the hub waits 5 minutes for a routable LAN IP. If none arrives it activates its own WiFi access point.
2. SSID: **MComzOS**, password: **mcomzos1** (change in \`/etc/hostapd/hostapd.conf\`).
3. Browse to **https://mcomz.local** (or **https://192.168.4.1** in AP mode). Accept the self-signed certificate.
4. VNC password for the JS8Call session: **mcomz**.

See the [README](https://github.com/$REPO/blob/main/README.md) for the full service list, port map, and hardware notes.
FOOTER

if [ -n "$COMPARE" ]; then
  printf '\n**Full Changelog**: %s\n' "$COMPARE"
fi
