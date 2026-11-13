# Number Lab

A small native RiverFlow learning game for bytes and Boolean logic. It computes every displayed conversion and gate answer. It opens no files or network connections and reads commands from borrowed standard input.

Build with a qualified native RF2 compiler, then apply ordinary macOS signing:

```sh
/path/to/rf2c examples/number-lab/main.rf2 output/number-lab --opt --compact
/usr/bin/codesign -s - output/number-lab
./output/number-lab
```

Type `help` for the guide. Try:

```text
show 65
and 12 10
or 12 10
xor 12 10
not 12
quiz 1 0
answer 1
answer 0
guess 20
guess 100
guess 42
quit
```

`show 65` computes decimal `65`, binary `01000001`, hex `41` and printable ASCII `A`. The gate examples give `8`, `14`, `6` and `243` respectively. In the quiz, a wrong answer keeps the question open so the learner can try again. AND produces 1 only for inputs 1 and 1.

The guessing round deliberately uses the fixed byte 42, making the teaching example reproducible. It is not a random-number generator or a competitive secret. `reset` starts the same teaching round again and clears a pending quiz. No children, classrooms or educational outcomes were studied; “kid-friendly” describes the simple instructions, not validated effectiveness.

Commands use lowercase ASCII names and decimal integers from 0 to 255. Leading zeros are accepted for up to three decimal digits. Hex is displayed but not accepted as command input. Printable ASCII bytes are shown as characters; control bytes and values outside ASCII are labelled without sending terminal control sequences. Inputs and errors never become source code, file paths, shell commands or network requests.

The program accepts lines of at most 63 bytes, ignoring a final CR before LF. An oversized line is rejected and drained so the next command can recover. A line without a newline is bounded at 4,096 bytes, after which the session ends. EOF processes a final partial line. Each session accepts at most 1,024 input lines. Invalid commands recover without changing the game state. These bounds are implementation choices rather than claims of general parser safety.

The application is a CLI, not a graphical toolkit or a browser game. Current execution qualification is macOS ARM64. No Linux, Windows, QEMU, phone, SoC acceleration, energy or model-token advantage is established by this example. Native users need no Python or Node runtime. The independent controller is developer tooling:

```sh
RF2_TEST_COMPILER=/path/to/rf2c python3 tests/standalone/number_lab_verify.py
```

The controller checks conversions and operations against independent Python arithmetic, interactive quiz/guessing state, malformed commands, line bounds and recovery, EOF, argument refusal, deterministic output across compiler modes, and explicit function-cache clean-image equivalence. Retain the actual receipt before claiming that a particular compiler candidate passed.
