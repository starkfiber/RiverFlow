# Your first native .flow application

This walkthrough builds a small data analyser on an Apple Silicon Mac. It reads numbers you supply and reports count, minimum, maximum, sum and lower median. It uses two shared RF2 libraries. It neither collects sensor observations nor changes input files.

You need a source checkout and the explicitly selected **0.36 development bundle**. Its Mac compiler supports the collection syntax used here. The stable 0.17 runtime remains included for MCP; that runtime version does not describe the separate compiler's capabilities.

## 1. Get the tools

Download [RF2 0.36 for Apple Silicon macOS](https://raw.githubusercontent.com/starkfiber/RiverFlow/main/dist/0.36-candidate/RF2-0.36-dev-macos-arm64.zip), and compare its SHA-256 with the [published checksum](../dist/0.36-candidate/RF2-0.36-dev-macos-arm64.zip.sha256):

```sh
shasum -a 256 "$HOME/Downloads/RF2-0.36-dev-macos-arm64.zip"
```

Extract it with Finder. The expected folder is `RF2-0.36-dev-macos-arm64`. The binaries are ad-hoc signed, not notarized. Follow your normal macOS software approval process if prompted; these instructions do not disable Gatekeeper or remove quarantine attributes.

Get the source separately, then enter its directory:

```sh
git clone https://github.com/starkfiber/RiverFlow.git
cd RiverFlow
export RF2_HOME="$HOME/Downloads/RF2-0.36-dev-macos-arm64"
sh tools/dev.sh doctor
```

Already have a checkout? Enter that directory instead of cloning again. `RF2_HOME` must name the extracted folder containing `rf2c` and `rf2`, not the ZIP or the source repository. Adjust it to your chosen location.

`doctor` checks the supported host, executables and local code signatures, then prints runtime status. It does not verify every manifest hash, establish publisher identity, install tools, change system settings or qualify all compiler features. Seeing runtime version **0.17.0** is expected in the 0.36 bundle.

## 2. Check and build

```sh
sh tools/dev.sh check examples/collection-tools/telemetry-summary.flow
sh tools/dev.sh build examples/collection-tools/telemetry-summary.flow summary-build --opt
```

`check` validates the trusted Mac program without creating an executable or running it. `build` creates a new directory, compiles and applies local macOS signing. It never runs the application. Existing build directories are refused; choose `summary-build-2` for another build. A failed build may leave its newly created directory for inspection.

The source entry imports `lib/numbers.rf2` and `lib/output.rf2`. The first parses, sorts and summarises; the second writes results. The `.flow` extension is accepted alongside `.rf2`; the selected compiler and source profile determine the machine target.

## 3. Run it with your input

```sh
printf '9,1,9,3,2' | ./summary-build/program
```

Expected output:

```json
{"count":5,"minimum":1,"maximum":9,"sum":24,"median_lower":3}
```

The example input is supplied test data. Replace it with your own nonnegative integer values, separated by commas or whitespace. Input limits are 1 MiB and 65,536 values. The sum must fit an unsigned 64-bit integer. The [application guide](../examples/collection-tools/README.md) explains median rules, numeric JSON limitations and failures.

Try an invalid input:

```sh
printf '9,,3' | ./summary-build/program
```

It writes `Error 22` to standard error, exits with status 1 and emits no JSON. The doubled comma is an empty field. Correct the input and run again; no rebuild is needed for new data.

## 4. Build a second app from the same libraries

```sh
sh tools/dev.sh build examples/collection-tools/value-frequency.flow frequency-build --opt
printf '9,1,9,3,2' | ./frequency-build/program
```

Expected output:

```json
{"count":5,"unique":4,"frequencies":[{"value":1,"count":1},{"value":2,"count":1},{"value":3,"count":1},{"value":9,"count":2}]}
```

Both programs compile the same physical parser/sort module. Try different inputs, then read or change a helper and build into another new directory. This is local source-module reuse, not dynamic linking or a package registry.

## Which command should I use?

| Job | Command | Boundary |
| --- | --- | --- |
| Check the selected installation | `sh tools/dev.sh doctor` | Local executable/signature checks, not provenance attestation |
| Check a trusted Mac program | `sh tools/dev.sh check SOURCE.flow` | No output image or source-program execution |
| Build a trusted Mac program | `sh tools/dev.sh build SOURCE.flow NEW-DIR --opt` | Compiles and signs; execution is separate |
| Start the existing MCP service | `sh tools/dev.sh mcp` | Nine bounded tools; no raw systems compilation |
| Build ESP32-C3 firmware | `sh tools/dev.sh firmware SOURCE.flow NEW-PREFIX` | `.elf`, `.bin`, `.map`; no flash or device access |

The helper is a small shell convenience around existing native tools. It adds no language, compiler optimisation or MCP authority. For direct native commands, see [standalone tools](STANDALONE.md). For firmware, use the [ESP32-C3 guide](../examples/esp32c3/README.md), not the Mac analyser source.

## If something fails

| Message or symptom | What to do |
| --- | --- |
| Bundle directory does not exist / missing executable | Point `RF2_HOME` at the extracted bundle; inspect its contents |
| Signature check failed | Obtain the intended package again and compare its checksum; do not disable protections |
| Unknown `--check` / unsupported `collection` | Use the selected 0.36 bundle, not an older stable compiler |
| Build directory already exists | Choose a new output directory; the helper does not delete or replace it |
| Compiler error | Keep the message and reported source position; imported source positions may refer to expanded source |
| macOS approval prompt | Use the normal human approval process; the helper cannot approve it |

No learning-time, productivity, runtime speed or AI-token advantage is established by this walkthrough. See the [executed verification record](ONBOARDING-VERIFICATION.json). The reproducible developer controller is `tests/standalone/onboarding_verify.py`; Python is used only by that test controller, not by this user journey.
