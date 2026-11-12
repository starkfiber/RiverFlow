# Native RF2 latency summary

A complete supplied-sample analyzer using checked arrays and typed module parameters. It requires the post-0.11 development compiler; see [build instructions](../../docs/CHECKED-ARRAYS.md).

Pass 1 to 128 decimal integers, each at most 4,294,967,295 and no more than ten digits. Leading zeros within that width are accepted. Empty, negative, fractional, nonnumeric and over-capacity input rejects with status 1. Standard output contains JSON only on success. No input files are written.

The caller chooses and consistently supplies the measurement unit. This program does not measure latency itself. It also works on other nonnegative integer samples. Results:

- `median_lower` selects sorted position floor((n-1)/2), using zero-based positions. It does not average the middle pair.
- `p95_nearest_rank` selects sorted position ceil(0.95*n)-1.
- `sum` fits u64 for the admitted maximum sample and count.

The sample module uses stable insertion sort over the populated prefix. It checks logical counts before sorting, and checks count/percentile before percentile access. Fixed capacity is 128; unused cells are zero-initialized but are excluded from statistics. This is a bounded standard-library starting point, not a claim of optimal sorting or a general statistics package.
