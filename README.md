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

## Setup (local)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # Windows: copy .env.example .env
# optional: add ANTHROPIC_API_KEY to .env for LLM features

streamlit run app.py
```

Open http://localhost:8501. The app works without an API key; only the LLM
features are switched off.

## Run with Docker

```bash
docker build -t smartpid .
docker run -p 8501:8501 --env-file .env smartpid
```

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

## Demo script (5 minutes)

1. Open **Upload**, drop the sample IO MDB, confirm the auto-mapped columns.
2. Open **Rules**, show the rule panel, toggle one rule, add a custom rule.
3. Open **Allocation**, click *Allocate*, show the cabinet heat-map.
4. Open **Report**: 0 violations, fill %, spares, TQ list, download Excel.
5. Open **Revise**, load Rev B, show the impact report (added / deleted /
   moved, cabinets hit).

## Tests

```bash
pytest -q
```

## Team

Team SmartPID 