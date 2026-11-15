"""Concrete RF2 discovery briefs; planning records are never counted as runs."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
roles=[
 ('beginner','Build and change a room booking app','macOS ARM64','local HTML forms','Booking and Core Studio work within bounds; learner trial missing'),
 ('application-developer','Share multi-room reservation logic across CLI GUI and agent tool','macOS ARM64','versioned capability request','Owned nested values and transactional multi-room storage missing'),
 ('systems-admin','Search bounded logs and summarize repeated codes','macOS ARM64','stdin and regular files','Text/collection apps implemented; deployment workload not independently qualified'),
 ('service-developer','Run a concurrent reservation service','Linux x86-64','HTTPS and SQL','Linux app backend, TLS/database libraries and language concurrency missing'),
 ('embedded-developer','Log temperature readings with watchdog progress','ESP32-C3','UART and I2C','Bounded emulator backend exists; physical sensor and electrical tests missing'),
 ('mobile-developer','Build a booking app with accessible native controls','Android ARM64','platform UI and local storage','Application adapter, packaging and device acceptance missing'),
 ('desktop-developer','Build a cross-platform document viewer','Windows x86-64','native widgets and files','Windows backend and widget toolkit missing'),
 ('numerical-developer','Compute calibrated sensor statistics','macOS ARM64','numeric arrays','Unsigned integer apps exist; signed/floating/decimal numeric model incomplete'),
 ('accessibility-tester','Complete booking by keyboard on narrow screen','macOS ARM64','browser events','Needs actual rendered scenario assertions; compiler success is insufficient'),
 ('compiler-developer','Update a nested record leaf without invalidating aliases','macOS ARM64','native function calls','Experimental borrowed composition only; full value ownership not qualified'),
 ('release-engineer','Reproduce a package and diagnose stale dependency cache','macOS ARM64','build artifacts and versioned manifests','Qualified bounded reuse exists; no universal cache/security claim'),
 ('OS-developer','Recover from one deliberately injected driver failure','ARM64 emulator','boot interrupts and device MMIO','RF2 app compiler is not an OS; driver/isolation/recovery acceptance needed')]
conditions=[('nominal','Valid inputs produce the specified output'),('invalid-input','Malformed/out-of-range inputs cause a clear refusal before external changes'),('exhausted-resource','Resource limit produces explicit failure without false success'),('stale-state','Changed dependencies or stale state invalidate previous preparation'),('interrupted','Interruption produces the documented completed/failed/uncertain state'),('repeated','Repeating or retrying does not silently duplicate a state-changing effect')]
rows=[]
for role,goal,target,protocol,gap in roles:
 for condition,invariant in conditions:
  rows.append(dict(id=role+'-'+condition,role=role,goal=goal,target=target,protocol=protocol,condition=condition,invariant=invariant,status='planned-not-executed',gap=gap,executionEvidence=None))
p=root/'docs/RF2-USAGE-SCENARIOS.json';p.write_text(json.dumps({'kind':'72 concrete discovery briefs, not users/personas/tests','scenarios':rows,'coveragePolicy':'Execution requires a pinned artifact and application-specific oracle; existing general tests do not automatically satisfy these briefs.'},indent=2)+'\n');print(len(rows),'scenario briefs, zero counted as executed')
