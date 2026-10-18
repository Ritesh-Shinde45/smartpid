# SmartPID - DeltaV IO Signal Sudoku

Allocates every field signal to **cabinet › CIOC › baseplate › CHARM** using
editable rules, verifies the result with an independent validator, and handles
customer revisions (Rev A → Rev B) with minimal moves.

Built for VIT Code Apex 3.0 (Track 1, Emerson).

## Principles

1. **Rules are data, not code**: rules live in `config/*.json`.
2. **Revision-first**: Rev B keeps unchanged signals in place.
3. **Verify, then trust**: `core/validator.py` re-checks every result. The LLM
   only helps at the edges (column mapping, plain-English rules, TQ wording).

## Project layout

```
app.py                 entry page (project selector, pipeline status)
config/                hardware, CHARM types, column aliases, default rules
core/                  engine: parser, mapper, rules, allocator, validator...
services/              db.py (SQLite) and llm_client.py
pages/                 Upload, Rules, Allocation, Report, Revise
ui_components/         session helpers, heat-map, tables
data/                  sample IO MDB + output template
tests/                 pytest suites
```

## Build status

- [x] Phase 0: scaffold, config, entry page
- [x] Phase 1: parser, column mapper, CHARM mapper
- [x] Phase 2: rule engine, block builder, allocator
- [x] Phase 3: validator + tests
- [ ] Phase 4: exporter + TQ generator
- [ ] Phase 5: Streamlit pages + heat-map
- [ ] Phase 6: revision logic + SQLite
- [ ] Phase 7: LLM features + CP-SAT fallback
- [ ] Phase 8: Docker polish, stress test



---
## Team

Team SmartPID 