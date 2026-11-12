# Free cloud integration, checked 13 November 2026

The implemented arithmetic backend is RF2-generated WebAssembly. A stateless Cloudflare Worker adapter is in examples/cloudflare-worker. It was tested locally using the real module and actual Request/Response handler code. It has not been deployed to Cloudflare. No account/API token is configured, no model was invoked, no model weights were trained and no Redis/KV service is claimed.

The existing public GitHub Actions qualification is the cloud execution used in this sprint. It builds the compiler and WebAssembly tool and runs finite comparisons. Hosted Mac runners are themselves VMs, so direct hardware guest tests are not promoted from that environment. Public standard-runner allowances are not an unlimited GPU or inference service.

GitHub Models is no longer an available inference route. GitHub's current official page says the playground, catalog and inference API were retired on 30 July 2026. Source: https://docs.github.com/en/github-models . This is separate from GitHub Actions and Copilot.

Cloudflare currently documents Workers Free at 100,000 requests/day, 10 ms CPU/request and 128 MB memory. Workers AI separately includes 10,000 Neurons/day; several model choices require a paid plan. These are provider quotas, not measurements of this application. The user authorized free services only. Deployment must therefore verify the account's Free plan first and must not upgrade a plan, attach a paid model or create new billing arrangements automatically.

Sources inspected: https://developers.cloudflare.com/workers/platform/limits/ ; https://developers.cloudflare.com/workers-ai/platform/pricing/ ; https://developers.cloudflare.com/changelog/post/2026-07-28-models-require-workers-paid/ . Provider terms and quotas can change.

The Worker uses GET-only canonical numeric input, a 1,024-value cap and a per-request WebAssembly instance. It has no storage, AI binding or outbound fetch. Local tests cover success, overflow, malformed/duplicate arguments, count limits and refused methods. This is a deployable candidate, not a Cloudflare production or latency result. Optional Wrangler deployment tooling does not become a native RF2 runtime dependency.

A useful next AI experiment is an independently scored, public-source-only RF2 task set with compiler/test acceptance and actual provider usage receipts. A deterministic regression corpus is not a trained model. Free inference access, when configured, must be recorded separately from compiler improvements and must preserve failed/generated-but-rejected programs.
