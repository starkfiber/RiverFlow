#!/bin/sh
set -eu
rf2_root=$(CDPATH= cd -- "${0%/*}/.." && pwd)
rf2_bin=${RF2_BIN:-"$rf2_root/output/bin/rf2"}
if [ ! -x "$rf2_bin" ]; then
 printf '%s\n' 'RF2 native executable missing. Supply RF2_BIN or build the documented macOS ARM64 target. No Node fallback.' >&2
 exit 1
fi
if [ "${RF2_MCP_COMPACT:-0}" = 1 ]; then
 exec "$rf2_bin" mcp --compact
fi
exec "$rf2_bin" mcp
