#!/bin/sh
set -eu
rf2_root=$(CDPATH= cd -- "${0%/*}/.." && pwd)
rf2_trust_bin=${RF2_TRUST_BIN:-"$rf2_root/output/trust-0.18/rf2-trust"}
rf2_key_file=${RF2_TRUST_KEY_FILE:-"$HOME/.config/riverflow/receipts.key"}
if [ ! -x "$rf2_trust_bin" ] || [ ! -f "$rf2_key_file" ]; then
 printf '%s\n' 'Supply the native RF2_TRUST_BIN and an administrator-created RF2_TRUST_KEY_FILE. No automatic key creation or runtime fallback.' >&2
 exit 1
fi
exec "$rf2_trust_bin" mcp "$rf2_key_file"
