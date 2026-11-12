# Reusable modules and nominal records, 0.10

The native RF2 systems compiler now accepts local source modules and records. This is a systems-language feature, compiled to ARM64. Bounded Core/MCP input does not gain imports, raw memory or OS effects.

```rf2
profile RF2_SYSTEM_A64_V1
use "lib/workload.rf2"
fn main(argc, argv)
 let job = Job(7, 4, 12)
 let summary = Summary(0, 0, 0, 0)
 do workload_accept(job, summary)
 return summary.late
end
```

## Modules

A library begins with `module name`, followed by optional `use "lib/file.rf2"` lines, then declarations. The entry retains its systems profile. Imports resolve from the entry directory, including imports in libraries. They precede declarations, traverse in dependency order, and deduplicate restricted relative paths. A library is source composition into one native executable, not a dynamic library, namespace/package registry, remote fetch or incremental compilation cache. Functions share one namespace; collisions refuse. Declare record types before their uses.

At most 32 files including the entry, 16 active traversal levels including the entry, and 524,288 total source/expanded bytes. Module paths use identifier-like segments separated by `/` and a final `.rf2` extension. Absolute paths, `.`/`..`, repeated slashes, missing files, final-component symlinks and cycles refuse. Ancestor directories can still be OS symlinks; this is a trusted local compiler, not filesystem containment. No imported source is automatically executed by compilation. Ordinary legacy files without imports retain their original source bytes. The image digest of an imported program fingerprints expanded source, not the original path graph; retain separate file hashes for provenance.

## Records

Declare `record Job(id: u64, duration: u64, deadline: u64)`. Up to 32 record types, each with 1 to 16 uniquely named u64 fields. Construct with all positional values: `let job = Job(7, 4, 12)`. Read `job.duration` and update with `set job.duration = 5`. Function parameters can be annotated `job: Job`; a different record with identical field names is still a different nominal type.

Owned records occupy the current function's stack frame, with each field stored separately. A constructor must be at function level; it cannot be declared inside an if/while. Records are borrowed by reference when passed to typed parameters, so field changes are visible to the caller. Scalar arguments cannot impersonate records. Record returns, assignment/copy/rebinding, arithmetic, raw-intrinsic arguments and use before initialisation refuse. Main receives scalar argc/argv only. Record storage counts toward the existing 256-local limit.

This is a deliberately narrow type boundary. Fields are machine words; legacy systems scalars can also represent addresses. There are no nested records, strings, arrays, enums, generics, ownership inference or whole-program memory-safety proof. Raw systems memory remains trusted. The borrow restriction prevents record pointers escaping through ordinary typed calls/returns; it does not make arbitrary low-level code memory-safe.

## Optional code generation optimisation

`rf2c source.rf2 new-output --opt` uses a numeric-right-operand register path rather than four temporary stack operations when precedence permits it. Function-call and nonconstant operands retain normal evaluation order. Default compilation preserves the prior machine-code path. This is a local lowering optimisation, not a general algebraic, vectorising or loop optimiser. Executed comparisons retain unsigned arithmetic, overflow, branch, call and division behavior.

Use `tools/build-program.sh rf2c source new-directory --opt` for compilation and normal OS signing. It does not run the result. Legacy programs still compile, and the compiler reproduces its default native image through successive generations. See MODULES-TYPES-0.10-VERIFICATION.json and MODULE-BOUNDS-0.10.json.
