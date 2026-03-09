# Governance Roadmap

## Status
Draft for steering and implementation planning.

## Objective
Evolve the current governance framework from repository-level controls into an operational governance program with measurable outcomes, automated evidence packaging, and cross-domain compliance integration.

## Baseline (Completed)
The following foundation controls are already implemented:
- Policy definition
- CI enforcement (`governance-guard`)
- Policy change control with CAB triggers
- Governance architecture overview
- Governance evidence matrix
- Governance integrity test suite
- Governance release checklist

## Phase 1: Foundation Stabilization (0-30 days)
Goal: harden and operationalize existing controls.

Deliverables:
- Enable required status checks in branch protection:
  - `governance-guard`
  - `governance-integrity`
- Enable required CODEOWNERS review on governed paths
- Align branch protection settings with `governance/repository-governance.md`
- Add governance section to release notes template

Exit Criteria:
- No governance-related merge to `main` bypasses required checks
- Quarterly review owner assigned
- First governance review minutes documented

## Phase 2: Evidence Automation (30-60 days)
Goal: reduce audit preparation effort by automating evidence bundles.

Deliverables:
- Generate per-PR governance evidence bundle (JSON/Markdown)
- Include:
  - PR metadata
  - approvals
  - checks summary
  - merge commit SHA
  - changed governed files
- Add immutable evidence index path convention under `evidence/`

Exit Criteria:
- One-click retrieval of governance evidence for any merged governance PR
- Evidence completeness check integrated into CI

## Phase 3: Operational Integration (60-90 days)
Goal: connect governance controls with detection operations and risk workflows.

Deliverables:
- Integrate governance signals into detection CI dashboards
- Add governance drift alerting (e.g., missing required docs/check rules)
- Link CAB decisions with risk-gate outputs for major governance changes
- Add runbook extension for governance incidents (control failure, policy mismatch)

Exit Criteria:
- Governance drift conditions alert within one CI cycle
- CAB-triggered governance changes produce complete linked records

## Phase 4: Compliance Mapping and Maturity (90-180 days)
Goal: map governance controls to external frameworks and establish maturity metrics.

Deliverables:
- Control mapping appendix to relevant standards (e.g., ISO 27001, SOC 2, KRITIS context)
- Governance KPI/SLO definition and reporting cadence
- Quarterly control effectiveness review template
- Annual governance tabletop exercise for rollback and evidence traceability

Exit Criteria:
- Documented control-to-framework mapping approved by stakeholders
- Quarterly KPI report published
- Improvement backlog maintained with owners and due dates

## Governance KPIs (Initial)
- Governance PRs with complete evidence pack: target `100%`
- Governance check pass rate on first run: target `>= 95%`
- Mean time to governance review completion: target `< 2 business days`
- CAB-triggered governance PR traceability completeness: target `100%`
- Drift incidents detected pre-merge: target `100%`

## Governance SLOs (Initial)
- Critical governance control breakage detection: `<= 1 CI run`
- Recovery time for governance CI gate failures: `< 1 business day`
- Evidence retrieval readiness for audited governance PRs: `<= 15 minutes`

## Roles and Ownership
- Governance owner: repository maintainer / security engineering lead
- CAB approver group: security + platform + operations representatives
- CI owner: DevSecOps/Platform engineering
- Audit liaison: compliance/security governance function

## Review Cadence
- Weekly: governance PR trend review
- Monthly: control drift and exceptions review
- Quarterly: governance architecture and KPI/SLO review

## Risks and Mitigations
- Risk: governance fatigue from excessive blocking checks
  - Mitigation: calibrate gates with measurable thresholds and exceptions process
- Risk: evidence quality degradation over time
  - Mitigation: enforce integrity checks and periodic evidence sampling
- Risk: policy-doc drift from runtime settings
  - Mitigation: scheduled branch-protection verification against policy document

## Next Actions
1. Merge governance-guard PR and enable required checks on `main`.
2. Create evidence bundle generator task for Phase 2.
3. Schedule first quarterly governance review meeting.
4. Define owners for KPI and SLO reporting.
