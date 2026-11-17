"""Small condition-boundary controls; not a sandbox or complete program checker."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
HERE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists()
    spec=importlib.util.spec_from_file_location('matched_controller',HERE/'study.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    tests=[
        ('manual-text','manual','use "@rf2/v1/text.flow"\nfn main()\n return 0\nend\n',True),
        ('manual-comment','manual','use "@rf2/v1/text.flow" # allowed import\n# Report report_number text_report_entry\nfn main()\n return 0\nend\n',True),
        ('manual-string-not-api','manual','use "@rf2/v1/text.flow"\nfn main()\n return io_size("Report report_number text_report_entry")\nend\n',True),
        ('manual-forbidden-import','manual','use "@rf2/v1/report.flow"\n',False),
        ('manual-forbidden-cli','manual','use "@rf2/v1/text-report-cli.flow"\n',False),
        ('manual-undefined-record-deferred-to-compiler','manual','use "@rf2/v1/text.flow"\nfn f()\n let r=Report(0,0,0)\n return 0\nend\n',True),
        ('manual-undefined-helper-deferred-to-compiler','manual','use "@rf2/v1/text.flow"\nfn f()\n do report_number(r,out,"X",1,0)\n return 0\nend\n',True),
        ('manual-own-report-helper','manual','use "@rf2/v1/text.flow"\nfn report_json(value)\n return value\nend\nfn main()\n return report_json(0)\nend\n',True),
        ('manual-local-import','manual','use "@rf2/v1/text.flow"\nuse "./answer.flow"\n',False),
        ('cli-callback-delegation','cli','use "@rf2/v1/text-report-cli.flow"\nfn text_report_fields (input:TextReportInput,report:Report,out:Writer):IO\n return ok(0)\nend\nfn main(argc,argv)\n return text_report_entry (argc,argv,"X",1,0)\nend\n',True),
        ('cli-no-delegation','cli','use "@rf2/v1/text-report-cli.flow"\nfn text_report_fields()\n return 0\nend\n',False),
        ('cli-no-callback','cli','use "@rf2/v1/text-report-cli.flow"\nfn main(argc,argv)\n return text_report_entry(argc,argv,"X",1,0)\nend\n',False),
    ]
    rows=[]
    for label,condition,source,want in tests:
        errors=m.condition_errors(source,condition);assert(not errors)==want,(label,errors)
        rows.append({'case':label,'condition':condition,'admitted':not errors,'expected':want,'passed':True})
    record={'schema':'rf2.refinement.condition-controls.v1','controllerSHA256':hashlib.sha256((HERE/'study.py').read_bytes()).hexdigest(),'passed':True,'cases':rows,'scope':'Condition import/API identity only; source effects still require independent root review and complete native oracle'}
    a.out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(rows)}))
if __name__=='__main__':main()
