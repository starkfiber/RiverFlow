# RiverFlow editor qualification

The test uses the actual TextMate and Oniguruma engines, with explicit development dependencies. Tested versions: vscode-textmate9.3.2, vscode-oniguruma2.0.1 and VSCE4.1.1. Keep them in a private development directory rather than adding an execution dependency to native user applications.

```sh
RF2_EDITOR_TEST_DEPS=/absolute/development-dependencies \
RF2_EDITOR_COMPILER=/absolute/qualified-0.44-rf2c \
RF2_EDITOR_REPORT=/absolute/new-report.json \
node tests/editor/grammar.mjs
```

The dependency directory contains package.json/node_modules for those engine packages. The compiler parameter explicitly enables native compilation/execution of the expanded entry snippet; omit it for lexical-only work and do not report a native-snippet pass. Cases check declaration scopes, ownership, profiles, strings, Unicode, escapes, comments, identifier boundaries and `//` division. The entire tracked RF2 corpus is tokenized with a per-line engine budget. Highlighting is not syntax/type validation.

Use the official VSCE packager in editors/vscode to generate a VSIX with --no-dependencies. Then:

```sh
python3 tools/verify-editor-package.py SELECTED.vsix NEW-REPORT.json
```

The verifier checks the fixed eight-entry declarative archive and byte identity for the six packaged source/configuration files. It never installs an editor/extension. Current evidence has no actual installed VS Code host or Marketplace trial. [Receipt](../../docs/EDITOR-LANGUAGE-0.1.json).
