"""Read-only provider DNS/TCP/TLS probe; never loads credentials or sends HTTP."""
import datetime,json,os,socket,ssl,time,urllib.request
host='api.deepseek.com';start=time.monotonic()
result={'schema':'rf2.provider.connectivity-probe.v1','timeUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'targetHost':host,'port':443,'proxiesPresent':{k:bool(os.environ.get(k))for k in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','http_proxy','https_proxy','all_proxy','no_proxy']},'urllibProxySchemes':sorted(urllib.request.getproxies()),'credentialFilesRead':False,'authenticatedRequests':0,'httpRequests':0,'certificateVerification':True,'perSocketTimeoutSeconds':5,'maxAddresses':3}
try:
    rows=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
    addresses=[]
    for family,kind,proto,canon,address in rows:
        entry=(family,address[0])
        if entry not in addresses:addresses.append(entry)
    result['dnsAnswers']=[{'family':family.name,'address':ip}for family,ip in addresses]
    result['connections']=[]
    for family,ip in addresses[:3]:
        begin=time.monotonic();row={'family':family.name,'address':ip,'tcpConnected':False,'tlsVerified':False}
        try:
            with socket.socket(family,socket.SOCK_STREAM)as sock:
                sock.settimeout(5);sock.connect((ip,443));row['tcpConnected']=True;row['tcpSeconds']=round(time.monotonic()-begin,6)
                with ssl.create_default_context().wrap_socket(sock,server_hostname=host)as tls:
                    row['tlsVerified']=True;row['tlsVersion']=tls.version();row['cipher']=tls.cipher()[0]
        except Exception as error:row.update(errorType=type(error).__name__,errno=getattr(error,'errno',None))
        row['elapsedSeconds']=round(time.monotonic()-begin,6);result['connections'].append(row)
except Exception as error:result.update(errorType=type(error).__name__,errno=getattr(error,'errno',None))
result['elapsedSeconds']=round(time.monotonic()-start,6)
print(json.dumps(result,indent=2))
