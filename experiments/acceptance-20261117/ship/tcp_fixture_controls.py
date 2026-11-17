"""Independent admission controls for the exact expanded TCP refresh fixture.

No QEMU, network or guest mutation. Positive admission stops at first peer write.
"""
from pathlib import Path
import hashlib,json,struct,textwrap
HERE=Path(__file__).resolve().parent
class ReachedReply(Exception):pass
class Peer:
    def sendall(self,data):raise ReachedReply()
def main():
    wanted=bytearray(60);wanted[12:14]=b'\x08\x00';wanted[30:34]=bytes([198,51,100,9]);wanted=bytes(wanted)
    probe=bytearray(60);probe[12:14]=b'\x08\x06';probe[38:42]=wanted[30:34];probe=bytes(probe)
    old=bytearray(256);struct.pack_into('<Q',old,0,2);old[8:12]=wanted[30:34];struct.pack_into('<Q',old,24,100)
    fragment=textwrap.dedent((HERE/'tcp_neighbor.py.in').read_text())+'\nassert actual==wanted\n'
    rows=[]
    for label,actual,now,neighbor,admitted in [
        ('expired-exact-probe',probe,131,bytes(old),True),
        ('premature-probe',probe,129,bytes(old),False),
        ('backward-clock',probe,99,bytes(old),False),
        ('wrong-probe-target',probe[:38]+bytes([198,51,100,8])+probe[42:],131,bytes(old),False),
        ('wrong-source-byte',bytes([1])+probe[1:],131,bytes(old),False),
        ('unrelated-ipv4',probe[:12]+b'\x08\x00'+probe[14:],131,bytes(old),False),
        ('no-previous-resolved-neighbor',probe,131,bytes(256),False),
    ]:
        env=dict(actual=actual,wanted=wanted,slot=0,label=label,neighbor_before=neighbor,wire=[],peers=[Peer(),Peer()],struct=struct,json=json,arp_probe=lambda hop:probe,arp_reply=lambda hop:b'fixture-reply',memory=lambda at,size:(now if at==0x53f18 else 30).to_bytes(8,'little'))
        observed=False
        try:exec(compile(fragment,str(HERE/'tcp_neighbor.py.in'),'exec'),env)
        except ReachedReply:observed=True
        except AssertionError:pass
        else:raise AssertionError((label,'unexpected fixture completion'))
        assert observed==admitted,(label,observed,admitted)
        rows.append({'label':label,'admitted':observed,'expected':admitted,'passed':True})
    return {'schema':'rf2ship.tcp-fixture-controls.v1','fixtureSHA256':hashlib.sha256((HERE/'tcp_neighbor.py.in').read_bytes()).hexdigest(),'passed':True,'cases':rows,'scope':'Independent fixture admission controls; not guest/network execution'}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.write_text(json.dumps(main(),indent=2)+'\n')
