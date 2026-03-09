# Policy Change Control

## Status
Approved

## Purpose
This document defines the mandatory process for changing governance policies in this repository.

## Scope
Applies to all changes in:
- `governance/**`
- `.github/CODEOWNERS`
- `.github/workflows/governance-guard.yml`
- repository branch protection requirements documented in policy files

## Change Classification
- `minor`: editorial or clarification-only changes without control impact
- `standard`: control, workflow, or ownership changes with expected low risk
- `major`: changes that weaken gates, reduce approvals, alter signature verification, or change rollback integrity controls

## Required Controls By Change Type

### Minor
- Pull request required
- At least 1 approval
- All required checks pass

### Standard
- Pull request required
- At least 1 approval
- CODEOWNERS review required
- All required checks pass
- "Governance impact" section completed in PR

### Major
- Pull request required
- At least 2 approvals (recommended via repository settings)
- CODEOWNERS review required
- All required checks pass
- CAB review required
- Explicit risk acceptance statement required
- Evidence links required (forecast, manifest/signature index, rollback impact)

## Mandatory PR Content
Every governance-affecting PR must include:
1. Change type (`minor|standard|major`)
2. Governance impact summary
3. Risk and compensating controls
4. Rollback plan
5. Evidence references

## CAB Trigger Conditions
CAB review is mandatory when at least one is true:
- Risk score is `>= 60`
- Any critical finding exists
- Signature verification behavior changes
- Rollback resolver/executor behavior changes
- Branch protection requirements are reduced

## Prohibited Changes
The following are not allowed without an approved exception:
- Removing required checks from protected branches
- Allowing force push or deletion on `main`
- Disabling signed commits on `main`
- Bypassing CODEOWNERS on governance-critical paths
- Weakening rollback integrity verification without compensating controls

## Exception Process
An exception must be documented in the PR with:
- business justification
- risk statement
- compensating controls
- approver
- expiry date

Expired exceptions must be removed immediately.

## Evidence Requirements
For standard and major changes, attach or reference:
- CI run URL
- relevant workflow/job results
- manifest/signature index delta (if applicable)
- rollback validation evidence (if applicable)

## Merge Rules
A governance policy change may merge only when:
- required approvals are present
- required checks pass
- required CAB decision exists (if triggered)
- no unresolved review conversations remain

## Post-Merge Review
- Validate branch protection settings still match policy
- Confirm guard workflows are green on the merge commit
- Record review outcome in release/governance notes

## Review Cadence
- Quarterly control review
- Immediate review after incidents, audit findings, or major workflow changes
