# Delay timers and repeat rates

**Do not make mission-critical behavior depend on a delay, a repeat interval,
or their ordering across layer changes.** The author reports that adding and
removing layers can disturb both delayed actions and held repeats. A saved
timer value describes the intended interval; it does not guarantee the
interval Steam will deliver during a layer transition.

These are the author's Deck observations, updated on 2026-10-09 while
returning to 90.38 as the working baseline. The exact triggers and Steam's
internal scheduling remain unresolved. This documentation does not change
the existing timers, repeat rates, or layer bindings.

## What the settings mean

| Setting | Intended behavior | Limit during layer changes |
|---|---|---|
| Fire Start Delay, `delay_start` | Wait the configured milliseconds before firing an eligible activator | A removal can restart or postpone it in some cases. In other transitions a following delay can appear to fire immediately |
| Hold to Repeat, `hold_repeats` | Keep firing while the activator remains eligible | Holding the input through a layer change can disrupt the interaction |
| Repeat Rate, `repeat_rate` | Configure the interval in milliseconds between repeats; a smaller interval means faster repetition | Removal can shorten the effective interval, so repeats happen faster than intended |

These are configured values, not measured guarantees. An omitted repeat rate
also has no established client default in this repository; the simulator's
100 ms default is an assumption (A35).

## What has been observed

### Removal can accelerate held repeats

The author reports that removing layers can make an action repeat faster
while its input remains held. This reduces the effective interval between
repeats; it does not establish that Steam rewrites the saved `repeat_rate`.
The held-repeat interaction can be disrupted significantly. The affected
removal targets, exact intervals, and conditions that preserve or disturb
the schedule have not been isolated.

Do not infer stable repetition from a passing scenario or a configured rate.
The former assumption that a repeating activator always keeps its schedule
after another layer is removed is contradicted by this report (A31).

### Removal does not give a dependable timer reset

Earlier observations showed a `remove_layer` restarting a delayed apply,
including a case that waited the full 300 ms again. Repeated removal of the
delayed target also recovered an interrupted apply that otherwise failed
on the next press. Those observations motivated the existing reset pattern
(A12 and R120).

The author's later experience is inconsistent: removals still appear to reset
or postpone delays in some cases, but not every time. Treat the old restart
model as a description of observed cases, not a universal rule. Whether a
particular removal restarts, leaves, or otherwise disturbs a pending timer
remains unresolved (A13). Adding a layer is not a dependable way to preserve
the timer either, because it can change which binding answers the held input.

### A following delay can appear to fire immediately

The author reports this especially around the delayed addition of the cursor
driver: when an interaction adds and removes layers at the same time, or
transitions essentially instantaneously, the following delayed action can
appear to execute immediately instead of waiting its configured interval.

The report does not establish that every combined add/remove sequence does
this, or which command or timer owns the cause. A timer restart alone does
not explain all the observations. Do not assume a newly exposed or newly
added binding will always wait its full delay (A13 and A16).

The layout also intentionally completes some pending adds on stick-touch
release before cleaning up the stick helpers (R123). That explicit immediate
route is separate from the reported premature firing of a delayed action;
record which binding fired when investigating the cursor case.

## How to design and interpret checks

- Keep essential cleanup and correctness independent of an exact deadline,
  minimum wait, repeat count, or relative timer order. A delay or repeat may
  support an interaction, but should not be its sole correctness mechanism.
- Treat existing repeated-removal resets as a workaround with uncertain
  timing. The configured delay-plus-50-ms convention (R121) does not prove
  that a target always arrives before the next reset.
- Keep layer-change ordering explicit within a command list, including the
  existing Always On isolation rules. Such ordering does not establish the
  schedule of separate activators or later delayed actions.
- Interpret simulator timings as model outcomes. Static audits can check
  configured values and command order; they cannot establish the Deck's
  actual timer or repeat behavior under layer changes.

Existing bindings and recovery repeats remain in place. The documentation
records their limits; it does not claim that all existing interactions have
already been redesigned to eliminate timing dependencies.

For a focused reproduction, compare the same held input with no layer change,
an isolated removal, an isolated addition, and a combined add/remove. Record
the active layers, exact command order, whether the input was held before the
transition, and the actual output times. Repeat the gesture: a single restart
or a single successful wait cannot settle an inconsistent interaction.

See [Steam behaviour assumptions](Steam%20Behaviour%20Assumptions.md) for
A12, A13, A16 and A31; [the reset pattern](Steam%20Input%20JSON%20Structure.md#interrupted-delayed-layer-applies)
for the existing bindings; and the [90.36 delay inventory](../findings/2026-10-06-delay-interruptions/README.md)
for the historical audit. The inventory's restart labels and simulated
deadlines reflect its model at the time, not guaranteed runtime outcomes.
