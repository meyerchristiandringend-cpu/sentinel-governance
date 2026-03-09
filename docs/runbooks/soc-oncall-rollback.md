# SOC Oncall Runbook: Rollback and Forensics

## Ziel
Schnelles, nachvollziehbares Rollback auf signierten Snapshot und forensische Sicherung relevanter Artefakte.

## Voraussetzungen
- Zugriff auf GitHub Actions Logs und Artifacts
- Berechtigung zum Ausloesen des Workflows `Rollback From Snapshot`
- Zugriff auf `releases/current/manifest.json` und `governance/signatures/index.json`

## Ablauf
1. Alert bestaetigen
- Forecast report und Gate Reason pruefen.
- `snapshot_id`, `risk_score`, `forecast.json` referenzieren.

2. CAB informieren
- CAB Template verwenden: `governance/templates/cab-comment-template.md`.

3. Rollback ausloesen
- GitHub Actions -> `Rollback From Snapshot`.
- `snapshot_tag` aus signiertem Index eingeben.

4. Verifikation
- Workflow muss Signatur-Gate bestehen.
- `governance/rollback_audit.json` als Nachweis sichern.

5. Nachkontrolle
- Detection-Deploy auf letzten signierten Stand pruefen.
- Post-Mortem mit CAB und Detection Engineering.

## Forensik-Artefakte
- `governance/selected_snapshot.json`
- Snapshot artifact (z. B. `snapshot.tar.gz`)
- `governance/rollback_audit.json`
- Workflow logs inkl. Cosign verification output

## Quick Commands
```bash
python tools/resolve_snapshot_entry.py --manifest governance/manifest.json --index governance/signatures/index.json --tag <snapshot_tag> --out governance/selected_snapshot.json
python tools/verify_signatures.py --workflow-ref <workflow_ref> --artifact <artifact> --signature <sig> --certificate <cert>
gh workflow run rollback.yml -f snapshot_tag=<snapshot_tag>
```

## Escalation
- Level 1: SOC Lead (Rollback fehlgeschlagen oder checksum mismatch)
- Level 2: DevOps + CAB (mehrere invalide snapshots/signatures)
- Level 3: Legal/Compliance (Integritaets- oder Audit-Relevanz)
