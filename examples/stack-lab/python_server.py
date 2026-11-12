"""Matched single-worker reference server. Local/disposable lab only."""
import argparse,http.server,socketserver,socket,json,platform,pathlib
p=argparse.ArgumentParser();p.add_argument('--port',type=int,required=True);p.add_argument('--bind',default='127.0.0.1');p.add_argument('--deployment',required=True);p.add_argument('--site',required=True);a=p.parse_args();SITE=pathlib.Path(a.site).read_bytes()
INFO={'backend':'Python / '+a.deployment,'language':'CPython','version':platform.python_version(),'system':platform.system(),'architecture':platform.machine(),'workers':1,'maxIterations':100000}
def compute(n):
 state=1;total=0
 for _ in range(n):
  state=(state*1664525+1013904223)&0xffffffff;total+=state
 return {'iterations':n,'checksum':total,'state':state}
class Handler(http.server.BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1'
 def log_message(self,*args):pass
 def handle(self):
  self.connection.settimeout(2);self.connection.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
  try:super().handle()
  except (TimeoutError,ConnectionError):pass
 def send(self,status,body,kind='application/json'):
  if isinstance(body,dict):body=(json.dumps(body,separators=(',',':'))+'\n').encode()
  names={200:'OK',400:'Bad Request',404:'Not Found',405:'Method Not Allowed',414:'URI Too Long',431:'Request Header Fields Too Large'}
  head=f'HTTP/1.1 {status} {names[status]}\r\nContent-Type: {kind}\r\nContent-Length: {len(body)}\r\nConnection: close\r\nCache-Control: no-store\r\n\r\n'.encode();self.wfile.write(head+body);self.close_connection=True
 def do_GET(self):
  if len(self.path)>256:return self.send(414,{'error':'path-limit'})
  if not self.raw_requestline.endswith(b'\r\n')or any(ord(c)<33 or ord(c)>126 for c in self.path):return self.send(400,{'error':'request'})
  content=self.headers.get_all('Content-Length',[]);hosts=self.headers.get_all('Host',[])
  if len(content)>1 or (content and content[0].strip()!='0')or self.headers.get('Transfer-Encoding')is not None or len(hosts)>1 or(self.request_version=='HTTP/1.1'and len(hosts)!=1):return self.send(400,{'error':'framing'})
  if self.path=='/':return self.send(200,SITE,'text/html; charset=utf-8')
  if self.path=='/health':return self.send(200,{'ok':True})
  if self.path=='/api/info':return self.send(200,INFO)
  prefix='/api/compute?iterations='
  if self.path.startswith(prefix):
   v=self.path[len(prefix):]
   if not v.isascii()or not v.isdigit()or len(v)>6 or(len(v)>1 and v[0]=='0')or int(v)>100000:return self.send(400,{'error':'iterations'})
   return self.send(200,compute(int(v)))
  return self.send(404,{'error':'route'})
 def do_POST(self):self.send(405,{'error':'method'})
 def do_PUT(self):self.send(405,{'error':'method'})
class Server(socketserver.TCPServer):allow_reuse_address=True;request_queue_size=128
with Server((a.bind,a.port),Handler)as s:s.serve_forever(poll_interval=.05)
