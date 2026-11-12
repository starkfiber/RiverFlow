"""Build a disposable NoCloud seed. No host secrets or directories are shared."""
from pathlib import Path
import subprocess,hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'artifacts/virtual-lab';seed=D/'seed';seed.mkdir(exist_ok=True)
assert not (D/'seed.iso').exists() and not (D/'guest-overlay.qcow2').exists(),'Existing VM evidence is preserved; choose a new isolated lab directory before rebuilding.'
files={'/opt/rf2-lab/server.py':(R/'examples/stack-lab/python_server.py').read_text(),'/opt/rf2-lab/index.html':(R/'examples/stack-lab/index.html').read_text(),'/etc/systemd/system/rf2-web.service':'''[Unit]
Description=Disposable RF2 comparison Python server
After=network.target
[Service]
ExecStart=/usr/bin/python3 /opt/rf2-lab/server.py --bind 0.0.0.0 --port 8080 --deployment linux-guest --site /opt/rf2-lab/index.html
DynamicUser=yes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
Restart=on-failure
[Install]
WantedBy=multi-user.target
'''}
text='#cloud-config\nusers: []\nssh_pwauth: false\ndisable_root: true\npackage_update: false\npackage_upgrade: false\nwrite_files:\n'
for path,content in files.items():text+=f"  - path: {path}\n    permissions: '0644'\n    content: |\n"+'\n'.join('      '+line for line in content.splitlines())+'\n'
text+='runcmd:\n  - [systemctl, daemon-reload]\n  - [systemctl, enable, --now, rf2-web.service]\n  - [systemctl, disable, --now, systemd-timesyncd.service]\n';(seed/'user-data').write_text(text);(seed/'meta-data').write_text('instance-id: rf2-lab-20261113\nlocal-hostname: rf2-lab\n')
subprocess.run(['/usr/bin/hdiutil','makehybrid','-o',str(D/'seed.iso'),'-iso','-joliet','-default-volume-name','cidata',str(seed)],check=True)
base=D/'ubuntu-24.04-minimal-cloudimg-arm64.img';out=D/'guest-overlay.qcow2';subprocess.run(['/opt/homebrew/bin/qemu-img','create','-f','qcow2','-F','qcow2','-b',str(base),str(out)],check=True)
(D/'seed-manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in [seed/'user-data',seed/'meta-data',D/'seed.iso']},indent=2)+'\n')
