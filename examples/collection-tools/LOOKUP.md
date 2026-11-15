# Shared sorted lookup, development source

`lib/ranges.flow` adds numbers_equal_range(values,needle,out) over an ascending sorted borrowed Numbers collection. It returns the count, and writes a half-open [first,after) range to NumberRange. An absent value has first==after at its insertion position. Empty input is valid. No allocation/mutation of the collection or ownership transfer occurs. The caller must establish sorted order; the low-level function does not rescan to prove it.

The new lookup.flow application reuses the existing canonical unsigned parser, relocating Numbers collection and heapsort. It sorts supplied input before invoking the range library. It accepts exactly one unsigned query value and bounded numeric stdin; it is not a string map, generic collection, SQL database or measured service.

```sh
sh tools/build-program.sh /absolute/qualified/rf2c examples/collection-tools/lookup.flow new-lookup --opt
printf '9,1,9,3,2' | ./new-lookup/program 9
# {"first":3,"after":5,"matches":2}
```

Lower/upper-bound search is established prior art, not a novel algorithm. See docs/PLATFORM-SPRINT-0.40.md for actual qualification. Native user execution requires no controller language. Reproduction tests use Python bisect as an independent expected-result oracle, separately from RF2 sorting/search.
