"""Stop only the explicitly recorded local demonstration processes; reject reused PIDs."""
from pathlib import Path
import json,subprocess,signal,os
p=Path(__file__).resolve().parents[1]/'artifacts/virtual-lab/showcase-processes.json';rows=json.loads(p.read_text())['processes']
for row in rows:
 q=subprocess.run(['/bin/ps','-p',str(row['pid']),'-o','lstart=','-o','command='],capture_output=True,text=True)
 if q.returncode:print('Already stopped:',row['role']);continue
 if q.stdout.strip()!=row['identity']:raise SystemExit('Process identity changed; refusing to stop '+row['role'])
 os.kill(row['pid'],signal.SIGTERM);print('Stopped:',row['role'])
