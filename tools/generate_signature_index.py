#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def entry(name: str, artifact: str, sig: str, cert: str):
    artifact_path = Path(artifact)
    if not artifact_path.exists():
        raise FileNotFoundError(f'Missing artifact for signature index: {artifact}')
    if not Path(sig).exists():
        raise FileNotFoundError(f'Missing signature file for signature index: {sig}')
    if not Path(cert).exists():
        raise FileNotFoundError(f'Missing certificate file for signature index: {cert}')

    return {
        'name': name,
        'path': artifact,
        'digest_sha256': sha256_file(artifact_path),
        'signature': sig,
        'certificate': cert,
    }


def main():
    parser = argparse.ArgumentParser(description='Generate governance signature index JSON')
    parser.add_argument('--output', default='governance/signatures/index.json')
    parser.add_argument('--workflow-ref', default='', help='Signer workflow identity (e.g. github.workflow_ref)')
    parser.add_argument('--oidc-issuer', default='https://token.actions.githubusercontent.com')
    parser.add_argument('--include-cab', action='store_true')
    parser.add_argument('--include-snapshot', action='store_true')
    args = parser.parse_args()

    artifacts = [
        entry('forecast.json', 'governance/forecast.json', 'governance/signatures/forecast.json.sig', 'governance/signatures/forecast.json.pem'),
        entry('detection-snapshot.json', 'governance/baselines/detection-snapshot.json', 'governance/signatures/detection-snapshot.json.sig', 'governance/signatures/detection-snapshot.json.pem'),
        entry('compiled-rules.json', 'governance/compiled-rules.json', 'governance/signatures/compiled-rules.json.sig', 'governance/signatures/compiled-rules.json.pem'),
    ]

    if args.include_cab:
        artifacts.append(entry('cab-report.md', 'governance/cab-report.md', 'governance/signatures/cab-report.md.sig', 'governance/signatures/cab-report.md.pem'))

    if args.include_snapshot:
        artifacts.append(
            entry('snapshot.tar.gz', 'governance/snapshots/current/snapshot.tar.gz', 'governance/signatures/snapshot.tar.gz.sig', 'governance/signatures/snapshot.tar.gz.pem')
        )

    doc = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'workflow_ref': args.workflow_ref,
        'oidc_issuer': args.oidc_issuer,
        'artifacts': artifacts,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {out}')


if __name__ == '__main__':
    main()
