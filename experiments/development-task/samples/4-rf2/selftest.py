"""Local black-box test harness. Application runtime is entirely RF2."""
import socket, datetime, fcntl, http.client, json, os, pathlib, re, subprocess, tempfile, urllib.parse
ROOT = pathlib.Path(__file__).resolve().parent
APP = str(ROOT / 'app')
checks = 0

def check(condition, label):
    global checks
    assert condition, label
    checks += 1
    print('PASS', label)

def run(*args, error=None):
    p = subprocess.run([APP, *map(str,args)], capture_output=True, text=True)
    data = json.loads(p.stdout)
    assert p.returncode == (0 if error is None else 2), (args,p.returncode,p.stdout,p.stderr)
    if error is not None:
        assert data == {'error':error}, (args,data)
    return data

with tempfile.TemporaryDirectory(dir=ROOT / 'artifacts') as folder:
    db = str(pathlib.Path(folder)/'rooms.db')
    check(run('init',db)['revision']==1,'exclusive initialization')
    run('init',db,error=17); check(True,'existing path refused')
    run('list',db+'missing',error=404); check(True,'missing workspace refused')
    def reserve(rev, ident, room, day, start, end, error=None):
        return run('reserve',db,rev,ident,room,day,start,end,error=error)
    s=reserve(1,'18446744073709551615',1,'0001-01-01','00:00','01:00')
    check(s['bookings'][0]['day']==1,'maximum u64 ID and first Gregorian day')
    reserve(2,2,1,'0001-01-01','00:30','01:30',error=409)
    check(run('list',db)==s,'overlap preserves revision and state')
    s=reserve(2,2,1,'0001-01-01','01:00','02:00')
    check(len(s['bookings'])==2,'adjacent intervals allowed')
    s=reserve(3,3,2,'0001-01-01','00:00','01:00')
    s=reserve(4,4,1,'9999-12-31','23:59','24:00')
    check(s['bookings'][-1]['day']==3652059,'independent rooms and last Gregorian day with end 24:00')
    reserve(4,5,1,'2024-02-29','12:00','13:00',error=409)
    run('cancel',db,4,2,error=409)
    check(run('list',db)==s,'stale reserve and cancel preserve state')
    for ident,room,day,start,end in [
        ('01',1,'2024-02-29','12:00','13:00'),('0',1,'2024-02-29','12:00','13:00'),
        ('18446744073709551616',1,'2024-02-29','12:00','13:00'),
        ('5',17,'2024-02-29','12:00','13:00'),('5',0,'2024-02-29','12:00','13:00'),
        ('5',1,'1900-02-29','12:00','13:00'),('5',1,'0000-01-01','12:00','13:00'),
        ('5',1,'2024-2-29','12:00','13:00'),('5',1,'2024-02-29','24:00','24:00'),
        ('5',1,'2024-02-29','9:00','10:00'),('5',1,'2024-02-29','10:00','10:00'),
        ('5',1,'2024-02-29','12:00','11:00')]:
        reserve(5,ident,room,day,start,end,error=22)
    check(run('list',db)==s,'12 invalid ID/room/date/time cases preserve state')
    reserve(5,2,3,'2024-02-29','12:00','13:00',error=17)
    run('cancel',db,5,99,error=404)
    s=run('cancel',db,5,2)
    check([b['id'] for b in s['bookings']]==['18446744073709551615','3','4'],'exact cancellation preserves insertion order')
    with open(db,'rb') as locked:
        fcntl.flock(locked,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run('list',db,error=35)
    check(True,'SDK lock contention refused')
    requests=[
        {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'selftest','version':'1'}}},
        {'jsonrpc':'2.0','method':'notifications/initialized'},
        {'jsonrpc':'2.0','id':2,'method':'tools/list'},
        {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'booking_list','arguments':{}}},
        {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'booking_list','arguments':{'path':'x'}}},
        {'jsonrpc':'2.0','id':5,'method':'write'},
    ]
    lines=[json.dumps(x) for x in requests]+['{"jsonrpc":"2.0","id":6,"method":"ping","m\\u0065thod":"ping"}', '{bad', 'x'*65537,json.dumps({'jsonrpc':'2.0','id':7,'method':'ping'})]
    p=subprocess.run([APP,'mcp',db],input='\n'.join(lines)+'\n',capture_output=True,text=True)
    replies=[json.loads(line) for line in p.stdout.splitlines()]
    check(p.returncode==0 and len(replies)==9,'MCP newline framing and notification silence')
    check(replies[1]['result']['tools'][0]['name']=='booking_list' and len(replies[1]['result']['tools'])==1,'exactly one read-only tool')
    check(replies[2]['result']['structuredContent']==s,'MCP selected workspace state')
    check(replies[3]['result']['isError'] and 'error' in replies[4],'MCP arguments and unknown method refused')
    check(all('error' in r for r in replies[5:8]) and replies[-1]['result']=={},'duplicate decoded keys, malformed and oversized lines recover')
    additional=[
        '[1,2,3]',
        '{"jsonrpc":"2.0","id":"escaped\\nID","method":"ping"}',
        json.dumps({'jsonrpc':'2.0','id':8,'method':'tools/call','params':{'name':'booking_list'}}),
        json.dumps({'jsonrpc':'2.0','id':9,'method':'tools/call','params':{'name':'booking_list','arguments':None}}),
        json.dumps({'jsonrpc':'2.0','method':'tools/call','params':{'name':'reserve','arguments':{}}}),
        json.dumps({'jsonrpc':'2.0','id':10,'method':'initialize','params':{'protocolVersion':'2025-11-25','path':'x'}}),
        json.dumps({'jsonrpc':'2.0','id':11,'method':'ping'})]
    p=subprocess.run([APP,'mcp',db],input='\n'.join(additional)+'\n',capture_output=True,text=True)
    more=[json.loads(line) for line in p.stdout.splitlines()]
    check(p.returncode==0 and len(more)==6 and 'error' in more[0] and more[1]['id']=='escaped\nID' and more[2]['result']['isError'] and more[3]['result']['isError'] and 'error' in more[4] and more[-1]['result']=={} and run('list',db)==s,'MCP root, escaped IDs, missing/null arguments, notification and initialize admission')
    origin='http://127.0.0.1:12345'
    print('LIMITATION loopback bind denied by sandbox; HTTP checked through inherited local socket pairs')
    def http(method,path='/',body=None,headers=None):
        client, child = socket.socketpair()
        headers=dict(headers or {})
        headers.setdefault('Host','127.0.0.1:12345')
        payload=(body or '').encode()
        if method=='POST': headers['Content-Length']=str(len(payload))
        request=(method+' '+path+' HTTP/1.1\r\n'+''.join(k+': '+v+'\r\n' for k,v in headers.items())+'\r\n').encode()+payload
        p=subprocess.Popen([str(ROOT/'http-selftest'),db,str(child.fileno())],pass_fds=(child.fileno(),),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        child.close()
        client.settimeout(5)
        client.sendall(request)
        response=b''
        while True:
            part=client.recv(65536)
            if not part: break
            response+=part
        client.close()
        output,errors=p.communicate(timeout=5)
        assert p.returncode==0,(output,errors)
        head, content=response.split(b'\r\n\r\n',1)
        return int(head.split(b' ')[1]),content.decode()
    status,page=http('GET')
    check(status==200 and all(re.search(r'name="?'+x+r'"?(?: |>)',page) for x in ['room','date','start','end']),'browser visible labelled reservation inputs')
    token=re.search(r'name=token value="([0-9a-f]{32})"',page)[1]
    rev=run('list',db)['revision']
    fields=dict(action='reserve',rev=str(rev),id='5',room='3',date='2024-02-29',start='12:00',end='13:00',token=token)
    def post(fields,extra='',origin_value=origin):
        return http('POST','/action',urllib.parse.urlencode(fields)+extra,{'Content-Type':'application/x-www-form-urlencoded','Origin':origin_value})
    before=run('list',db)
    check(http('GET',headers={'Host':'evil.invalid'})[0]==400,'wrong Host refused')
    check(post(fields,origin_value='http://evil.invalid')[0]==400,'wrong Origin refused')
    bad=dict(fields,token='0'*32)
    check(post(bad)[0]==400,'wrong CSRF token refused')
    check(post(fields,'&room=4')[0]==400 and post(fields,'&extra=x')[0]==400,'duplicate and unknown form fields refused')
    check(run('list',db)==before,'rejected HTTP requests preserve saved state')
    status,page=post(fields)
    s=run('list',db)
    check(status==200 and 'Saved to your workspace' in page and s['revision']==rev+1,'browser reserve uses shared durable engine')
    stale=dict(fields,id='6',room='4')
    status,page=post(stale)
    check('could not be saved' in page and 'value="2024-02-29"' in page and 'value="12:00"' in page and f'name=rev value="{rev+1}"' in page,'stale form refreshes revision and retains reserve inputs')
    cancel=dict(action='cancel',rev=str(rev+1),id='5',token=token)
    status,page=post(cancel)
    check(status==200 and all(b['id']!='5' for b in run('list',db)['bookings']),'browser explicit cancellation')
    capacity_db=str(pathlib.Path(folder)/'capacity.db')
    run('init',capacity_db)
    for i in range(1,257):
        day=(datetime.date(2024,1,1)+datetime.timedelta(days=i)).isoformat()
        state=run('reserve',capacity_db,i,i,1,day,'09:00','10:00')
    check(len(state['bookings'])==256 and state['revision']==257,'256 durable current reservations supported')
    run('reserve',capacity_db,257,257,2,'2024-01-01','09:00','10:00',error=22)
    check(run('list',capacity_db)==state,'reservation 257 refused without mutation')
    # Two fresh CLI processes compete on the same expected revision.
    race_db=str(pathlib.Path(folder)/'race.db')
    run('init',race_db)
    racing=[subprocess.Popen([APP,'reserve',race_db,'1',str(i),'1','2024-02-29','09:00','10:00'],stdout=subprocess.PIPE,text=True) for i in (1,2)]
    results=[(p.communicate()[0],p.returncode) for p in racing]
    check(sum(code==0 for _,code in results)==1 and len(run('list',race_db)['bookings'])==1,'concurrent writers cannot both save the same revision')
    corrupt=pathlib.Path(folder)/'corrupt.db'; corrupt.write_bytes(b'not a journal')
    p=subprocess.run([APP,'list',str(corrupt)],capture_output=True,text=True)
    check(p.returncode==2 and 'error' in json.loads(p.stdout),'corrupt storage remains failure')
print(f'{checks} checks passed')
