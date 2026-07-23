# find-unknowns eval run

examiner=sonnet sim=sonnet judge=opus

| cell | name | result | leak | mem | basis-leak? | graders | judge ebm |
|---|---|---|---|---|---|---|---|
| C1 | classify-route-and-establish-home | PASS |  |  |  | ledger_written=P, ledger_validates=P, classification_expected=P, rail_read_before_write=P, grounding_search_first=P, ledger_home_offer=P | True |
