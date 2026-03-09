#!/usr/bin/env python3
import json
from collections import defaultdict
from pathlib import Path


def parse_rule(path):
    name = path.stem
    techniques = []
    in_mitre = False
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        stripped = line.strip()
        if stripped.startswith('name:') and name == path.stem:
            name = stripped.split(':', 1)[1].strip().strip('"').strip("'")
        if stripped.startswith('mitre_techniques:'):
            in_mitre = True
            continue
        if in_mitre:
            if stripped.startswith('- '):
                techniques.append(stripped[2:].strip().strip('"').strip("'"))
            elif stripped and not stripped.startswith('#'):
                in_mitre = False
    return name, techniques


def main():
    coverage = defaultdict(set)
    for path in Path('detections').glob('**/*.yaml'):
        name, mitre = parse_rule(path)
        for technique in mitre:
            coverage[technique].add(name)

    output = {
        'techniques': {k: sorted(v) for k, v in sorted(coverage.items())},
        'total_techniques': len(coverage),
    }

    out = Path('governance/mitre-coverage.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    print(f'Generated {out}')


if __name__ == '__main__':
    main()
