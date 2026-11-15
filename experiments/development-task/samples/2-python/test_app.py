"""Isolated standard-library integration checks; no external services."""
import http.client
import json
import os
from pathlib import Path
import re
import sqlite3
import socket
import io
from unittest.mock import patch
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent

class AppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.db = str(Path(self.tmp.name) / 'rooms.db')
    def tearDown(self):
        self.tmp.cleanup()
    def cli(self, *args, error=None):
        p = subprocess.run([sys.executable, str(ROOT/'app.py'), *map(str,args)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2 if error else 0, p.stderr + p.stdout)
        data = json.loads(p.stdout)
        if error: self.assertEqual(data, {'error':error})
        return data
    def reserve(self, rev, id='1', room='1', date='2026-11-15', start='09:00', end='10:00', error=None):
        return self.cli('reserve', self.db, rev, id, room, date, start, end, error=error)
    def test_domain_and_persistence(self):
        self.assertEqual(self.cli('init',self.db), {'revision':1,'bookings':[]})
        self.cli('init',self.db,error=17)
        self.reserve(1)
        self.reserve(1,'2',error=409)
        self.reserve(2,'2',start='09:59',error=409)
        self.reserve(2,'2',start='10:00',end='24:00')
        self.reserve(3,'3',room='2')
        self.reserve(4,'4',date='0001-01-01',start='00:00',end='00:01')
        self.reserve(5,'18446744073709551615',date='9999-12-31')
        self.assertEqual([b['id'] for b in self.cli('list',self.db)['bookings']],['1','2','3','4','18446744073709551615'])
        self.cli('cancel',self.db,6,'3')
        self.cli('cancel',self.db,7,'3',error=404)
        self.assertEqual(self.cli('list',self.db)['revision'],7)
    def test_invalid_and_busy(self):
        self.cli('list',self.db,error=404)
        self.cli('init',self.db)
        for changes in ({'id':'01'},{'id':'0'},{'id':'18446744073709551616'},{'room':'17'},{'date':'2026-02-29'},{'date':'2026-1-01'},{'start':'24:00'},{'start':'9:00'},{'end':'09:00'},{'end':'24:01'}):
            self.reserve(1,error=22,**changes)
        c = sqlite3.connect(self.db)
        c.execute('BEGIN IMMEDIATE')
        try: self.reserve(1,error=35)
        finally: c.rollback();c.close()
        self.assertEqual(self.cli('list',self.db)['revision'],1)
    def test_capacity(self):
        self.cli('init',self.db)
        from booking_sdk import execute
        for i in range(256):
            execute(self.db,'reserve',expected=i+1,id=str(i+1),room=1,day=i+1,start=0,finish=1)
        self.reserve(257,'257',error=22)
        self.assertEqual(len(self.cli('list',self.db)['bookings']),256)
    def test_mcp_recovery(self):
        self.cli('init',self.db)
        requests = [
          '{bad', '{"jsonrpc":"2.0","id":1,"id":2,"method":"ping"}',
          json.dumps({'jsonrpc':'2.0','id':3,'method':'initialize','params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'test','version':'1'}}}),
          json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'}),
          json.dumps({'jsonrpc':'2.0','id':4,'method':'tools/list'}),
          json.dumps({'jsonrpc':'2.0','id':5,'method':'tools/call','params':{'name':'booking_list','arguments':{'path':'other'}}}),
          'x'*65537,
          json.dumps({'jsonrpc':'2.0','id':6,'method':'tools/call','params':{'name':'booking_list','arguments':{}}}),
          json.dumps({'jsonrpc':'2.0','id':7,'method':'ping'})]
        p = subprocess.run([sys.executable,str(ROOT/'app.py'),'mcp',self.db],input='\n'.join(requests)+'\n',capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        out = [json.loads(l) for l in p.stdout.splitlines()]
        self.assertEqual(len(out),8)
        self.assertTrue(out[4]['result']['isError'])
        self.assertEqual(out[6]['result']['structuredContent'],{'revision':1,'bookings':[]})
        self.assertEqual(out[7]['result'],{})
    def test_http_handler_without_socket(self):
        import app
        self.cli('init',self.db)
        captured={}
        class FakeServer:
            server_address=('127.0.0.1',43210)
            def __init__(self,address,handler):
                if handler is not None: captured['handler']=handler
            def serve_forever(self): pass
            def server_close(self): pass
        with patch.object(app,'HTTPServer',FakeServer), patch('sys.stdout',io.StringIO()):
            app.serve(self.db)
        class Connection:
            def __init__(self, raw):
                self.input=io.BytesIO(raw);self.output=io.BytesIO()
            def makefile(self,mode,*args): return self.input if mode=='rb' else self.output
            def sendall(self,data): self.output.write(data)
        def request(method='GET', form=None, origin='http://127.0.0.1:43210', host='127.0.0.1:43210'):
            body=(form or '').encode()
            headers=f'{method} {"/action" if method=="POST" else "/"} HTTP/1.0\r\nHost: {host}\r\n'
            if method=='POST': headers+=f'Origin: {origin}\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {len(body)}\r\n'
            conn=Connection((headers+'\r\n').encode()+body)
            captured['handler'](conn,('127.0.0.1',1234),FakeServer(None,None))
            return conn.output.getvalue().decode()
        page=request()
        self.assertIn('200 OK',page)
        token=re.search(r'name="token" value="([a-f0-9]+)"',page)[1]
        form=dict(action='reserve',rev='1',id='1',room='1',date='2026-11-15',start='09:00',end='10:00',token=token)
        self.assertIn('403 Forbidden',request('POST',urlencode(form),origin='http://evil.test'))
        self.assertIn('403 Forbidden',request(host='evil.test'))
        self.assertIn('400 Bad Request',request('POST',urlencode(form)+'&id=2'))
        self.assertIn('400 Bad Request',request('POST',urlencode(dict(form,token='bad'))))
        self.assertEqual(self.cli('list',self.db)['revision'],1)
        self.assertIn('200 OK',request('POST',urlencode(form)))
        stale=request('POST',urlencode(dict(form,id='2')))
        self.assertIn('409 Conflict',stale)
        self.assertIn('Revision 2',stale)
        self.assertIn('name="id" value="2"',stale)
        self.assertIn('200 OK',request('POST',urlencode(dict(action='cancel',rev='2',id='1',token=token))))
        self.assertEqual(self.cli('list',self.db),{'revision':3,'bookings':[]})

    def test_browser(self):
        probe=socket.socket()
        try:
            probe.bind(('127.0.0.1',0))
        except PermissionError as e:
            self.skipTest('Environment denies loopback bind: ' + str(e))
        finally:
            probe.close()
        self.cli('init',self.db)
        p = subprocess.Popen([sys.executable,str(ROOT/'app.py'),'serve',self.db],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            url=p.stdout.readline().strip()
            self.assertRegex(url,r'^http://127\.0\.0\.1:[0-9]+/$')
            port=int(url.split(':')[2].strip('/'))
            def request(method='GET',body=None,origin=None,host=None):
                c=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
                headers={}
                if method=='POST': headers={'Content-Type':'application/x-www-form-urlencoded','Origin':origin or url.rstrip('/')}
                if host: headers['Host']=host
                c.request(method,'/action' if method=='POST' else '/',body,headers)
                r=c.getresponse();result=(r.status,r.read().decode());c.close();return result
            status,page=request()
            self.assertEqual(status,200)
            token=re.search(r'name="token" value="([a-f0-9]+)"',page)[1]
            form=dict(action='reserve',rev='1',id='1',room='1',date='2026-11-15',start='09:00',end='10:00',token=token)
            self.assertEqual(request('POST',urlencode(form),origin='http://evil.test')[0],403)
            self.assertEqual(request(host='evil.test')[0],403)
            self.assertEqual(request('POST',urlencode(form)+'&id=2')[0],400)
            bad=dict(form,token='invalid')
            self.assertEqual(request('POST',urlencode(bad))[0],400)
            self.assertEqual(self.cli('list',self.db)['revision'],1)
            self.assertEqual(request('POST',urlencode(form))[0],200)
            status,page=request('POST',urlencode(dict(form,id='2')))
            self.assertEqual(status,409)
            self.assertIn('value="2"',page)
            self.assertIn('Revision 2',page)
            cancel=dict(action='cancel',rev='2',id='1',token=token)
            self.assertEqual(request('POST',urlencode(cancel))[0],200)
            self.assertEqual(self.cli('list',self.db),{'revision':3,'bookings':[]})
        finally:
            p.terminate();p.communicate(timeout=5)

if __name__=='__main__': unittest.main(verbosity=2)
