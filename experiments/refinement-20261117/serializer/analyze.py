#!/usr/bin/env python3
"""Audit the once-only frozen R5 campaign; never invoke/retry a native sample."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import statistics

HERE = Path(__file__).resolve().parent
EXPECTED_FROZEN = "fae78095254925724ae98e2ce0bb350df32622a4f257b1b22350d1979689d669"
EXPECTED_PROTOCOL = "113f3e97d07ecd0b4654db0cafe9701da374611442aa389895d2b095efa05ec0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paired(base, candidate):
    ratios = [c / b for b, c in zip(base, candidate)]
    assert len(ratios) == 31 and all(math.isfinite(x) and x > 0 for x in ratios)
    return statistics.median(ratios)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    directory = args.benchmark.resolve()
    frozen_path = directory / "FROZEN.json"
    protocol_path = directory / "PROMOTION-PROTOCOL.json"
    assert sha(frozen_path) == EXPECTED_FROZEN
    assert sha(protocol_path) == EXPECTED_PROTOCOL
    frozen = json.loads(frozen_path.read_text())
    protocol = json.loads(protocol_path.read_text())
    raw = json.loads((directory / "RESULTS.json").read_text())
    assert raw["complete"] is True and "failure" not in raw
    assert raw["frozenSHA256"] == EXPECTED_FROZEN
    assert len(raw["rows"]) == 26
    assert sha(HERE / "benchmark.py") == frozen["controllerSHA256"]
    assert sha(HERE / "json_spans.flow") == frozen["candidateSourceSHA256"]
    events = [json.loads(line) for line in (directory / "SAMPLES.jsonl").read_text().splitlines()]
    comparisons = [event for event in events if event["context"]["phase"] == "comparison"]
    assert len(comparisons) == 26 * 31 * 3
    assert len(events) == len(comparisons) + 26
    assert all(event["exit"] == 0 and event["stdoutSHA256"] == event["wantedSHA256"] for event in events)
    assert len((directory / "TRIALS.jsonl").read_text().splitlines()) == 26 * 31
    rows, rejected = [], []
    seen = set()
    for index, row in enumerate(raw["rows"]):
        profile = row["profile"]
        key = (profile["size"], profile["density"], row["mode"])
        assert key not in seen
        seen.add(key)
        assert len(row["trials"]) == 31
        durations = {variant: [] for variant in ("baseline", "previous", "candidate")}
        processes = {variant: [] for variant in durations}
        for number, trial in enumerate(row["trials"]):
            assert trial["trial"] == number and set(trial["order"]) == set(durations)
            for variant, measurement in trial["measurements"].items():
                assert measurement["nativeUs"] > 0 and measurement["processSeconds"] > 0
                durations[variant].append(measurement["nativeUs"])
                processes[variant].append(measurement["processSeconds"])
            output_hashes = {m["outputSHA256"] for m in trial["measurements"].values()}
            checksums = {m["checksum"] for m in trial["measurements"].values()}
            assert len(output_hashes) == len(checksums) == 1
        scalar = row["ratios"]["candidate"]
        previous = row["candidateVsR3"]
        assert paired(durations["baseline"], durations["candidate"]) == scalar["point"]
        assert paired(durations["previous"], durations["candidate"]) == previous["point"]
        for comparison in (scalar, previous):
            assert 0 < comparison["lower95"] <= comparison["upper95"]
        minimum = min(value for values in durations.values() for value in values)
        small = profile["size"] <= 32
        dense = profile["size"] in protocol["denseTargets"]["sizes"] and profile["density"] == "escaped"
        small_pass = not small or (
            scalar["point"] <= protocol["small"]["medianCandidateBaselineAtMost"]
            and scalar["upper95"] <= protocol["small"]["upper95AtMost"]
            and min(durations["baseline"] + durations["candidate"]) >= protocol["small"]["minimumNativeUs"]
        )
        dense_pass = not dense or (
            scalar["upper95"] < protocol["denseTargets"]["eachCandidateBaselineUpper95Below"]
            and previous["upper95"] < protocol["denseTargets"]["eachCandidateR3Upper95Below"]
            and minimum >= protocol["denseTargets"]["minimumNativeUs"]
        )
        reasons = []
        if small and not small_pass:
            if scalar["point"] > protocol["small"]["medianCandidateBaselineAtMost"]:
                reasons.append("small median-ratio bound exceeded")
            if scalar["upper95"] > protocol["small"]["upper95AtMost"]:
                reasons.append("small upper95 bound exceeded")
            if min(durations["baseline"] + durations["candidate"]) < protocol["small"]["minimumNativeUs"]:
                reasons.append("small minimum native duration below 50ms")
        if dense and not dense_pass:
            reasons.append("dense superiority or minimum-duration requirement not met")
        summary = {
            "size": key[0], "density": key[1], "mode": key[2],
            "scalarRatio": {name: scalar[name] for name in ("point", "lower95", "upper95")},
            "r3Ratio": {name: previous[name] for name in ("point", "lower95", "upper95")},
            "speedupVsScalar": 1 / scalar["point"], "speedupVsR3": 1 / previous["point"],
            "minimumNativeUsAllThree": minimum,
            "minimumNativeUsScalarAndCandidate": min(durations["baseline"] + durations["candidate"]),
            "smallGateRequired": small, "smallGatePassed": small_pass if small else None,
            "denseGateRequired": dense, "denseGatePassed": dense_pass if dense else None,
            "secondaryProcessMedianPairedRatioVsScalar": paired(processes["baseline"], processes["candidate"]),
            "secondaryProcessMedianPairedRatioVsR3": paired(processes["previous"], processes["candidate"]),
            "reasons": reasons,
        }
        rows.append(summary)
        if reasons:
            rejected.append(summary)
    small_rows = [row for row in rows if row["smallGateRequired"]]
    dense_rows = [row for row in rows if row["denseGateRequired"]]
    assert len(small_rows) == 8 and len(dense_rows) == 6
    result = {
        "schema": "rf2.serializer.r5.evidence.v1", "complete": True,
        "promotionEligible": all(row["smallGatePassed"] for row in small_rows) and all(row["denseGatePassed"] for row in dense_rows),
        "smallGatesPassed": sum(row["smallGatePassed"] for row in small_rows), "smallGatesTotal": 8,
        "denseGatesPassed": sum(row["denseGatePassed"] for row in dense_rows), "denseGatesTotal": 6,
        "profiles": 26, "pairedTrialsPerProfile": 31, "comparativeNativeInvocations": len(comparisons),
        "allRecordedOutputHashesAndExitCodesMatch": True, "pairedPointsIndependentlyRecomputed": True,
        "confidenceIntervals": "Preserved paired bootstrap median ratios from frozen controller; 10000 resamples, not newly refitted",
        "frozenSHA256": EXPECTED_FROZEN, "promotionProtocolSHA256": EXPECTED_PROTOCOL,
        "candidateSHA256": frozen["candidateSourceSHA256"], "compilerSHA256": frozen["compilerSHA256"],
        "sourceSHA256": {path.name: sha(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.suffix in (".py", ".flow", ".in")},
        "rawSHA256": {name: sha(directory / name) for name in ("RESULTS.json", "STARTED.json", "COUNTS-FROZEN.json", "TRIALS.jsonl", "SAMPLES.jsonl", "MEASURE-BUILD.json", "MEASURE-SMOKE.json")},
        "scope": "Isolated Darwin ARM64 source candidate. All rows retained; no retries or recalibration after comparison. Unrelated Mac load not controlled. Default SDK and stable release unchanged.",
        "rows": rows, "rejectedRows": rejected,
    }
    destination = args.out.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "EVIDENCE.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# R5 once-only campaign", "", f"Promotion eligible: **{result['promotionEligible']}**. Small gates: {result['smallGatesPassed']}/8; dense targets against both scalar and R3: {result['denseGatesPassed']}/6.", "", "| Bytes | Density | Mode | Speedup vs scalar | Speedup vs R3 | Candidate/scalar 95% CI | Minimum native ms, all three | Gate refusal |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        ratio = row["scalarRatio"]
        lines.append(f"| {row['size']} | {row['density']} | {row['mode']} | {row['speedupVsScalar']:.3f}× | {row['speedupVsR3']:.3f}× | {ratio['lower95']:.5f}–{ratio['upper95']:.5f} | {row['minimumNativeUsAllThree']/1000:.3f} | {'; '.join(row['reasons']) or '—'} |")
    lines += ["", result["scope"], "", "A duration gate refusal is not a measured slowdown. It still prevents promotion under the frozen protocol. Smaller native times are not replaced with startup-inclusive process timing. No stable/default replacement follows from these results."]
    (destination / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({key: result[key] for key in ("complete", "promotionEligible", "smallGatesPassed", "denseGatesPassed", "profiles")}))


if __name__ == "__main__":
    main()
