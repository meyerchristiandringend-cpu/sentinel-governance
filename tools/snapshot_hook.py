#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def collect_rule_snapshot(rule_path: Path) -> dict:
    data = yaml.safe_load(rule_path.read_text(encoding='utf-8-sig'))
    metadata = data.get('metadata', {})
    spec = data.get('spec', {})
    query_spec = spec.get('query', {})

    return {
        'id': data.get('id') or metadata.get('name') or rule_path.stem,
        'name': data.get('name') or metadata.get('displayName') or rule_path.stem,
        'pack': metadata.get('pack', 'unknown'),
        'lifecycle': metadata.get('lifecycle', 'production'),
        'severity': spec.get('incident', {}).get('severity', 'Medium'),
        'enabled': spec.get('enabled', True),
        'threshold': query_spec.get('threshold', {}),
        'stable_id': metadata.get('stable_id', ''),
        'sha256': file_sha256(rule_path),
        'path': str(rule_path).replace('\\', '/'),
    }


def parse_mitre_coverage(coverage_file: Path) -> dict:
    if not coverage_file.exists():
        return {'techniques': {}, 'total_techniques': 0}
    return json.loads(coverage_file.read_text(encoding='utf-8-sig'))


def files_from_compiled(compiled_path: Path) -> list[Path]:
    if not compiled_path.exists():
        return []
    doc = json.loads(compiled_path.read_text(encoding='utf-8-sig'))
    out = []
    for item in doc.get('compiled', []):
        p = Path(item.get('file', ''))
        if p.exists():
            out.append(p)
    return sorted(out)


def main():
    parser = argparse.ArgumentParser(description='Create baseline snapshot for generated detections')
    parser.add_argument('--rules-root', default='detections', help='detections root')
    parser.add_argument('--compiled', default='governance/compiled-rules.json', help='compiled rules JSON')
    parser.add_argument('--coverage', default='governance/mitre-coverage.json', help='current MITRE coverage')
    parser.add_argument('--output', default='governance/baselines/detection-snapshot.json', help='snapshot output json')
    parser.add_argument('--mitre-output', default='governance/baselines/mitre-coverage.snapshot.json', help='MITRE baseline output json')
    args = parser.parse_args()

    compiled_files = files_from_compiled(Path(args.compiled))
    if compiled_files:
        rule_files = compiled_files
    else:
        rules_root = Path(args.rules_root)
        rule_files = sorted(rules_root.glob('**/rules/generated/*.yaml'))

    snapshots = [collect_rule_snapshot(path) for path in rule_files]

    snapshot_doc = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'rules': snapshots,
        'count': len(snapshots),
        'packs': sorted({r['pack'] for r in snapshots}),
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot_doc, indent=2) + '\n', encoding='utf-8')

    coverage = parse_mitre_coverage(Path(args.coverage))
    mitre_out = Path(args.mitre_output)
    mitre_out.parent.mkdir(parents=True, exist_ok=True)
    mitre_out.write_text(json.dumps(coverage, indent=2) + '\n', encoding='utf-8')

    print(f'Wrote snapshot: {out}')
    print(f'Wrote MITRE baseline: {mitre_out}')


if __name__ == '__main__':
    main()
