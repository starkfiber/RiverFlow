"""Render declared RF2 acceptance progress; never infer completion from test counts."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = {'pending', 'active', 'done'}


def render(data):
    assert data['schema'] == 'rf2.pipeline.v1', 'Unsupported pipeline schema'
    lines = ['# RF2 development progress', '',
             'Generated from [PIPELINE.json](PIPELINE.json). Progress counts the declared acceptance checks below, not language coverage, market leadership or universal platform readiness.', '',
             '[Mission and continuity](PROJECT-CONTINUITY.md) · [RF2 everywhere](RF2-EVERYWHERE.md) · [Typed application values](APPLICATION-VALUES.md)', '']
    for title, rows in [('Platform expansion gates', data['platformGates']),
                        ('Current sprint: '+data['sprint']['title'], data['sprint']['checks'])]:
        assert rows, 'A progress group must contain acceptance checks'
        ids = [r['id'] for r in rows]
        assert len(ids) == len(set(ids)), 'Duplicate acceptance ID'
        for row in rows:
            assert row['state'] in STATES, 'Unknown progress state'
            assert row.get('acceptance'), 'Missing acceptance condition'
            if row['state'] == 'done':
                assert row.get('evidence'), 'Completed checks require evidence'
            for evidence in row.get('evidence', []):
                p = (ROOT/evidence).resolve()
                assert p.is_relative_to(ROOT) and p.is_file(), 'Missing/outside project evidence: '+evidence
        done = sum(r['state'] == 'done' for r in rows)
        percent = 100*done//len(rows)
        bar = '█'*(percent//10)+'░'*(10-percent//10)
        lines += ['## '+title, '', f'`{bar}` **{done}/{len(rows)} complete ({percent}%)**', '',
                  '| ID | State | Acceptance condition | Evidence / current boundary |',
                  '| --- | --- | --- | --- |']
        for row in rows:
            links = ', '.join(f'[{Path(p).name}]({Path(p).relative_to("docs") if p.startswith("docs/") else "../"+p})' for p in row.get('evidence', []))
            note = row.get('note', '')
            lines.append('| '+ ' | '.join([row['id'], row['state'], row['acceptance'], links+(' · '+note if note else '')])+' |')
        lines.append('')
    lines += ['## Read these counters correctly', '',
              'Platform expansion counts the eight new gates from the roadmap. Its zero completed gates does not erase the existing compiler, applications, libraries, MCP tools or emulator evidence. Active work is visible but earns no completed-gate credit.', '',
              'The current sprint counts only its named deliverables. A design/documentation check is labelled as such. Passing borrowed-record examples does not complete general owned values. Reaching 100% of this sprint does not mean RF2 runs everywhere.', '',
              'The generator validates IDs, states and local evidence-file existence. It does not independently endorse the evidence or inspect every claim. Reviewers must inspect the linked result and its limitations. Run `python3 tools/project-progress.py --check` from the repository root to detect stale rendering.', '']
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
