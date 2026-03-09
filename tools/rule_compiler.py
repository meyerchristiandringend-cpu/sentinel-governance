#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path

import yaml

from validators.kql_safety import guard_query_parts


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding='utf-8-sig'))


def dump_yaml(data: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=False), encoding='utf-8')


def stable_guid(name: str, version: int, env: str) -> str:
    seed = f"{name}-v{version}-{env}".encode('utf-8')
    digest = hashlib.sha1(seed).hexdigest()
    return str(uuid.UUID(digest[:32]))


def build_entity_mappings(entities: list) -> list:
    id_map = {
        'Account': 'FullName',
        'Host': 'HostName',
        'Ip': 'Address',
        'Url': 'Url',
        'File': 'Name',
        'Process': 'ProcessId',
        'AzureResource': 'ResourceId',
        'Mailbox': 'MailboxPrimaryAddress',
    }
    out = []
    for entity in entities or []:
        entity_type = entity['type']
        column = entity['field']
        identifier = id_map.get(entity_type, 'Field')
        out.append({'entityType': entity_type, 'fieldMappings': [{'identifier': identifier, 'columnName': column}]})
    return out


def resolve_metric(reduce: str, requested: str, metric_fallback: str = 'cnt') -> str:
    if not reduce:
        return requested or metric_fallback
    metric = requested or metric_fallback
    if metric and metric_fallback and metric != metric_fallback:
        if metric not in reduce and metric_fallback in reduce:
            return metric_fallback
    return metric


def synthesize_query(source_func: str, where: str, reduce: str, threshold: dict | None, metric_fallback: str = 'cnt') -> str:
    parts = [f"{source_func}()", f"| where {where or 'true'}"]
    if reduce and reduce.strip():
        parts.append(f"| {reduce.strip()}")
    if threshold:
        operator = threshold['operator']
        value = threshold['value']
        op_str = '>' if operator == 'GreaterThan' else '<' if operator == 'LessThan' else '=='
        metric = resolve_metric(reduce, threshold.get('metric', metric_fallback), metric_fallback)
        parts.append(f"| where {metric} {op_str} {value}")
    return '\n'.join(parts)


def ensure_pack_output(root: Path, pack: str) -> Path:
    out = root / f'detections/{pack}/rules/generated'
    out.mkdir(parents=True, exist_ok=True)
    return out


def list_functions(root: Path) -> set:
    found = set()
    for path in (root / 'detections').rglob('functions/*.kql'):
        found.add(path.stem)
    return found


def enforce_lifecycle(yaml_doc: dict):
    lifecycle = yaml_doc.get('metadata', {}).get('lifecycle', 'production')
    if lifecycle == 'experimental':
        incident = yaml_doc.setdefault('spec', {}).setdefault('incident', {})
        incident['createIncident'] = False
        incident['severity'] = incident.get('severity', 'Informational')


def derive_threshold(base: int, lookback_iso: str, multiplier: float | None = None) -> int:
    if multiplier is not None:
        return max(1, int(round(base * multiplier)))
    lb = lookback_iso.upper()
    if lb.startswith('PT') and lb.endswith('M'):
        minutes = int(lb[2:-1])
        factor = max(1, minutes // 5)
        return max(1, base * factor)
    if lb.startswith('PT') and lb.endswith('H'):
        hours = int(lb[2:-1])
        factor = max(1, (hours * 60) // 5)
        return max(1, base * factor)
    if lb.startswith('P') and 'D' in lb:
        days = int(lb[1 : lb.index('D')])
        factor = max(1, (days * 24 * 60) // 5)
        return max(1, base * factor)
    return base


def compile_from_config(repo_root: Path, technique_template: dict, params: dict, known_funcs: set, dry_run: bool = False):
    technique = technique_template['technique']
    base_name = technique_template['name']
    version = int(technique_template.get('version', 1))
    bindings = technique_template.get('bindings', [])
    default_owner = technique_template.get('owner', {})
    default_pack = technique_template.get('pack', None)

    compiled = []

    for binding in bindings:
        pack = binding.get('pack', default_pack)
        if not pack:
            raise ValueError("Binding must define 'pack' or template must have default 'pack'.")

        source_func = binding['sourceFunction']
        where = binding.get('where', 'true')
        reduce = binding.get('reduce', 'project TimeGenerated')
        entities = binding.get('entities', [])
        metadata_overrides = binding.get('metadata', {})

        if source_func not in known_funcs:
            raise ValueError(f"Unknown function '{source_func}' not found in detections/**/functions.")

        guard_query_parts(source_func, where, reduce)

        for variant in params.get('variants', []):
            env = variant.get('env', 'prod')
            schedule = variant['schedule']
            frequency = schedule['frequency']
            lookback = schedule['lookback']

            threshold_cfg = variant.get('threshold', {})
            base_threshold = threshold_cfg.get('base', 10)
            multiplier = threshold_cfg.get('multiplier')
            threshold_value = derive_threshold(base_threshold, lookback, multiplier)
            threshold = {
                'operator': threshold_cfg.get('operator', 'GreaterThan'),
                'value': threshold_value,
                'metric': threshold_cfg.get('metric', 'cnt'),
            }
            threshold['metric'] = resolve_metric(reduce, threshold.get('metric', 'cnt'), 'cnt')

            query = synthesize_query(source_func, where, reduce, threshold, metric_fallback='cnt')
            rule_name = f"{technique.lower()}-{base_name}-{binding['bindingName']}-{env}".replace('_', '-')
            display_name = metadata_overrides.get('displayName', f"{technique} {base_name} - {binding['bindingName']} ({env})")
            guid = stable_guid(rule_name, version, env)

            rule_doc = {
                'id': rule_name,
                'name': display_name,
                'query': query,
                'apiVersion': 'v1',
                'kind': 'scheduledRule',
                'metadata': {
                    'name': rule_name,
                    'displayName': display_name,
                    'owner': metadata_overrides.get('owner', default_owner or {'team': 'soc'}),
                    'domain': metadata_overrides.get('domain', pack),
                    'lifecycle': metadata_overrides.get('lifecycle', 'production'),
                    'version': version,
                    'mitre_techniques': [technique],
                    'pack': pack,
                    'stable_id': guid,
                },
                'entities': entities,
                'spec': {
                    'query': {
                        'sourceFunction': source_func,
                        'where': where,
                        'reduce': reduce,
                        'threshold': threshold,
                    },
                    'schedule': {'frequency': frequency, 'lookback': lookback},
                    'incident': {
                        'severity': metadata_overrides.get('severity', variant.get('severity', 'Medium')),
                        'createIncident': variant.get('createIncident', True),
                        'grouping': variant.get('grouping', {'enabled': True, 'lookback': 'PT1H', 'byEntities': ['User']}),
                    },
                    'suppression': variant.get('suppression', {'enabled': False}),
                    'enabled': variant.get('enabled', True),
                    'environments': [{'name': env, 'enabled': variant.get('enabled', True)}],
                },
                'metadata_ext': {'entityMappings': build_entity_mappings(entities)},
            }

            enforce_lifecycle(rule_doc)

            out_dir = ensure_pack_output(repo_root, pack)
            out_file = out_dir / f'{rule_name}.yaml'
            if not dry_run:
                dump_yaml(rule_doc, out_file)

            compiled.append({'name': rule_name, 'file': str(out_file), 'env': env, 'pack': pack, 'threshold': threshold_value, 'stable_id': guid})

    return compiled


def run_hook(cmd: list[str], cwd: Path):
    print('Running hook:', ' '.join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True)


def main():
    parser = argparse.ArgumentParser(description='Rule Compiler: Technique + Bindings + Param-Matrix -> synthesized rules')
    parser.add_argument('--repo', default='.', help='Repository root')
    parser.add_argument('--template', required=True, help='Technique template (JSON)')
    parser.add_argument('--params', required=True, help='Parameter matrix (YAML)')
    parser.add_argument('--dry-run', action='store_true', help='Do not write files')
    parser.add_argument('--snapshot', action='store_true', help='Run baseline snapshot hook')
    parser.add_argument('--forecast', action='store_true', help='Run forecast hook')
    parser.add_argument('--compiled-output', default='governance/compiled-rules.json', help='compiled rules output JSON')
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    technique_template = json.loads(Path(args.template).read_text(encoding='utf-8-sig'))
    params = load_yaml(Path(args.params))
    known_functions = list_functions(repo_root)

    compiled = compile_from_config(repo_root, technique_template, params, known_functions, dry_run=args.dry_run)
    compiled_doc = {'compiled': compiled, 'count': len(compiled)}

    compiled_out = repo_root / args.compiled_output
    if not args.dry_run:
        compiled_out.parent.mkdir(parents=True, exist_ok=True)
        compiled_out.write_text(json.dumps(compiled_doc, indent=2) + '\n', encoding='utf-8')

    if args.snapshot and not args.dry_run:
        run_hook([
            sys.executable,
            'tools/snapshot_hook.py',
            '--rules-root', 'detections',
            '--compiled', args.compiled_output,
            '--coverage', 'governance/mitre-coverage.json',
            '--output', 'governance/baselines/detection-snapshot.json',
            '--mitre-output', 'governance/baselines/mitre-coverage.snapshot.json',
        ], repo_root)

    if args.forecast and not args.dry_run:
        run_hook([
            sys.executable,
            'tools/forecast_hook.py',
            '--compiled', args.compiled_output,
            '--coverage', 'governance/mitre-coverage.json',
            '--previous-coverage', 'governance/baselines/mitre-coverage.snapshot.json',
            '--output', 'governance/forecast.json',
        ], repo_root)

    print(json.dumps(compiled_doc, indent=2))


if __name__ == '__main__':
    main()
