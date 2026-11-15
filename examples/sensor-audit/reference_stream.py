#!/usr/bin/env python3
"""Single-pass stdlib comparator, same strict v2 contract; not an RF2 dependency."""
import json,os,re,stat,sys
HEADER=b'sensor_id,timestamp_ms,temperature_mC'
U64=2**64-1

def canonical(raw,minimum,maximum):
    if not re.fullmatch(rb'0|[1-9][0-9]*|-[1-9][0-9]*',raw):raise ValueError('canonical integer')
    value=int(raw)
    if not minimum<=value<=maximum:raise ValueError('range')
    return value

def oracle(data,low=0,high=50000):
    if len(data)>1048576:raise ValueError('input bound')
    lines=data.split(b'\n')
    if lines[-1]==b'':lines.pop()
    if not lines:raise ValueError('header')
    ending=data.endswith(b'\n')
    header=lines[0][:-1]if lines[0].endswith(b'\r')and(len(lines)>1 or ending)else lines[0]
    if header!=HEADER:raise ValueError('header')
    if len(lines)-1>4096:raise ValueError('row count')
    sensors={}
    for i,line in enumerate(lines[1:],1):
        if line.endswith(b'\r')and(i<len(lines)-1 or ending):line=line[:-1]
        if not 0<len(line)<=128:raise ValueError('record size')
        fields=line.split(b',')
        if len(fields)!=3:raise ValueError('shape')
        ident=canonical(fields[0],1,32);stamp=canonical(fields[1],0,U64);temp=canonical(fields[2],-100000,200000)
        state=sensors.get(ident)
        if state is None:
            sensors[ident]=[1,stamp,stamp,temp,temp,temp,int(temp<low),int(temp>high)]
        else:
            if stamp<=state[2]:raise ValueError('sensor time order')
            state[0]+=1;state[2]=stamp
            if temp<state[3]:state[3]=temp
            if temp>state[4]:state[4]=temp
            state[5]+=temp;state[6]+=int(temp<low);state[7]+=int(temp>high)
    result=[]
    for ident,state in sorted(sensors.items()):
        count,first,last,minimum,maximum,total,below,above=state
        result.append(dict(id=ident,count=count,first_ms=first,last_ms=last,minimum_mC=minimum,maximum_mC=maximum,sum_mC=total,mean=dict(numerator_mC=total,denominator=count),below_low=below,above_high=above))
    return dict(schema='rf2.sensor-audit.v1',rows=len(lines)-1,low_mC=low,high_mC=high,sensors=result)

def main():
    if len(sys.argv)not in(2,4):
        print('Usage: sensor-reference FILE [LOW_MC HIGH_MC]',file=sys.stderr)
        return 2
    try:
        low,high=0,50000
        if len(sys.argv)==4:
            low=canonical(sys.argv[2].encode(),-100000,200000)
            high=canonical(sys.argv[3].encode(),-100000,200000)
            if low>high:raise ValueError('reversed thresholds')
        fd=os.open(sys.argv[1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('regular file required')
            with os.fdopen(fd,'rb',closefd=False)as input_file:data=input_file.read(1048577)
        finally:os.close(fd)
        result=oracle(data,low,high)
        result['schema']='rf2.sensor-audit.v2'
        for sensor in result['sensors']:
            sensor['first_ms']=str(sensor['first_ms']);sensor['last_ms']=str(sensor['last_ms'])
    except(OSError,ValueError,UnicodeError)as error:
        print('Sensor audit refused: '+str(error),file=sys.stderr)
        return 2
    try:
        sys.stdout.write(json.dumps(result,separators=(',',':'))+'\n')
        sys.stdout.flush()
    except OSError:
        return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
