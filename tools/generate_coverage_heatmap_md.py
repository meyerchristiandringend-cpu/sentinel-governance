#!/usr/bin/env python3
import json
from pathlib import Path


def main():
    cov = json.loads(Path('governance/mitre-coverage.json').read_text(encoding='utf-8-sig'))
    out = Path('governance/mitre-heatmap.md')
    lines = ['# MITRE Coverage Heatmap', '']
    for tech, rules in sorted(cov.get('techniques', {}).items()):
        lines.append(f'## {tech}')
        for rule in rules:
            lines.append(f'- {rule}')
        lines.append('')
    out.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
    print(f'Generated {out}')


if __name__ == '__main__':
    main()
