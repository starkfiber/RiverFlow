"""Create one explicit, versioned source SDK from reviewed repository modules.

This is a development packaging tool. The resulting compiler and apps do not
require Python. Hashes bind modules to this package manifest, not an author.
"""
from pathlib import Path
import hashlib, importlib.util, json, re, sys

R = Path(__file__).resolve().parents[2]
FILES = ('io.flow','text.flow','json.flow','mcp.flow','collections.flow','sha256.rf2')

def create(destination):
    destination=Path(destination).resolve()
    if destination.exists():raise ValueError('Use a new SDK directory')
    destination.mkdir(parents=True)
    provenance=[]
    for name in FILES:
        source=R/'examples/document-audit/lib'/name
        raw=source.read_bytes()
        content=re.sub(r'(?m)^use "lib/([^"\n]+)"$',r'use "@rf2/v1/\1"',raw.decode()).encode()
        transformation='Version package import lines only'
        extra=[]
        if name=='io.flow':
            policy=R/'experiments/sdk-packages/io-policy.flow'
            content+=('\n'+policy.read_text()).encode()
            extra.append(dict(path=str(policy.relative_to(R)),SHA256=hashlib.sha256(policy.read_bytes()).hexdigest()))
            transformation='Version package imports; append explicit Darwin descriptor-scoped io_write_no_sigpipe; retain io_write_all body'
        if name=='mcp.flow':
            patch=R/'experiments/sdk-packages/transport.py'
            spec=importlib.util.spec_from_file_location('rf2_package_transport',patch)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            content=module.apply(content.decode()).encode()
            extra.append(dict(path=str(patch.relative_to(R)),SHA256=hashlib.sha256(patch.read_bytes()).hexdigest()))
            transformation='Version imports; typed first transport error and descriptor-scoped no-SIGPIPE/restore; unchanged JSON protocol/parser/schema'
        if name=='text.flow':
            # Preserve the old search body, adding a separately named helper.
            start=raw.decode().index('fn text_search(')
            end=raw.decode().index('\n# 0-based LF line lookup',start)
            overlap=raw.decode()[start:end].replace('fn text_search(', 'fn text_search_overlapping(',1)
            guard=' if (n>1048576)|(m>256)|(fold>1)\n  return 0\n end\n'
            assert overlap.count(guard)==1
            overlap=overlap.replace(guard,'',1)
            overlap=overlap.replace(' set out.status=22\n',' if (n>1048576)|(m==0)|(m>128)|(fold>1)\n  return 0\n end\n set out.status=22\n',1)
            finish='   set out.count=out.count+1\n   set j=0'
            assert overlap.count(finish)==1
            overlap=overlap.replace(finish,'   set out.count=out.count+1\n   set j=prefix[j-1]',1)
            content+=('\n# Separate bounded overlapping KMP; invalid arguments preserve caller outputs.\n'+overlap+'\n').encode()
            transformation='Version package imports; append separately named 1..128-byte overlapping KMP derived from text_search; retain original body'
        (destination/name).write_bytes(content)
        provenance.append(dict(path=name,source=str(source.relative_to(R)),sourceSHA256=hashlib.sha256(raw).hexdigest(),packageSHA256=hashlib.sha256(content).hexdigest(),transformation=transformation,additionalInputs=extra))
    lines=['rf2-sdk-v1']+[x['packageSHA256']+' '+x['path'] for x in provenance]
    (destination/'rf2-sdk.manifest').write_text('\n'.join(lines)+'\n')
    (destination/'PROVENANCE.json').write_text(json.dumps(dict(schema='rf2.sdk-source-package.v1',version=1,edition='0.50B-transport',namespace='@rf2/v1/',transformation='Version exact SDK imports; separate overlapping search and explicit checked output helpers; recoverable MCP transport; no application entry or renderer',files=provenance),indent=2)+'\n')
    return destination

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: package.py NEW-SDK-DIRECTORY')
    print(create(sys.argv[1]))
