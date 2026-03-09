#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path, default=None):
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8-sig'))
    return default


def find_metric_in_reduce(reduce_expr: str, metric: str) -> bool:
    if not reduce_expr or not metric:
        return False
    return metric in reduce_expr


def add_finding(findings, severity, category, rule_id, message):
    findings.append(
        {
            'severity': severity,
            'category': category,
            'rule_id': rule_id,
            'message': message,
        }
    )


def score_findings(findings):
    weight = {'critical': 40, 'high': 20, 'medium': 10, 'low': 4}
    return sum(weight.get(f['severity'], 0) for f in findings)


def gate_status(risk_score, findings):
    has_critical = any(f['severity'] == 'critical' for f in findings)
    return 'BLOCK' if has_critical or risk_score >= 80 else 'ALLOW'


def build_mitre_diff(current, previous):
    cur = set((current or {}).get('techniques', {}).keys())
    prev = set((previous or {}).get('techniques', {}).keys())
    return {
        'added': sorted(cur - prev),
        'removed': sorted(prev - cur),
        'unchanged': sorted(cur & prev),
        'current_total': len(cur),
        'previous_total': len(prev),
    }


def main():
    parser = argparse.ArgumentParser(description='Create forecast and CAB risk summary')
    parser.add_argument('--compiled', default='governance/compiled-rules.json', help='compiler output json')
    parser.add_argument('--coverage', default='governance/mitre-coverage.json', help='current MITRE coverage')
    parser.add_argument('--previous-coverage', default='governance/baselines/mitre-coverage.snapshot.json', help='baseline MITRE coverage')
    parser.add_argument('--output', default='governance/forecast.json', help='forecast output file')
    args = parser.parse_args()

    compiled_doc = load_json(Path(args.compiled), default={'compiled': []})
    compiled_rules = compiled_doc.get('compiled', [])
    current_cov = load_json(Path(args.coverage), default={'techniques': {}, 'total_techniques': 0})
    previous_cov = load_json(Path(args.previous_coverage), default={'techniques': {}, 'total_techniques': 0})

    findings = []
    per_pack = defaultdict(lambda: {'rules': 0, 'experimental': 0, 'high_severity': 0})

    for item in compiled_rules:
        rule_file = Path(item['file'])
        if not rule_file.exists():
            add_finding(findings, 'critical', 'integrity', item.get('name', 'unknown'), 'Compiled rule file missing on disk.')
            continue

        import yaml

        data = yaml.safe_load(rule_file.read_text(encoding='utf-8-sig'))
        rid = data.get('id', item.get('name', 'unknown'))
        metadata = data.get('metadata', {})
        spec = data.get('spec', {})
        query_spec = spec.get('query', {})
        incident = spec.get('incident', {})
        pack = metadata.get('pack', item.get('pack', 'unknown'))

        per_pack[pack]['rules'] += 1

        lifecycle = metadata.get('lifecycle', 'production')
        if lifecycle == 'experimental':
            per_pack[pack]['experimental'] += 1
            if incident.get('createIncident', True):
                add_finding(findings, 'critical', 'lifecycle', rid, 'Experimental rule must set createIncident=false.')
            else:
                add_finding(findings, 'low', 'lifecycle', rid, 'Experimental rule detected (incident creation disabled).')

        sev = str(incident.get('severity', 'Medium')).lower()
        if sev in ('high', 'critical'):
            per_pack[pack]['high_severity'] += 1
            add_finding(findings, 'medium', 'severity', rid, f'High-impact severity configured: {incident.get("severity")}.')

        threshold = query_spec.get('threshold', {})
        threshold_value = threshold.get('value', 0)
        if isinstance(threshold_value, int) and threshold_value <= 0:
            add_finding(findings, 'high', 'threshold', rid, 'Threshold must be greater than 0.')

        metric = threshold.get('metric', 'cnt')
        reduce_expr = query_spec.get('reduce', '')
        if reduce_expr and metric and not find_metric_in_reduce(reduce_expr, metric):
            add_finding(findings, 'high', 'query', rid, f"Threshold metric '{metric}' is not produced in reduce expression.")

        entities = data.get('entities', [])
        if not entities:
            add_finding(findings, 'medium', 'entities', rid, 'No entities defined; triage quality may degrade.')

    raw_score = min(100, score_findings(findings))
    mitre_diff = build_mitre_diff(current_cov, previous_cov)

    if mitre_diff['added']:
        raw_score = max(0, raw_score - min(20, len(mitre_diff['added']) * 5))
    if mitre_diff['removed']:
        raw_score = min(100, raw_score + min(30, len(mitre_diff['removed']) * 10))

    risk_score = int(raw_score)
    status = gate_status(risk_score, findings)

    summary = {
        'compiled_rules': len(compiled_rules),
        'findings_total': len(findings),
        'findings_by_severity': {
            'critical': sum(1 for f in findings if f['severity'] == 'critical'),
            'high': sum(1 for f in findings if f['severity'] == 'high'),
            'medium': sum(1 for f in findings if f['severity'] == 'medium'),
            'low': sum(1 for f in findings if f['severity'] == 'low'),
        },
    }

    forecast = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'risk_score': risk_score,
        'gate_status': status,
        'summary': summary,
        'mitre_diff': mitre_diff,
        'pack_summary': dict(sorted(per_pack.items())),
        'findings': findings,
        'rules': compiled_rules,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(forecast, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {output}')


if __name__ == '__main__':
    main()
