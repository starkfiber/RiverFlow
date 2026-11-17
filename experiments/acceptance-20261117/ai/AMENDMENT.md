# Explicit budget amendment, before any further model calls

The original5000completion-token plan made one A/manual call. It consumed all5000
in reasoning, returned length with no final source, and failed. Preserve that
original FROZEN/receipt; do not classify it as a low-cost success or include it
silently in another condition's comparison. No other call ran under that plan.

The new study-wide.py/controller and study-2 directory restart the same declared
four-attempt A/manual,A/report,B/report,B/manual comparison. Both conditions now
receive max10000completion tokens,180second HTTP/195second transport observation,
and at most one actual-feedback repair per attempt (eight calls total). Other
model/thinking/task/guide/oracle settings remain unchanged. This amendment
supersedes only the old protocol's output/observation budget. Stop rather than
repeating an incomplete response automatically. Keep original+amended total
spend visible when discussing engineering effort; compare conditions only inside
the amended study. Provider reported counts, not billed dollars or universal
population estimates. Source-specific trust and manual review remain unchanged.
