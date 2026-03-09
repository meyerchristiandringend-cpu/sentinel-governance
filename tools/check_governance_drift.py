#!/usr/bin/env python3
import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path

CORE_REQUIRED_FILES = [
    'governance/repository-governance.md',
]

OPTIONAL_GOV_FILES = [
    '.github/CODEOWNERS',
    '.github/workflows/governance-guard.yml',
    '.github/workflows/governance-integrity.yml',
    '.github/workflows/governance-evidence-packaging.yml',
    'governance/policy-change-control.md',
    'governance/governance-architecture-overview.md',
    'governance/governance-evidence-matrix.md',
    'governance/governance-release-checklist.md',
    'governance/quarterly-governance-review-cycle.md',
    'governance/governance-maturity-rubric.md',
]

REQUIRED_CODEOWNERS_RULES = [
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

REQUIRED_QUARTERLY_REFERENCES = [
    'governance/policy-change-control.md',
    '.github/workflows/governance-guard.yml',
    '.github/workflows/governance-integrity.yml',
]


@dataclass
class Violation:
    severity: str
    kind: str
    message: str
    artifact: str


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def classify(violations: list[Violation]) -> tuple[bool, str, int]:
    actionable = [v for v in violations if v.severity in {'low', 'medium', 'high'}]
    if not actionable:
        return False, 'none', 0
    if any(v.severity == 'high' for v in actionable):
        return True, 'high', 2
    if any(v.severity == 'medium' for v in actionable):
        return True, 'medium', 1
    return True, 'low', 1


def build_markdown(report: dict) -> str:
    severity = report['severity']
    emoji = '🟢' if severity == 'none' else ('🟡' if severity in ('low', 'medium') else '🔴')

    lines = [
        '# Governance Drift Report',
        '',
        f"Status: {emoji} `{severity.upper()}`",
        f"Drift detected: `{str(report['drift_detected']).lower()}`",
        f"Violations: `{len(report['violations'])}`",
        '',
        '| Severity | Type | Artifact | Message |',
        '|---|---|---|---|',
    ]

    if report['violations']:
        for v in report['violations']:
            lines.append(f"| {v['severity']} | {v['kind']} | `{v['artifact']}` | {v['message']} |")
    else:
        lines.append('| none | none | `n/a` | No drift violations found. |')

    lines.extend(['', '## Recommended Actions'])
    if report['recommended_actions']:
        lines.extend([f"- {a}" for a in report['recommended_actions']])
    else:
        lines.append('- No action required.')

    lines.extend([
        '',
        '## References',
        '- `governance/governance-evidence-matrix.md`',
        '- `governance/quarterly-governance-review-cycle.md`',
    ])

    return '\n'.join(lines) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description='Detect governance drift and emit JSON/Markdown reports')
    parser.add_argument('--repo', default='.', help='Repository root')
    parser.add_argument('--json-out', default='governance/drift-report.json', help='JSON report path')
    parser.add_argument('--md-out', default='governance/drift-report.md', help='Markdown report path')
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    violations: list[Violation] = []
    recommendations: list[str] = []

    for rel in CORE_REQUIRED_FILES:
        if not (repo / rel).is_file():
            violations.append(Violation('high', 'missing_core_artifact', 'Core governance artifact is missing.', rel))

    for rel in OPTIONAL_GOV_FILES:
        if not (repo / rel).is_file():
            violations.append(Violation('info', 'missing_optional_artifact', 'Governance artifact not present in this branch baseline.', rel))

    codeowners_path = repo / '.github/CODEOWNERS'
    if codeowners_path.is_file():
        codeowners = read_text(codeowners_path)
        for rule in REQUIRED_CODEOWNERS_RULES:
            if rule not in codeowners:
                violations.append(Violation('high', 'codeowners_drift', 'Required governed path rule is missing in CODEOWNERS.', '.github/CODEOWNERS'))

    guard_path = repo / '.github/workflows/governance-guard.yml'
    if guard_path.is_file():
        guard = read_text(guard_path)
        for marker in ['name: Governance Guard', 'pull_request:', 'core.setFailed']:
            if marker not in guard:
                violations.append(Violation('high', 'guard_workflow_drift', f'Governance guard workflow missing marker `{marker}`.', '.github/workflows/governance-guard.yml'))

    matrix_path = repo / 'governance/governance-evidence-matrix.md'
    if matrix_path.is_file():
        matrix = read_text(matrix_path)
        for ref in REQUIRED_MATRIX_REFERENCES:
            if ref not in matrix:
                violations.append(Violation('medium', 'matrix_drift', f'Evidence matrix missing reference `{ref}`.', 'governance/governance-evidence-matrix.md'))

    quarterly_path = repo / 'governance/quarterly-governance-review-cycle.md'
    if quarterly_path.is_file():
        quarterly = read_text(quarterly_path)
        for ref in REQUIRED_QUARTERLY_REFERENCES:
            if ref not in quarterly:
                violations.append(Violation('medium', 'quarterly_drift', f'Quarterly review cycle missing reference `{ref}`.', 'governance/quarterly-governance-review-cycle.md'))

    release_path = repo / 'governance/governance-release-checklist.md'
    if release_path.is_file():
        release = read_text(release_path)
        if 'governance-integrity' not in release:
            violations.append(Violation('low', 'release_checklist_drift', 'Release checklist should include governance-integrity check reference.', 'governance/governance-release-checklist.md'))

    drift_detected, severity, exit_code = classify(violations)

    if severity == 'high':
        recommendations.append('Trigger CAB escalation and block merge until high-severity drift is resolved.')
    elif severity == 'medium':
        recommendations.append('Block merge and remediate governance documentation/enforcement drift.')
    elif severity == 'low':
        recommendations.append('Resolve governance checklist/reference drift before release.')
    else:
        recommendations.append('No actionable governance drift detected.')

    report = {
        'drift_detected': drift_detected,
        'severity': severity,
        'violations': [asdict(v) for v in violations],
        'recommended_actions': recommendations,
    }

    json_out = repo / args.json_out
    md_out = repo / args.md_out
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    md_out.write_text(build_markdown(report), encoding='utf-8')

    print(f'Wrote JSON report: {json_out}')
    print(f'Wrote Markdown report: {md_out}')
    print(f"Drift detected={drift_detected} severity={severity} exit_code={exit_code}")
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
