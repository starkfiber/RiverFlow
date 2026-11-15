# RiverFlow Linguist intake preparation

This is preparation, not an upstream submission or accepted language. Reviewed15November2026 against the actual [registry](https://github.com/github-linguist/linguist/blob/main/lib/linguist/languages.yml) and [contribution rules](https://github.com/github-linguist/linguist/blob/main/CONTRIBUTING.md#adding-a-language). RiverFlow and its two extensions were not registered. Recheck before proposing a change.

The [MIT TextMate grammar](../vscode/syntaxes/riverflow.tmLanguage.json) has native-engine tests. A [declarative VS Code package](../vscode/README.md) was packaged with the official tool. No Marketplace release or installed-editor trial is claimed.

Candidate registry data, to be validated in an actual future Linguist checkout:

```yaml
RiverFlow:
  type: programming
  aliases:
  - rf2
  color: '#42C8D8'
  extensions:
  - '.flow'
  - '.rf2'
  tm_scope: source.riverflow
  ace_mode: text
```

Do not invent a language_id; Linguist's own update-ids script must allocate it. This fragment has not passed upstream Ruby/grammar/classifier tests. The existing compiler namespaces and platforms are not a claim of official ecosystem recognition.

Representative **actual application** sources, under the repository MIT licence, for later sample review:

- [Typed room rules](../../experiments/typed-booking/lib/booking.flow), source at [release commit](https://github.com/starkfiber/RiverFlow/blob/e0d347f2d76aa452c34967b2a6beb0a06c099689/experiments/typed-booking/lib/booking.flow).
- [Versioned durable storage](../../experiments/typed-booking/lib/store.flow), source at [release commit](https://github.com/starkfiber/RiverFlow/blob/e0d347f2d76aa452c34967b2a6beb0a06c099689/experiments/typed-booking/lib/store.flow).

These are maintained project sources, not tutorial Hello World files generated to inflate popularity. Do not copy thousands of samples, create artificial independent projects or count forks as adoption. Grammar metadata must be wired and tested by the current upstream intake process when that process is actually used.

The external gate remains genuine widespread usage, representative independent projects and upstream review/acceptance. The current repeatable-extension threshold is2,000 indexed non-fork files in the preceding year, with distribution across projects/users. No qualifying count or independent adoption survey is claimed here. A local .gitattributes override cannot register an unknown language or replace adoption. Keep R12 pending until actual acceptance is verified; do not publish a premature proposal as if it met the requirements.
