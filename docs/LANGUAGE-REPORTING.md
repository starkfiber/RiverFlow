# RiverFlow source and GitHub language reporting

Reviewed 15 November 2026. GitHub's sidebar classifies recognized tracked languages. It is not a runtime dependency graph, a compatibility list or a measure of the compiler's implementation quality.

The current [GitHub Linguist language registry](https://github.com/github-linguist/linguist/blob/main/lib/linguist/languages.yml) has no RiverFlow entry. Our native compiler and runtime are RF2 source even while the sidebar gives large shares to Python development tests and JavaScript reference tools. Adding C++, Rust or Java folders would not create interoperability with those languages.

## Project-owned inventory

Run from the repository root:

```sh
python3 tools/source-inventory.py
python3 tools/source-inventory.py --check
```

The generator reads tracked paths, the working file bytes and `linguist-generated` attributes. Stage reviewed new source paths before regenerating so they are included. The JSON gives every counted path, language, byte count and architectural area. Its suffix map is explicit. Markdown prose, archives, images and unlisted suffixes are outside the count. It excludes only source-suffix files actually marked generated; tests, reference tools and experiments remain visible.

[SOURCE-INVENTORY.json](SOURCE-INVENTORY.json) and [the chart](SOURCE-INVENTORY.svg) use the same inputs. `--check` refuses stale outputs without rewriting them. Results describe this working source snapshot; they are not a GitHub Linguist run, a signed attestation, code coverage or a speed comparison.

The learning HTML copies are produced from `book/learning-edition-1/README.md` by `tools/book/build-learning.mjs`. The main book and published browser-lab copies have their own existing generators. Generated output stays available for readers and Pages; its source and generator stay inspectable. Actual Python, JavaScript, HTML and assembly source keep their real classifications.

## Recognition path

GitHub uses [Linguist for syntax highlighting and language statistics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-repository-languages). An upstream language contribution needs a compatible syntax grammar, representative licensed source samples, registry data and evidence of genuine usage. Current [contribution requirements](https://github.com/github-linguist/linguist/blob/main/CONTRIBUTING.md#language-extension-and-filename-usage-requirements) require broad usage across repositories; for normal repeatable source extensions, the stated threshold is at least 2,000 indexed files in the last year excluding forks, with distribution across users and repositories. Owner-generated copies are not a substitute for adoption. These rules can change; recheck them before submitting.

- [ ] Maintain a grammar covering actual Core, Systems and embedded syntax, with positive/negative highlighting examples and a compatible licence.
- [ ] Distribute a tested editor language integration with the canonical RF2 name and existing extensions.
- [ ] Collect real, representative independent project usage and licensed samples.
- [ ] Recheck extension collisions, adoption requirements and classifier tests.
- [ ] Submit the upstream recognition proposal when evidence satisfies the requirements; retain its actual review outcome.

No upstream proposal or acceptance is claimed by this cleanup. A repository attribute cannot register an unknown language on GitHub. Do not force RF2 into another language or mark real test/reference source as generated to change the sidebar.
