"""Local Study Rooms CLI, browser UI, and read-only MCP server."""
import datetime as dt
import html
import json
import re
import secrets
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl
from booking_sdk import execute, BookingError


def number(s):
    if not isinstance(s, str) or not re.fullmatch(r'[0-9]+', s) or len(s) > 20:
        raise BookingError(22)
    return int(s)


def date(s):
    if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', s):
        raise BookingError(22)
    try:
        return dt.date.fromisoformat(s).toordinal()
    except ValueError:
        raise BookingError(22)


def minute(s, end=False):
    if not re.fullmatch(r'[0-9]{2}:[0-9]{2}', s):
        raise BookingError(22)
    h, m = map(int, s.split(':'))
    if h == 24 and m == 0 and end:
        return 1440
    if h > 23 or m > 59:
        raise BookingError(22)
    return h * 60 + m


def operation(db, action, f):
    if action == 'cancel':
        return execute(db, action, expected=number(f['rev']), id=f['id'])
    return execute(db, 'reserve', expected=number(f['rev']), id=f['id'],
                   room=number(f['room']), day=date(f['date']),
                   start=minute(f['start']), finish=minute(f['end'], True))


def code(e):
    # Normalize SDK filesystem absence and capacity to the public contract.
    return {2: 404, 27: 22}.get(e.code, e.code)


def dump(obj):
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=True)


MESSAGES = {22: 'Invalid input. Check the ID, room, date and time range.',
            17: 'That ID already exists. Choose another ID.',
            404: 'The workspace or reservation was not found.',
            409: 'The revision changed or this room overlaps a reservation. Review the refreshed list and try again.',
            35: 'The workspace is busy. Refresh and retry.'}


def serve(db):
    execute(db, 'list')
    token = secrets.token_hex(16)
    esc = lambda v: html.escape(str(v), quote=True)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def endpoint(self):
            return '127.0.0.1:' + str(self.server.server_address[1])

        def valid_host(self):
            return self.headers.get_all('Host', []) == [self.endpoint()]

        def page(self, message='', values=None, status=200):
            values = values or {}
            try:
                state = execute(db, 'list')
            except BookingError as e:
                self.send_error(503, 'Storage error ' + str(code(e)))
                return
            rev = state['revision']
            hidden = lambda name, value: f'<input type="hidden" name="{name}" value="{esc(value)}">'
            common = hidden('rev', rev) + hidden('token', token)
            rows = ''
            for b in state['bookings']:
                clock = lambda n: f'{n//60:02d}:{n%60:02d}'
                rows += f'<tr><td>{esc(b["id"])}</td><td>{b["room"]}</td><td>{dt.date.fromordinal(b["day"]).isoformat()}</td><td>{clock(b["start"])}–{clock(b["finish"])}</td><td><form method="post" action="/action">{common}{hidden("action", "cancel")}{hidden("id", b["id"])}<button>Cancel reservation {esc(b["id"])}</button></form></td></tr>'
            inputs = ''
            for name, label, default in [('id', 'Reservation ID', ''), ('room', 'Room (1–16)', '1'), ('date', 'Date (YYYY-MM-DD)', dt.date.today().isoformat()), ('start', 'Start (HH:MM)', '09:00'), ('end', 'End (HH:MM, up to 24:00)', '10:00')]:
                inputs += f'<label>{label}<input name="{name}" value="{esc(values.get(name, default))}" required></label>'
            body = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Study Rooms</title>
<style>:root{{background:#f3f5fa;color:#202737;color-scheme:light dark;font:16px system-ui;background:light-dark(#f3f5fa,#141923);color:light-dark(#202737,#e7edf8)}}@media(prefers-color-scheme:dark){{:root{{background:#141923;color:#e7edf8}}}}body{{max-width:1050px;margin:auto;padding:24px}}h1{{margin-bottom:4px}}section{{background:light-dark(white,#202838);border:1px solid #78869a;border-radius:14px;padding:20px;margin:24px 0}}.fields{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px}}label{{display:grid;gap:8px}}input,button{{font:inherit;padding:10px;border:1px solid #78869a;border-radius:6px}}button{{cursor:pointer;background:light-dark(#254fbd,#a9c3ff);color:light-dark(white,#102142)}}:focus-visible{{outline:3px solid #dc961b;outline-offset:3px}}table{{width:100%;border-collapse:collapse}}td,th{{text-align:left;padding:12px;border-bottom:1px solid #78869a}}.scroll{{overflow:auto}}.notice{{padding:14px;border:1px solid #78869a;border-radius:8px}}.submit{{margin-top:18px}}</style>
<h1>Study Rooms</h1><p>Local room reservations · Revision {rev}</p><p>Rooms 1–16. Adjacent bookings are welcome; overlapping bookings are refused.</p>
{('<p class="notice" role="status">'+esc(message)+'</p>') if message else ''}
<section><h2>Reserve a room</h2><form method="post" action="/action">{common}{hidden('action','reserve')}<div class="fields">{inputs}</div><button class="submit">Reserve room</button></form></section>
<section><h2>Saved reservations ({len(state['bookings'])}/256)</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Room</th><th>Date</th><th>Time</th><th>Action</th></tr></thead><tbody>{rows}</tbody></table></div>{'<p>No reservations yet.</p>' if not rows else ''}</section><p>Local access only. Refresh to load changes made by another client.</p></html>'''
            data = body.encode()
            self.send_response(status)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if not self.valid_host():
                self.send_error(403); return
            if self.path != '/':
                self.send_error(404); return
            self.page()

        def do_POST(self):
            if not self.valid_host() or self.headers.get_all('Origin', []) != ['http://' + self.endpoint()]:
                self.send_error(403); return
            if self.path != '/action':
                self.send_error(404); return
            f = {}
            try:
                lengths = self.headers.get_all('Content-Length', [])
                if len(lengths) != 1 or self.headers.get('Transfer-Encoding'):
                    raise BookingError(22)
                n = number(lengths[0])
                if n > 8192 or self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/x-www-form-urlencoded':
                    raise BookingError(22)
                raw = self.rfile.read(n).decode('utf-8', 'strict')
                if re.search(r'%(?![0-9a-fA-F]{2})', raw):
                    raise BookingError(22)
                pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True, encoding='utf-8', errors='strict', max_num_fields=12)
                f = dict(pairs)
                action = f.get('action')
                required = {'action','rev','id','token'} | ({'room','date','start','end'} if action == 'reserve' else set())
                if len(f) != len(pairs) or action not in ('reserve','cancel') or set(f) != required:
                    raise BookingError(22)
                if not secrets.compare_digest(f['token'].encode('utf-8'), token.encode('ascii')):
                    raise BookingError(22)
                operation(db, action, f)
                self.page('Reservation saved.' if action == 'reserve' else 'Reservation cancelled.')
            except (BookingError, ValueError, UnicodeError) as e:
                c = code(e) if isinstance(e, BookingError) else 22
                self.page(MESSAGES.get(c, f'Storage error {c}. Refresh before retrying.'), f, 409 if c == 409 else 400)

    server = HTTPServer(('127.0.0.1', 0), Handler)
    print(f'http://127.0.0.1:{server.server_address[1]}/', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def unique(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError('duplicate key')
        result[k] = v
    return result


def mcp(db):
    execute(db, 'list')
    stream = sys.stdin.buffer
    while True:
        line = stream.readline(65537)
        if not line:
            break
        request_id = None
        try:
            if len(line) > 65536:
                while not line.endswith(b'\n'):
                    line = stream.readline(65537)
                    if not line: break
                raise ValueError('line too long')
            r = json.loads(line, object_pairs_hook=unique, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        except (ValueError, UnicodeError):
            print(dump({'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Invalid JSON or oversized line'}}), flush=True)
            continue
        notification = isinstance(r, dict) and 'id' not in r
        try:
            if not isinstance(r, dict) or r.get('jsonrpc') != '2.0' or set(r) - {'jsonrpc','id','method','params'} or not isinstance(r.get('method'), str):
                raise ValueError('Invalid request')
            request_id = r.get('id')
            if request_id is not None and (isinstance(request_id, bool) or not isinstance(request_id, (str, int))):
                request_id = None
                raise ValueError('Invalid request ID')
            method, p = r['method'], r.get('params', {})
            if not isinstance(p, dict): raise ValueError('Invalid params')
            if method == 'initialize':
                if p.get('protocolVersion') != '2025-11-25': raise ValueError('Unsupported protocol')
                result = {'protocolVersion':'2025-11-25','capabilities':{'tools':{'listChanged':False}},'serverInfo':{'name':'study-rooms','version':'1.0'}}
            elif method in ('ping','notifications/initialized'):
                if p: raise ValueError('Invalid params')
                result = {}
            elif method == 'tools/list':
                if p: raise ValueError('Invalid params')
                result = {'tools':[{'name':'booking_list','description':'Read saved study-room reservations.','inputSchema':{'type':'object','properties':{},'additionalProperties':False}}]}
            elif method == 'tools/call':
                if set(p) != {'name','arguments'} or p['name'] != 'booking_list' or type(p['arguments']) is not dict or p['arguments']:
                    result = {'isError':True,'content':[{'type':'text','text':'Only booking_list with explicit empty arguments is supported.'}]}
                else:
                    try:
                        state = execute(db, 'list')
                        result = {'structuredContent':state,'content':[{'type':'text','text':f"Revision {state['revision']}: {len(state['bookings'])} reservations."}]}
                    except BookingError as e:
                        result = {'isError':True,'content':[{'type':'text','text':f'Storage error {code(e)}'}]}
            else:
                if not notification:
                    print(dump({'jsonrpc':'2.0','id':request_id,'error':{'code':-32601,'message':'Unknown method'}}), flush=True)
                continue
            if not notification:
                print(dump({'jsonrpc':'2.0','id':request_id,'result':result}), flush=True)
        except ValueError as e:
            if not notification:
                print(dump({'jsonrpc':'2.0','id':request_id,'error':{'code':-32602,'message':str(e)}}), flush=True)


def main(args):
    try:
        if len(args) < 2: raise BookingError(22)
        action, db, *rest = args
        if action in ('init','list','serve','mcp') and not rest:
            if action == 'serve': serve(db); return 0
            if action == 'mcp': mcp(db); return 0
            state = execute(db, action)
        elif action == 'reserve' and len(rest) == 6:
            state = operation(db, action, dict(zip(('rev','id','room','date','start','end'), rest)))
        elif action == 'cancel' and len(rest) == 2:
            state = operation(db, action, dict(zip(('rev','id'), rest)))
        else: raise BookingError(22)
        print(dump(state)); return 0
    except BookingError as e:
        print(dump({'error':code(e)})); return 2
    except OSError as e:
        print(dump({'error':e.errno or 5})); return 2
    except ValueError:
        print(dump({'error':22})); return 2

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
