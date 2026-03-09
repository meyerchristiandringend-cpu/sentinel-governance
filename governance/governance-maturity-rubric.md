# Governance Maturity Rubric (Level 1-5)

## Overview
This rubric defines governance maturity levels for the SENTINEL repository and provides measurable criteria for control quality, operational rigor, and audit readiness.

## How To Use
- Evaluate the repository against each level's criteria.
- A level is achieved only if all mandatory criteria for that level are met.
- Re-evaluate quarterly and after major governance or workflow changes.

## Level 1 - Ad-hoc
### Characteristics
- Governance is mostly implicit and person-dependent.
- Control decisions are inconsistent across changes.

### Indicators
- No formal governance policy in repository.
- No path ownership enforcement.
- No mandatory CI governance gates.

### Evidence
- Incomplete or missing governance documents.
- Governance outcomes only visible in ad-hoc discussions.

### Exit Criteria
- A versioned governance policy exists in the repository.
- Basic review model is documented.

## Level 2 - Documented
### Characteristics
- Governance expectations are documented.
- Processes exist but are not consistently enforced by automation.

### Indicators
- Governance policy documents are present.
- Review expectations are defined.
- Branch protection partially configured.

### Evidence
- Versioned policy files in `governance/`.
- PR templates/checklists reference governance expectations.

### Exit Criteria
- Governed paths are explicitly owned via `CODEOWNERS`.
- Governance checks are introduced in CI.

## Level 3 - Enforced
### Characteristics
- Governance controls are actively enforced in CI and PR flow.
- Policy changes follow defined approval paths.

### Indicators
- `CODEOWNERS` active on governed paths.
- Governance guard workflow blocks non-compliant PR states.
- Policy-change control with CAB trigger conditions exists.

### Evidence
- Successful/failed `governance-guard` runs.
- PR approval logs and governed-file summaries.
- Policy-change PRs include required governance impact sections.

### Exit Criteria
- Integrity tests validate governance artifact presence and structure.
- Evidence mapping between controls and artifacts is documented.

## Level 4 - Integrated
### Characteristics
- Governance controls are connected across policy, CI, evidence, and operations.
- Evidence flow is explicit and repeatable.

### Indicators
- Governance architecture overview is documented.
- Evidence matrix maps controls to verification outputs.
- Integrity suite is running and required for governed changes.

### Evidence
- `governance-integrity` check history.
- Architecture and evidence documents updated with control changes.
- Clear link between policy changes and CI enforcement outcomes.

### Exit Criteria
- Governance release checklist is operationally used.
- Governance roadmap and ownership cadence are defined.

## Level 5 - Optimized
### Characteristics
- Governance is measured, continuously improved, and strategy-aligned.
- Governance performance is managed via KPIs/SLOs.

### Indicators
- Governance KPIs and SLOs are defined and tracked.
- Quarterly governance reviews produce actions and follow-up.
- Drift detection and evidence packaging are automated where possible.

### Evidence
- KPI trend reports and quarterly review records.
- Time-bound exceptions with expiry and compensating controls.
- Release evidence bundles covering governed changes.

### Exit Criteria
- Governance improvements are backlog-driven and prioritized.
- Control effectiveness is reviewed and tuned on a recurring cycle.

## Scoring Guidance
- Score each indicator as `met`, `partial`, or `not_met`.
- Minimum recommendation to claim a level: all mandatory indicators at that level are `met`.
- Suggested maturity claim for this repository (current target): **Level 4 progressing to Level 5**.

## Review Template (Quick)
- Current level:
- Evidence reviewed:
- Gaps identified:
- Actions:
- Owners:
- Due dates:
