#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import jsonschema
import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--schema', default='docs/detection-rule.schema.json')
    parser.add_argument('--rules-root', dest='rules_root')
    parser.add_argument('--path', dest='rules_path')
    args = parser.parse_args()

    root = args.rules_root or args.rules_path
    if not root:
        raise SystemExit('Provide --rules-root or --path')

    schema = json.loads(Path(args.schema).read_text(encoding='utf-8-sig'))
    files = sorted(Path(root).glob('**/*.yaml'))
    if not files:
        raise SystemExit('No rule files found.')

    for rule_file in files:
        data = yaml.safe_load(rule_file.read_text(encoding='utf-8-sig'))
        jsonschema.validate(data, schema)

    print(f'Validated {len(files)} rule(s).')


if __name__ == '__main__':
    main()
