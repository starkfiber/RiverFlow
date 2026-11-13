# SHA40: a fixed-input compiler workload

This native example reads exactly40bytes from standard input and writes their complete32byte SHA-256 digest to standard output. Other lengths reject with exit4, extra arguments with2, input errors with3 and output errors with5.

```sh
/path/to/rf2c examples/sha40/main.rf2 output/sha40 --opt --compact
/usr/bin/codesign -s - output/sha40
./output/sha40 < message-of-exactly-40-bytes.bin > digest.bin
```

It follows the standard [SHA-256 construction in FIPS180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final). It introduces no new cryptography. `tools/generate-sha40.py` emits readable scalar round code from the retained standard constants; rerunning it must reproduce `rounds.rf2` exactly. The test compares complete digests against independent hashlib.

Four scalar helpers recompute the compression and return separate digest-word pairs. This deliberately trades runtime efficiency for a clear, substantial compile/reuse workload. It is not a recommended cryptographic library, a general-length hash interface or a claim of accelerated hashing. Prefer the existing file-checksum example for general file hashing.

With optimized code, each helper is within the current64KiB unit limit and can be reused independently. Default unoptimized helpers exceed that limit and correctly fall back to ordinary generation. The qualification controller tests both routes and their actual hit counts.

`tools/benchmark-reuse-edit.py` changes real entry-function error handling while preserving the kernel, comparing complete cached and clean images and independently checking digest and error behavior. It reports compilation time separately from application execution. Developer controllers/generator use Python; the produced app uses native RF2 only.
