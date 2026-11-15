#!/bin/sh
# Explicit native developer entry point. Never downloads or executes source apps.
set -eu
usage() {
 /bin/cat <<'EOF'
Usage: tools/dev.sh [--home NATIVE-BUNDLE] COMMAND
  doctor                         Check the host and selected native tools
  status                         Show the bounded runtime's status
  check SOURCE                   Check trusted Mac source without an output file
  build SOURCE NEW-DIRECTORY [--opt]
                                 Compile and locally sign a Mac application
  firmware SOURCE NEW-PREFIX      Compile an ESP32-C3 image; never flash it
  mcp                            Start the existing bounded native MCP service
Set RF2_HOME instead of --home to retain an explicit bundle selection.
Run a built application yourself: NEW-DIRECTORY/program
EOF
}
fail() { printf '%s\n' "RF2: $*" >&2; exit 2; }
bundle=${RF2_HOME:-}
if [ "${1:-}" = '--home' ]; then
 [ "$#" -ge 2 ] || fail '--home needs a directory'
 bundle=$2; shift 2
fi
command=${1:-help}
case "$command" in
 help|--help|-h) usage; exit 0 ;;
 doctor|status|mcp) [ "$#" -eq 1 ] || fail "$command takes no arguments" ;;
 check) [ "$#" -eq 2 ] || fail 'check needs one source path' ;;
 build)
 [ "$#" -eq 3 ] || [ "$#" -eq 4 ] || fail 'build needs source, new directory and optional --opt'
 [ "$#" -ne 4 ] || [ "$4" = '--opt' ] || fail 'only --opt is supported'
 ;;
 firmware) [ "$#" -eq 3 ] || fail 'firmware needs source and new output prefix' ;;
 *) fail "unknown command: $command (use --help)" ;;
esac
[ -n "$bundle" ] || fail 'select the native bundle with RF2_HOME or --home; see docs/FIRST-APP.md'
[ -d "$bundle" ] || fail "bundle directory does not exist: $bundle"
# Resolve relative bundle paths once; preserve spaces and avoid PATH lookup.
bundle=$(CDPATH='' cd -- "$bundle" && pwd -P)
[ "$(/usr/bin/uname -s)" = Darwin ] && [ "$(/usr/bin/uname -m)" = arm64 ] || fail 'these native tools require an Apple Silicon Mac in a native terminal'
tool() {
 [ -f "$bundle/$1" ] && [ -x "$bundle/$1" ] || fail "missing executable: $bundle/$1"
 /usr/bin/codesign --verify "$bundle/$1" || fail "signature check failed for $1; obtain the intended bundle again"
}
case "$command" in
 doctor)
 tool rf2c; tool rf2
 printf '%s\n' "Host: Apple Silicon macOS" "Bundle: $bundle" 'Mac compiler and runtime: executable; local signatures verified'
 if [ -e "$bundle/rf2-esp32c3" ]; then
  tool rf2-esp32c3
  printf '%s\n' 'ESP32-C3 compiler: executable; local signature verified'
 else
  printf '%s\n' 'ESP32-C3 compiler: absent (not required for Mac apps)'
 fi
 printf '%s\n' 'Signatures do not establish publisher identity or notarization.'
 "$bundle/rf2" status
 ;;
 status|mcp) tool rf2; exec "$bundle/rf2" "$command" ;;
 check) tool rf2c; exec "$bundle/rf2c" --check "$2" ;;
 build)
 tool rf2c
 script_dir=$(CDPATH='' cd -- "$(/usr/bin/dirname -- "$0")" && pwd -P)
 exec /bin/sh "$script_dir/build-program.sh" "$bundle/rf2c" "$2" "$3" ${4:+"$4"}
 ;;
 firmware) tool rf2-esp32c3; exec "$bundle/rf2-esp32c3" "$2" "$3" ;;
esac
