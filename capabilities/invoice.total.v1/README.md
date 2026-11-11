# invoice.total@1

Calculate an invoice total with explicit integer cents and a stated tax rate. The complete readable plan is:

```rf2
rf2 app v1
invoice total
currency MYR
tax 600 bps
```

Save it as quote.rf2. Supply lines such as `[{"quantity":2,"unit_cents":1250},{"quantity":1,"unit_cents":399}]`:

```sh
./rf2 app quote.rf2 lines.json
```

The result is subtotal 2899 cents, tax 174 cents and total 3073 cents. The fixture is a programming example, not a customer transaction. The 600 basis points are an explicitly selected calculation input, not a statement of an applicable tax rate.

## Contract

RF2_APP_V1 admits this exact ten-word plan in order. ASCII spaces, tabs, CR and LF separate words. Currency is three uppercase ASCII letters: a label, not a validated ISO registry entry. Tax is a canonical decimal integer from 0 to 10000 basis points, without a sign, fraction or leading zeros. Maximum plan size is 256 bytes. Unknown operations, versions, extra words, effects and Unicode whitespace reject. This is deterministic capability selection, not unrestricted natural-language interpretation.

At most 1000 lines, each with exactly quantity and unit_cents. Quantity is an integer from 1 through 4294967295. Price is an integer from 0 through 4294967295. A zero price is valid. Empty input totals zero. Duplicate JSON keys, extra fields, negative numbers, fractional values and excessive inputs reject. Mathematically integral JSON forms follow the existing native number contract.

The generated Core kernel multiplies each quantity by its price and sums the line amounts. Each line and subtotal must fit u32 cents. Invoice-level tax is `floor((subtotal * tax_bps + 5000) / 10000)`. This is half-up rounding applied once to the subtotal, not separately to each line. The intermediate fits u64 under the stated bounds. Subtotal plus tax must also fit u32 cents; overflow rejects rather than wrapping.

`total.flow` is compiled into `native/invoice-kernel.rf2` through checked native lowering. Generated symbols are prefixed to avoid collisions with attendance. Reproduction and source fingerprints are checked in the verification suite and capability manifest. The adapter performs validation, currency handling and explicit tax rounding in RiverFlow systems source.

## Effects and scope

The CLI reads only the explicitly supplied plan and lines files, returns JSON on stdout and writes no application file. MCP `invoice_total` accepts plan and lines, returns the same totals, and accepts no path, network or permission arguments. It does not create a legally compliant invoice, invoice PDF, accounting ledger, customer database, tax determination or payment. Discounts, fractional quantities, exchange rates and credit notes are outside this version. Do not silently infer these policies.

The native runtime and this capability are written in RiverFlow. JavaScript and Python remain development comparators, tests, measurement and publishing tools. The current platform is Apple Silicon macOS, not every machine.

## Verification and measurement

See docs/INVOICE-VERIFICATION.json for independent integer arithmetic, existing 0.6 Core comparisons, JavaScript comparisons, rounding boundaries, malformed plans, overflow, parser mutations, CLI read failures and MCP recovery. The reference comparator is a developer JSON-lines program; it is not a second independently audited production implementation. Its ordinary JSON parser does not share the native transport's duplicate-key refusal.

See docs/CAPABILITY-MEASUREMENTS-0.7.json and docs/CAPABILITY-MEASUREMENTS.md for every timing trial and exact tokenizer fixtures. Results are mixed: compact source does not automatically mean fewer tool-context tokens or faster execution. No billed inference, model reasoning, energy or end-to-end AI task saving was measured.
