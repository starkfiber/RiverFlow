"""All admitted DHCP padding lengths and single-byte corruption positions.

Checks both original/durable parsers, both implementations and both compiler modes.
Exact metadata is independent here; it is not a baseline/candidate agreement only.
"""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess
H=Path(__file__).resolve().parent
C=Path('/Users/ik/Projects/RiverFlow/artifacts/sdk-050-builder-final/program')
ENTRY='''profile RF2_SYSTEM_A64_V1
use "dhcp.flow"
fn exact(fd,p,n)
 let i=0
 while i<n
  let got=read(fd,p+i,n-i)
  if any(got==0,got>>63)
   return 0
  end
  set i=i+got
 end
 return 1
end
fn main(argc,argv)
 let header=buffer("header",2)
 let input=buffer("input",576)
 let output=buffer("output",80)
 let p=DhcpPacket()
 let m=DhcpMeta()
 let count=0
 while count<4096
  let got=read(0,header,1)
  if got==0
   return 0
  end
  if any(got!=1,exact(0,header+1,1)==0)
   return 2
  end
  let n=load8(header)+load8(header+1)*256
  if n>576
   return 2
  end
  if exact(0,input,n)==0
   return 2
  end
  let j=0
  while j<n
   set p[j]=load8(input+j)
   set j=j+1
  end
  let code=dhcp_parse(p,n,m)
  do store64(output,code)
  set j=0
  while j<9
   do store64(output+8+j*8,m[j])
   set j=j+1
  end
  if write(1,output,80)!=80
   return 3
  end
  set count=count+1
 end
 return 0
end
'''
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();d=a.out.resolve();d.mkdir(parents=True,exist_ok=False)
    assert sha(C)=='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
    t=Path(os.environ['TMPDIR']).resolve();assert '/Volumes/Mac Work Cache/'in str(t);binroot=t/('net-padding-'+hashlib.sha256(str(d).encode()).hexdigest()[:12]);binroot.mkdir()
    base=bytearray(244);base[:3]=b'\1\1\6';base[7]=1;base[28:34]=bytes.fromhex('020000000001');base[236:240]=bytes.fromhex('63825363');base[240:]=b'\x35\1\1\xff'
    rows=[]
    for n in range(244,577):
        b=bytes(base).ljust(n,b'\0');rows.append((n,b,0))
        for pos in range(244,n):
            bad=bytearray(b);bad[pos]=1+pos%255;rows.append((n,bytes(bad),10))
    result={'schema':'rf2.net.padding.v2','casesPerProbe':len(rows),'checks':[],'mutations':[],'oracle':'Direct expected code and nine LEu64 metadata fields from fixed explicitly encoded DHCP client1/kind1/xid1 fixture; all lengths244..576 and every individual nonzero byte afterEND'}
    def build(family,variant,mode,mutant=False):
        sd=d/'source'/(family+'-'+variant+'-'+mode+('-bad'if mutant else''));sd.mkdir(parents=True)
        text=(H/variant/family/'dhcp.flow').read_text()
        if mutant:assert text.count('if p[i]!=0')==1;text=text.replace('if p[i]!=0','if p[i]==999',1)
        (sd/'dhcp.flow').write_text(text);(sd/'probe.flow').write_text(ENTRY)
        binary=binroot/sd.name;p=subprocess.run([str(C),str(sd/'probe.flow'),str(binary),'--compact']+(['--opt']if mode=='opt'else[]),capture_output=True,timeout=30);(sd/'build.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0,p.stderr
        subprocess.run(['codesign','-s','-',str(binary)],capture_output=True,check=True);return binary
    def packed(batch):return b''.join(struct.pack('<H',n)+b for n,b,_ in batch)
    def expected(batch):return b''.join(struct.pack('<10Q',code,0x020000000001,1,0,0,0,1,0,0,0)for _,_,code in batch)
    for family in ['dhcp','dhcp-durable']:
      for variant in ['baseline','candidate']:
       for mode in ['plain','opt']:
        binary=build(family,variant,mode);obs=hashlib.sha256();want_digest=hashlib.sha256()
        for i in range(0,len(rows),4000):
            batch=rows[i:i+4000];want=expected(batch);p=subprocess.run([str(binary)],input=packed(batch),capture_output=True,timeout=15)
            if p.returncode!=0 or p.stdout!=want:
                (d/'FAILED-INPUT.bin').write_bytes(packed(batch));(d/'FAILED-ACTUAL.bin').write_bytes(p.stdout);(d/'FAILED-EXPECTED.bin').write_bytes(want);raise AssertionError((family,variant,mode,i,p.returncode))
            obs.update(p.stdout);want_digest.update(want)
        result['checks'].append({'family':family,'variant':variant,'mode':mode,'cases':len(rows),'passed':True,'actualSHA256':obs.hexdigest(),'expectedSHA256':want_digest.hexdigest(),'binarySHA256':sha(binary)})
        print(family,variant,mode,len(rows),'padding+metadata controls pass',flush=True)
      for mode in ['plain','opt']:
        binary=build(family,'candidate',mode,True);batch=[(245,bytes(base)+b'\1',10)];p=subprocess.run([str(binary)],input=packed(batch),capture_output=True,timeout=3);assert p.returncode==0 and p.stdout!=expected(batch)
        result['mutations'].append({'family':family,'mode':mode,'tailValidationMutantDetected':True})
    result['allPassed']=True;(d/'RESULTS.json').write_text(json.dumps(result,indent=2));print('All padding/metadata and negative controls passed')
if __name__=='__main__':main()
