#!/usr/bin/env python3
import argparse
import json
import subprocess
from datetime import date
from pathlib import Path


def find_rule_files(root):
    return sorted(Path(root).glob('**/*.yaml'))


def pack_from_path(path):
    parts = path.parts
    if 'detections' in parts:
        idx = parts.index('detections')
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return 'unknown'


def parse_mitre_techniques(path):
    techniques = []
    in_block = False
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        stripped = line.strip()
        if stripped.startswith('mitre_techniques:'):
            in_block = True
            continue
        if in_block:
            if stripped.startswith('- '):
                value = stripped[2:].strip().strip('"').strip("'")
                if value.startswith('T'):
                    techniques.append(value)
            elif stripped and not stripped.startswith('#'):
                break
    return techniques


def changed_files():
    try:
        out = subprocess.check_output(
            ['git', 'diff', '--name-status', 'HEAD~1', 'HEAD'],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []

    changes = []
    for line in out.splitlines():
        parts = line.split('\t', 1)
        if len(parts) == 2:
            status, file_path = parts
            changes.append((status.strip(), file_path.strip()))
    return changes


def load_signatures_index(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rules', required=True, help='detections root path')
    parser.add_argument('--output', required=True, help='output manifest path')
    parser.add_argument('--release', default='current', help='release label')
    parser.add_argument('--signatures-index', default='governance/signatures/index.json', help='signature index JSON path')
    args = parser.parse_args()

    rules_root = Path(args.rules)
    files = find_rule_files(rules_root)

    packs = {}
    mitre = set()
    for f in files:
        pack = pack_from_path(f)
        packs[pack] = packs.get(pack, 0) + 1
        for t in parse_mitre_techniques(f):
            mitre.add(t)

    changes = changed_files()
    new_rules = 0
    updated_rules = 0
    deprecated_rules = 0
    for status, fpath in changes:
        if not (fpath.startswith('detections/') and fpath.endswith('.yaml')):
            continue
        if status == 'A':
            new_rules += 1
        elif status == 'D':
            deprecated_rules += 1
        elif status in ('M', 'R', 'C'):
            updated_rules += 1

    manifest = {
        'release': args.release,
        'released_at': date.today().isoformat(),
        'rules': len(files),
        'new_rules': new_rules,
        'updated_rules': updated_rules,
        'deprecated_rules': deprecated_rules,
        'packs': dict(sorted(packs.items())),
        'mitre_coverage': {
            'total_techniques': len(mitre),
            'techniques': sorted(mitre),
        },
    }

    sig_index = load_signatures_index(Path(args.signatures_index))
    if sig_index is not None:
        manifest['signatures'] = sig_index

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {out}')


if __name__ == '__main__':
    main()
