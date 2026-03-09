#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re

PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
REQUIRED_KEYS = {"template_id", "technique", "name", "base_query", "parameters", "bindings"}


def render(text, values):
    def repl(match):
        key = match.group(1)
        return str(values.get(key, match.group(0)))

    return PLACEHOLDER.sub(repl, text)


def quote_string(value):
    if value == "" or any(ch in value for ch in [":", "#", "{", "}"]):
        return json.dumps(value)
    return value


def to_yaml(obj, indent=0):
    pad = " " * indent
    if isinstance(obj, dict):
        lines = []
        for key, value in obj.items():
            if isinstance(value, dict):
                lines.append(f"{pad}{key}:")
                lines.append(to_yaml(value, indent + 2))
            elif isinstance(value, list):
                lines.append(f"{pad}{key}:")
                lines.append(to_yaml(value, indent + 2))
            elif isinstance(value, str) and "\n" in value:
                lines.append(f"{pad}{key}: |")
                for line in value.splitlines():
                    lines.append(f"{pad}  {line}")
            elif isinstance(value, bool):
                lines.append(f"{pad}{key}: {'true' if value else 'false'}")
            elif value is None:
                lines.append(f"{pad}{key}: null")
            elif isinstance(value, (int, float)):
                lines.append(f"{pad}{key}: {value}")
            else:
                lines.append(f"{pad}{key}: {quote_string(str(value))}")
        return "\n".join(lines)

    if isinstance(obj, list):
        lines = []
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.append(to_yaml(item, indent + 2))
            elif isinstance(item, str):
                lines.append(f"{pad}- {quote_string(item)}")
            else:
                lines.append(f"{pad}- {item}")
        return "\n".join(lines)

    return f"{pad}{obj}"


def load_templates(input_dir=None, template=None):
    paths = []
    if input_dir:
        root = Path(input_dir)
        paths.extend(sorted(p for p in root.glob("*.json") if not p.name.endswith("schema.json")))
    if template:
        paths.append(Path(template))
    return paths


def remove_stale_rule_outputs(output_root, rule_id, target_path):
    for existing in Path(output_root).glob(f"*/rules/generated/{rule_id}.yaml"):
        if existing.resolve() != target_path.resolve():
            existing.unlink(missing_ok=True)


def is_expand_template(doc: dict) -> bool:
    return isinstance(doc, dict) and REQUIRED_KEYS.issubset(set(doc.keys()))


def expand_template(template_path, output_root):
    template = json.loads(Path(template_path).read_text(encoding="utf-8-sig"))
    if not is_expand_template(template):
        return 0

    default_owner = template.get(
        "owner",
        {"team": "detection-engineering", "slack": "#soc-detections", "oncall": "sec-detect-oncall"},
    )
    default_pack = template.get("default_pack", "identity")

    generated = 0
    for binding in template.get("bindings", []):
        source = binding["source"]
        pack = binding.get("pack", default_pack)
        mapping = dict(binding.get("mapping", {}))

        for pname, pdef in template.get("parameters", {}).items():
            mapping.setdefault(pname, pdef.get("default"))

        query = render(template["base_query"], mapping)
        name = f"{template['name']} ({source})"
        rule_id = f"{template['template_id']}-{source}"

        rule = {
            "id": rule_id,
            "name": name,
            "query": query,
            "metadata": {
                "name": name,
                "template_id": template["template_id"],
                "source": source,
                "mitre_techniques": [template["technique"]],
                "owner": dict(default_owner),
            },
        }

        out_dir = Path(output_root) / pack / "rules" / "generated"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{rule_id}.yaml"
        remove_stale_rule_outputs(output_root, rule_id, out_file)
        out_file.write_text(to_yaml(rule) + "\n", encoding="utf-8")
        generated += 1
    return generated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Directory containing technique templates (.json)")
    parser.add_argument("--template", help="Single template path (.json)")
    parser.add_argument("--output", required=True, help="Detections root directory")
    args = parser.parse_args()

    templates = load_templates(input_dir=args.input, template=args.template)
    if not templates:
        raise SystemExit("No templates found. Use --input or --template.")

    total = 0
    processed = 0
    for path in templates:
        generated = expand_template(path, args.output)
        if generated > 0:
            processed += 1
        total += generated

    print(f"Generated {total} rule(s) from {processed} compatible template(s).")


if __name__ == "__main__":
    main()
