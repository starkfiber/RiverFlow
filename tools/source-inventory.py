"""Source inventory including RiverFlow, which GitHub Linguist does not yet list."""
from pathlib import Path
import subprocess,json,collections,html
R=Path(__file__).resolve().parents[1]
paths=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=R,text=True).splitlines()
generated={'examples/evidence-contract/lib/json_transport.rf2','docs/book/index.html','site/book/index.html','native/attendance-kernel.rf2','native/invoice-kernel.rf2'}
languages={'.rf2':'RiverFlow','.flow':'RiverFlow','.py':'Python','.mjs':'JavaScript','.js':'JavaScript','.html':'HTML','.css':'CSS','.sh':'Shell','.c':'C','.h':'C/C++ headers','.cpp':'C++','.s':'Assembly','.S':'Assembly','.rs':'Rust'}
totals=collections.Counter();files=[]
for name in sorted(set(paths)):
 p=R/name;language=languages.get(p.suffix)
 if language and name not in generated:
  size=p.stat().st_size;totals[language]+=size;files.append({'path':name,'language':language,'bytes':size})
report={'schema':'rf2.source.inventory.v1','method':'Tracked and unignored source files by the explicit supported-suffix map, excluding explicitly generated book HTML and kernels. Includes developer tools, references and website source. Bytes, not runtime dependencies or quality. GitHub Linguist has its own supported-language list.','supportedSuffixes':languages,'generatedExcluded':sorted(generated),'bytesByLanguage':dict(totals.most_common()),'files':files}
(R/'docs/SOURCE-INVENTORY.json').write_text(json.dumps(report,indent=2)+'\n')
rows=list(totals.most_common());height=80+len(rows)*36;svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="{height}" viewBox="0 0 640 {height}"><rect width="640" height="{height}" rx="18" fill="#0a2133"/><g font-family="sans-serif" fill="#e3f5fa"><text x="24" y="30" font-size="19">RiverFlow source inventory</text><text x="24" y="52" font-size="11">Source bytes · generated outputs excluded · development tools included</text>']
for i,(name,n)in enumerate(rows):
 y=84+i*36;w=round(300*n/max(totals.values()));svg.append(f'<text x="24" y="{y}" font-size="14">{html.escape(name)}</text><rect x="140" y="{y-13}" width="{w}" height="18" rx="4" fill="{"#82e6ef"if name=="RiverFlow"else"#49748e"}"/><text x="460" y="{y}" font-size="12">{n:,} bytes</text>')
svg.append('</g></svg>');(R/'docs/SOURCE-INVENTORY.svg').write_text(''.join(svg)+'\n');print(json.dumps(report['bytesByLanguage']))
