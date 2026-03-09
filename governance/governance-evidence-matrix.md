# Governance Evidence Matrix

## Purpose
This matrix maps governance components to control intent, enforcement mechanism, and produced evidence.

| Component | Purpose | Enforcement Mechanism | Evidence Output | Verification Point |
|---|---|---|---|---|
| `governance/repository-governance.md` | Defines mandatory repository governance controls and branch protection baseline. | Review-gated changes via PR + governance guard on governed paths. | Versioned policy in Git history and merge commits. | PR review + merged commit on `main`. |
| `.github/CODEOWNERS` | Assigns accountable reviewers for governance-critical paths. | GitHub CODEOWNERS required review (when branch protection enables it). | Review assignment + approval record in PR timeline. | PR review logs and merge gate decisions. |
| `.github/workflows/governance-guard.yml` | Enforces governance checks for governed-path PRs. | CI workflow checks changed files, approval threshold, and draft blocking. | Workflow run logs + Step Summary decision output. | Required status check result before merge. |
| `governance/policy-change-control.md` | Controls how governance policies may be changed. | Mandatory PR content, change classification, CAB trigger conditions. | PR description content + CAB decision references. | PR checklist + CAB record when triggered. |
| `governance/governance-architecture-overview.md` | Documents end-to-end governance architecture and evidence flow. | Controlled via governed-path review and CI checks. | Versioned architecture model in repository history. | PR review + merged documentation state. |
| Branch protection (`main`) | Prevents bypass of governance controls in production branch. | Required checks, required reviews, signed commits, linear history, no force push. | GitHub branch rules + protected-branch events. | Repository settings audit + merge behavior. |

## Evidence Collection Minimum Set
For each governance-relevant PR, collect at minimum:
1. PR URL and merge commit SHA
2. `governance-guard` workflow result URL
3. Approval evidence (reviewers and states)
4. Changed governed files list
5. CAB decision reference (if trigger conditions are met)

## CAB Trigger Linkage
CAB review is required when defined trigger conditions in `governance/policy-change-control.md` are met. This matrix does not redefine triggers; it maps where CAB evidence is expected.

## Operational Use
- Use this matrix during PR review to verify control coverage.
- Use this matrix during audits to quickly map controls to objective evidence.
- Update this matrix whenever governance components or enforcement paths change.
