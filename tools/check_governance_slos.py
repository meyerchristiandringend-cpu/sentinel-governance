#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class SLOResult:
    id: str
    target: str
    actual: str
    status: str  # pass|warn|fail
    severity: str  # low|medium|high
    message: str
    action: str


def load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def check_core_policy(repo: Path) -> SLOResult:
    rel = 'governance/repository-governance.md'
    exists = (repo / rel).is_file()
    if exists:
        return SLOResult(
            id='core_policy_present',
            target='repository-governance.md exists',
            actual='present',
            status='pass',
            severity='low',
            message='Core governance policy is present.',
            action='No action required.',
        )
    return SLOResult(
        id='core_policy_present',
        target='repository-governance.md exists',
        actual='missing',
        status='fail',
        severity='high',
        message='Core governance policy is missing.',
        action='Restore governance/repository-governance.md before merge.',
    )


def check_forecast_risk(repo: Path) -> SLOResult:
    path = repo / 'governance/forecast.json'
    data = load_json(path)
    if data is None:
        return SLOResult(
            id='forecast_risk_threshold',
            target='risk_score < 80',
            actual='unavailable',
            status='warn',
            severity='medium',
            message='Forecast data unavailable; risk threshold cannot be evaluated.',
            action='Generate governance/forecast.json in CI before release decisions.',
        )

    score = data.get('risk_score', data.get('riskScore'))
    try:
        score_num = float(score)
    except Exception:
        return SLOResult(
            id='forecast_risk_threshold',
            target='risk_score < 80',
            actual='invalid',
            status='warn',
            severity='medium',
            message='Forecast risk score is missing or invalid.',
            action='Fix forecast schema/output to include numeric risk_score.',
        )

    if score_num < 80:
        status, severity, action = 'pass', 'low', 'No action required.'
    elif score_num < 90:
        status, severity, action = 'warn', 'medium', 'Review risk drivers and request CAB review if needed.'
    else:
        status, severity, action = 'fail', 'high', 'Block merge/release and remediate high risk conditions.'

    return SLOResult(
        id='forecast_risk_threshold',
        target='risk_score < 80',
        actual=str(score_num),
        status=status,
        severity=severity,
        message='Forecast risk threshold evaluation completed.',
        action=action,
    )


def check_drift_severity(repo: Path) -> SLOResult:
    path = repo / 'governance/drift-report.json'
    data = load_json(path)
    if data is None:
        return SLOResult(
            id='drift_critical_absence',
            target='no high-severity drift',
            actual='unavailable',
            status='warn',
            severity='medium',
            message='Drift report unavailable; critical drift state cannot be verified.',
            action='Run governance-drift-alert workflow to produce drift-report.json.',
        )

    severity = str(data.get('severity', 'none')).lower()
    if severity == 'high':
        return SLOResult(
            id='drift_critical_absence',
            target='no high-severity drift',
            actual='high',
            status='fail',
            severity='high',
            message='High-severity governance drift detected.',
            action='Escalate to CAB and resolve drift before merge.',
        )
    if severity == 'medium':
        return SLOResult(
            id='drift_critical_absence',
            target='no high-severity drift',
            actual='medium',
            status='warn',
            severity='medium',
            message='Medium-severity governance drift detected.',
            action='Resolve drift and re-run checks.',
        )

    return SLOResult(
        id='drift_critical_absence',
        target='no high-severity drift',
        actual=severity,
        status='pass',
        severity='low',
        message='No actionable drift severity detected.',
        action='No action required.',
    )


def check_evidence_packaging(repo: Path) -> SLOResult:
    root = repo / 'governance/evidence/quarterly'
    manifests = sorted(root.glob('*/*/package-manifest.json'))
    if manifests:
        return SLOResult(
            id='evidence_packaging_availability',
            target='quarterly package-manifest available',
            actual='present',
            status='pass',
            severity='low',
            message='At least one governance evidence package manifest is available.',
            action='No action required.',
        )

    return SLOResult(
        id='evidence_packaging_availability',
        target='quarterly package-manifest available',
        actual='missing',
        status='warn',
        severity='medium',
        message='No governance evidence package manifest found.',
        action='Run governance-evidence-packaging workflow to generate quarterly evidence artifacts.',
    )


def derive_status(results: list[SLOResult]) -> tuple[str, int]:
    if any(r.status == 'fail' for r in results):
        return 'fail', 2
    if any(r.status == 'warn' for r in results):
        return 'warn', 1
    return 'pass', 0


def to_markdown(status: str, results: list[SLOResult], actions: list[str]) -> str:
    icon = {'pass': '🟢', 'warn': '🟡', 'fail': '🔴'}.get(status, '⚪')
    lines = [
        '# Governance SLO Enforcement Report',
        '',
        f'Status: {icon} `{status.upper()}`',
        '',
        '| SLO | Target | Actual | Status | Severity |',
        '|---|---|---|---|---|',
    ]
    for r in results:
        lines.append(f"| `{r.id}` | {r.target} | {r.actual} | {r.status} | {r.severity} |")

    lines.extend(['', '## Findings'])
    for r in results:
        lines.append(f"- `{r.id}`: {r.message}")

    lines.extend(['', '## Required Actions'])
    for a in actions:
        lines.append(f'- {a}')

    lines.extend([
        '',
        '## References',
        '- `governance/governance-roadmap.md`',
        '- `governance/governance-maturity-rubric.md`',
        '- `governance/quarterly-governance-review-cycle.md`',
        '- `governance/governance-evidence-matrix.md`',
    ])

    return '\n'.join(lines) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description='Check governance SLOs and emit JSON/Markdown report')
    parser.add_argument('--repo', default='.', help='Repository root')
    parser.add_argument('--json-out', default='governance/slo-report.json', help='JSON output path')
    parser.add_argument('--md-out', default='governance/slo-report.md', help='Markdown output path')
    args = parser.parse_args()

    repo = Path(args.repo).resolve()

    results = [
        check_core_policy(repo),
        check_forecast_risk(repo),
        check_drift_severity(repo),
        check_evidence_packaging(repo),
    ]

    status, exit_code = derive_status(results)
    actions = [r.action for r in results if r.status in {'warn', 'fail'}]
    if not actions:
        actions = ['No action required.']

    report = {
        'slo_status': status,
        'violations': [asdict(r) for r in results if r.status in {'warn', 'fail'}],
        'checks': [asdict(r) for r in results],
        'required_actions': actions,
        'exit_code': exit_code,
    }

    json_out = repo / args.json_out
    md_out = repo / args.md_out
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    md_out.write_text(to_markdown(status, results, actions), encoding='utf-8')

    print(f'Wrote JSON report: {json_out}')
    print(f'Wrote Markdown report: {md_out}')
    print(f'SLO status={status} exit_code={exit_code}')
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
