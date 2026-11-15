"""Inventory tracked source honestly; GitHub Linguist recognition is separate."""
import argparse
from collections import Counter, defaultdict
import html
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = {
    '.rf2': 'RiverFlow', '.flow': 'RiverFlow', '.py': 'Python',
    '.mjs': 'JavaScript', '.js': 'JavaScript', '.html': 'HTML',
    '.css': 'CSS', '.sh': 'Shell', '.c': 'C', '.h': 'C/C++ headers',
    '.cpp': 'C++', '.s': 'Assembly', '.S': 'Assembly', '.rs': 'Rust',
}
AREAS = {
    'native': 'Compiler and native runtime',
    'examples': 'Application and target examples',
    'book': 'Teaching source',
    'experiments': 'Unreleased experiments',
    'tests': 'Verification and independent oracles',
    'tools': 'Build and publishing tools',
    'bootstrap': 'Historical seeds and references',
    'src': 'Historical seeds and references',
    'bin': 'Historical seeds and references',
    'site': 'Website and documentation source',
    'docs': 'Website and documentation source',
    'plugin': 'MCP integration',
}


def inventory():
    # NUL framing preserves spaces. Untracked local inputs are deliberately excluded.
    paths = sorted(set(subprocess.check_output(
        ['git', 'ls-files', '-z', '--cached'], cwd=ROOT
    ).decode().rstrip('\0').split('\0')))
    sources = [p for p in paths if Path(p).suffix in LANGUAGES]
    attributes = subprocess.check_output(
        ['git', 'check-attr', '-z', '--stdin', 'linguist-generated'],
        cwd=ROOT, input=('\0'.join(sources) + '\0').encode(),
    ).decode().rstrip('\0').split('\0') if sources else []
    generated = {attributes[i] for i in range(0, len(attributes), 3)
                 if attributes[i + 2] in ('set', 'true')}
    totals, counts = Counter(), Counter()
    areas = defaultdict(Counter)
    files = []
    for name in sources:
        if name in generated:
            continue
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'Tracked source must be a regular existing file: {name}')
        language = LANGUAGES[path.suffix]
        area = AREAS.get(name.split('/')[0], 'Other development source')
        size = path.stat().st_size
        totals[language] += size
        counts[language] += 1
        areas[area][language] += size
        files.append({'path': name, 'language': language, 'area': area, 'bytes': size})
    return {
        'schema': 'rf2.source.inventory.v2',
        'method': 'Tracked source files in the working tree, using the explicit suffix map. '
                  'Excludes source-suffix files marked linguist-generated in .gitattributes. '
                  'Includes tests, references, experiments and website source. '
                  'Counts bytes, not runtime dependencies, interoperability or quality. '
                  'GitHub Linguist uses its own recognized-language list. Markdown prose, '
                  'archives, images and other unlisted suffixes are outside this inventory.',
        'supportedSuffixes': LANGUAGES,
        'generatedExcluded': sorted(generated),
        'bytesByLanguage': dict(totals.most_common()),
        'filesByLanguage': dict(sorted(counts.items())),
        'bytesByArea': {area: dict(sorted(values.items()))
                        for area, values in sorted(areas.items())},
        'files': files,
    }


def chart(report):
    rows = list(report['bytesByLanguage'].items())
    height = 90 + len(rows) * 36
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
           f'aria-labelledby="title desc" width="700" height="{height}" '
           f'viewBox="0 0 700 {height}">',
           '<title id="title">RiverFlow source inventory</title>',
           '<desc id="desc">Tracked source bytes by language. Generated outputs excluded; '
           'tests, development tools and reference implementations included. '
           'This is not GitHub Linguist classification or a performance measure.</desc>',
           f'<rect width="700" height="{height}" rx="18" fill="#0a2133"/>',
           '<g font-family="sans-serif" fill="#e3f5fa">',
           '<text x="24" y="30" font-size="19">RiverFlow source inventory</text>',
           '<text x="24" y="52" font-size="11">Tracked bytes · generated outputs excluded · development tools included</text>']
    largest = max((n for _, n in rows), default=1) or 1
    for i, (name, size) in enumerate(rows):
        y = 84 + i * 36
        width = round(300 * size / largest)
        color = '#82e6ef' if name == 'RiverFlow' else '#49748e'
        svg.append(f'<text x="24" y="{y}" font-size="14">{html.escape(name)}</text>'
                   f'<rect x="155" y="{y-13}" width="{width}" height="18" rx="4" fill="{color}"/>'
                   f'<text x="475" y="{y}" font-size="12">{size:,} bytes</text>')
    return ''.join(svg) + '</g></svg>\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='refuse stale outputs without writing')
    args = parser.parse_args()
    report = inventory()
    outputs = {
        'docs/SOURCE-INVENTORY.json': json.dumps(report, indent=2) + '\n',
        'docs/SOURCE-INVENTORY.svg': chart(report),
    }
    stale = []
    for name, content in outputs.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_bytes() != content.encode():
                stale.append(name)
        else:
            path.write_bytes(content.encode())
    if stale:
        parser.exit(1, 'Stale inventory: ' + ', '.join(stale) + '\n')
    print(json.dumps({'checked' if args.check else 'written': list(outputs),
                      'files': len(report['files']), 'bytesByLanguage': report['bytesByLanguage']}))


if __name__ == '__main__':
    main()
