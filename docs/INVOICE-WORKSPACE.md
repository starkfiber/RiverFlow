# Native invoice workspace

Release 0.8 adds a file-based workspace. The compiler, document handling, line edits, arithmetic and PDF writer are RiverFlow source. No Node, Python, C++ or external PDF renderer runs in the user workflow. This is a command-line workspace with editable JSON documents, not a graphical editor or tax-compliant accounting suite.

```sh
./rf2 invoice save capabilities/invoice.total.v1/quote.rf2 \
  capabilities/invoice.total.v1/test-lines.json first.invoice.json
./rf2 invoice inspect first.invoice.json
./rf2 invoice set first.invoice.json 0 2 250 edited.invoice.json
./rf2 invoice set edited.invoice.json 2 1 99 appended.invoice.json
./rf2 invoice remove appended.invoice.json 1 revised.invoice.json
./rf2 invoice pdf revised.invoice.json worksheet.pdf
```

Line indices start at zero. Set replaces an existing line; an index equal to the line count appends. Remove deletes a line. An index beyond the admitted range rejects. Every edit writes an explicitly named new document; the input remains unchanged. Existing files and symlinks are refused. Files are owner-only 0600. A failed write may leave an incomplete new file; transactional/crash-safe storage is not claimed.

The document has exactly format, plan and lines. Its format is rf2.invoice.document.v1. It preserves the explicit currency and tax calculation contract. Totals are recomputed on inspection and PDF export. Unknown stored total fields reject instead of being treated as evidence. Canonical documents fit the existing 131072-byte file-read boundary. Limits and arithmetic are the same as invoice.total@1.

PDF export is written directly by RiverFlow: PDF 1.4 objects, standard Helvetica font, page tree, content streams and cross-reference offsets. It uses A4-sized pages, 40 lines per page, and totals on the last page. Inputs remain restricted to safe numeric fields and uppercase currency labels, so no arbitrary document markup is admitted. The worksheet displays amounts in cents and a reminder to verify business/tax rules. It is not a legally complete invoice: customer identity, registration numbers, tax-law decisions, signatures, payment and accounting integration are outside this version.

MCP tools still accept no workspace paths and never save or export files. The explicit local CLI owns file authority; prepared plans grant no new effects. Exporting a PDF is separate from approving a transaction.

WORKSPACE-0.8-VERIFICATION.json records six saved-document cases, six PDF cases including zero/40/41/1000-line boundaries, three edits and 15 refusals/protection checks. A separate PDF library parses the actual generated files, checks page counts, totals and text bounds; the delivered example was rendered and visually inspected. Tests use programming fixtures, not real invoices or evidence of customer adoption. A graphical editor remains a future interface, not a feature claimed here.
