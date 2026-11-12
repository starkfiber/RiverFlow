# RF2 WebAssembly Worker candidate

Arithmetic executes the RF2-emitted `sum.wasm`. The small JavaScript wrapper supplies the Workers HTTP interface. GET `/sum?values=19,23` returns42. At most1024canonical u32values are accepted; arithmetic overflow returns422.

This candidate was tested locally with the same module and platform-handler code. It has not been deployed to Cloudflare. No model, KV, Redis, external fetch, account token or paid service is configured. The current task authorizes free services only: verify the target account is on Workers Free before deploying. Do not upgrade a plan or add an inference binding automatically.

Wrangler is optional developer deployment tooling, not an RF2 user runtime. Its supported WebAssembly module import is used by worker.mjs. The browser and native tools remain separately usable without Cloudflare.

Cloudflare currently documents100000requests/day and10msCPU/request on Workers Free; those quotas do not prove this application meets a workload target. Workers AI's10000freeNeurons/day is a separate allowance with model restrictions. Neither allowance is compiler/model training, and no inference/training occurred in this experiment. See docs/FREE-CLOUD-0.19.md for dated primary sources and remaining authentication gates.
