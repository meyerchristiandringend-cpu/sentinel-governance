# Auditor Quick Pack

## Scope
This pack provides the minimum artifact set and verification commands for a SENTINEL governance audit.

## Core Artifacts
- `governance/forecast.json`
- `governance/baselines/detection-snapshot.json`
- `governance/compiled-rules.json`
- `governance/cab-report.md`
- `governance/snapshots/current/snapshot.tar.gz`
- `governance/signatures/index.json`
- `releases/current/manifest.json`
- `governance/rollback_audit.json` (when rollback executed)

## Signature Verification
Expected OIDC issuer:
- `https://token.actions.githubusercontent.com`

Verify standard governance artifacts:
```bash
python tools/verify_signatures.py --workflow-ref "<github.workflow_ref>" --include-cab
```

Verify rollback snapshot package:
```bash
python tools/verify_signatures.py \
  --workflow-ref "<github.workflow_ref>" \
  --artifact governance/snapshots/current/snapshot.tar.gz \
  --signature governance/signatures/snapshot.tar.gz.sig \
  --certificate governance/signatures/snapshot.tar.gz.pem
```

## Forecast and Policy Validation
Validate forecast JSON schema:
```bash
python tools/validate_json.py --schema tools/forecast.schema.json --input governance/forecast.json
```

Evaluate risk gate:
```bash
python tools/risk_gate.py \
  --forecast governance/forecast.json \
  --verify-signatures \
  --workflow-ref "<github.workflow_ref>" \
  --include-cab \
  --fail-on-block
```

## Rollback Forensics
Resolve and verify selected snapshot entry:
```bash
python tools/resolve_snapshot_entry.py \
  --manifest releases/current/manifest.json \
  --index governance/signatures/index.json \
  --tag <snapshot_tag> \
  --out governance/selected_snapshot.json
```

Execute rollback restore:
```bash
python tools/rollback_from_snapshot.py \
  --snapshot-dir governance/snapshot \
  --manifest governance/selected_snapshot.json
```

Audit evidence file:
- `governance/rollback_audit.json`

Required fields to review:
- `snapshot_id`
- `git_commit`
- `status`
- `backup_path`
- `replaced_paths`
- `duration_seconds`
- `error`

## CI Evidence Points
- Workflow: `.github/workflows/detections-ci.yml`
- Workflow: `.github/workflows/rollback.yml`
- Workflow: `.github/workflows/rollback-smoke.yml`
- Unit tests: `tests/test_rollback.py`, `tests/test_rollback_mid_swap.py`

## Release Readiness Quick Check
- Signatures generated and verified
- Forecast schema validation passed
- Risk gate status is `ALLOW`
- CAB report published to PR comment and step summary
- Manifest includes `signatures` section
- Rollback smoke test passed
