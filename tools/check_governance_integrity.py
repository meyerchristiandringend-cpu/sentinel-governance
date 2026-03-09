#!/usr/bin/env python3
import sys
from pathlib import Path


REQUIRED_FILES = [
    '.github/CODEOWNERS',
    '.github/workflows/governance-guard.yml',
    'governance/repository-governance.md',
    'governance/policy-change-control.md',
    'governance/governance-architecture-overview.md',
    'governance/governance-evidence-matrix.md',
]

REQUIRED_CODEOWNERS_PATHS = [
    '/.github/workflows/*',
    '/governance/**',
    '/tools/**',
    '/detections/**',
]

REQUIRED_MATRIX_REFERENCES = [
    'governance/repository-governance.md',
    '.github/CODEOWNERS',
    '.github/workflows/governance-guard.yml',
    'governance/policy-change-control.md',
    'governance/governance-architecture-overview.md',
]

REQUIRED_GUARD_MARKERS = [
    'name: Governance Guard',
    'pull_request:',
    'pull_request_review:',
    'core.setFailed',
    "governance/",
    ".github/workflows/",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def main() -> int:
    repo = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    failures = []
    warnings = []

    for rel in REQUIRED_FILES:
        p = repo / rel
        if not p.is_file():
            failures.append(f"missing required file: {rel}")

    codeowners_path = repo / '.github/CODEOWNERS'
    if codeowners_path.is_file():
        codeowners = read_text(codeowners_path)
        for rule in REQUIRED_CODEOWNERS_PATHS:
            if rule not in codeowners:
                failures.append(f"CODEOWNERS missing rule: {rule}")

    guard_path = repo / '.github/workflows/governance-guard.yml'
    if guard_path.is_file():
        guard = read_text(guard_path)
        for marker in REQUIRED_GUARD_MARKERS:
            if marker not in guard:
                failures.append(f"governance-guard workflow missing marker: {marker}")

    matrix_path = repo / 'governance/governance-evidence-matrix.md'
    if matrix_path.is_file():
        matrix = read_text(matrix_path)
        for reference in REQUIRED_MATRIX_REFERENCES:
            if reference not in matrix:
                warnings.append(f"evidence matrix missing explicit reference: {reference}")

    print('Governance Integrity Check')
    print(f'- Repository: {repo}')
    print(f'- Failures: {len(failures)}')
    print(f'- Warnings: {len(warnings)}')

    if warnings:
        print('\nWarnings:')
        for w in warnings:
            print(f'- {w}')

    if failures:
        print('\nFailures:')
        for f in failures:
            print(f'- {f}')
        return 1

    print('\nAll required governance integrity checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
