# Governance Architecture Overview

## Purpose
This document summarizes the governance architecture for this repository in an audit-ready form.

## Architecture Layers

### Layer 1: Policy Definition
Defines mandatory governance controls and repository rules.

Primary artifacts:
- `governance/repository-governance.md`
- branch protection configuration in GitHub settings

Key controls:
- required PR reviews
- required status checks
- signed commits and linear history
- non-bypassable protection settings

### Layer 2: Policy Enforcement
Implements automated and ownership-based enforcement of defined controls.

Primary artifacts:
- `.github/CODEOWNERS`
- `.github/workflows/governance-guard.yml`

Key controls:
- governed path detection
- approval threshold enforcement for governed paths
- draft PR blocking on governed path changes
- CI summary output for reviewer transparency

### Layer 3: Policy Change Control
Defines how governance controls themselves may be changed.

Primary artifact:
- `governance/policy-change-control.md`

Key controls:
- change classification (`minor`, `standard`, `major`)
- CAB trigger conditions
- mandatory PR content for governance changes
- exception process with expiry and compensating controls

## Evidence Flow
1. Change is proposed in a PR.
2. `CODEOWNERS` routes review ownership.
3. `governance-guard` evaluates governed-path impact and approvals.
4. Required checks pass and merge criteria are met.
5. Merge commit on `main` provides immutable change anchor.
6. Policy and control artifacts remain versioned in Git history.

## Audit Mapping
This architecture provides:
- deterministic traceability for governance-relevant changes
- explicit accountability through ownership and approvals
- non-silent control enforcement through CI gates
- controlled policy evolution with documented exceptions

## Operational Model
- Governance changes are merged only through reviewed PRs.
- Governance controls are treated as code and versioned with the same rigor.
- Periodic review is required to keep policy and enforcement aligned.

## Review Cadence
- Quarterly governance architecture review
- Immediate review after:
  - audit findings
  - incidents affecting control integrity
  - changes to branch model, CI checks, or signing requirements
