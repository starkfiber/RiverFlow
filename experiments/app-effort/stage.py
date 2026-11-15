"""Stage the explicit app-effort SDK, never an application entry point."""
from pathlib import Path
import shutil,sys
R=Path(__file__).resolve().parents[2]
def stage(destination):
 destination=Path(destination);destination.mkdir(parents=True)
 for p in (R/'experiments/typed-booking/lib').glob('*.flow'):shutil.copy2(p,destination/p.name)
 for name in ('io','storage','text','datetime'):shutil.copy2(R/f'examples/documents/lib/{name}.flow',destination/f'{name}.flow')
 shutil.copy2(R/'examples/evidence-contract/lib/sha256.rf2',destination/'sha256.rf2')
 shutil.copy2(R/'examples/collection-tools/lib/output.rf2',destination/'output.rf2')
 shutil.copy2(R/'experiments/app-effort/lib/mcp.flow',destination/'mcp.flow')
if __name__=='__main__':stage(sys.argv[1])
