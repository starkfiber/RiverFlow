# RiverFlow Studio 0.9

The graphical editor is a reference application for the RF2 systems platform. Its launcher, controller, routing, validation, state, rendering and PDF writer are compiled RF2. Standard browser HTML/CSS provides display and form input, with no client script or model client. It is a local browser workspace, not a native AppKit window or complete accounting system.

## Use

Open RiverFlow Studio.app, or run `rf2 editor --open`. `rf2 editor` alone prints the private URL. Add rows, enter integer quantities and decimal unit prices, choose a three-letter currency and explicit basis-point tax rate, then apply changes. Save a document to retain the draft. Open document accepts only the versioned invoice document. Export PDF uses the same native writer as the CLI. New draft asks for confirmation; Close workspace exits the controller. Unsaved drafts do not survive process exit.

Prices have at most two decimal digits and are converted exactly to integer cents. There are at most 1,000 rows. Line, subtotal, tax and total limits and invoice-level half-up rounding follow invoice.total@1. No descriptions, customer ledger, invoice numbering, payment gateway or tax compliance determination is implemented yet. Generated files are worksheets, not certified tax invoices.

## Effects and safeguards

The controller listens only on 127.0.0.1 at an ephemeral port. Mutations and downloads require an OS-entropy nonce, exact local Origin/Host and current revision. Stale forms refuse. Downloads use POST. No arbitrary server file path is accepted; uploaded document bytes are validated. A failed edit restores both committed data and visible fields. Headers, body, multipart boundary and document sizes are bounded. Duplicate request fields, transfer encoding and unsupported methods reject. Eight polled client slots keep browser idle preconnections from blocking active forms. A ready partial request has a five-second timeout.

CSP disallows scripts, outside assets and embedding. These protections are tested local-controller controls, not an independent security certification or authorization for public hosting. MCP remains the same nine bounded tools; editor and raw system calls are not remotely exposed through MCP.

## Evidence

See EDITOR-0.9-VERIFICATION.json, PLATFORM-0.9-VERIFICATION.json, STUDIO-MEASUREMENTS-0.9.json and the executable tests. The PDF output is compared byte-for-byte with frozen 0.8 for the same document. Browser testing separately checks displayed totals and actual downloads. The Mac bundle is ad-hoc signed, not Developer ID signed or notarized. Use only on the qualified macOS ARM64 target.
