"""Study Rooms: local CLI, HTML forms and read-only JSON-RPC."""
import datetime as dt
import html
import json
import re
import secrets
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qsl
from booking_sdk import execute, BookingError


def number(s):
    if not isinstance(s, str) or not re.fullmatch(r'[0-9]+', s) or len(s) > 20:
        raise BookingError(22)
    return int(s)


def day(s):
    if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', s):
        raise BookingError(22)
    try:
        return dt.date.fromisoformat(s).toordinal()
    except ValueError:
        raise BookingError(22)


def minute(s, end=False):
    if end and s == '24:00':
        return 1440
    if not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', s):
        raise BookingError(22)
    return int(s[:2])*60+int(s[3:])


def operation(db, action, values):
    args = dict(expected=number(values['rev']), id=values['id'])
    if action == 'reserve':
        args.update(room=number(values['room']), day=day(values['date']),
                    start=minute(values['start']), finish=minute(values['end'], True))
    return execute(db, action, **args)


def storage(db, action, **kw):
    try:
        return execute(db, action, **kw)
    except BookingError as e:
        raise BookingError({2:404, 27:22}.get(e.code, e.code))


MESSAGES = {22:'Invalid input. Check the ID, room, date and time range.',
            17:'That reservation ID already exists. Use a different ID.',
            404:'The workspace or reservation was not found.',
            409:'The form is stale or the room overlaps a booking. Review the refreshed list and try again.',
            35:'The workspace is busy. Wait briefly, refresh and try again.'}


def serve(db):
    storage(db, 'list')
    token = secrets.token_hex(16)
    esc = lambda value: html.escape(str(value), quote=True)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def endpoint(self):
            return '127.0.0.1:%d' % self.server.server_address[1]

        def reply(self, status, body):
            data = body.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def host_ok(self):
            return self.headers.get_all('Host') == [self.endpoint()]

        def page(self, message='', values=None, status=200):
            values = values or {}
            try:
                state = storage(db, 'list')
            except BookingError as e:
                self.reply(503, '<h1>Storage unavailable</h1><p>Error %s. Refresh before retrying.</p>' % e.code)
                return
            rev = state['revision']
            def hidden(name, value):
                return '<input type="hidden" name="%s" value="%s">' % (name, esc(value))
            common = hidden('rev', rev)+hidden('token', token)
            rows = ''
            for b in state['bookings']:
                clock = lambda n: '%02d:%02d' % divmod(n, 60)
                rows += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s–%s</td><td><form method="post" action="/action">%s%s%s<button>Cancel reservation %s</button></form></td></tr>' % (esc(b['id']), b['room'], dt.date.fromordinal(b['day']).isoformat(), clock(b['start']), clock(b['finish']), common, hidden('action','cancel'), hidden('id',b['id']), esc(b['id']))
            fields = ''
            for name, label, default, kind in [('id','Reservation ID','1','text'),('room','Room (1–16)','1','number'),('date','Date (YYYY-MM-DD)',dt.date.today().isoformat(),'text'),('start','Start (HH:MM)','09:00','text'),('end','End (HH:MM; 24:00 allowed)','10:00','text')]:
                fields += '<label for="%s">%s<input required id="%s" name="%s" type="%s" value="%s"></label>' % (name,label,name,name,kind,esc(values.get(name,default)))
            self.reply(status, '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Study Rooms</title><style>
:root{color-scheme:light dark;font-family:system-ui,sans-serif;background:#f3f6fa;color:#182536;background:light-dark(#f3f6fa,#141b26);color:light-dark(#182536,#e6edf6)}body{max-width:1050px;margin:auto;padding:24px}section{background:light-dark(white,#202c3b);padding:24px;border-radius:16px;margin:24px 0}h1{font-size:2.4rem}label{display:flex;flex-direction:column;gap:8px}input,button{font:inherit;padding:12px;border:1px solid #8291a5;border-radius:7px}button{cursor:pointer;background:light-dark(#184d96,#96c4ff);color:light-dark(white,#102033)}:focus-visible{outline:3px solid #e79c28;outline-offset:3px}.fields{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:20px}.scroll{overflow:auto}table{width:100%%;border-collapse:collapse}td,th{text-align:left;padding:12px;border-bottom:1px solid #8291a5}.notice{padding:16px;border-left:4px solid #e79c28}small{line-height:1.6}</style>
<body><h1>Study Rooms</h1><p>Find your focus. Reserve one of 16 rooms.</p><p class="notice" role="status">%s</p><section><h2>Reserve a room</h2><p>Same-day bookings; adjacent time slots are welcome. Use a unique positive numeric ID.</p><form action="/action" method="post">%s%s<div class="fields">%s</div><button>Reserve room</button></form></section><section><h2>Saved reservations</h2><p>Revision %s · %s reservations</p><div class="scroll"><table><thead><tr><th>ID</th><th>Room</th><th>Date</th><th>Time</th><th>Action</th></tr></thead><tbody>%s</tbody></table></div>%s</section><small>Local workspace only. Times are entered as local calendar values without timezone conversion. Refresh before retrying an uncertain storage result.</small></body></html>''' % (esc(message or 'Ready to reserve.'), common, hidden('action','reserve'), fields, rev, len(state['bookings']), rows, '' if rows else '<p>No reservations yet.</p>'))

        def do_GET(self):
            if not self.host_ok():
                self.reply(403, 'Invalid Host'); return
            if self.path != '/':
                self.reply(404, 'Not found'); return
            self.page()

        def do_POST(self):
            values = {}
            try:
                if not self.host_ok() or self.headers.get_all('Origin') != ['http://'+self.endpoint()]:
                    raise BookingError(22)
                if self.path != '/action' or self.headers.get_content_type() != 'application/x-www-form-urlencoded':
                    raise BookingError(22)
                lengths = self.headers.get_all('Content-Length')
                if not lengths or len(lengths)!=1 or self.headers.get('Transfer-Encoding'):
                    raise BookingError(22)
                size = number(lengths[0])
                if size > 16384: raise BookingError(22)
                raw = self.rfile.read(size).decode('utf-8', 'strict')
                if re.search(r'%(?![0-9a-fA-F]{2})',raw): raise BookingError(22)
                pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True, encoding='utf-8', errors='strict', max_num_fields=12)
                for key, value in pairs:
                    if key in values: raise BookingError(22)
                    values[key] = value
                action = values.get('action')
                expected = {'action','rev','id','token'} | ({'room','date','start','end'} if action=='reserve' else set())
                if action not in ('reserve','cancel') or set(values)!=expected or not secrets.compare_digest(values['token'].encode('utf-8'), token.encode('ascii')):
                    raise BookingError(22)
                operation(db, action, values)
                self.page('Reservation saved.' if action=='reserve' else 'Reservation cancelled.')
            except (BookingError, ValueError, UnicodeError) as e:
                code = getattr(e,'code',22)
                self.page(MESSAGES.get(code,'Storage error %s. Refresh before retrying.' % code), values, 400)

    server = HTTPServer(('127.0.0.1',0), Handler)
    print('http://127.0.0.1:%d/' % server.server_address[1], flush=True)
    server.serve_forever()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('duplicate key')
        result[key] = value
    return result


def mcp(db):
    storage(db,'list')
    def send(value):
        print(json.dumps(value, separators=(',',':')), flush=True)
    while True:
        line = sys.stdin.buffer.readline(65537)
        if not line: return
        if len(line)>65536:
            while line and not line.endswith(b'\n'):
                line = sys.stdin.buffer.readline(65537)
            send({'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Request too large'}})
            continue
        ident = None
        try:
            request = json.loads(line, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError, UnicodeError):
            send({'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Invalid JSON'}}); continue
        try:
            if not isinstance(request,dict) or request.get('jsonrpc')!='2.0' or set(request)-{'jsonrpc','id','method','params'}:
                raise ValueError()
            ident = request.get('id')
            if 'id' in request and (type(ident) not in (str,int) and ident is not None): raise ValueError()
            method = request.get('method')
            params = request.get('params',{})
            if not isinstance(method,str) or not isinstance(params,dict): raise ValueError()
            result = None
            if method=='initialize':
                if params.get('protocolVersion')!='2025-11-25' or set(params)-{'protocolVersion','capabilities','clientInfo'}: raise ValueError()
                result={'protocolVersion':'2025-11-25','capabilities':{'tools':{}},'serverInfo':{'name':'study-rooms','version':'1.0'}}
            elif method in ('ping','notifications/initialized'):
                if params: raise ValueError()
                result={}
            elif method=='tools/list':
                if params: raise ValueError()
                result={'tools':[{'name':'booking_list','description':'Read reservations in the selected workspace.','inputSchema':{'type':'object','properties':{},'additionalProperties':False}}]}
            elif method=='tools/call':
                if set(params)!={'name','arguments'} or params['name']!='booking_list' or type(params['arguments']) is not dict or params['arguments']!={}: raise ValueError()
                try:
                    state=storage(db,'list')
                    result={'content':[{'type':'text','text':'Revision %s; %s reservations.' % (state['revision'],len(state['bookings']))}],'structuredContent':state,'isError':False}
                except BookingError as e:
                    result={'content':[{'type':'text','text':'Storage error %s' % e.code}],'isError':True}
            else:
                if 'id' in request: send({'jsonrpc':'2.0','id':ident,'error':{'code':-32601,'message':'Unknown method'}})
                continue
            if 'id' in request: send({'jsonrpc':'2.0','id':ident,'result':result})
        except (ValueError,TypeError):
            if not isinstance(request,dict) or 'id' in request:
                send({'jsonrpc':'2.0','id':ident,'error':{'code':-32602,'message':'Invalid request or arguments'}})


def main(args):
    try:
        if len(args)<2: raise BookingError(22)
        action, db, *rest = args
        if action in ('init','list') and not rest:
            result=storage(db,action)
        elif action=='reserve' and len(rest)==6:
            result=operation(db,action,dict(zip(('rev','id','room','date','start','end'),rest)))
        elif action=='cancel' and len(rest)==2:
            result=operation(db,action,dict(zip(('rev','id'),rest)))
        elif action in ('serve','mcp') and not rest:
            (serve if action=='serve' else mcp)(db); return 0
        else: raise BookingError(22)
        print(json.dumps(result)); return 0
    except (BookingError,ValueError,OSError) as e:
        code=getattr(e,'code',getattr(e,'errno',22))
        print(json.dumps({'error':{2:404,27:22}.get(code,code)})); return 2

if __name__=='__main__':
    sys.exit(main(sys.argv[1:]))
