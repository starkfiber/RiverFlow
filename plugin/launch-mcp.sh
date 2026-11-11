#!/bin/sh
set -eu
rf2_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
for rf2_node in "${RF2_NODE:-}" /opt/homebrew/opt/node@22/bin/node /usr/local/opt/node@22/bin/node node; do
 [ -n "$rf2_node" ] || continue
 if "$rf2_node" -e 'if(Number(process.versions.node.split(".")[0])<22)process.exit(1)' >/dev/null 2>&1; then
  exec "$rf2_node" "$rf2_root/src/mcp.mjs"
 fi
done
printf '%s\n' 'RF² requires working Node 22+. Set RF2_NODE to its path.' >&2
exit 1
