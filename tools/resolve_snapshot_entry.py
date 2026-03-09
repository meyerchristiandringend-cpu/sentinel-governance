#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def pick_snapshot_entry(manifest: dict, sig_index: dict, tag: str) -> dict:
    artifacts = sig_index.get('artifacts', [])

    # Preferred names for rollback package first, then baseline snapshot json fallback.
    preferred = [
        a for a in artifacts if a.get('name') in ('snapshot.tar.gz', 'detection-snapshot.tar.gz', 'detection-snapshot.json')
    ]

    if not preferred:
        raise SystemExit('No snapshot artifact entry found in signature index.')

    selected = None
    for entry in preferred:
        name = entry.get('name', '')
        path = entry.get('path', '')
        if tag and (tag in name or tag in path):
            selected = entry
            break

    if selected is None:
        selected = preferred[0]

    snapshot_id = tag or manifest.get('release', 'current')
    return {
        'id': snapshot_id,
        'manifest_release': manifest.get('release', 'current'),
        'git_commit': manifest.get('git_commit', ''),
        'timestamp': manifest.get('released_at', ''),
        'snapshot_artifact_path': selected.get('path', ''),
        'snapshot_signature_path': selected.get('signature', ''),
        'snapshot_certificate_path': selected.get('certificate', ''),
        'workflow_ref': sig_index.get('workflow_ref', ''),
        'oidc_issuer': sig_index.get('oidc_issuer', 'https://token.actions.githubusercontent.com'),
        'checksums': {
            selected.get('path', ''): selected.get('digest_sha256', '')
        },
    }


def main():
    parser = argparse.ArgumentParser(description='Resolve a rollback snapshot entry from manifest and signature index')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--index', required=True)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()

    manifest = load_json(Path(args.manifest))
    sig_index = load_json(Path(args.index))
    selected = pick_snapshot_entry(manifest, sig_index, args.tag)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(selected, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {out}')


if __name__ == '__main__':
    main()
