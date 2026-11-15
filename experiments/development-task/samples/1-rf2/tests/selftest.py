"""Local acceptance probes only. Application runtime is exclusively RF2."""
import datetime
import fcntl
import http.client
import json
import pathlib
import re
import subprocess
import socket
import tempfile
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = str(ROOT / 'app')
checks = 0

def check(condition, detail):
    global checks
    assert condition, detail
    checks += 1

def cli(*args, error=None):
    p = subprocess.run([APP, *map(str, args)], capture_output=True, text=True)
    data = json.loads(p.stdout)
    check(p.returncode == (2 if error is not None else 0), (args, p.returncode, p.stdout, p.stderr))
    if error is not None:
        check(data == {'error': error}, (args, data))
    return data

with tempfile.TemporaryDirectory(dir=ROOT / 'artifacts', prefix='selftest-') as folder:
    db = pathlib.Path(folder) / 'rooms.db'
    check(cli('init', db)['revision'] == 1, 'initial revision')
    cli('init', db, error=17)
    cli('list', str(db) + '-missing', error=404)
    s = cli('reserve', db, 1, 1, 1, '2024-02-29', '09:00', '10:00')
    check(s['bookings'][0]['day'] == datetime.date(2024, 2, 29).toordinal(), 'ordinal')
    cli('reserve', db, 1, 2, 1, '2024-02-29', '10:00', '11:00', error=409)
    cli('reserve', db, 2, 2, 1, '2024-02-29', '09:30', '10:30', error=409)
    cli('reserve', db, 2, 1, 2, '2024-02-29', '10:00', '11:00', error=17)
    s = cli('reserve', db, 2, 2, 1, '2024-02-29', '10:00', '11:00')
    s = cli('reserve', db, 3, '18446744073709551615', 16, '9999-12-31', '23:59', '24:00')
    s = cli('reserve', db, 4, 3, 2, '2024-02-29', '09:00', '10:00')
    check([r['id'] for r in s['bookings']] == ['1', '2', '18446744073709551615', '3'], 'insertion order')
    for id_, room, date, start, end in [
        ('01', 1, '2024-02-29', '12:00', '13:00'),
        ('0', 1, '2024-02-29', '12:00', '13:00'),
        ('18446744073709551616', 1, '2024-02-29', '12:00', '13:00'),
        ('4', 0, '2024-02-29', '12:00', '13:00'),
        ('4', 17, '2024-02-29', '12:00', '13:00'),
        ('4', 1, '2023-02-29', '12:00', '13:00'),
        ('4', 1, '0000-01-01', '12:00', '13:00'),
        ('4', 1, '2024-2-29', '12:00', '13:00'),
        ('4', 1, '2024-02-29', '24:00', '24:00'),
        ('4', 1, '2024-02-29', '9:00', '13:00'),
        ('4', 1, '2024-02-29', '13:00', '12:00'),
        ('4', 1, '2024-02-29', '12:00', '12:00')]:
        cli('reserve', db, 5, id_, room, date, start, end, error=22)
    check(cli('list', db) == s, 'invalid operations leave state unchanged')
    cli('cancel', db, 5, 999, error=404)
    s = cli('cancel', db, 5, 2)
    check([r['id'] for r in s['bookings']] == ['1', '18446744073709551615', '3'], 'cancel exact row')
    s = cli('reserve', db, 6, 4, 1, '0001-01-01', '00:00', '00:01')
    check(s['bookings'][-1]['day'] == 1, 'first Gregorian day')

    # Competing writers: one revision wins, no lost update.
    commands = [[APP, 'reserve', str(db), '7', str(i), '3', '2024-03-01', '12:00', '13:00'] for i in (5, 6)]
    processes = [subprocess.Popen(c, stdout=subprocess.PIPE, text=True) for c in commands]
    results = [json.loads(p.communicate()[0]) for p in processes]
    check(sum(p.returncode == 0 for p in processes) == 1, ('concurrent winners', results))
    check(all(p.returncode == 0 or r.get('error') in (35, 409) for p, r in zip(processes, results)), 'concurrency refuses safely')

    server = subprocess.Popen([APP, 'serve', str(db)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        url = server.stdout.readline().strip()
        fallback = url == '{"error":5}'
        if fallback:
            probe = socket.socket()
            try:
                probe.bind(('127.0.0.1', 0))
            except PermissionError:
                print('LIMITATION: sandbox denies loopback bind; HTTP tests use native inherited socket pairs.')
            else:
                raise AssertionError('serve failed despite permitted bind')
            finally:
                probe.close()
            url = 'http://127.0.0.1:43123/'
        check(re.fullmatch(r'http://127\.0\.0\.1:\d+/', url) is not None, ('server URL', url))
        endpoint = urllib.parse.urlsplit(url)
        origin = url[:-1]
        def request(method='GET', target='/', body=None, headers=None):
            if fallback:
                client, native = socket.socketpair()
                client.settimeout(5)
                h = {'Host': endpoint.netloc, **(headers or {})}
                payload = (body or '').encode()
                if method == 'POST':
                    h['Content-Length'] = str(len(payload))
                raw = (f'{method} {target} HTTP/1.1\r\n' + ''.join(f'{k}: {v}\r\n' for k, v in h.items()) + '\r\n').encode() + payload
                proc = subprocess.Popen([str(ROOT / 'tests/http_harness'), str(db), str(native.fileno()), '0123456789abcdef0123456789abcdef', 'unused'], pass_fds=(native.fileno(),))
                native.close()
                client.sendall(raw)
                response = http.client.HTTPResponse(client)
                response.begin()
                result = response.status, response.read().decode()
                client.close()
                check(proc.wait(timeout=5) == 0, 'HTTP native harness exit')
                return result
            c = http.client.HTTPConnection(endpoint.hostname, endpoint.port, timeout=5)
            c.request(method, target, body, headers or {})
            response = c.getresponse()
            result = response.status, response.read().decode()
            c.close()
            return result
        status, html = request()
        check(status == 200 and '<h1>Study Rooms</h1>' in html, 'browser home')
        for field in ('room', 'date', 'start', 'end'):
            check(f'name="{field}"' in html or f'name={field}' in html, ('labelled field', field))
        token = re.search(r'name=token value="([a-f0-9]{32})"', html).group(1)
        revision = cli('list', db)['revision']
        fields = dict(action='reserve', rev=revision, id='90', room='4', date='2026-11-15', start='09:00', end='10:00', token=token)
        headers = {'Origin': origin, 'Content-Type': 'application/x-www-form-urlencoded'}
        def post(fields_, extra='', headers_=None):
            return request('POST', '/action', urllib.parse.urlencode(fields_) + extra, headers if headers_ is None else headers_)
        before = cli('list', db)
        check(post({**fields, 'token': 'bad'})[0] == 400, 'CSRF refusal')
        check(post(fields, headers_={**headers, 'Origin': 'http://example.invalid'})[0] == 400, 'origin refusal')
        check(request(headers={'Host': 'localhost:1'})[0] == 400, 'Host refusal')
        check(post(fields, '&room=5')[0] == 400, 'duplicate form refusal')
        check(post(fields, '&unknown=x')[0] == 400, 'unknown form refusal')
        check(cli('list', db) == before, 'rejected HTTP requests unchanged')
        status, html = post(fields)
        check(status == 200 and 'Saved to your workspace.' in html, 'browser reserve success')
        check(cli('list', db)['bookings'][-1]['id'] == '90', 'browser reserve persisted')
        status, html = post({**fields, 'id': '91', 'start': '09:30'})
        check('current bookings below' in html and 'value="09:30"' in html, 'stale refresh and retained input')
        newrev = cli('list', db)['revision']
        status, html = post(dict(action='cancel', rev=newrev, id='90', token=token))
        check('Saved to your workspace.' in html and all(r['id'] != '90' for r in cli('list', db)['bookings']), 'browser explicit cancellation')
        status, html = post({**fields, 'rev': newrev + 1, 'date': '2023-02-29'})
        check('Check the booking details.' in html and 'value="2023-02-29"' in html, 'invalid date retained')
    finally:
        server.terminate()
        server.communicate(timeout=5)

    rpc = subprocess.Popen([APP, 'mcp', str(db)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    def exchange(value, raw=False):
        rpc.stdin.write((value if raw else json.dumps(value)) + '\n')
        rpc.stdin.flush()
        return json.loads(rpc.stdout.readline())
    def call(method, params=None, id_=1):
        msg = dict(jsonrpc='2.0', id=id_, method=method)
        if params is not None:
            msg['params'] = params
        return exchange(msg)
    try:
        check(call('initialize', dict(protocolVersion='2025-11-25', capabilities={}, clientInfo={'name': 'selftest', 'version': '1'}))['result']['protocolVersion'] == '2025-11-25', 'MCP initialize')
        rpc.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        rpc.stdin.flush()
        check(call('ping', id_='hello')['id'] == 'hello', 'MCP ID echo')
        tools = call('tools/list')['result']['tools']
        check(len(tools) == 1 and tools[0]['name'] == 'booking_list' and tools[0]['inputSchema']['additionalProperties'] is False, 'MCP exact tool')
        check(call('tools/call', {'name': 'booking_list', 'arguments': {}})['result']['structuredContent'] == cli('list', db), 'MCP saved state')
        for params in ({'name': 'booking_list'}, {'name': 'booking_list', 'arguments': {'path': 'x'}}, {'name': 'reserve', 'arguments': {}}):
            check(call('tools/call', params)['result']['isError'] is True, 'MCP tool refusal')
        check(call('unknown')['error']['code'] == -32601, 'MCP method refusal')
        for raw in ('{', '{"jsonrpc":"2.0","id":1,"method":"ping","metho\\u0064":"ping"}', 'x' * 65537):
            check(exchange(raw, True)['error']['code'] == -32700, 'malformed/duplicate/oversized MCP refusal')
        rpc.stdin.write('{"jsonrpc":"2.0","method":"tools/call","params":{"name":"reserve","arguments":{}}}\n')
        rpc.stdin.flush()
        check(call('ping')['result'] == {}, 'MCP survives rejection and notification')
    finally:
        rpc.stdin.close()
        rpc.wait(timeout=5)
    # Lock refusal and full current-reservation capacity.
    with open(db, 'rb') as locked:
        fcntl.flock(locked, fcntl.LOCK_EX | fcntl.LOCK_NB)
        cli('reserve', db, 1, 100, 1, '2024-03-01', '00:00', '00:01', error=35)
    full = pathlib.Path(folder) / 'full.db'
    cli('init', full)
    for i in range(256):
        day = (datetime.date(2024, 1, 1) + datetime.timedelta(days=i)).isoformat()
        capacity_state = cli('reserve', full, i + 1, i + 1, 1, day, '00:00', '00:01')
    check(len(capacity_state['bookings']) == 256, '256 current bookings supported')
    p = subprocess.run([APP, 'reserve', str(full), '257', '257', '2', '2025-01-01', '00:00', '00:01'], capture_output=True, text=True)
    check(p.returncode == 2 and 'error' in json.loads(p.stdout), '257th booking refused')
    check(cli('list', full) == capacity_state, 'capacity refusal unchanged')
    cli('cancel', full, 257, 1)
    check(len(cli('reserve', full, 258, 257, 2, '2025-01-01', '00:00', '00:01')['bookings']) == 256, 'capacity reusable after cancellation')
    # Detect corruption rather than fabricating an empty workspace.
    corrupt = pathlib.Path(folder) / 'corrupt.db'
    corrupt.write_bytes(b'broken')
    cli('list', corrupt, error=9001)
print(f'PASS: {checks} assertions; CLI, persistence, concurrency, HTTP forms/security, MCP, corruption')
