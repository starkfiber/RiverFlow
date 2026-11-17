"""Emit a bounded, source-bound authoring card only after native admission.

Explicit trusted SDK/parents; this is a developer aid, not signature verification,
an embedded model, raw-source MCP effect, or a safety sandbox.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
COMPILER='4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--compiler',type=Path,required=True);ap.add_argument('--sdk-root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    assert sha(a.compiler)==COMPILER,'Select the qualified compiler'
    sdk=a.sdk_root.resolve();manifest_path=sdk/'rf2-sdk.manifest'
    assert manifest_path.is_file()and not manifest_path.is_symlink()and manifest_path.stat().st_size<=32768,'Manifest file/bound'
    manifest=manifest_path.read_text().splitlines();assert manifest[0]=='rf2-sdk-v1'and 1<len(manifest)<=33
    modules={}
    for line in manifest[1:]:
        expected,name=line.split(' ');p=sdk/name
        assert p.resolve().parent==sdk and p.is_file()and not p.is_symlink()and p.stat().st_size<=524288 and sha(p)==expected,'Manifest/source mismatch'
        assert name not in modules,'Duplicate module';modules[name]=expected
    assert {'report.flow','text.flow','io.flow'}<=set(modules)
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    p=subprocess.run([str(a.compiler.resolve()),'--check',str(HERE/'style.flow'),'--compact','--opt','--sdk-root',str(sdk),'--diagnostic-json'],capture_output=True,timeout=15)
    (out/'native-admission.stderr').write_bytes(p.stderr);assert p.returncode==0,p.stderr.decode()
    # The exact admitted syntax travels alongside the API, not an invented recipe.
    card=(HERE/'REPORT-API.md').read_text()+'\n## Native-checked RF2 style\n```flow\n'+(HERE/'style.flow').read_text()+'```\n'
    assert len(card.encode())<=8192
    (out/'CONTEXT.md').write_text(card)
    receipt={'schema':'rf2.verified-authoring-context.v1','compilerSHA256':sha(a.compiler),'manifestSHA256':sha(sdk/'rf2-sdk.manifest'),'modules':modules,'styleSHA256':sha(HERE/'style.flow'),'cardSHA256':sha(out/'CONTEXT.md'),'nativeAdmissionExit':p.returncode,'bytes':len(card.encode()),'scope':'Native syntax admission and explicit API identities. No model success, execution, host isolation or token savings inferred.'}
    (out/'RECEIPT.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
if __name__=='__main__':main()
