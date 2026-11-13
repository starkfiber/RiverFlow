# Measuring an AI development advantage

This is a proposed experiment, not a result. No model-token saving, developer-time advantage or universal language superiority has been established by the native compiler and search tests.

## Freeze the task before the attempts

Choose an application and a published feature list. Give RF2 and the comparator stack the same functional inputs, output contract, error behaviour, persistence requirements and independent acceptance suite. The suite must not inspect implementation spelling or reward a prebuilt demonstration simply because its language is familiar to the evaluator.

Useful first tasks include a bounded text tool, a read-only local document index and a stateful application with preview and recovery. Each is a different scope. A native text tool does not complete the document-index or application tasks.

## Preserve the actual cost

Record exact repository and tool versions, target OS/hardware, model and provider configuration, prompts, available documentation and pre-existing libraries. Save provider-reported input/output usage, retries, tool calls, human interventions and elapsed time. Encoded source-token counts are a separate observation, not a substitute for provider usage. Local tests do not establish model-inference cost.

Run repeated attempts with independent clean workspaces and matched task instructions. Counterbalance attempt order. Define the stop condition and maximum resources in advance. Preserve failures and incomplete features in the denominator. Do not select only a successful RF2 attempt against an unsuccessful comparator attempt.

## Review behaviour independently

Run the same frozen acceptance tests from a fresh process. Check generated code and dependencies for permission changes, omitted requirements, hidden network calls and unsupported claims. Review interruption/recovery and installation on an actual qualified target. Keep evaluator changes separate from the generated implementation.

Report distributions and individual attempts, not one headline. Distinguish developer time, compile time, application runtime and model usage. A result may favour different stacks on different axes. Adoption and ease of learning need actual developer/learner observations beyond a test agent's judgement.
