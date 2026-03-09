# Repository Governance Policy (GitHub)

## Status
Approved

## Scope
This policy defines mandatory repository controls for detection engineering, governance artifacts, rollback workflows, and audit evidence in this repository.

## Protected Branches
- `main`
- `codex/compliance-engine`

## Branch Protection: `main`

### Pull Request Controls (Required)
- Require a pull request before merging: enabled
- Required approvals: 1 minimum
- Require review from CODEOWNERS: enabled
- Dismiss stale approvals when new commits are pushed: enabled
- Require conversation resolution before merging: enabled

### CI Gate Controls (Required)
- Require status checks to pass before merging: enabled
- Require branches to be up to date before merging: enabled
- Required checks:
  - `rollback-smoke`
  - `forecast-schema-validation`
  - `detection-validation`
  - `risk-gate`

### Integrity Controls (Required)
- Require signed commits: enabled
- Require linear history: enabled
- Allow force pushes: disabled
- Allow deletions: disabled
- Allow bypassing branch protections: disabled

### Hardening Controls (Recommended)
- Lock branch: enabled for governance-critical phases

## Branch Protection: `codex/compliance-engine`

### Merge and Mutation Controls (Required)
- Require a pull request before merging: enabled
- Allow direct pushes: disabled
- Allow force pushes: disabled
- Allow deletions: disabled

### Optional Controls
- Require status checks: optional for iteration speed
- Require signed commits: optional (recommended if team enforces org-wide signing)

## CODEOWNERS Requirement
A `CODEOWNERS` file must define owners for at least:
- `.github/workflows/*`
- `governance/**`
- `tools/**`
- `detections/**`

## Change Management Rules
Any change affecting the following requires explicit "Governance impact" notes in the PR description:
- signature generation or verification
- risk gating thresholds or logic
- rollback resolver/executor behavior
- manifest/signature index structure
- required CI checks

## Audit Mapping
This policy supports:
- deterministic release evidence
- controlled change approvals
- non-bypassable quality and risk gates
- traceable rollback and integrity controls

## Review Cadence
- Quarterly policy review
- Immediate review after any CI workflow rename, gate change, or branch model change

## Exception Handling
Exceptions must be time-bound and documented in a PR with:
- reason
- risk assessment
- compensating controls
- expiry date
- approver
