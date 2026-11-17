# DeepSeek / WhatIF review disposition

Six real provider calls ran; final skeptical review was DeepSeek V4-Pro,
thinking enabled/low. Model output is a hypothesis source, never authority.

- **Escape distributions:** useful lead. Four additional64KiBpatterns (late,
  early, clustered and alternating escapes), both modes,11paired trials and208
  exact capacity controls now pass. These measured1.15–1.35× complete serialization
  improvements, not a guarantee about every distribution. Tiny losses remain.
- **Alias off-by-one:** unproved hypothesis. Existing73728states per mode already
  compare complete writer state with the preserved scalar implementation. Retain
  it as finite coverage rather than inventing a new detected flaw.
- **DHCP malformed padding:** existing55611length/corruption controls already
  exercise this, including a deliberately incorrect native mutant. Model did not
  discover a demonstrated acceptance bug in the final scan.
- **Poly1305 overflow/timing:** exact integer and CryptoKit checks constrain output
  mistakes; no side-channel certification follows. Reject the suggested oracle
  “p-value>0.05means no timing leak”: failure to detect a signal does not prove its
  absence. Replacing source is not safe merely because a model endorsed it.
- **Report state/error:** independent Codex agent reproduced the actual first
  helper-state flaw, and root fixed pending-state admission. Main API
  begin/text/number/end,1024field boundary, UTF8/capacity/no-success-output controls
  pass. Internal composition helpers and direct record mutation are not a
  hostile-caller boundary in the trusted Systems profile.
- **Cross-platform testing:** cannot simply run native Mac `.flow` code on
  Linux/Windows. A real target backend/ABI and runtime/HAL must exist first.
- **AI savings:** model correctly declines a benefit claim. Four original
  attempts failed compilation; one separate repair passed37functional controls.
  Model-generated reports do not independently verify their supplied hashes.
- **WhatIF source leads:** seven `exec` matches load function definitions from a
  reviewed, hash-recorded local oracle snapshot in developer controllers. They
  are not shell execution or confirmed input-driven injection. Native behavior
  is covered by separate controllers; heuristic scan is not full SAST.

OpenClaw/DeepClaw services were not used for this project. Three Codex subagents
performed the native work; two follow-up turns failed at provider policy review
before producing additional results. No extra independent security review is
claimed from those failed turns. Root reviewed the retained source and receipts.
