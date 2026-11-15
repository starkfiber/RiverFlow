"""Render declared RF2 acceptance progress; never infer completion from test counts."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = {'pending', 'active', 'done'}


def render(data):
    if data['schema']!='rf2.pipeline.v2':
        raise ValueError('Unsupported pipeline schema')
    scope=data['deliveryScope']
    rows=scope['requirements']
    if scope['id']!='rf2-owner-delivery-2026-11-15' or scope['lockedRequirementCount']!=12 or len(rows)!=12:
        raise ValueError('The agreed twelve-item delivery scope must not be silently replaced')
    if [r['id'] for r in rows]!=[f'R{i:02}' for i in range(1,13)]:
        raise ValueError('Delivery requirement IDs/order changed')
    for row in rows:
        if row['state'] not in STATES or not row.get('acceptance'):
            raise ValueError('Invalid acceptance state or condition')
        if row['state']=='done' and not row.get('evidence'):
            raise ValueError('Completed checks require evidence')
        for evidence in row.get('evidence',[]):
            p=(ROOT/evidence).resolve()
            if not p.is_relative_to(ROOT) or not p.is_file():
                raise ValueError('Missing/outside project evidence: '+evidence)
    done=sum(row['state']=='done' for row in rows)
    percent=100*done//len(rows)
    bar='█'*(percent//10)+'░'*(10-percent//10)
    lines=['# RF2 delivery progress','',
           f'`{bar}` **{done}/12 requested requirements complete ({percent}%)**','',
           'This is the fixed delivery checklist reviewed with the owner on 15 November 2026. It counts accepted requirements equally, not engineering hours or universal language coverage. Partial implementations earn no completed-item credit. No sprint percentage is presented as product completion.','',
           '[Mission](PROJECT-CONTINUITY.md) · [Canonical ledger](PIPELINE.json) · [Current owned-field evidence](OWNED-VALUES-0.42.md)','',
           '| ID | State | Acceptance condition | Evidence and boundary |',
           '| --- | --- | --- | --- |']
    for row in rows:
        links=', '.join(f'[{Path(p).name}]({Path(p).relative_to("docs") if p.startswith("docs/") else "../"+p})' for p in row.get('evidence',[]))
        note=row.get('note','')
        lines.append('| '+' | '.join([row['id'],row['state'],row['acceptance'],links+(' · '+note if note else '')])+' |')
    lines+=['','## Active implementation','',data['activeWork']['requirement']+': '+data['activeWork']['description'],'',
            'The eight longer-term platform gates and historical sprint evidence remain in PIPELINE.json. They do not produce extra completion badges. GitHub recognition depends on real external adoption and review; implementing a grammar or documenting requirements does not complete R12.','',
            'The renderer checks the fixed scope, states and local evidence-file existence. It does not independently validate every claim. Reaching the final item requires reviewing its actual acceptance evidence. Run `python3 tools/project-progress.py --check` to detect stale rendering.','']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    content = render(json.loads((ROOT/'docs/PIPELINE.json').read_text())).encode()
    target = ROOT/'docs/PROGRESS.md'
    if args.check:
        if not target.exists() or target.read_bytes() != content:
            parser.exit(1, 'Progress is stale; regenerate after reviewing pipeline changes.\n')
    else:
        target.write_bytes(content)
    print('Progress verified.' if args.check else 'Progress rendered.')


if __name__ == '__main__':
    main()
