#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
from shutil import copy2


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def copy_if_exists(src: Path, dst: Path):
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        copy2(src, dst)


def main():
    parser = argparse.ArgumentParser(description='Build evidence pack for PR/release auditing')
    parser.add_argument('--id', required=True, help='Evidence id (e.g. pr-142 or run-12345)')
    parser.add_argument('--manifest', default='releases/current/manifest.json')
    parser.add_argument('--forecast', default='governance/forecast.json')
    parser.add_argument('--compiled', default='governance/compiled-rules.json')
    parser.add_argument('--schema-validation', default='governance/schema-validation.json')
    parser.add_argument('--output-root', default='evidence')
    args = parser.parse_args()

    out = Path(args.output_root) / args.id
    out.mkdir(parents=True, exist_ok=True)

    manifest = Path(args.manifest)
    forecast = Path(args.forecast)
    compiled = Path(args.compiled)
    schema_validation = Path(args.schema_validation)

    copy_if_exists(manifest, out / 'manifest.json')
    copy_if_exists(forecast, out / 'forecast.json')
    copy_if_exists(compiled, out / 'compiled-rules.json')
    copy_if_exists(schema_validation, out / 'schema-validation.json')

    if manifest.exists():
        (out / 'manifest-digest.txt').write_text(f"{sha256(manifest)}  {manifest.as_posix()}\n", encoding='utf-8')

    metadata = {
        'evidence_id': args.id,
        'included': sorted([p.name for p in out.glob('*') if p.is_file()]),
    }
    (out / 'ci-run.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote evidence pack: {out}')


if __name__ == '__main__':
    main()
