#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
from pathlib import Path


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def quarter_now() -> str:
    now = dt.datetime.now(dt.UTC)
    q = ((now.month - 1) // 3) + 1
    return f"{now.year}-Q{q}"


def status_from_exists(path: Path, severity='medium') -> tuple[str, str, str]:
    if path.is_file():
        return 'green', 'present', 'Artifact present'
    return ('red' if severity == 'high' else 'yellow'), 'missing', 'Artifact missing'


def load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate governance KPI snapshot')
    parser.add_argument('--repo', default='.', help='Repository root')
    parser.add_argument('--quarter', default=None, help='Quarter like YYYY-Q1')
    parser.add_argument('--json-out', default='governance/kpi-snapshot.json')
    parser.add_argument('--md-out', default='governance/kpi-summary.md')
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    quarter = args.quarter or quarter_now()
    if not re.match(r'^\d{4}-Q[1-4]$', quarter):
        raise SystemExit('quarter must match YYYY-Q[1-4]')

    ts = utc_now()
    kpis = []

    # KPI 1: PR approval compliance proxy via CODEOWNERS presence
    s, v, note = status_from_exists(repo / '.github/CODEOWNERS', severity='high')
    kpis.append({
        'id': 'kpi_governed_pr_approval_compliance',
        'name': 'Governance PR Approval Compliance',
        'category': 'control_enforcement',
        'target': '100%',
        'value': 'proxy: CODEOWNERS ' + v,
        'status': s,
        'severity': 'high',
        'source': '.github/CODEOWNERS',
        'timestamp_utc': ts,
        'notes': note,
    })

    # KPI 2: Integrity suite pass readiness proxy
    s, v, note = status_from_exists(repo / '.github/workflows/governance-integrity.yml', severity='high')
    kpis.append({
        'id': 'kpi_integrity_suite_pass_readiness',
        'name': 'Integrity Suite Pass Rate Readiness',
        'category': 'integrity_and_drift',
        'target': '100%',
        'value': 'proxy: governance-integrity workflow ' + v,
        'status': s,
        'severity': 'high',
        'source': '.github/workflows/governance-integrity.yml',
        'timestamp_utc': ts,
        'notes': note,
    })

    # KPI 3: Drift-free status from latest drift report if available
    drift = load_json(repo / 'governance/drift-report.json')
    if drift is None:
        status, value, note = 'yellow', 'unknown', 'No drift report found'
    else:
        sev = str(drift.get('severity', 'none')).lower()
        if sev == 'high':
            status, value, note = 'red', 'high_drift', 'High-severity drift present'
        elif sev in {'medium', 'low'}:
            status, value, note = 'yellow', f'{sev}_drift', 'Non-critical drift present'
        else:
            status, value, note = 'green', 'none', 'No actionable drift detected'
    kpis.append({
        'id': 'kpi_drift_free_state',
        'name': 'Drift-Free State',
        'category': 'integrity_and_drift',
        'target': 'no high-severity drift',
        'value': value,
        'status': status,
        'severity': 'medium',
        'source': 'governance/drift-report.json',
        'timestamp_utc': ts,
        'notes': note,
    })

    # KPI 4: Evidence packaging timeliness readiness
    pkg_root = repo / 'governance/evidence/quarterly'
    manifests = sorted(pkg_root.glob('*/*/package-manifest.json'))
    if manifests:
        status, value, note = 'green', 'available', 'At least one package manifest exists'
    else:
        status, value, note = 'yellow', 'missing', 'No package manifest found yet'
    kpis.append({
        'id': 'kpi_evidence_packaging_readiness',
        'name': 'Evidence Packaging Timeliness Readiness',
        'category': 'evidence',
        'target': '<24h from trigger',
        'value': value,
        'status': status,
        'severity': 'medium',
        'source': 'governance/evidence/quarterly/*/*/package-manifest.json',
        'timestamp_utc': ts,
        'notes': note,
    })

    # KPI 5: SLO compliance from latest report if available
    slo = load_json(repo / 'governance/slo-report.json')
    if slo is None:
        status, value, note = 'yellow', 'unknown', 'No SLO report found'
    else:
        slo_status = str(slo.get('slo_status', 'warn')).lower()
        status_map = {'pass': 'green', 'warn': 'yellow', 'fail': 'red'}
        status = status_map.get(slo_status, 'yellow')
        value = slo_status
        note = 'Derived from governance/slo-report.json'
    kpis.append({
        'id': 'kpi_slo_compliance_rate',
        'name': 'SLO Compliance Rate',
        'category': 'slo_sla',
        'target': '>=95%',
        'value': value,
        'status': status,
        'severity': 'high',
        'source': 'governance/slo-report.json',
        'timestamp_utc': ts,
        'notes': note,
    })

    # KPI 6: CAB SLA readiness proxy via policy document
    s, v, note = status_from_exists(repo / 'governance/policy-change-control.md', severity='medium')
    kpis.append({
        'id': 'kpi_cab_decision_sla_readiness',
        'name': 'CAB Decision SLA Readiness',
        'category': 'review_and_cab',
        'target': '<48h',
        'value': 'proxy: policy-change-control ' + v,
        'status': s,
        'severity': 'medium',
        'source': 'governance/policy-change-control.md',
        'timestamp_utc': ts,
        'notes': note,
    })

    if any(k['status'] == 'red' for k in kpis):
        overall = 'red'
    elif any(k['status'] == 'yellow' for k in kpis):
        overall = 'yellow'
    else:
        overall = 'green'

    actions = []
    for k in kpis:
        if k['status'] == 'red':
            actions.append(f"Immediate remediation required: {k['id']}")
        elif k['status'] == 'yellow':
            actions.append(f"Review and improve: {k['id']}")

    snapshot = {
        'generated_at_utc': ts,
        'quarter': quarter,
        'overall_status': overall,
        'kpis': kpis,
        'actions': actions,
    }

    json_out = repo / args.json_out
    md_out = repo / args.md_out
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(snapshot, indent=2) + '\n', encoding='utf-8')

    lines = [
        '# Governance KPI Snapshot',
        '',
        f"- Generated at: `{ts}`",
        f"- Quarter: `{quarter}`",
        f"- Overall status: `{overall}`",
        '',
        '| KPI | Target | Value | Status | Severity |',
        '|---|---|---|---|---|',
    ]
    for k in kpis:
        lines.append(f"| `{k['id']}` | {k['target']} | {k['value']} | {k['status']} | {k['severity']} |")
    lines.extend(['', '## Actions'])
    if actions:
        lines.extend([f'- {a}' for a in actions])
    else:
        lines.append('- No action required.')

    md_out.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print(f'Wrote KPI JSON snapshot: {json_out}')
    print(f'Wrote KPI Markdown summary: {md_out}')
    print(f'Overall status={overall}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
