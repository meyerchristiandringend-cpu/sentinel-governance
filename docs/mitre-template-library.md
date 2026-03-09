# MITRE Technique Template Library

## Ziel
Skalierbare Rule-Generierung pro MITRE-Technik durch Template + Binding.

## Architektur
1. Technique Template (`templates/mitre-techniques/*.json`)
2. Parameter Expansion (`tools/expand_mitre_templates.py`)
3. Log Source Binding (`bindings` im Template)
4. Generated Rules (`detections/<domain>/rules/generated/*.json`)

## Flow
- Ein Template definiert Basislogik und Parameter.
- Bindings mapen Log-Source-Felder auf Platzhalter.
- Expansion erzeugt pro Binding eine konkrete Rule.
- Coverage kann über `metadata.mitre_techniques` aggregiert werden.

## Beispiel
Template: `T1110-password-spray.json`
Bindings: `entra-id`, `vpn`
Output: zwei konkrete Regeln mit stabilen IDs.

