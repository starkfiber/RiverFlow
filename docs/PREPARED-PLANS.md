# Prepared invoice plans

invoice_prepare checks the exact RF2_APP_V1 plan and returns plan_id, capability, currency and taxBps. Review these visible rules before reuse. invoice_apply accepts plan_id and fresh lines and returns the same checked totals as invoice_total. invoice_release removes a plan; a released number is never reissued in the same process.

Plans are immutable, process-local and in memory only. There are 32 slots. Capacity exhaustion rejects; it never evicts another live plan. Release a plan explicitly when finished. Process exit destroys all plans. Reconnecting clients must discard old handles and prepare again. Handles are locators, not identity, authorization, signatures or durable IDs. Separate principals should use separate server processes; the service provides no multi-user isolation.

A process-specific u32 mask comes from an internal read of OS /dev/urandom. A bounded monotonic counter XORs with that mask, skips zero and refuses exhaustion. This bijection prevents reissue within the process; it does not prove globally unique handles across processes. Each process has a separate cache and clients must not carry handles between them. If OS entropy is unavailable, preparation fails rather than using a predictable fallback. No caller can choose an entropy path. OS entropy access does not grant arbitrary file access.

No currency/tax overrides, file paths, permissions or network arguments are accepted by apply. Failed validation and unprepared calculations do not change saved rules. Numeric transport handling retains the existing exact integer contract. The lifecycle adds no file-writing, payment or remote execution authority.

PREPARED-0.8-VERIFICATION.json records full capacity, distinct handles, rule isolation, repeated application, refusals, release/reuse and empty-state rejection in a fresh process. These checks are software verification, not independent security certification. Token measurements include the added schemas, preparation, application and release rather than counting only a short handle.
