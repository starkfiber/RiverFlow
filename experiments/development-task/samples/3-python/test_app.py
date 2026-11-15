import http.client
import io
from unittest.mock import patch
import app
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlencode, urlsplit

ROOT=os.path.dirname(os.path.abspath(__file__))

class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT)
        self.db=os.path.join(self.temp.name,'rooms.db')
        self.cli('init',self.db)
    def tearDown(self): self.temp.cleanup()
    def cli(self,*args,error=None):
        p=subprocess.run([sys.executable,'app.py',*args],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(p.returncode,2 if error else 0,p.stderr+p.stdout)
        value=json.loads(p.stdout)
        if error: self.assertEqual(value,{'error':error})
        return value
    def test_cli(self):
        self.cli('init',self.db,error=17)
        self.cli('list',self.db+'missing',error=404)
        a=self.cli('reserve',self.db,'1','18446744073709551615','16','9999-12-31','23:00','24:00')
        self.assertEqual(a['revision'],2)
        self.cli('reserve',self.db,'1','2','1','2026-01-01','09:00','10:00',error=409)
        for ident,date,start,end in [('01','2026-01-01','09:00','10:00'),('2','2026-02-29','09:00','10:00'),('2','2026-01-01','24:00','24:00'),('2','2026-01-01','9:00','10:00')]:
            self.cli('reserve',self.db,'2',ident,'1',date,start,end,error=22)
        self.cli('reserve',self.db,'2','2','16','9999-12-31','23:30','24:00',error=409)
        b=self.cli('reserve',self.db,'2','2','16','9999-12-31','22:00','23:00')
        self.assertEqual([x['id'] for x in b['bookings']],['18446744073709551615','2'])
        self.cli('cancel',self.db,'3','3',error=404)
        c=self.cli('cancel',self.db,'3','2')
        self.assertEqual(c['revision'],4)
        self.assertEqual(self.cli('list',self.db),c)
    def test_capacity_and_locking(self):
        import sqlite3
        from booking_sdk import execute, BookingError
        for i in range(256):
            execute(self.db,'reserve',expected=i+1,id=str(i+1),room=1,day=i+1,start=0,finish=1)
        self.cli('reserve',self.db,'257','257','1','2026-01-01','09:00','10:00',error=22)
        con=sqlite3.connect(self.db,isolation_level=None)
        try:
            con.execute('BEGIN IMMEDIATE')
            self.cli('cancel',self.db,'257','1',error=35)
        finally:
            con.rollback();con.close()
        self.assertEqual(len(self.cli('list',self.db)['bookings']),256)
        self.cli('cancel',self.db,'257','1')
        self.cli('reserve',self.db,'258','257','1','2026-01-01','09:00','10:00')

    def test_mcp(self):
        requests=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'test','version':'1'}}}, {'jsonrpc':'2.0','method':'notifications/initialized'}, {'jsonrpc':'2.0','id':2,'method':'tools/list'}, {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'booking_list','arguments':{'path':'bad'}}}, {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'booking_list','arguments':{}}}, {'jsonrpc':'2.0','method':'tools/call','params':{'name':'booking_list','arguments':{}}}]
        data='{"id":1,"id":2}\n'+'x'*65537+'\n'+'\n'.join(json.dumps(r) for r in requests)+'\n'
        p=subprocess.run([sys.executable,'app.py','mcp',self.db],input=data,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        rows=[json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual(len(rows),6)
        self.assertEqual(rows[0]['error']['code'],-32700)
        self.assertEqual(rows[1]['error']['code'],-32700)
        self.assertEqual(rows[3]['result']['tools'][0]['name'],'booking_list')
        self.assertIn('error',rows[4])
        self.assertEqual(rows[5]['result']['structuredContent'],{'revision':1,'bookings':[]})
    def test_http_handler_in_memory(self):
        captured={}
        class FakeServer:
            server_address=('127.0.0.1',43210)
            def __init__(self,address,handler):
                if handler is not None: captured['handler']=handler
            def serve_forever(self): pass
        with patch.object(app,'HTTPServer',FakeServer), patch('sys.stdout',io.StringIO()):
            app.serve(self.db)
        class StreamSocket:
            def __init__(self,raw): self.input=io.BytesIO(raw);self.output=io.BytesIO()
            def makefile(self,*args): return self.input
            def sendall(self,data): self.output.write(data)
        def request(method,fields=None,extra='',host='127.0.0.1:43210',origin=True):
            body=urlencode(fields).encode() if fields is not None else b''
            headers='Host: '+host+'\r\n'
            if fields is not None:
                headers+='Content-Type: application/x-www-form-urlencoded\r\nContent-Length: '+str(len(body))+'\r\n'
                if origin: headers+='Origin: http://127.0.0.1:43210\r\n'
            raw=(method+' '+('/action' if method=='POST' else '/')+' HTTP/1.0\r\n'+headers+extra+'\r\n').encode()+body
            sock=StreamSocket(raw)
            captured['handler'](sock,('127.0.0.1',123),FakeServer(None,None))
            return sock.output.getvalue().decode()
        page=request('GET');self.assertIn('200 OK',page)
        token=re.search(r'name="token" value="([a-f0-9]+)"',page).group(1)
        fields=dict(action='reserve',rev='1',id='1',room='1',date='2026-11-15',start='09:00',end='10:00',token=token)
        self.assertIn('403',request('GET',host='evil'))
        self.assertIn('400',request('POST',fields,origin=False))
        self.assertIn('400',request('POST',dict(fields,token='wrong')))
        self.assertIn('400',request('POST',dict(fields,token='é')))
        self.assertEqual(self.cli('list',self.db)['revision'],1)
        self.assertIn('200 OK',request('POST',fields))
        page=request('POST',fields);self.assertIn('stale',page)
        self.assertIn('value="2026-11-15"',page)
        self.assertIn('400',request('POST',list(fields.items())+[('id','2')]))
        self.assertIn('400',request('POST',dict(fields,unknown='x')))
        self.assertEqual(self.cli('list',self.db)['revision'],2)
        self.assertIn('200 OK',request('POST',dict(action='cancel',rev='2',id='1',token=token)))
        self.assertEqual(self.cli('list',self.db)['bookings'],[])

    def test_browser(self):
        p=subprocess.Popen([sys.executable,'app.py','serve',self.db],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            url=p.stdout.readline().strip()
            if url == '{"error": 1}':
                self.skipTest('Sandbox denies loopback bind (EPERM); live HTTP not verified')
            parts=urlsplit(url)
            self.assertEqual(parts.hostname,'127.0.0.1')
            def request(method,path='/',fields=None,host=None,origin=True):
                c=http.client.HTTPConnection(parts.hostname,parts.port,timeout=3)
                headers={'Host':host or parts.netloc}
                if fields is not None:
                    headers['Content-Type']='application/x-www-form-urlencoded'
                    if origin: headers['Origin']=url.rstrip('/')
                body=urlencode(fields) if fields is not None else None
                c.request(method,path,body,headers); r=c.getresponse(); out=(r.status,r.read().decode()); c.close(); return out
            status,page=request('GET'); self.assertEqual(status,200)
            token=re.search(r'name="token" value="([a-f0-9]+)"',page).group(1)
            fields=dict(action='reserve',rev='1',id='1',room='1',date='2026-11-15',start='09:00',end='10:00',token=token)
            self.assertEqual(request('GET',host='evil.example')[0],403)
            self.assertEqual(request('POST','/action',fields,origin=False)[0],400)
            self.assertEqual(self.cli('list',self.db)['revision'],1)
            self.assertEqual(request('POST','/action',fields)[0],200)
            status,page=request('POST','/action',fields); self.assertEqual(status,400)
            self.assertIn('stale',page)
            self.assertIn('value="2026-11-15"',page)
            fields['rev']='2'; fields['id']='2'
            duplicate=list(fields.items())+[('id','3')]
            self.assertEqual(request('POST','/action',duplicate)[0],400)
            self.assertEqual(self.cli('list',self.db)['revision'],2)
            cancel=dict(action='cancel',rev='2',id='1',token=token)
            self.assertEqual(request('POST','/action',cancel)[0],200)
            self.assertEqual(self.cli('list',self.db)['bookings'],[])
        finally:
            p.terminate();p.wait(timeout=5)
            p.stdout.close();p.stderr.close()

if __name__=='__main__': unittest.main(verbosity=2)
