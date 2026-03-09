#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Fail CI when forecast gate status is BLOCK')
    parser.add_argument('--forecast', default='governance/forecast.json')
    parser.add_argument('--fail-on-block', action='store_true')
    parser.add_argument('--verify-signatures', action='store_true', help='Require valid cosign signatures before evaluating risk gate')
    parser.add_argument('--workflow-ref', help='Expected workflow identity for signature verification')
    parser.add_argument('--include-cab', action='store_true', help='Also verify CAB report signature')
    args = parser.parse_args()

    if args.verify_signatures:
        if not args.workflow_ref:
            raise SystemExit('--workflow-ref is required when --verify-signatures is set')
        cmd = [sys.executable, 'tools/verify_signatures.py', '--workflow-ref', args.workflow_ref]
        if args.include_cab:
            cmd.append('--include-cab')
        subprocess.run(cmd, check=True)

    forecast = json.loads(Path(args.forecast).read_text(encoding='utf-8-sig'))
    status = forecast.get('gate_status', 'ALLOW')
    risk = forecast.get('risk_score', 0)

    print(f'Gate status: {status}')
    print(f'Risk score: {risk}')

    if args.fail_on_block and status == 'BLOCK':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
