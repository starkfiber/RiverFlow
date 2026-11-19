# A reusable RF2 browser view binding

`FlowSession` connects a web interface to the existing bounded RF2 Simple V3 worker.
It contains no rover movement, wall or win logic. Those stay in `rover/rover.flow`.

```js
import {FlowSession, numberField} from './flow-session.js';
const session = new FlowSession();
const ready = await session.start(source);  // parses/checks/runs to an ask or end
const moved = await session.answer('1');    // supplies input, continues RF2
const x = numberField(moved.snapshot, 'x', 3);
// Draw x with your interface. Reject values outside that view's contract.
session.stop();
```

Validate `ok`, errors, snapshot kind and every view-bound value before rendering.
The adapter uses actual Worker requests, independent IDs and generation fences,
terminates stale sessions and has a page-side deadline. It does not silently replace
failed RF2 execution with JavaScript business logic. Source and worker work/output
bounds remain enforced by the existing reference engine. Do not conflate these
controls with hostile browser isolation or authentication.

Rover is a graphical **web** app: RF2 controls state, HTML/CSS/SVG controls the view,
and JavaScript binds user actions to RF2 answers. It is not a native RF2 widget API,
GUI generator, all-platform binary or a measured development-time/token advantage.
The native CLI benchmark is a separate full-native implementation of the same
4×4 movement rules; its repeated-work/checksum contract and timing scope differ
from this six-turn teaching game and are documented separately.

In the rover view, x/y must be0..3, turn<=turns<=1000, blocked/won0..1. Modified
source outside the view contract preserves the last rendered board and disables
movement until restart. Edits stage until Apply; Reset applies the editor's current
rules. Replay reruns real worker input commands under the last applied source.
