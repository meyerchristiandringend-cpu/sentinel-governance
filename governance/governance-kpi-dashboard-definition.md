# Governance KPI Dashboard Definition

## Purpose
Defines governance KPIs used to measure control effectiveness, operational reliability, and audit readiness for this repository.

## KPI Categories
1. Control enforcement KPIs
2. Integrity and drift KPIs
3. Evidence packaging KPIs
4. SLA/SLO KPIs
5. Review and CAB KPIs
6. Maturity progression KPIs

## KPI Definitions

### KPI 1: Governance PR Approval Compliance
- Description: Percentage of governed-path PRs approved according to required ownership/review rules.
- Target: `100%`
- Source: `.github/CODEOWNERS`, `governance-guard` workflow runs
- Severity: High

### KPI 2: Integrity Suite Pass Rate
- Description: Successful governance integrity checks divided by total integrity runs.
- Target: `100%`
- Source: `governance-integrity` workflow
- Severity: High

### KPI 3: Drift-Free Quarters
- Description: Quarters without high-severity governance drift.
- Target: `4/4`
- Source: `governance-drift-alert` workflow reports
- Severity: Medium

### KPI 4: Evidence Packaging Timeliness
- Description: Time between review trigger and evidence package generation.
- Target: `< 24h`
- Source: `governance-evidence-packaging` workflow and package manifest timestamps
- Severity: Medium

### KPI 5: SLO Compliance Rate
- Description: Proportion of governance SLO checks with pass status.
- Target: `>= 95%`
- Source: `governance-slo-enforcement` reports
- Severity: High

### KPI 6: CAB Decision SLA
- Description: Time from CAB trigger to CAB decision capture.
- Target: `< 48h`
- Source: policy change-control records and quarterly review decisions
- Severity: Medium

## Dashboard Outputs
- Machine-readable JSON snapshot
- Human-readable Markdown summary
- Optional CI step summary export

## Data Quality Rules
- Every KPI must include:
  - id
  - display name
  - target
  - current value
  - status (`green|yellow|red`)
  - timestamp
  - source reference
- Missing data must be flagged as `yellow` or `red`, never silently omitted.

## Evidence Integration
Store KPI snapshots under:
- `governance/evidence/quarterly/YYYY-QX/kpi-snapshot.json`
- `governance/evidence/quarterly/YYYY-QX/kpi-summary.md`

## Governance and Change Control
This dashboard definition is governed by:
- `governance/policy-change-control.md`
- `governance/repository-governance.md`
- `.github/workflows/governance-guard.yml`

## Review Cadence
- KPI snapshot generation: at least weekly and at quarterly governance review
- KPI threshold review: quarterly
