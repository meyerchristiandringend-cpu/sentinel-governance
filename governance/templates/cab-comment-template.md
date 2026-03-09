## CAB Report - Rule Compiler Forecast

**Commit**: `{{ commit }}`
**Compiler Version**: `{{ compiler_version }}`
**Generated Variants**: **{{ variants_count }}**
**Risk Score**: **{{ risk_score }} / 100**
**Gate Status**: **{{ gate_status }}**

### Executive Summary
- **Neue Regeln**: **{{ new_rules }}**
- **Geaenderte Regeln**: **{{ changed_rules }}**
- **Fehlende Bindings**: **{{ missing_bindings }}**
- **KQL Safety Critical**: **{{ kql_critical_count }}**

### MITRE Heatmap Diff
| Technique | Current | Forecast | Delta |
|---|---:|---:|---:|
{{ heatmap_rows }}

<details>
<summary>Compact Rule Diff</summary>

```diff
{{ rule_diff }}
```

</details>

### Signatures
- **Forecast signed**: `{{ forecast_signed }}`
- **Snapshot signed**: `{{ snapshot_signed }}`
- **Compiled signed**: `{{ compiled_signed }}`
- **Signature Index**: `{{ signatures_index_path }}`

### Recommended Action
- **Approve** if `risk_score < 60` and `missing_bindings == 0` and `kql_critical_count == 0`.
- **CAB Review** if `60 <= risk_score < 80`.
- **Block** if `risk_score >= 80` or `kql_critical_count > 0` or signatures invalid.

---

**Decision**: _[Approve | CAB Review | Block]_
**Reviewer**: _[name]_
**Notes**: _[free text]_
