#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


def changed_files():
    try:
        out = subprocess.check_output(['git', 'diff', '--name-status', 'HEAD~1', 'HEAD'], text=True)
    except Exception:
        return []
    lines = []
    for line in out.splitlines():
        parts = line.split('\t', 1)
        if len(parts) == 2:
            lines.append((parts[0], parts[1]))
    return lines


def rule_name_from_path(path: str) -> str:
    return Path(path).stem


def main():
    parser = argparse.ArgumentParser(description='Generate release notes from rule changes')
    parser.add_argument('--release', default='current')
    parser.add_argument('--output', default='releases/current/release-notes.md')
    args = parser.parse_args()

    added, updated, deprecated = [], [], []
    for status, file_path in changed_files():
        if not (file_path.startswith('detections/') and file_path.endswith('.yaml')):
            continue
        name = rule_name_from_path(file_path)
        if status == 'A':
            added.append(name)
        elif status in ('M', 'R', 'C'):
            updated.append(name)
        elif status == 'D':
            deprecated.append(name)

    lines = [f'# SENTINEL Detection Release {args.release}', '']

    lines.append('## Added')
    lines.extend([f'- {x}' for x in sorted(set(added))] or ['- none'])
    lines.append('')

    lines.append('## Updated')
    lines.extend([f'- {x}' for x in sorted(set(updated))] or ['- none'])
    lines.append('')

    lines.append('## Deprecated')
    lines.extend([f'- {x}' for x in sorted(set(deprecated))] or ['- none'])
    lines.append('')

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote {out}')


if __name__ == '__main__':
    main()
