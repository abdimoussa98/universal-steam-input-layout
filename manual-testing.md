# Manual testing (Deck)

Implementation work is tracked in [todos.md](todos.md). Unchecked items below remain pending runtime validation.

- Covers every release from 90.6 to 90.13, newest first, and below them the
  areas from before 90.6 that were never run (menu buttons, modifiers, cursor
  gyro, triggers and ramp-up, recovery, held inputs)
- Nothing here has been run on the Deck
- Load both VDFs fresh, not in the live editing session, and run every check on both layouts
- Written for the default. In the alternative, swap LB / RB ↔ LT / RT: the bumpers fire, and the soft-pull triggers are the modifiers
- If a bind applies the wrong layer, suspect the load-order swap (`findings/2026-07-11-layer-order-swap/`)

