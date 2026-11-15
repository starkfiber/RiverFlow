# RiverFlow RF2 language support

An MIT-licensed declarative editor package for `.flow` and `.rf2`. It contributes RiverFlow syntax highlighting, comment/bracket/indent behavior and four explicit snippets. There is no JavaScript extension entry, telemetry, network connection, automatic compiler download, source execution, debugger or language server.

Highlighting covers the current Core/compact and Systems spellings, profiles, functions, nominal type declarations, ownership, results, strings, comments, decimal integers and operators. `//` is integer division, **not a line comment**. A word inside a comment/string does not become a keyword. Highlighting is lexical; it does not prove a program valid. Compiler/target qualification remains authoritative. The owned-result snippet requires the0.43+ candidate, not stable0.17.

For VS Code development, open this directory as an extension-development project or package it as a VSIX using the official tooling. Select **RiverFlow RF2** as the file's language mode if an existing association takes precedence. No global editor settings or extensions are changed by creating this source package.

[VS Code syntax grammar documentation](https://code.visualstudio.com/api/language-extensions/syntax-highlight-guide) describes the TextMate engine used by the tests. [Language contribution points](https://code.visualstudio.com/api/references/contribution-points#contributes.languages) define the manifest.

This is editor support, not GitHub Linguist registration. Actual GitHub recognition still requires independent adoption and upstream acceptance. The source grammar is reusable by compatible TextMate editors under MIT. Do not relabel real Python/JavaScript source or manufacture repository usage to change a language chart.

Executed qualification: TextMate9.3.2/Oniguruma2.0.1 passed26 checks, including193 tracked RF2 files/45,879 lines and a snippet compiled/executed by the native0.44 compiler. VSCE4.1.1 packaged the declarative VSIX; all six shipped source files match the archive. No VS Code host is installed on this Mac, so an actual editor-window installation/interaction trial remains pending. No Marketplace publication is claimed. [Source-bound receipt](https://github.com/starkfiber/RiverFlow/blob/main/docs/EDITOR-LANGUAGE-0.1.json).
