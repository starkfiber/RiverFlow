"""Exercise exact neighbor-expiry handling using host delay, unchanged guest lifetime."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--prepared-root',type=Path,required=True);p.add_argument('--image',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert os.environ.get('TMPDIR','').startswith('/Volumes/Mac Work Cache/')
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    source=a.prepared_root.resolve()/'candidate-normal';s=(source/'tcp_verify.py').read_text()
    anchor="   check(0,tcp(0,seq=5,ack=9006,flags=16),label='dataACK-exact')"
    assert s.count(anchor)==1
    delay="""   # Delay only the host peer, after inbound data refreshed TCP state.
   neighbors=memory(0x55100,256);entry=[neighbors[i:i+64]for i in range(0,256,64)if neighbors[i+8:i+12]==bytes([198,51,100,9])and int.from_bytes(neighbors[i:i+8],'little')==2]
   assert len(entry)==1
   stamp=int.from_bytes(entry[0][24:32],'little');ttl=int.from_bytes(memory(0x5a68,8),'little');now=int.from_bytes(memory(0x53f18,8),'little');period=int.from_bytes(memory(0x5a58,8),'little')
   pause=max(0,stamp+ttl-now)*period/1e15+0.08;assert 0<pause<3.1
   (D/('HOST-DELAY-'+machine+'.json')).write_text(json.dumps({'seconds':pause,'timestamp':stamp,'lifetime':ttl,'lastGuestNow':now,'periodFemtoseconds':period,'guestLifetimeUnchanged':True},indent=2)+'\\n')
   time.sleep(pause)
"""
    s=s.replace(anchor,delay+anchor,1)
    # The prepared script selects evidence through RF2_SHIP_EVIDENCE.
    fixture=HERE/('loss-source-'+out.name);fixture.mkdir();script=fixture/'tcp_verify.py';script.write_text(s)
    for n in ['wire_peer.py','route_oracle.py']:(fixture/n).write_bytes((source/n).read_bytes())
    (out/'rf2ship.img').symlink_to(a.image.resolve());env=os.environ.copy();env.update(RF2_SHIP_EVIDENCE=str(out),PYTHONDONTWRITEBYTECODE='1')
    with(out/'RUN.log').open('wb')as log:q=subprocess.run([sys.executable,'-B',str(script)],cwd=ROOT,env=env,stdout=log,stderr=log,timeout=120)
    rows=[json.loads((out/('TCP-NEIGHBOR-REFRESH-'+model+'.json')).read_text())for model in ['pc','q35']]if q.returncode==0 else[]
    assert q.returncode==0 and all(rows),'Inspect preserved run log; both models must exercise renewal'
    result={'schema':'rf2ship.actual-tcp-neighbor-expiry.v1','passed':True,'scriptSHA256':sha(script),'fixtureSHA256':sha(HERE/'tcp_neighbor.py.in'),'guestImageSHA256':sha(a.image),'models':['pc','q35'],'completed':json.loads((out/'TCP-VERIFICATION.json').read_text())['completed'],'refreshCount':[len(x)for x in rows],'scope':'Actual unchanged guest; host peer delayed to exercise legitimate neighbor expiry'}
    (out/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
