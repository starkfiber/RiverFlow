# Owned function values, candidate 0.43

This isolated native compiler extends the fixed 0.42 candidate. It is development source, not a replacement for published downloads. Python prepares source and runs development checks; compiled user programs have no Python/Node dependency.

```sh
python3 experiments/owned-functions/prepare.py NEW-CANDIDATE
sh tools/build-program.sh PATH-TO-QUALIFIED-rf2c NEW-CANDIDATE/compiler.flow NEW-CANDIDATE/compiler --opt
RF2_FUNCTION_OWNER_COMPILER=NEW-CANDIDATE/compiler/program python3 tests/standalone/owned_functions_verify.py
```

Use a new output directory. `prepare.py` refuses patch drift and a changed base. The build script applies the required local Mac signing. Select the candidate explicitly when compiling applications. The entry below expects the same `lib/numbers.rf2` and `lib/output.rf2` modules as the earlier owned-batch example: snapshot the reviewed files from `examples/collection-tools/lib/` into a private build tree.

```flow
result Made(own Packet,u64)
fn produce(n):Made
 own p=Packet(Title(),Numbers(),n)
 return ok(move(p))
end
fn forward(own p:Packet):Made
 return ok(move(p))
end
fn work():IO
 handle produce(7)
 ok own p:Packet
  handle forward(move(p))
  ok own q:Packet
   return ok(q.id)
  err cause
   return err(cause)
  end
 err failure
  return err(failure)
 end
 return err(22)
end
```

`Packet`, `Title`, `Numbers` and `IO` must be declared as in the tested example. `examples/batch-pipeline.flow` loads actual supplied UTF-8/numeric input into a returned owner, then consumes it in a separate renderer. It shares the earlier parser/output implementation and emits the same independently checked JSON.

The caller supplies result storage in x8. A successful return rebases descriptors into that storage and consumes the callee owner before its frame disappears. A consuming parameter receives a full storage pointer, moves ownership into private callee storage at entry, and disarms its caller. Evaluate all scalar arguments before the call. Consuming and borrowed typed parameters cannot appear together in one signature. Each consuming argument requires `move`; a bare reference refuses. No owner is delivered as a plain scalar or an unannotated result.

An owned handler cleans its binding on normal arm exit. A return through the arm uses function cleanup. A result moved successfully by the producer can still fail during another local's cleanup: the caller disposes that undeliverable result before handling its error. Arm cleanup failure attempts peer cleanup, preserves the first error and retries retained arm ownership during function cleanup. Existing primary-error precedence applies.

Bounds remain 16 cleanup registrations and 256 frame slots per function, eight parameters, flat aggregates with text/u64-collection fields, ordinary-return cleanup and Apple Silicon macOS only. Owners in loops require runtime liveness guards. Moving a branch conservatively consumes it statically. A handler must be inside a compatible result-returning function. No mixed consuming/borrowed signature, general nested owner, structured collection, async ownership or whole-language memory-safety proof is claimed. Failed callee-local OS unmaps can retain mappings until process exit. Traps, signals, raw systems interference and process termination are outside guaranteed cleanup.

See [executed findings](../../docs/OWNED-FUNCTIONS-0.43.md). The nine existing bounded MCP tools retain their previous authority and never admit arbitrary Systems source.
