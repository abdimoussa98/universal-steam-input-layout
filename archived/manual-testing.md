# Manual testing (retired)

**Retired on 2026-10-03.** This was the Deck checklist: 137 checks in 17
sections, none of which was ever ticked. Every check now lives somewhere a
script can run it, or where it belongs:

- **Press-by-press checks** are scenario tests: `tests/test_scenarios_*.py`,
  run on both layouts by a press simulator (`python3 -m tests.scenario` lists
  them, and which rest on an unverified Steam assumption).
- **What Steam does** is in
  [Steam Behaviour Assumptions](../resources/Steam%20Behaviour%20Assumptions.md),
  each entry with one Deck procedure. The Deck is for settling those, once.
- **Feel** is in the tuning notes at the end of that document.

Where each of the 137 went, with its original wording:
[the migration record](../findings/2026-10-03-deck-check-sorting/README.md).
