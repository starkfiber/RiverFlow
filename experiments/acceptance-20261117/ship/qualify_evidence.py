"""Fresh receipt qualification, not native execution or a security attestation."""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();d=a.evidence.resolve()
    original=read(d/'run-1/RESULTS.json');assert len(original['runs'])==30
    failures=[r for r in original['runs']if not r['passed']]
    assert len(failures)==2 and all(r['label'].endswith('/crypto_verify.py')for r in failures)
    for r in failures:assert 'FileNotFoundError' in (ROOT/r['log']).read_text()
    host=read(d/'host-replay/RESULTS.json');assert host['allPassed']and len(host['rows'])==2
    final=read(d/'run-final/RESULTS.json');assert final['allPassed']and len(final['runs'])==31
    assert final['variants']['candidate']['clientSHA256']==sha(HERE/'intent_client.py')
    assert final['variants']['baseline']['clientSHA256']=='086385b6595bc6e821b09bdf965a876ab3c3946e88fbd5b592c15ab19affe2f6'
    for variant in ['baseline','candidate']:
        for name,file,count in [('secure_verify','SECURE-VERIFICATION.json',80),('tcp_verify','TCP-VERIFICATION.json',134),('baseline_verify','PENDING-VERIFICATION.json',80),('baseline_multiflow_verify','MULTIFLOW-VERIFICATION.json',12),('regression_verify','VERIFICATION.json',11),('regression_irq_verify','IRQ-VERIFICATION.json',6),('start_verify','START-CLOCK-VERIFICATION.json',2),('fault_verify','FAULT-VERIFICATION.json',18),('guard_verify','DMA-GUARD-VERIFICATION.json',4),('mmio_guard_verify','MMIO-GUARD-VERIFICATION.json',4),('new_page_guard_verify','NEW-PAGE-GUARDS.json',16)]:
            result=read(d/'run-final'/variant/name/file);assert result['passed']and result['completed']==count,(variant,name)
        assert read(d/'run-final'/variant/'guard_verify/BIOS-MEMORY-VERIFICATION.json')['passed']
        assert read(d/'run-final'/variant/'peer_crypto_verify/PEER-CRYPTO-VERIFICATION.json')['checks']==304
        assert read(d/'run-final'/variant/'crypto_verify/CRYPTO-HOST-VERIFICATION.json')['checks']==900
    red=read(d/'loss-red-2/RESULTS.json');green=read(d/'loss-green-2/RESULTS.json')
    assert not red['passed']and green['passed']
    assert red['fixtureSHA256']==green['fixtureSHA256'] and red['scriptSHA256']==green['scriptSHA256']
    assert red['guestImageSHA256']==green['guestImageSHA256']=='4ac4f627c82f403865facf94235bf58ea4952c1ce4d9c594f0c20f659d9e2450'
    for row in read(d/'loss-red-2/SECURE-VERIFICATION.json')['rows']:
        assert not row['passed']and 'unsafe-mutation-replayed' in row['error']
    result=read(d/'loss-green-2/SECURE-VERIFICATION.json');assert result['passed']and result['completed']==94
    assert [len(r['cases'])for r in result['rows']]==[47,47]
    assert sha(HERE/'intent_client.py')==green['clientAfterSHA256']=='ba26053fd5453235fa1161094dfa5cefacd5f7f642e632f36523950a729e74a2'
    assert sha(HERE/'loss_cases.py.in')==green['fixtureSHA256']
    current=read(d/'run-final/candidate/loss_verify/SECURE-VERIFICATION.json');assert current['passed']and current['completed']==94
    assert final['variants']['candidate']['normalImageSHA256']==green['guestImageSHA256']
    controls=read(d/'TCP-FIXTURE-CONTROLS.json');assert controls['passed']and len(controls['cases'])==7
    assert controls['fixtureSHA256']==sha(HERE/'tcp_neighbor.py.in')
    expiry=read(d/'tcp-expiry/RESULTS.json');assert expiry['passed']and expiry['completed']==134
    assert expiry['guestImageSHA256']==final['variants']['candidate']['normalImageSHA256']
    assert expiry['fixtureSHA256']==controls['fixtureSHA256']
    for model in ['pc','q35']:
        for row in read(d/('tcp-expiry/TCP-NEIGHBOR-REFRESH-'+model+'.json')):
            assert row['guestNow']-row['neighborTimestamp']>=row['lifetime']
            assert row['releasedTCP']==row['expectedTCP']and row['controlFrameBudget']==1
    build=read(d/'development-build/RESULTS.json');assert build['buildOnly']and not build['guestLaunched']
    assert build['clientSHA256']==final['variants']['candidate']['clientSHA256']
    assert build['cryptoSHA256']==final['variants']['candidate']['cryptoSHA256']
    assert build['imageSHA256']==final['variants']['candidate']['normalImageSHA256']
    mcp=read(d/'mcp-final/MCP-SMOKE.json');assert mcp['passed']and len(mcp['toolNames'])==9
    record={'schema':'rf2ship.acceptance-qualification.v1','allImplementedLocalSuitesPassed':True,'originalRunFailuresPreserved':2,'hostReplayPassed':True,'matchedActualGuestUnsafeRetryReproducedAndFixed':True,'expandedCasesPerModel':47,'models':['pc','q35'],'unchangedMCPPassed':True,'fullFirewallGatesQualified':False,'pendingGates':13,'fullyQualifiedGates':0,'scope':'Current implemented local0.18 contracts, not production or independent crypto approval'}
    (d/'QUALIFIED.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
