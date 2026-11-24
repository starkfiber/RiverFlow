"""Installed core MCP and application regressions."""
import hashlib
import json
from pathlib import Path
import re
import select
import subprocess

from candidate049 import signed_image

ROOT = Path(__file__).resolve().parents[2]


def command(*args, cwd, env, data=None, allowed=(0,)):
    child = subprocess.run(args, cwd=cwd, env=env, input=data, capture_output=True, timeout=30)
    if child.returncode not in allowed:
        raise RuntimeError((args, child.returncode, child.stderr[-1500:]))
    return child


def build_app(compiler, work, env, app, label):
    source = ROOT / "examples" / app / "main.rf2"
    directory = work / label
    directory.mkdir()
    target = directory / "program"
    command(compiler, "--check", source, cwd=work, env=env)
    fingerprint = signed_image(compiler, source, target, ["--compact", "--opt"], env)
    return target, fingerprint


def mcp(exe, env, cwd):
    with subprocess.Popen([exe, "mcp"], cwd=cwd, env=env, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as runtime:
        count = 0

        def send(message):
            runtime.stdin.write(json.dumps(message).encode() + b"\n")
            runtime.stdin.flush()

        def request(method, params):
            nonlocal count
            count += 1
            send({"jsonrpc": "2.0", "id": count, "method": method, "params": params})
            assert select.select([runtime.stdout], [], [], 5)[0], method
            response = json.loads(runtime.stdout.readline())
            assert response["id"] == count
            return response

        initialize = request("initialize", {"protocolVersion": "2024-11-05"})
        assert "result" in initialize
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        tools = request("tools/list", {})["result"]["tools"]
        tool_names = sorted(item["name"] for item in tools)
        assert len(set(tool_names)) == 9 and "rf2_run" in tool_names
        status = request("tools/call", {"name": "rf2_status", "arguments": {}})["result"]
        assert not status.get("isError")
        source = (ROOT / "examples/sum.flow").read_text()
        denied = request("tools/call", {"name": "rf2_run", "arguments": {
            "source": "profile RF2_SYSTEM_A64_V1\nfn main(a,b)\n return 0\nend\n", "data": [1, 2, 3]}})
        assert "error" in denied or denied["result"].get("isError"), denied
        valid = request("tools/call", {"name": "rf2_run", "arguments": {
            "source": source, "data": [1, 2, 3]}})["result"]
        structured = valid.get("structuredContent", {})
        assert not valid.get("isError") and structured.get("value") == 6, valid
        runtime.stdin.close()
        assert runtime.wait(timeout=5) == 0 and not runtime.stderr.read()
    return {"tools": tool_names, "refused_systems_then_core_value": structured["value"], "clean_exit": True}


def text_search(compiler, work, env, label):
    binary, fingerprint = build_app(compiler, work, env, "text-search", label)
    payload, query = "banana banana தமிழ்".encode(), b"ana"
    positions = [i for i in range(len(payload)) if payload.startswith(query, i)]
    expected = {"bytes": len(payload), "query_bytes": len(query),
                "matches": len(positions), "first_byte": positions[0]}
    assert json.loads(command(binary, query, "--overlap", cwd=work, env=env, data=payload).stdout) == expected
    return {"raw_sha256": fingerprint, "result": expected}


def text_audit(compiler, work, env, label):
    binary, fingerprint = build_app(compiler, work, env, "text-audit", label)
    # The first two-byte scalar straddles the app's 128-byte read boundary.
    prefix = b"x" * 127 + "é தமிழ் ".encode()
    suffix = "\nRF² 😀\x00tail".encode()
    outcomes = {}
    for name, invalid in (("valid", b""), ("invalid", b"\xff")):
        payload = prefix + invalid + suffix
        display = payload.decode(errors="ignore")
        tokens = re.split(r"[\x00\t\n\v\f\r ]+", display)
        expected = {
            "bytes": len(payload), "unicode_scalars": len(display), "lf_newlines": display.count("\n"),
            "ascii_whitespace_words": sum(bool(token) for token in tokens), "invalid_sequences": len(invalid),
            "first_invalid_byte": len(prefix) if invalid else None, "nul_scalars": display.count("\0"),
            "io_status": 0, "detail": 0,
        }
        status = 2 if invalid else 0
        fixture = work / f"{label}-{name}.txt"
        fixture.write_bytes(payload)
        piped = command(binary, cwd=work, env=env, data=payload, allowed=(status,)).stdout
        stored = command(binary, fixture, cwd=work, env=env, allowed=(status,)).stdout
        assert piped == stored and json.loads(stored) == expected
        outcomes[name] = {"status": status, "input_sha256": hashlib.sha256(payload).hexdigest(), "summary": expected}
    return {"raw_sha256": fingerprint, "results": outcomes}
