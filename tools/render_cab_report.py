#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Render CAB markdown report from forecast.json')
    parser.add_argument('--forecast', default='governance/forecast.json')
    parser.add_argument('--output', default='governance/cab-report.md')
    args = parser.parse_args()

    forecast = json.loads(Path(args.forecast).read_text(encoding='utf-8-sig'))

    lines = []
    lines.append('# Detection CAB Forecast')
    lines.append('')
    lines.append(f"- Gate: **{forecast['gate_status']}**")
    lines.append(f"- Risk Score: **{forecast['risk_score']} / 100**")
    lines.append(f"- Compiled Rules: **{forecast['summary']['compiled_rules']}**")
    lines.append(f"- Findings: **{forecast['summary']['findings_total']}**")
    lines.append('')

    fbs = forecast['summary']['findings_by_severity']
    lines.append('## Findings by Severity')
    lines.append(f"- Critical: {fbs['critical']}")
    lines.append(f"- High: {fbs['high']}")
    lines.append(f"- Medium: {fbs['medium']}")
    lines.append(f"- Low: {fbs['low']}")
    lines.append('')

    md = forecast['mitre_diff']
    lines.append('## MITRE Coverage Diff')
    lines.append(f"- Added techniques: {', '.join(md['added']) if md['added'] else 'none'}")
    lines.append(f"- Removed techniques: {', '.join(md['removed']) if md['removed'] else 'none'}")
    lines.append(f"- Current total: {md['current_total']} (previous: {md['previous_total']})")
    lines.append('')

    lines.append('## Pack Summary')
    for pack, vals in forecast.get('pack_summary', {}).items():
        lines.append(
            f"- {pack}: rules={vals['rules']}, experimental={vals['experimental']}, high_severity={vals['high_severity']}"
        )
    lines.append('')

    lines.append('## Top Findings')
    for finding in forecast.get('findings', [])[:15]:
        lines.append(
            f"- [{finding['severity'].upper()}] {finding['rule_id']} ({finding['category']}): {finding['message']}"
        )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
    print(f'Wrote {out}')


if __name__ == '__main__':
    main()
