#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import jsonschema


def main():
    parser = argparse.ArgumentParser(description='Validate JSON file against JSON schema')
    parser.add_argument('--schema', required=True)
    parser.add_argument('--input', required=True)
    args = parser.parse_args()

    schema = json.loads(Path(args.schema).read_text(encoding='utf-8-sig'))
    data = json.loads(Path(args.input).read_text(encoding='utf-8-sig'))
    jsonschema.validate(data, schema)
    print(f'Validated {args.input} against {args.schema}')


if __name__ == '__main__':
    main()
