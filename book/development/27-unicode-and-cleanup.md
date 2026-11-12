# 27. Text people can read, resources programs release

Readable programming needs real text and predictable file lifetimes. Tamil, combining marks, emoji and malformed input all matter. Early returns should also release a registered named input file.

Release 0.14 adds validated Unicode scalar views and deferred close actions. The compiler checks their contracts and emits native instructions.

## Bytes and characters need different names

```rf2
array Bytes(u8,255)
textview Text(Bytes)
fn count(data:Bytes,n)
 let text=Text(data,0,n)
 return text.length
end
```

The constructor chooses a byte range and validates that range as strict UTF-8. It rejects truncated sequences, overlong encodings, surrogate values and values beyond U+10FFFF. NUL remains valid text. The surrounding owner may contain unrelated malformed bytes; only the chosen span is the text value.

A text view has two useful lengths. Its byte_length property is the encoded byte count. Its length property is the Unicode scalar count. Indexing returns a scalar value. A displayed family emoji can contain several scalars; a combining mark is also a scalar. This interface does not count graphemes or normalize words. Calling every visible shape a character would hide a distinction the program needs.

The descriptor does not copy source bytes. It stays in the function frame and cannot escape or mutate its owner. Existing view freezes still prohibit ordinary calls and array element updates after construction. This conservative restriction is less convenient than a complete borrowing system, but it has a contract that can be tested. Scalar indexing scans from the start and carries no speed claim.

Invalid UTF-8 construction is a fatal process trap, just as an invalid view range is a bounds trap. A document tool needing recovery first validates bytes and then constructs the view. Recoverability is an application decision with an explicit checked path, not a promise hidden behind a constructor.

## Capture once, release when returning

```rf2
fn inspect_file(path)
 let fd=open(path,0,0)
 if fd>>63
  return 1
 end
 defer close(fd)
 return 0
end
```

The defer statement captures the descriptor when reached. An ordinary function return automatically attempts the close. Captures run in reverse registration order, and early returns before a registration leave it unarmed. A shared native epilogue preserves both registers of a typed result while performing cleanup. Scalar fallthrough also runs registered actions.

The first form supports close only, at function level, with at most sixteen registrations. It does not run arbitrary callbacks or establish linear ownership. A failed close does not replace the function's authored result. Fatal traps, direct process exit and signals bypass these epilogues. A raw descriptor manually closed and reused can still refer to another resource when the deferred action runs. These limits belong beside the feature, not in an invisible footnote.

## A multilingual document tool

The unicode-lines application processes stdin or one named file. It reports accepted and rejected lines, Unicode scalar counts, Tamil-block counts and a fingerprint over accepted scalars. Malformed rows are rejected without preventing later valid rows from being processed. A separate strict prevalidator checks bytes before a text view is constructed. The view then supplies scalar indexing for the actual summary.

Opening and reading have typed outcomes with exhaustive handlers. A named descriptor has a deferred close; borrowed stdin does not. Tests inspect descriptor validity in a still-running process, including early error returns, rather than relying on the operating system to close files after termination. The input and line limits, partial statistics and output failure limitations are explicit in the application contract.

## Keep failures as part of the story

Independent tests found that the first candidate rejected a valid byte-order mark. A wrong native shift instruction and an incorrect error-string constant were corrected. A later boundary review found a maximum-index collision with the decoder's internal validation mode. An explicit scalar bounds check fixed it. Those failed candidates remain in the local evidence record.

Agent-authored programs compare native behavior with independent strict UTF-8 decoding and file-descriptor expectations. These are finite checks, not human peer review or a compiler proof. Existing compiler and MCP regressions also remain required.

Next are typed ownership, observable cleanup errors, structured results, composable immutable calls and growable storage. No new speed or token-saving conclusion follows.

