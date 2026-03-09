#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
from shutil import copy2

ARTIFACTS = [
    '.github/CODEOWNERS',
    '.github/workflows/governance-guard.yml',
    '.github/workflows/governance-integrity.yml',
    'governance/repository-governance.md',
    'governance/policy-change-control.md',
    'governance/governance-architecture-overview.md',
    'governance/governance-evidence-matrix.md',
    'governance/governance-release-checklist.md',
    'governance/quarterly-governance-review-cycle.md',
    'governance/governance-maturity-rubric.md',
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            digest.update(chunk)
    return digest.hexdigest()


def quarter_from_date(now: dt.datetime) -> str:
    q = ((now.month - 1) // 3) + 1
    return f"{now.year}-Q{q}"


def normalize_quarter(value: str | None) -> str:
    if not value:
        return quarter_from_date(dt.datetime.now(dt.UTC))
    if not re.match(r'^\d{4}-Q[1-4]$', value):
        raise ValueError('quarter must match YYYY-Q[1-4]')
    return value


def copy_artifact(repo: Path, rel: str, package_root: Path, included: dict, missing: list | None):
    src = repo / rel
    if not src.is_file():
        if missing is not None:
            missing.append(rel)
        return
    dst = package_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    copy2(src, dst)
    included[rel] = {
        'sha256': sha256(src),
        'bytes': src.stat().st_size,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Build governance evidence package')
    parser.add_argument('--repo', default='.', help='Repository root path')
    parser.add_argument('--quarter', default=None, help='Quarter identifier (YYYY-Q1..Q4)')
    parser.add_argument('--run-id', default=None, help='Run identifier, defaults to timestamp')
    parser.add_argument('--output-root', default='governance/evidence/quarterly', help='Evidence root output directory')
    parser.add_argument('--fail-on-missing', action='store_true', help='Return non-zero when required artifacts are missing')
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    quarter = normalize_quarter(args.quarter)
    run_id = args.run_id or dt.datetime.now(dt.UTC).strftime('%Y%m%dT%H%M%SZ')

    package_root = repo / args.output_root / quarter / run_id
    package_root.mkdir(parents=True, exist_ok=True)

    included = {}
    missing = []

    for rel in ARTIFACTS:
        copy_artifact(repo, rel, package_root, included, missing)

    optional_inputs = [
        'governance/forecast.json',
        'governance/compiled-rules.json',
        'governance/cab-report.md',
        'governance/signatures/index.json',
        'releases/current/manifest.json',
    ]
    optional_present = []
    for rel in optional_inputs:
        src = repo / rel
        if src.is_file():
            copy_artifact(repo, rel, package_root, included, missing=None)
            optional_present.append(rel)

    metadata = {
        'generated_at_utc': dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        'quarter': quarter,
        'run_id': run_id,
        'source_repo': str(repo),
        'source_ref': os.getenv('GITHUB_REF', ''),
        'source_sha': os.getenv('GITHUB_SHA', ''),
        'workflow': os.getenv('GITHUB_WORKFLOW', ''),
        'workflow_run_id': os.getenv('GITHUB_RUN_ID', ''),
        'included_count': len(included),
        'missing_required': sorted(missing),
        'optional_present': sorted(optional_present),
        'artifacts': included,
    }

    manifest_path = package_root / 'package-manifest.json'
    manifest_path.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')

    summary_path = package_root / 'summary.md'
    summary_lines = [
        '# Governance Evidence Package',
        '',
        f'- Quarter: `{quarter}`',
        f'- Run ID: `{run_id}`',
        f'- Included required artifacts: `{len(included) - len(optional_present)}`',
        f'- Included optional artifacts: `{len(optional_present)}`',
        f'- Missing required artifacts: `{len(missing)}`',
        '',
    ]
    if missing:
        summary_lines.extend(['## Missing Required Artifacts', ''])
        summary_lines.extend([f'- `{x}`' for x in sorted(missing)])
        summary_lines.append('')
    summary_lines.extend(['## Included Artifacts', ''])
    summary_lines.extend([f'- `{p}`' for p in sorted(included.keys())])
    summary_path.write_text('\n'.join(summary_lines) + '\n', encoding='utf-8')

    print(f'Wrote governance evidence package: {package_root}')
    print(f'Manifest: {manifest_path}')
    print(f'Summary: {summary_path}')

    if missing and args.fail_on_missing:
        print('Missing required artifacts detected.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

