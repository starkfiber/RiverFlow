# Follow a function change

This checked example exits 0 with its original source. Use a qualified native 0.27 compiler:

```sh
/path/to/rf2c examples/function-changes/main.rf2 output/before --opt --compact --functions
/usr/bin/codesign -s - output/before
./output/before
```

Make a reviewed copy of the source, change `leaf` from `x+1` to `x+2`, and compile that copy to a new `output/after` with the same flags. Then inspect the change evidence:

```sh
python3 tools/function-impact.py output/before.functions output/after.functions
```

Expected: leaf has changed; caller and main need revalidation; separate has unchanged source. The changed program intentionally fails the original expected answer until the author reviews the behavior and its test. Do not alter a test merely to hide a compiler failure.

The sidecars contain token fingerprints, code ranges, relocation records and direct call edges. They do not contain reusable object code. The tool always reports machineCodeReused false. Type/declaration or compiler-mode changes cause conservative global revalidation. Compiler identity and object/type effects must still be retained separately before any future code reuse.

The [compact image contract](../../docs/COMPACT-IMAGES-0.27.md) explains zero-filled storage. The [developer reference](../../docs/DEVELOPER-EXAMPLES.md) distinguishes .rf2 systems programs from bounded .flow Core input.
