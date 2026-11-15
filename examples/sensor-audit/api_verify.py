"""Direct native library refusal/state-preservation checks in both modes."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
C=Path(sys.argv[1]).resolve();D=Path(tempfile.mkdtemp(prefix='sensor-api-',dir=ROOT/'artifacts'));shutil.copytree(HERE/'lib',D/'lib');checks=[]
for opt in(False,True):
    for name,ident,stamp,temp,low,high,count,oldstamp,error in[
        ('zero-id',0,2,100000,100000,150000,1,1,22),
        ('high-id',33,2,100000,100000,150000,1,1,22),
        ('bad-temperature',1,2,300001,100000,150000,1,1,22),
        ('reversed-limits',1,2,100000,200000,100000,1,1,22),
        ('high-limit',1,2,100000,100000,300001,1,1,22),
        ('row-cap',1,2,100000,100000,150000,4096,1,27),
        ('duplicate-time',1,1,100000,100000,150000,1,1,22),
        ('reversed-time',1,0,100000,100000,150000,1,1,22),
    ]:
        source='''profile RF2_SYSTEM_A64_V1
use "lib/sensor.flow"
fn main(argc,argv)
 let states=SensorStates()
 let sample=SensorSample(IDENT,STAMP,TEMP)
 let limits=SensorLimits(LOW,HIGH)
 let observed=0
 let i=0
 set states[0]=COUNT
 set states[1]=100
 set states[2]=OLDSTAMP
 set states[3]=80000
 set states[4]=120000
 set states[5]=900000
 set states[6]=2
 set states[7]=3
 handle sensor_add(states,sample,limits)
 ok added
  return 200
 err cause
  set observed=cause
 end
 if observed!=ERROR
  return 201
 end
 if (states[0]!=COUNT)|(states[1]!=100)|(states[2]!=OLDSTAMP)|(states[3]!=80000)|(states[4]!=120000)|(states[5]!=900000)|(states[6]!=2)|(states[7]!=3)
  return 202
 end
 set i=8
 while i<256
  if states[i]!=0
   return 203
  end
  set i=i+1
 end
 return 0
end
'''
        replacements=[('IDENT',ident),('STAMP',stamp),('TEMP',temp),('LOW',low),('HIGH',high),('COUNT',count),('OLDSTAMP',oldstamp),('ERROR',error)]
        for key,value in sorted(replacements,key=lambda item:len(item[0]),reverse=True):source=source.replace(key,str(value))
        path=D/(name+('-opt'if opt else'-plain')+'.flow');path.write_text(source);exe=path.with_suffix('')
        q=subprocess.run([str(C),str(path),str(exe),'--compact',*(['--opt']if opt else[])],capture_output=True,timeout=30)
        passed=q.returncode==0
        if passed:
            subprocess.run(['/usr/bin/codesign','-s','-',str(exe)],check=True,capture_output=True)
            trial=subprocess.run([str(exe)],capture_output=True,timeout=5);passed=trial.returncode==0
        checks.append(dict(name=name,opt=opt,passed=passed,compileExit=q.returncode,diagnostic=q.stderr.decode(),sourceSHA256=hashlib.sha256(source.encode()).hexdigest()))
report=dict(checks=len(checks),passed=sum(x['passed']for x in checks),allPassed=all(x['passed']for x in checks),compilerSHA256=hashlib.sha256(C.read_bytes()).hexdigest(),results=checks)
(D/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(directory=str(D),checks=len(checks),passed=report['passed'])))
assert report['allPassed']
