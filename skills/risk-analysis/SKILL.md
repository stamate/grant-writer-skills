---
name: risk-analysis
description: Structured risk assessment with scenario analysis, risk matrix, and mitigation strategies for grant feasibility.
---


# Risk & Feasibility Analysis

You are conducting a structured risk assessment for a grant proposal, using scenario analysis to identify threats and generate mitigation strategies that strengthen the implementation plan.

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)

Parse from the user's message.

## Procedure

### 0. Locate Plugin Root

```bash
```

### 1. Load Context

Read from the proposal directory:
- `sections/objectives.md` — research objectives
- `sections/methodology.md` or `sections/excellence.md` — the proposed approach
- `sections/work_plan.md` or `sections/implementation.md` — timeline and milestones
- `config.yaml` — agency and mechanism

### 2. Invoke What-If Oracle

Run `/what-if-oracle` in Deep Oracle mode on the research plan. Provide the objectives and methodology as context and ask it to explore failure scenarios:

```
/what-if-oracle "What if the proposed research plan for <proposal title> encounters obstacles?" --mode deep
```

Provide the objectives and methodology text as context for the oracle.

### 3. Build Risk Matrix

Structure the oracle output and your own analysis as a risk matrix across 5 categories:

| Category | Risk | Likelihood | Impact | Mitigation |
|----------|------|-----------|--------|------------|
| **Technical** | Key method fails to produce expected results | Medium | High | Alternative approach B; pilot validation in WP1 |
| **Personnel** | Key researcher leaves the project | Low | High | Cross-training; overlap in WP responsibilities |
| **Timeline** | Data collection delays due to external dependencies | Medium | Medium | Buffer time built into schedule; parallel WPs |
| **Budget** | Equipment costs exceed estimates | Low | Medium | Contingency fund (10%); phased procurement |
| **Regulatory** | Ethics approval delays | Medium | Medium | Early submission; pre-consultation with ethics board |

Rate each risk:
- **Likelihood**: Low / Medium / High
- **Impact**: Low / Medium / High

Generate a mitigation strategy for every Medium or High risk.

### 4. Generate Risk Mitigation Document

Write `sections/risk_mitigation.md` containing:

1. **Risk identification methodology** (brief description of the assessment approach)
2. **Risk matrix table** (all identified risks with likelihood, impact, mitigation)
3. **Contingency plans** for the top 3 highest-risk items (detailed alternative approaches)
4. **Monitoring approach** (how risks will be tracked during project execution)

### 5. Feed Into Implementation Section

For EU proposals, risk management is expected within the Implementation section. Provide the key risk findings as input to the proposal writing phase:

- Contingency plans should be referenced in the relevant work packages
- Alternative approaches should be mentioned in the methodology
- Timeline buffers should be visible in the Gantt chart

Update the existing `sections/implementation.md` or `sections/methodology.md` if they already exist, adding risk-aware language and contingency references.

## EU-Specific Notes

- **Horizon Europe**: Risk management is an explicit sub-section within Part B2 (Implementation). Frame risks using the standard EU terminology: "risk identification", "risk assessment", "risk mitigation measures", "risk monitoring".
- **ERC**: Risk is addressed implicitly through the "high-risk/high-gain" framing. Emphasize that ambitious goals have identified risks with credible mitigation paths.
- **MSCA**: Career development risks (e.g., host institution changes, training plan disruptions) should be included alongside scientific risks.

## Notes

- If `/what-if-oracle` is not available, perform the risk analysis manually by systematically evaluating each objective against the 5 risk categories.
- Be honest about risks — reviewers appreciate realistic assessment over optimistic hand-waving.
- The risk matrix should contain 8-15 risks. Fewer suggests shallow analysis; more suggests padding.
