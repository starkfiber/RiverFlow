# Thermostat Lab and counter: shared RF2 GUI widgets

Open `/rf2/playground/thermostat/` through the local preview. The heater is a manual
simulation, not an electrical controller, live sensor reader or safety system.
The RF2 program decides heating and accepts/rejects readings. HTML/CSS/SVG draws
the interface. Browser execution uses the existing Simple V3 reference worker,
not native machine code.

Try 17, 20 and 25. The default RF2 lower/upper boundaries are18/24 Celsius:
heating starts below18, stops above24, and retains its state between/equal to the
boundaries. Eight submissions form a run.61 is outside this lesson's range and
leaves heating unchanged. A malformed numeric answer stops the current VM; use
Restart. Change `let upper = 24` to26 in the rules, Apply, and test25/27.

The counter below is an independent RF2 session using the **same** widgets and
lifecycle controller. It adds five whole-number inputs; no JavaScript counter
calculation is used as a fallback. Its graphical projection is limited to numbers
within JavaScript's exact safe integer range, while RF2 itself uses checked u64.

## Shared API

`../ui/components.js` exports Status, Metric, InputForm, Actions, SourcePanel,
ReceiptPanel and RuleView. `RuleView` owns the existing FlowSession, busy/draft
state, input history, resets, visible errors and an unsigned source/input-bound
receipt. The app supplies a source program, a projection that validates every
field used by the view, and an onCommit renderer. Source edits stage until Apply.

```js
import {Metric, RuleView} from '../ui/components.js';
import {numberField} from '../ui/flow-session.js';
const metric = new Metric(display, {label: 'Points'});
const view = new RuleView({
  root: controls,
  source,
  inputLabel: 'Points to add',
  project: snapshot => ({count: numberField(snapshot, 'count', 1000)}),
  onCommit: state => metric.set(state.count)
});
await view.start();
```

This is a reusable web-binding API, not an automatic GUI builder, native widget
API or measured authoring/token advantage. The shared framework has its own source
cost; do not report only the consumer configuration as the complete app size.

## Contract and checks

Thermostat view accepts numeric temperature0..1,000,000 for displaying rejected
submissions, heating/accepted0..1, attempts/readings0..1000, ordered thresholds
within0..60 and reading<=attempts. RF2's default acceptance rule is0..60.
Source outside the graphical contract fails before a new view commit. Default
runs, invalid numeric input, boundaries and checked overflow are compared with
actual native quick execution. Worker-abort and delayed-input/reset interventions
are browser-local tests, not network/server recovery or hardware certification.

Evidence is under `artifacts/rf2-gui-components-20261119/`: native/reference parity,
actual browser outcomes, one preserved draft-notice race and corrected replay.
These are AI-assisted automated checks, not human learners or field outcomes.

Source commit behavior: **Apply rules & restart** commits a valid edited program. Ordinary restart uses the last successfully started source. An unapplied edit changes its label to **Discard edits & restart** and is visibly discarded. If applying invalid source fails, restart can recover the prior working rules. The original failing behavior and independent corrected replay are retained in `artifacts/rf2-independent-challenge-20261119-v2/`.
