"""Independent native-clock output/refusal checks; no native timing."""
from pathlib import Path
import argparse, importlib.util, json, struct

H=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('net_native_controller',H/'controller.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    good=[123,37,3,100,1000,125,3,2]
    wire=lambda fields:struct.pack('<QQQQQIIQ',*fields)
    assert c.decode(wire(good),123,2,3,100)['nativeUs']==37
    failures={
        'checksum':(0,124), 'elapsed':(1,38), 'repetitions':(2,4), 'zero-start':(3,0),
        'backwards':(4,99), 'zero-numerator':(5,0), 'zero-denominator':(6,0), 'warm-consumption':(7,3)}
    rejected=[]
    for name,(slot,value) in failures.items():
        fields=good[:];fields[slot]=value
        try:c.decode(wire(fields),123,2,3,100)
        except AssertionError:rejected.append(name)
        else:raise AssertionError(name)
    for name,data in [('truncated',wire(good)[:-1]),('trailing',wire(good)+b'\0')]:
        try:c.decode(data,123,2,3,100)
        except AssertionError:rejected.append(name)
        else:raise AssertionError(name)
    overflow=good[:];overflow[3]=1;overflow[4]=(1<<64)-1
    try:c.decode(wire(overflow),123,2,3,100)
    except AssertionError:rejected.append('timebase-overflow')
    else:raise AssertionError('timebase-overflow')
    outside=good[:];outside[1]=100000;outside[3]=100;outside[4]=2400100
    try:c.decode(wire(outside),123,2,3,100)
    except AssertionError:rejected.append('outside-process-envelope')
    else:raise AssertionError('outside-process-envelope')
    result={'allPassed':True,'nativeExecution':False,'validOutputControls':1,'invalidOutputControls':rejected,
            'estimatorControls':c.estimator_controls(),'controllerSHA256':c.sha(H/'controller.py')}
    (out/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();main(a.out.resolve())
