# Graphical Number Lab

A small private browser learning game whose server, rendering, validation and arithmetic are native RiverFlow. The browser displays ordinary HTML/CSS forms. There is no browser script, model client, external font, image CDN, Python or Node user runtime.

Build with a qualified compiler and use a fresh output path:

```sh
/path/to/rf2c examples/number-lab-web/main.rf2 output/number-lab-web --opt --compact
/usr/bin/codesign -s - output/number-lab-web
./output/number-lab-web
```

The program prints an ephemeral `http://127.0.0.1:PORT/` address. Open that address in a browser on this Mac. It does not open a browser automatically. “Close playground” stops the server and discards its in-memory state.

## Play

Start with decimal 65. Tap any of the eight bit switches to toggle its weight. Decimal, hexadecimal and ASCII update together from the calculated byte. Printable ASCII is safely escaped as HTML; control bytes and values outside ASCII are labelled rather than sent to the terminal or interpreted as markup.

The gate form computes AND, OR, XOR or an eight-bit NOT. NOT ignores the second byte, as stated next to the form. The quiz lets the learner choose two single-bit inputs and predict their AND result. Wrong answers keep the question active; a correct answer increments the score. These are actual arithmetic and bitwise results, not prewritten feedback samples.

The visual direction follows the UI/UX Pro Max accessibility and interaction guidance: clear native labels, visible keyboard focus, large controls, sufficient contrast, eight-pixel switch spacing, a four-column bit layout on narrower screens, and a single-column layout on phones. Blue fill is accompanied by a visible 0/1 value and `aria-pressed`. No animation is necessary for the task. System fonts keep the page self-contained. A generic sales-page recommendation from the design search was rejected as irrelevant to this learning application; targeted touch guidance was used instead.

This is a browser interface, not an AppKit or Tkinter window. “Kid-friendly” describes the instructions and interaction, not a measured educational outcome or a claim that children were studied.

## Local controller contract

The listener binds only to `127.0.0.1` on an OS-selected port. GET `/` is read-only. POST `/play` and `/quit` require the exact listener Host, exact local Origin, an OS-entropy 128-bit token, and the current revision. Incorrect tokens and stale forms refuse without changing game state. Tokens protect this local browser workflow; they do not authenticate against a malicious local process that can read the page.

HTTP/1.1 headers are bounded to 4,096 bytes, request lines to 255 bytes, individual headers to 1,023 bytes, targets to 30 bytes, and URL-encoded bodies to 256 bytes. Duplicate security/framing headers, transfer encoding, Expect, ambiguous length, binary controls, unsupported methods, unknown routes, duplicate/unknown form fields and extra request bytes refuse. Response bodies are bounded to 32 KiB and no user-controlled text is interpolated as markup. No caller-supplied file path, command, source program or outbound URL is accepted.

Eight polled client slots keep idle browser preconnections from blocking an active request. A ready request gets one monotonic two-second deadline across header and body reads. Response writes also have a two-second deadline. A partial ready request can therefore temporarily occupy the sequential controller, but cannot indefinitely extend its read budget by sending one byte at a time. This is a bounded local demo, not a parallel public web service. A full slot table may evict a waiting connection. Each process handles at most 4,096 requests; a new launch starts a fresh session.

The server closes accepted connections after one response. An accepted quit closes waiting clients and the listener. Startup failures close the descriptors acquired so far. The controller accesses `/dev/urandom` only to initialize its ephemeral token; it writes no participant records and persists no game data.

CSP disallows scripts, external assets, embedded frames and foreign form actions. Other defensive response headers prohibit caching and MIME sniffing. `Referrer-Policy: same-origin` preserves the exact Origin on legitimate browser form posts while withholding referrers from foreign destinations. An initial `no-referrer` policy caused real Chrome form clicks to fail the exact-Origin check, so they were refused despite the HTTP-controller tests passing. A numeric-reason diagnostic reproduced that refusal; the response policy was corrected without allowing `Origin: null` or weakening exact-Origin checks. Real browser acceptance is a separate required gate. These controls are tested application behavior, not an independent security certification or permission to host it publicly.

## Verification

```sh
RF2_TEST_COMPILER=/path/to/rf2c python3 tests/standalone/number_lab_web_verify.py
```

The independent developer controller executes native HTTP requests, checks calculated byte/gate/quiz outcomes, escaping, read-only GET behavior, nonce/origin/host/revision refusals, duplicate and malformed requests, partial-request deadlines, idle-connection recovery and verified quit cleanup. It retains source/compiler/controller/executable hashes and actual outcomes. HTTP acceptance is separate from browser rendering, keyboard and responsive visual verification.

Current native target is macOS ARM64. This example does not establish Linux, Windows, QEMU, mobile, GPU, SoC, energy, billed-token or general language-equivalence claims. No application runtime speed comparison is made here.
