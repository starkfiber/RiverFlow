#!/usr/bin/env python3
"""Standalone stdlib correctness/performance reference; not an RF2 dependency."""
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
    # Only LF or CRLF is accepted; final bare CR is not a line terminator.
    lines=data.split(b'\n')
    if lines[-1]==b'':lines.pop()
    normalized=[]
    for i,line in enumerate(lines):
        has_lf=i<len(lines)-1 or data.endswith(b'\n')
        normalized.append(line[:-1]if has_lf and line.endswith(b'\r')else line)
    if not normalized or normalized[0]!=HEADER:raise ValueError('header')
    if len(normalized)-1>4096:raise ValueError('row count')
    sensors={}
    for line in normalized[1:]:
        if not 0<len(line)<=128:raise ValueError('record size')
        fields=line.split(b',')
        if len(fields)!=3:raise ValueError('shape')
        ident=canonical(fields[0],1,32);stamp=canonical(fields[1],0,U64);temp=canonical(fields[2],-100000,200000)
        row=sensors.setdefault(ident,[])
        if row and stamp<=row[-1][0]:raise ValueError('sensor time order')
        row.append((stamp,temp))
    result=[]
    for ident,rows in sorted(sensors.items()):
        temps=[row[1]for row in rows];total=sum(temps)
        result.append(dict(id=ident,count=len(rows),first_ms=rows[0][0],last_ms=rows[-1][0],minimum_mC=min(temps),maximum_mC=max(temps),sum_mC=total,mean=dict(numerator_mC=total,denominator=len(rows)),below_low=sum(v<low for v in temps),above_high=sum(v>high for v in temps)))
    return dict(schema='rf2.sensor-audit.v1',rows=len(normalized)-1,low_mC=low,high_mC=high,sensors=result)

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
