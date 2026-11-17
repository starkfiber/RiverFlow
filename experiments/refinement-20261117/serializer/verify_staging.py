#!/usr/bin/env python3
"""Non-native packaging controls; never copy into protected trees."""
from pathlib import Path
from unittest import mock
import argparse
import hashlib
import importlib.util
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(directory):
    return {str(path.relative_to(directory)):sha(path) for path in sorted(directory.rglob('*')) if path.is_file()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    args=parser.parse_args()
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('r5_stage_guard',HERE/'stage_sdk.py')
    stage=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage)
    before=inventory(ROOT/'sdk/v1')
    cases=[]
    forbidden=[]
    for name in stage.PROTECTED:
        target=ROOT/name
        for suffix in ['', 'r5-forbidden-output', 'r5-forbidden-output/deeper']:
            forbidden.append((name+('/'+suffix if suffix else ''),target/suffix))
        alias=out/('alias-'+name.replace('/','-'))
        alias.symlink_to(target,target_is_directory=True)
        forbidden.append(('resolved-parent-alias/'+name,alias/'r5-forbidden-output'))
    forbidden.append(('normalized-sdk-descendant',ROOT/'sdk/v1/../v1/r5-forbidden-output'))
    existing=out/'existing-directory'
    existing.mkdir()
    forbidden.append(('existing-directory',existing))
    file=out/'existing-file'
    file.write_text('preserved\n')
    forbidden.append(('existing-file',file))
    leaf=out/'leaf-link'
    leaf.symlink_to(existing,target_is_directory=True)
    forbidden.append(('existing-leaf-symlink',leaf))
    broken=out/'broken-leaf-link'
    broken.symlink_to(out/'nonexistent-target')
    forbidden.append(('broken-leaf-symlink',broken))
    with mock.patch.object(stage.shutil,'copytree',side_effect=AssertionError('copytree reached for forbidden destination')) as copying:
        for name,path in forbidden:
            try:
                stage.stage(path)
            except ValueError as error:
                cases.append({'case':name,'passed':True,'refusal':str(error)})
            else:
                raise AssertionError('Admitted forbidden destination: '+name)
        assert copying.call_count==0
    assert not (out/'nonexistent-target').exists()
    assert file.read_text()=='preserved\n'
    cases.append({'case':'forbidden-destinations-never-reach-copytree','passed':True,'copyCalls':0})
    fresh=out/'fresh-sdk'
    assert stage.stage(str(fresh))==fresh
    reference=inventory(args.reference.resolve())
    actual=inventory(fresh)
    assert actual==reference
    cases.append({'case':'allowed-fresh-output-byte-identical-to-frozen-candidate-sdk','passed':True,'files':len(actual)})
    try:
        stage.stage(fresh)
    except ValueError:
        cases.append({'case':'fresh-output-reuse-refused','passed':True})
    else:
        raise AssertionError('Reused an existing staged output')
    assert before==inventory(ROOT/'sdk/v1')
    cases.append({'case':'original-sdk-file-inventory-unchanged','passed':True,'files':len(before)})
    result={'schema':'rf2.serializer.staging-guard-controls.v1','complete':True,'allPassed':True,
            'nativeSamplesRun':0,'sourceSHA256':sha(HERE/'stage_sdk.py'),'controllerSHA256':sha(Path(__file__)),
            'candidateSourceSHA256':sha(HERE/'json_spans.flow'),'stagedFileSHA256':actual,
            'checks':cases,'checkCount':len(cases),
            'scope':'Packaging-only destination guards; no adversarial concurrent-filesystem isolation claim.'}
    (out/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in ['complete','allPassed','checkCount','nativeSamplesRun']}))


if __name__=='__main__':
    main()
