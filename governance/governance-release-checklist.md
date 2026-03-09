# Governance Release Checklist

## Purpose
Defines mandatory release checks for governance-relevant changes before merge and before release tagging.

## PR Gate Checklist (Before Merge)
- [ ] PR includes governance impact summary
- [ ] Change type declared (`minor`, `standard`, `major`)
- [ ] Required approvals present
- [ ] CODEOWNERS review satisfied
- [ ] Required CI checks green:
  - [ ] `governance-guard`
  - [ ] `governance-integrity`
  - [ ] `risk-gate` (if applicable)
- [ ] No unresolved review conversations

## Control Integrity Checklist
- [ ] `governance/repository-governance.md` present and current
- [ ] `governance/policy-change-control.md` present and current
- [ ] `governance/governance-architecture-overview.md` present and current
- [ ] `governance/governance-evidence-matrix.md` present and current
- [ ] `.github/CODEOWNERS` includes governed path ownership
- [ ] `.github/workflows/governance-guard.yml` active
- [ ] `.github/workflows/governance-integrity.yml` active

## Evidence Checklist
- [ ] PR URL recorded
- [ ] Merge commit SHA recorded
- [ ] CI run URLs recorded
- [ ] Governed files changed list captured
- [ ] CAB decision reference attached (if triggered)
- [ ] Manifest/signature index references attached (if applicable)

## CAB Trigger Checklist
CAB review must be completed when one or more are true:
- [ ] Risk score `>= 60`
- [ ] Critical findings present
- [ ] Signature verification logic changed
- [ ] Rollback integrity logic changed
- [ ] Branch protection requirements reduced

## Release Readiness Checklist (Before Tag)
- [ ] Governance checks green on target commit
- [ ] No active governance exceptions without valid expiry
- [ ] Required runbooks and templates are present
- [ ] Release notes include governance-impact section
- [ ] Approvers and decision timestamp recorded

## Post-Release Verification
- [ ] Branch protection settings still match policy
- [ ] Governance workflows run successfully on `main`
- [ ] Evidence references archived with release artifacts
- [ ] Follow-up actions captured (if any)
