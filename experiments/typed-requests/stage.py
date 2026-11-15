"""Stage source-only request SDK and the real browser frontend overlay."""
from pathlib import Path
import importlib.util,shutil,sys
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('rf2_request_base_stage',R/'experiments/app-effort/stage.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
base_stage=base.stage
def stage(destination):
    destination=Path(destination)
    base_stage(destination/'lib')
    for p in (R/'experiments/typed-requests/lib').glob('*.flow'):shutil.copy2(p,destination/'lib'/p.name)
    s=(R/'experiments/typed-booking/web.flow').read_text()
    s=s.replace('use "lib/app-server.flow"','use "lib/app-server.flow"\nuse "lib/booking-request.flow"',1)
    start=s.index('fn web_request(');end=s.index('\nfn app_dispatch(',start)
    s=s[:start]+'fn web_request(values:FormValues,mask,request:StoreRequest):IO\n return booking_request(values,mask,request)\nend\n'+s[end:]
    (destination/'web.flow').write_text(s)
if __name__=='__main__':stage(sys.argv[1])
