# Typed request adapters and ownership correction, candidate 0.49

This source candidate fixes a reproduced 0.48 compiler defect and moves repeated form decoding into reusable RF2 modules. Public downloads remain unchanged. It does not claim lower model token use, universal ownership safety or platform parity.

## Build the corrected compiler

Use a qualified native 0.48B bootstrap and the existing developer preparation route:

```sh
python3 experiments/typed-requests/prepare.py /new/path/candidate
sh tools/build-program.sh /path/to/0.48B/compiler /new/path/candidate/compiler.flow /new/path/candidate/build --opt
python3 experiments/typed-requests/stage.py /new/path/request-sdk
sh tools/build-program.sh /new/path/candidate/build/program /new/path/request-sdk/web.flow /new/path/web-build --opt
/new/path/web-build/program /path/to/selected-booking-workspace
```

The final line explicitly launches the real loopback Booking frontend. The overlay changes its request decoder; shared persistence, GUI rendering, CSRF admission and storage transactions remain the same source. No workspace is automatically created until the user chooses its existing create action. Python is preparation/test tooling, not an emitted application dependency.

## Reuse the decoder

After the existing authenticated `app_form` admission returns a nonzero parsed mask, call:

```text
handle booking_request(values,mask,request)
ok parsed
 # request is now complete; call the selected storage operation
err invalid
 # retain values for redisplay; do not call storage
end
```

`values:FormValues` and `request:StoreRequest` are nominal borrowed parameters. The adapter accepts the exact existing reserve/cancel/initialize/migrate/recover masks. Appearance remains a separate GUI preference. It parses into a private local record and copies all seven output scalars only after every check succeeds. Invalid numeric/date/time/action/mask input returns22 and leaves the caller's entire request unchanged. Zero revision remains representable for the storage layer's revision/state rules. Reserved IDs and room IDs must be positive; rooms remain 1..16 and intervals strictly increase within one day. Business overlap, stale revisions, corruption and uncertain saves remain storage decisions.

`request-fields.flow` provides reusable `request_u64`, `request_positive`, `request_day`, `request_time` and `request_is` accessors. Keys are bounded to the 16 slots represented by the borrowed array; numeric overflow maps to input error22. These are post-admission adapters for trusted native process state, not a general schema language or a new authentication boundary. They do not accept caller-controlled memory over MCP. Only the parser knows the underlying pointer/length slots; app authors can use the typed request.

## Ownership regression and refusal

The old candidate admitted `set row.id=try consume(move(row))`: it checked the owned destination before the call, then wrote through its saved address after the call consumed that destination. The correction rechecks compiler ownership readiness after evaluating the RHS, before emitting the store. Consuming a containing ancestor also clears the descendant readiness and refuses. The check is conservative even when that called function would return an error. It adds no pending-stack runtime branch and preserves ordinary scalar propagation/cleanup.

The existing raw-pointer/trusted-Systems, cancellation and fatal-trap limits remain. This correction is not a complete borrow-checker proof. Stable0.17 and public0.46 did not contain the new scalar field-try syntax; do not silently label their packages defective or changed.

## Executed checks

```sh
RF2_REQUEST_COMPILER=/path/to/candidate/compiler RF2_REQUEST_BASELINE=/path/to/0.48B/compiler python3 tests/standalone/typed_requests_verify.py
RF2_STORE_COMPILER=/path/to/candidate/compiler RF2_REQUEST_SDK=/new/path/request-sdk python3 tests/standalone/booking_web_verify.py
```

The first controller tests the old admission and new refusal, nested ancestor moves,152 independent request cases per compiler mode and unchanged canary fields on failure. The second runs the same 178 browser protocol assertions against the explicit overlay, with its source hashes/environment bound by the outer receipt. Without `RF2_REQUEST_SDK` it retains the original frontend. A staging import-cycle error found by the read-only reviewer was corrected using a uniquely named base-module import; both CLI and imported staging now work.

The frontend's decoder shrinks from 82 application-local lines to a three-line delegation. The shared domain/generic libraries add 56 and 43 lines. That is source organization and reuse, not a net repository code reduction or a measured AI token saving.

Read [the application epoch evidence](../../docs/APPLICATION-EPOCHS-0.49.md) for the independent apps, original failures, reviewed source comparisons and remaining product proof.
