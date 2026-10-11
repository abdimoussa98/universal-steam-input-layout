# A pad click after a thumb leaves a stick (90.51)

Read-only, 2026-10-10. The author reported on 90.51 that a pad's button press
is interrupted by a stick thumb's release. `probe.py` runs five orders of
events on the press simulator (default layout, `Base` and `Steering`, both
sticks, both pads, centre and ring); `results.txt` is its output.

    python3 findings/2026-10-10-pad-click-after-stick-tap/probe.py

**The author's case (2026-10-10):** a click that is already held drops when a
thumb lifts from a stick, and letting go of the pad then gives no release
bump. The simulator does not show it: the click holds through the lift in
every order. On the lift the click layer's own Release removes the stick's
three layers, which sit under it; the click layer holds itself with
`hold_layer` (A42). Candidates and a four-step Deck trial are in
[the plan](../../plans/2026-10-10-stick-lifecycle-and-pad-click-after-stick-tap.md#part-2-a-held-pad-click-drops-when-a-thumb-leaves-a-stick).

**Also seen, and left as it is:** a click that starts inside 200 ms of the end
of a stick touch shorter than 150 ms waits for the stick's window
(`LST: Double Tap`, `RST: Double Tap`) to close. Windows override the pad
clicks by rule (R149, R172), and the author keeps that.
