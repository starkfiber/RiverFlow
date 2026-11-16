"""Immutable black-box Passage Desk acceptance; never repairs an attempt."""
from pathlib import Path
import hashlib
import html.parser
import json
import os
import re
import select
import subprocess
import sys
import tempfile


def expected(data, query):
    text = data.decode('utf-8')
    encoded = query.encode('utf-8')
    starts = [i for i in range(len(data)) if data.startswith(encoded, i)]
    words = 0
    inside = False
    for scalar in text:
        if scalar in '\t\n\r ':
            inside = False
        else:
            words += int(not inside)
            inside = True
    return dict(schema='passage-desk.v1', bytes=len(data), scalars=len(text),
                lines=data.count(b'\n') + int(bool(data) and not data.endswith(b'\n')),
                words_ascii_breaks=words, query=query, matches=len(starts),
                first_byte=starts[0] if starts else None)


class HTML(html.parser.HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids, self.stack, self.tags, self.attrs = {}, [], [], []
        self.id_tags, self.tag_text = {}, {}
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attrs = dict(attrs)
        self.attrs.append((tag, attrs))
        if tag not in ('meta', 'link', 'br', 'hr', 'input', 'img'):
            self.stack.append((tag, attrs.get('id')))
        if attrs.get('id'):
            self.ids.setdefault(attrs['id'], []).append('')
            self.id_tags.setdefault(attrs['id'], []).append(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, text):
        for tag, ident in self.stack:
            self.tag_text[tag] = self.tag_text.get(tag, '') + text
            if ident in self.ids:
                self.ids[ident][-1] += text


def grade(workspace, out):
    workspace, out = Path(workspace).resolve(), Path(out).resolve()
    checks = []

    def check(name, passed, detail=None):
        checks.append(dict(name=name, passed=bool(passed), detail=detail))

    try:
        launch = json.loads((workspace / 'launch.json').read_text())
        assert launch in (['./app'], ['python3', 'app.py'])
        check('launch', True)
    except Exception as exc:
        launch = ['./__missing_delivery__']
        check('launch', False, str(exc))

    def run(args):
        try:
            q = subprocess.run([*launch, *map(str, args)], cwd=workspace,
                               capture_output=True, timeout=10)
            return q.returncode, q.stdout, q.stderr
        except Exception as exc:
            return -1, b'', str(exc).encode()

    def parsed_report(code, raw, wanted):
        try:
            actual = json.loads(raw)
            # Python bool == int; enforce the exact contract, not only equality.
            return code == 0 and raw.endswith(b'\n') and actual == wanted and set(actual) == set(wanted) and all(
                type(actual[k]) is type(v) for k, v in wanted.items())
        except (ValueError, TypeError):
            return False

    with tempfile.TemporaryDirectory(prefix='passage-grade-') as temporary:
        root = Path(temporary)
        sources = {}
        cases = [
            ('empty', b'', 'a'), ('ascii', b'alpha beta\nalpha', 'alpha'),
            ('overlap', b'aaaaa', 'aa'), ('absent', b'alpha', 'z'),
            ('crlf', b'a\r\nb\r\nc\r', '\r\n'), ('whitespace', b'\t \r\n\n', ' '),
            ('unicode', 'தமிழ் café🙂 café\n'.encode(), 'café'),
            ('multibyte-offset', '🙂🙂a🙂'.encode(), 'a'),
            ('no-normalization', 'é e\u0301'.encode(), 'e\u0301'),
            ('nonascii-space', 'a\u00a0b c\u2003d'.encode(), 'b'),
            ('query128', b'x' * 129, 'x' * 128),
            ('bounded1MiB', b'ab' * 524288, 'aba'),
        ]
        for name, data, query in cases:
            p = root / (name + ' தமிழ் file.txt')
            p.write_bytes(data)
            sources[p] = data
            code, raw, err = run(['report', p, query])
            check('report:' + name, parsed_report(code, raw, expected(data, query)),
                  dict(exit=code, outputBytes=len(raw), stderr=err.decode(errors='replace')[:200]))
            check('preserved:' + name, p.read_bytes() == data)

        invalid = [
            ('bad-utf8', b'\xc0\xaf', 'a'), ('nul', b'a\0b', 'a'),
            ('control', b'a\x01b', 'a'), ('too-large', b'x' * 1048577, 'x'),
            ('empty-query', b'a', ''), ('long-query', b'a', 'x' * 129),
            ('byte-query-limit', b'a', '🙂' * 33), ('control-query', b'a', '\x01'),
        ]
        for name, data, query in invalid:
            p = root / name
            p.write_bytes(data)
            sources[p] = data
            for mode in ('report', 'html'):
                code, raw, err = run([mode, p, query])
                check('refusal:' + mode + ':' + name, code == 2 and raw == b'' and bool(err.strip()))
            check('preserved:' + name, p.read_bytes() == data)

        regular = root / 'selected.txt'
        regular.write_bytes(b'original')
        sources[regular] = b'original'
        link = root / 'link'
        link.symlink_to(regular)
        fifo = root / 'pipe'
        os.mkfifo(fifo)
        for name, p in [('missing', root / 'missing'), ('directory', root), ('symlink', link), ('fifo', fifo)]:
            code, raw, err = run(['report', p, 'a'])
            check('file-policy:' + name, code == 2 and raw == b'' and bool(err.strip()))
        for name, args in [('missing-args', []), ('extra-args', ['report', regular, 'a', 'extra']),
                           ('unknown-command', ['write', regular, 'a'])]:
            code, raw, err = run(args)
            check('arguments:' + name, code == 2 and raw == b'' and bool(err.strip()))

        # Known IDs are the public presentation contract; parse visible values.
        html_query = '<script>alert("x")</script>&\' தமிழ்'
        html_data = ('before ' + html_query + ' after\n').encode()
        hp = root / 'html-input'
        hp.write_bytes(html_data)
        sources[hp] = html_data
        code, raw, err = run(['html', hp, html_query])
        html_results = {}
        try:
            rendered = raw.decode('utf-8')
            page = HTML(rendered)
            wanted = expected(html_data, html_query)
            metrics = dict(bytes=wanted['bytes'], scalars=wanted['scalars'], lines=wanted['lines'],
                           words=wanted['words_ascii_breaks'], matches=wanted['matches'], first_byte=wanted['first_byte'])
            html_results['values'] = code == 0 and page.tags.count('td') == 6 and all(
                page.ids.get(k) == [str(v)] and page.id_tags.get(k) == ['td'] for k, v in metrics.items())
            html_results['escaped-query'] = page.ids.get('query') == [html_query] and '<script>' not in rendered.lower()
            html_results['semantics'] = (rendered.lstrip().lower().startswith('<!doctype html>') and page.tags.count('h1') == 1
                  and all(t in page.tags for t in ('title', 'table', 'caption', 'th', 'style'))
                  and all(page.tag_text.get(t, '').strip() for t in ('title', 'h1', 'caption', 'th', 'style'))
                  and any(t == 'html' and a.get('lang') == 'en' for t, a in page.attrs)
                  and any(t == 'meta' and a.get('name') == 'viewport' for t, a in page.attrs))
            html_results['no-active-remote-content'] = (not any(t in ('script', 'iframe', 'img', 'link') for t in page.tags)
                  and not any(k.lower().startswith('on') or 'http:' in v or 'https:' in v for _, a in page.attrs for k, v in a.items() if v)
                  and 'http:' not in rendered and 'https:' not in rendered)
            html_results['focus-link'] = ':focus' in rendered and any(t == 'a' and a.get('href', '').startswith('#') for t, a in page.attrs)
        except Exception as exc:
            html_results = {}
        for name in ('values', 'escaped-query', 'semantics', 'no-active-remote-content', 'focus-link'):
            check('html:' + name, html_results.get(name, False))
        empty_html = run(['html', root / 'empty தமிழ் file.txt', 'a'])
        try:
            check('html:absent-offset', empty_html[0] == 0 and HTML(empty_html[1].decode()).ids.get('first_byte') == ['none'])
        except Exception as exc:
            check('html:absent-offset', False, str(exc))

        # One persistent session proves actual reread and callback-error recovery.
        server = None
        pending = bytearray()
        protocol_results = []

        def read_line():
            import time
            deadline = time.monotonic() + 8
            while b'\n' not in pending:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([server.stdout], [], [], remaining)[0]:
                    raise TimeoutError('no bounded MCP response')
                chunk = os.read(server.stdout.fileno(), 65536)
                if not chunk:
                    raise EOFError('MCP server closed')
                pending.extend(chunk)
            line, _, rest = pending.partition(b'\n')
            pending[:] = rest
            return json.loads(line)

        def send(value, response=True):
            raw = value if isinstance(value, bytes) else json.dumps(value).encode() + b'\n'
            server.stdin.write(raw)
            server.stdin.flush()
            return read_line() if response else None

        def req(ident, method, params=None):
            value = dict(jsonrpc='2.0', id=ident, method=method)
            if params is not None:
                value['params'] = params
            response = send(value)
            assert response.get('jsonrpc') == '2.0' and response.get('id') == ident, 'MCP envelope/id mismatch'
            return response

        def protocol_check(name, function):
            try:
                check('mcp:' + name, function())
            except Exception as exc:
                check('mcp:' + name, False, type(exc).__name__ + ': ' + str(exc))

        def exact_report(actual, wanted):
            return isinstance(actual, dict) and actual == wanted and set(actual) == set(wanted) and all(
                type(actual[k]) is type(v) for k, v in wanted.items())

        try:
            server = subprocess.Popen([*launch, 'mcp', str(regular), 'a'], cwd=workspace,
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            protocol_check('initialize', lambda: req(1, 'initialize', dict(protocolVersion='2025-11-25', capabilities={}, clientInfo=dict(name='grader', version='1')))['result']['protocolVersion'] == '2025-11-25')
            send(dict(jsonrpc='2.0', method='notifications/initialized'), False)
            def schema():
                tools = req(2, 'tools/list', {})['result']['tools']
                return len(tools) == 1 and tools[0]['name'] == 'passage_report' and tools[0]['inputSchema'] == dict(type='object', properties={}, additionalProperties=False)
            protocol_check('exact-tool-schema', schema)
            call = dict(name='passage_report', arguments={})
            protocol_check('actual-selected-file', lambda: exact_report(req(3, 'tools/call', call)['result']['structuredContent'], expected(b'original', 'a')) and regular.read_bytes() == b'original')
            regular.write_bytes('a🙂aa'.encode())
            protocol_check('fresh-read', lambda: exact_report(req(4, 'tools/call', call)['result']['structuredContent'], expected('a🙂aa'.encode(), 'a')) and regular.read_bytes() == 'a🙂aa'.encode())
            regular.write_bytes(b'\0')
            def callback_error():
                result = req(5, 'tools/call', call)['result']
                return result.get('isError') is True and 'structuredContent' not in result and regular.read_bytes() == b'\0'
            protocol_check('callback-error', callback_error)
            regular.write_bytes(b'aaaa')
            protocol_check('callback-recovery', lambda: exact_report(req(6, 'tools/call', call)['result']['structuredContent'], expected(b'aaaa', 'a')) and regular.read_bytes() == b'aaaa')
            protocol_check('path-denial', lambda: 'error' in req(7, 'tools/call', dict(name='passage_report', arguments=dict(path='elsewhere'))))
            protocol_check('unknown-tool', lambda: 'error' in req(8, 'tools/call', dict(name='passage_write', arguments={})))
            protocol_check('explicit-empty-required', lambda: 'error' in req(9, 'tools/call', dict(name='passage_report')))
            protocol_check('unknown-method', lambda: 'error' in req(10, 'passage/write', {}))
            protocol_check('malformed', lambda: 'error' in send(b'{bad}\n'))
            protocol_check('duplicate-key', lambda: 'error' in send(b'{"jsonrpc":"2.0","id":11,"method":"ping","method":"tools/list"}\n'))
            protocol_check('decoded-duplicate-key', lambda: 'error' in send(b'{"jsonrpc":"2.0","id":11,"method":"ping","metho\\u0064":"tools/list"}\n'))
            protocol_check('oversize', lambda: 'error' in send(b' ' * 65537 + b'\n') and regular.read_bytes() == b'aaaa')
            # This tests notification silence. Non-invocation is qualified
            # separately with instrumented generic helpers and source review.
            regular.write_bytes(b'\0')
            send(dict(jsonrpc='2.0', method='tools/call', params=call), False)
            protocol_check('notification-silence-and-recovery', lambda: req(12, 'ping', {}).get('id') == 12 and regular.read_bytes() == b'\0')
            regular.write_bytes(b'original')
            server.stdin.close()
            server.wait(timeout=5)
            protocol_check('clean-eof', lambda: server.returncode == 0 and not pending)
        except Exception as exc:
            # Keep the count fixed even if a process never started.
            existing = {x['name'] for x in checks}
            for name in ('initialize', 'exact-tool-schema', 'actual-selected-file', 'fresh-read', 'callback-error', 'callback-recovery', 'path-denial', 'unknown-tool', 'explicit-empty-required', 'unknown-method', 'malformed', 'duplicate-key', 'decoded-duplicate-key', 'oversize', 'notification-silence-and-recovery', 'clean-eof'):
                if 'mcp:' + name not in existing:
                    check('mcp:' + name, False, str(exc))
        finally:
            regular.write_bytes(b'original')
            if server is not None:
                if server.poll() is None:
                    server.terminate()
                    try:
                        server.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        server.wait()
                for stream in (server.stdin, server.stdout, server.stderr):
                    if stream and not stream.closed:
                        stream.close()
        check('all-input-bytes-preserved', all(p.read_bytes() == data for p, data in sources.items()))
        check('readme', (workspace / 'README.md').is_file() and bool((workspace / 'README.md').read_text().strip()))
    report = dict(schema='rf2.passage-grade.v1', checks=len(checks), passed=sum(c['passed'] for c in checks),
                  allPassed=all(c['passed'] for c in checks), results=checks)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = grade(sys.argv[1], sys.argv[2])
    print(json.dumps({k: result[k] for k in ('checks', 'passed', 'allPassed')}))
