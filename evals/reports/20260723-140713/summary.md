# find-unknowns eval run

examiner=sonnet sim=sonnet judge=opus

| cell | name | result | leak | mem | basis-leak? | graders | judge ebm |
|---|---|---|---|---|---|---|---|
| CORR1 | correction-supersedes-never-edits | PASS |  |  |  | correction_protocol=P, ledger_validates=P | True |
| D1 | discovery-lists-and-asks | PASS |  |  |  | discovery_disambiguation=P | True |
| DEG1 | degradation-improvises-and-notes | PASS |  |  |  | degradation_note=P, ledger_validates=P | True |
| DEV1 | interim-deviation-when-told | FAIL |  |  |  | deviation_logged=F, ledger_validates=P | True |
| DEV2 | seeded-contradiction-skill-invoked | FAIL |  |  |  | command failed (rc=1): claude -p --model sonnet...
stderr tail:  | None |
| DEV3 | plant-only-uninvoked-session | PASS |  |  |  | deviation_logged=P, evidence_of_encounter=P, rail_read_before_write=P | True |
| G1 | deference-rail-fires-before-goahead | FAIL |  |  |  | deference_flag=F, gate_withheld=F, ledger_validates=P | True |
| P1 | plant-corruption-surfaced-and-rebuilt | FAIL |  |  |  | plant_corruption_recovered=F | True |
| Q1 | quiz-reveal-safe-pass | PASS |  |  |  | ledger_validates=P, anti_gaming_order=P, reveal_safe=P, variant_retake=P, pass_recomputation=P, quiz_gate_withheld=P | True |
| Q2 | quiz-defer-then-insist | PASS |  |  |  | quiz_defer_honored=P, ledger_validates=P | True |
| Q3 | pre-quiz-confirmation-id-only | PASS |  |  |  | confirmation_pass_flag=P, anti_gaming_order=P | True |
