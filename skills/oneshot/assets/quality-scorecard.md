# OneShot Quality Scorecard

| Category | Maximum | Score | Notes |
|---|---:|---:|---|
| Target fit | 10 |  |  |
| Research grounding | 15 |  |  |
| Outcome clarity | 10 |  |  |
| Scope and feasibility | 10 |  |  |
| Instruction architecture | 10 |  |  |
| Functional completeness | 10 |  |  |
| Verification and definition of done | 15 |  |  |
| Failure resilience and autonomy | 5 |  |  |
| Maintainability and expansion | 5 |  |  |
| Safety, privacy, legality, and originality | 5 |  |  |
| Output discipline and compression | 5 |  |  |
| **Total** | **100** |  |  |

## Critical-failure check

- [ ] The response writes the requested prompt rather than silently executing the underlying task.
- [ ] Material research claims are real and cited.
- [ ] Target tools and capabilities are verified or stated as requirements.
- [ ] Output contracts do not conflict.
- [ ] Definition of done is observable.
- [ ] Scope fits the target mode and environment.
- [ ] No protected expression is requested as a copy.
- [ ] No mandatory user constraint is omitted.
- [ ] No template placeholders remain.
- [ ] Completion claims require evidence.

## Five-pass review

- [ ] Contradiction pass complete.
- [ ] Dependency pass complete.
- [ ] Feasibility pass complete.
- [ ] Verification pass complete.
- [ ] Compression pass complete.

Delivery threshold: 85/100 with no critical failure.
