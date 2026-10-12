# Are all the removes needed? An audit of 90.57

Read-only, 2026-10-12, on the working layouts as they were then (90.57).
The audit built nothing and changed nothing in `neptune/`. Its candidates
were built afterwards as **90.58**, on the author's word
([record](../2026-10-12-removes-that-never-take-a-layer-off/README.md)). Its
scripts read the working layouts, which are 90.58 now: to rerun them, point
`scenario._layouts` at the 90.57 snapshot. The author, after the ten largest remove
counts were listed: "I want you to audit whether all these removes are
necessary".

## In short

- **No.** Of the 4,013 removes in the default layout, 1,162 never take a
  layer off (1,174 of 4,083 in the alternative). Without them the layout
  would have 2,851.
- **950 of them are in the fourteen 89-remove lists**, the clears that enter
  a transition or a mode. Each names every layer but one; between 1 and 27
  of the 89 were ever on the stack when it fired.
- **212 are a layer that answers first:** it binds the bind's own input and
  sits above, so while it is on, the bind underneath does not run. This is
  R132 as tightened in 90.57.
- **The proof:** a trial layout without the 1,162 played the same 48,000
  random walks as 90.57. Every walk's whole log is the same.
- **One thing to decide,** and it is the author's: the 950. They only matter
  in a state the layout cannot get into by any press sequence the chains or
  the simulator know. Keeping them is a safety net; the standing goal says
  no removes for safety.

## Terms

- **Bind:** one activator entry on one input of one layer. Its **list** is
  the layers its `remove_layer` commands name. Its **host** is the layer the
  bind sits in.
- **Chains:** the backward chains the audits use (`steam_layout/chains.py`).
  They say which layers can be on the stack together, and which can be above
  or below which. They follow no chord, no delayed add and no `hold_layer`.
- **Walk:** one random press sequence on the press simulator
  ([`walk.py`](walk.py)): 90 events from Base over every control, with the
  four menu-plus-stick-click gestures and both menu buttons held, so it
  passes through `Steering`, `Cursor Gyro`, `Gamepad` and `Menu Keys`. Half
  the walks miss one button release in ten (the Steam menu, A25).
- **Fired:** the bind ran its commands. For each remove the walks count how
  often its layer was on the stack at that moment.

Each remove gets one verdict ([`audit.py`](audit.py)):

| Verdict | What it means |
|---|---|
| Needed | The layer is the bind's own, or was on the stack at least once when the bind fired |
| Never there | The chains say the two are never on the stack together, and in 30 firings or more the walks never met it |
| Answers first | The layer binds the bind's own input and is only ever above the host (chains). The walks never met it on the stack when the bind fired, nor under the host when the host was added |
| Not shown | Possible by the chains and not met by the walks, or the bind fired under 30 times |

"Never" from the walks is a sample's answer, not a proof. Everything here is
the simulator's; nothing ran on the Deck.

## 1. The ten largest sizes

Default layout, 48,000 walks ([`audit.txt`](audit.txt)). The alternative is
the same within a few removes.

| Removes in one bind | Binds | Removes | Needed | Never there | Answers first | Not shown |
|---|---|---|---|---|---|---|
| 89 | 14 | 1,246 | 276 | 934 | 16 | 20 |
| 22 | 2 | 44 | 36 | 0 | 0 | 8 |
| 18 | 2 | 36 | 26 | 0 | 0 | 10 |
| 14 | 2 | 28 | 2 | 0 | 26 | 0 |
| 11 | 2 | 22 | 17 | 0 | 0 | 5 |
| 9 | 4 | 36 | 29 | 2 | 0 | 5 |
| 8 | 2 | 16 | 16 | 0 | 0 | 0 |
| 7 | 32 | 224 | 113 | 0 | 58 | 53 |
| 6 | 86 | 516 | 282 | 0 | 12 | 222 |
| 5 | 38 | 190 | 77 | 0 | 16 | 97 |
| **All ten** | 184 | **2,358** | 874 | 936 | 128 | 420 |

And the whole layout, by what fixes each remove:

| What fixes it | Removes | Needed | Never there | Answers first | Not shown |
|---|---|---|---|---|---|
| The bind's own layer | 775 | 775 | 0 | 0 | 0 |
| A whole-stack clear (R163) | 1,224 | 254 | 934 | 16 | 20 |
| A cleanup function, required by the cleanup rules (R128, R129) | 948 | 388 | 0 | 0 | 560 |
| A cleanup function, allowed and not required | 180 | 0 | 0 | 172 | 8 |
| A stick touch Release's three helpers (R123) | 466 | 315 | 34 | 0 | 117 |
| A timer's reset (R120) | 29 | 0 | 2 | 27 | 0 |
| The layer's own hold target, in one of its Releases (R120 to R122) | 22 | 8 | 0 | 14 | 0 |
| No rule fixes it | 369 | 266 | 6 | 34 | 63 |
| **Every remove** | **4,013** | 2,006 | 976 | 263 | 768 |

## 2. The fourteen lists of 89

Each removes every layer but one (`Gyro`, or `Menu Keys` in the two chords
that enter it) and then adds a transition or a mode.

| Bind | Fired | Needed | Never there | Answers first | Not shown |
|---|---|---|---|---|---|
| `Menu Left: Entry Point`, left stick click Release | 17,906 | 26 | 60 | 2 | 1 |
| `Menu Left: Entry Point`, right stick click Release | 13,223 | 26 | 60 | 2 | 1 |
| `Menu Right: Entry Point`, left stick click Release | 18,639 | 27 | 60 | 2 | 0 |
| `Menu Right: Entry Point`, right stick click Release | 13,404 | 27 | 60 | 2 | 0 |
| `Stateful \| Menu Left: Entry Point`, left click Release | 4,076 | 26 | 62 | 1 | 0 |
| `Stateful \| Menu Left: Entry Point`, right click Release | 2,676 | 24 | 62 | 1 | 2 |
| `Stateful \| Menu Right: Entry Point`, left click Release | 5,700 | 26 | 62 | 1 | 0 |
| `Stateful \| Menu Right: Entry Point`, right click Release | 3,271 | 23 | 62 | 1 | 3 |
| `Gamepad`, left stick click chord | 13,505 | 1 | 84 | 0 | 4 |
| `Gamepad`, right stick click chord | 12,536 | 1 | 84 | 0 | 4 |
| `Menu Left!Right: Entry Point`, the chord that enters `Menu Keys` | 6,778 | 20 | 65 | 1 | 3 |
| `Menu Right!Left: Entry Point`, the chord that enters `Menu Keys` | 7,817 | 21 | 65 | 1 | 2 |
| `Menu Keys`, left stick click chord | 4,940 | 14 | 74 | 1 | 0 |
| `Menu Keys`, right stick click chord | 4,703 | 14 | 74 | 1 | 0 |

- **`Gamepad` is the plainest case.** It is a closed layer: nothing can be
  added over it, and its entry cleared the stack. In 26,041 firings the only
  layer on the stack was `Gamepad` itself.
- **Why a modifier is never there.** A bumper modifier retypes Start and
  Select, so a menu Entry Point can't come on while one is on. A modifier
  left on by a missed release is taken off by its own cleanup function on
  that Start press, before any Entry Point exists. Every layer takes care of
  itself, as the rules ask.
- **49 of the 90 layers the fourteen name between them were on the stack at
  none of them**, in 129,174 firings.
- **The chains alone would be wrong here.** At the four Stateful Entry Points
  the walks met `LST: Tap Cover`, `LST: Temporary Gyro`, `RST: Tap Cover` and
  `RST: Temporary Gyro` on the stack, which the chains say can't be there
  (they follow no delayed add). Those sixteen removes are needed.

**The rule.** R163 reads "entering a transition clears the whole stack
first". The author's words when it was made (2026-10-02): "before you go to
the transition set you should always clean everything below you that is
possible". The 950 are what is not possible.

**What the 950 are for.** A state no press sequence reaches: a layer stuck
on the stack in a way neither the chains nor the simulator can produce, such
as a Steam fault. The whole list would still clear it; a short list would
not. Scenario 90.42 S3 says as much of `Steering`'s exit: "Seed a stale
stack deliberately; this checks the recovery list, without claiming this
full stack is normally reachable."

## 3. Layers that answer first

222 removes in the default layout (234 in the alternative). The layer binds
the bind's own input and is only ever above the host, so with it on, the
host's bind does not run (A1). The largest groups:

| Host | Names | Removes | Why it answers first |
|---|---|---|---|
| The four plain and Gyro modifiers | Their `Temp Cursor Gyro` layer | 68 | The cursor binds every one of those inputs as a cancel (R135) |
| The W and the S layer, cleanup functions | The six Steering stick layers | 48 | Each binds both stick touches and the left edge with a cleanup of its own |
| `Steering`'s exit on up and down | Its thirteen family layers | 26 | Each binds up and down. Only `Steering` itself was ever on the stack, in 1,494 firings |
| The four plain and Gyro Modifier 2 layers, cleanup functions | `L1&R1: Tap Cover` | 8 | The cover binds both stick touches |
| The stick modifiers and scroll layers, the menu stick guards, the Fn layers, the scroll layers, the ramp layers, the right pad's layers | Their own cover or second-press layer | 56 | The layer on top binds the same input |
| The clears of section 2 | `RTP: Double Tap`, a menu window, an Fn layer | 16 | The window blocks the stick clicks |

- **How strong.** For 99 of the 222 the bind fired 30 times or more with the
  layer never on. For 91 it fired fewer times, and for 32 never: those rest
  on the layer binding the input (read from the layout) and on the chains
  putting it only above. The hosts added least often in the walks were the
  two Steering scroll layers (12 and 21 times).
- **Where the chains' order is wrong, the walks say so.** They put the right
  and left pad's layers only above the Stateful Entry Points; the walks met
  them underneath (a thumb on a pad before the menu button). Those 22
  removes were on the stack when their bind fired, so they are "needed"
  here. An order check has to keep that walk guard.
- **The audit can find most of these itself.** 172 of the 222 are in cleanup
  functions, and they are exactly the removes its own rules allow but do not
  ask for: R129 wants a layer above the host removed only when it leaves the
  input alone. Not one of the 180 such removes was ever on the stack. So
  what I wrote in the 90.57 record, that no audit check is in reach, was too
  strong: "allowed, not required" is a check the audit can already compute.

## 4. Never there, and left alone by a rule

77 removes get the same two verdicts and are not counted in the 1,162:

| Rule | Removes | Why they stay |
|---|---|---|
| A stick touch Release's three helpers (R123) | 34 | The trio is fixed (author, 2026-10-02). Most are in the three transitions, where no helper can be on |
| A timer's reset (R120) | 29 | Its job is to restart a stuck delay by naming the target, not to take the layer off |
| The layer's own hold target, in one of its Releases | 14 | The same target; left alone for the same reason, on my judgment and not on a rule's wording |

## 5. Not shown either way

768 removes. 560 are in cleanup functions and required by the cleanup rules:
the Cleanup audit would report each as missing. A cleanup function only
runs after a missed release, on one input, so the walks fire few of them;
243 of the 952 binds never fired at all. 117 more are stick touch helpers.
The other 91 are possible by the chains and were not met, among them 18 in
the right pad's window (the lists of 22 and 18). None of these is called
unnecessary here.

## 6. The trial

[`trial.py`](trial.py) builds a copy of each layout without the candidates
and plays the same walks on both ([`trial.txt`](trial.txt)).

| | Default | Alternative |
|---|---|---|
| Removes taken out | 1,162 from 142 binds | 1,174 from 154 binds |
| Removes in the layout | 4,013 to 2,851 | 4,083 to 2,909 |
| Walks that finish on both | 46,892 | 48,000 |
| Walks whose whole log is the same | 46,892 | 48,000 |
| Walks whose log differs | 0 | 0 |
| Walks with a layer left over after everything is let go | 612 and 612 | 430 and 430 |

The log holds every key, wheel step, haptic and beep, and every layer going
on or off, with its time. (1,108 default walks stop in both versions at the
simulator's ramp loop, noted in the owner release audit.)

**The trial only takes removes out.** The author, 2026-10-12: "I want to
make sure that this is reductive and not additive." [`reductive.py`](reductive.py)
compares the two files key by key ([`reductive.txt`](reductive.txt)): the
binds that differ lose `remove_layer` commands and nothing else. Commands
added 0, binds whose remaining commands changed order 0, any other
difference 0, in both layouts. The fix pipeline run on the trial adds no
command either.

On the trial files, with the tools as they are:

- **Build audit:** Budget, Window and Flow pass. The Cleanup audit has one
  finding, "never there", on the sixteen removes of section 2 that the walks
  show are needed. A whole-stack clear is exempt from that check; a short
  one is not, and the chains don't see those four layers.
- **The fix pipeline would take those sixteen out.** A build has to keep them
  with a register entry, or teach the chains the delayed add.
- **Scenario tests:** 1 of 412 fails, 90.42 S3, the seeded stack of section
  2. The tests that are not scenarios were not run; some state whole lists.

## 7. The bumpers: the tap cover, and rocking

The author, 2026-10-12, asked how a remove is judged needed, and about two
cases: `L1: Modifier 0` removing `L1: Tap Cover`, and rocking in the plain
Modifier 2 layers ("not in steering but in traditional mod two").

**The modifier family** is the 19 layers a bumper owns outside `Steering`
(the triggers' soft pull in the alternative): the two modifiers, the two
Modifier 2 layers, their four `Gyro` twins, the covers, the Double Tap
windows, the two scroll layers and the two `Temp Cursor Gyro` layers.

- **The tap cover.** `L1: Modifier 0`'s cleanup functions name the cover on
  every button, and it was on the stack nearly every time one fired (93 of
  94 on Start, 52 of 53 on A). Those are needed. The cover's own L1 Release
  fired 24,644 times with the cover on each time. Only the modifier's
  cleanups on the two stick touches are candidates: the cover binds both
  touches itself. They fired 3 times and once, so that verdict rests on the
  layout, not on the walks.
- **No Release, reset, hold or entry bind of the family is a candidate.** Of
  the 76 removes in the Modifier 2 Releases, 65 are needed, 3 not shown and
  8 are the layer's own hold target (section 4).
- **The family hosts 88 candidates (96 in the alternative), all in cleanup
  functions,** which run only after a missed release: a modifier naming its
  `Temp Cursor Gyro` on 17 inputs (68), a modifier naming its cover on the
  two stick touches (8), a Modifier 2 layer naming `L1&R1: Tap Cover` there
  (8, and 16 in the alternative), a scroll layer naming its Double Tap
  Cover there (4).
- **From elsewhere, 266 removes name a family layer,** all in the clears of
  section 2 and all never there in 129,174 firings.

**Every short bumper sequence** ([`rocking.py`](rocking.py)), on 90.57 and
on the trial, from Base and from `Gyro`, with a bind exposed under a held
button firing at once and at its next repeat (A9). Not random: every
sequence of the given length is played and the whole logs compared.

| Sweep | Steps | Sequences per layout | Log the same | Differs | That scroll |
|---|---|---|---|---|---|
| L1 or R1 down or up, a tap of A; gaps of 20, 120 and 210 ms | 5 | 236,196 | 236,196 | 0 | 114,484 |
| The same with a release that can be missed and a thumb on or off the right stick; gaps of 30 and 250 ms | 4 | 25,600 | 25,600 | 0 | 4,474 |

The figures are the same in both layouts ([`rocking.txt`](rocking.txt)). The
nine tests of `tests/test_modifier_rocking.py` pass on the trial layouts.

**How strong.** 1,039 of the default layout's 1,162 candidates have 30
firings or more behind them. The other 123 (132 in the alternative) are all
"answers first" in cleanup functions; 63 of them (68) are in the family.

## 8. What is the author's to decide

**Answered, 2026-10-12:** "1. trim 2. are you asking me if i want to trim,
if so yes i want to trim". The clears are trimmed (point 1) and the modifier
family's 88 go with the rest (point 4). The
[plan](../../plans/2026-10-12-removes-that-never-take-a-layer-off.md) has
both, and it is built as 90.58. The points as they were put:

1. **The 950 in the clears.** Trim them to what can be on the stack, or keep
   the whole lists as a net for states nobody can reach. With the trim R163
   reads "clears every layer that can be on the stack there". My pick is to
   trim: the walks cover missed releases, each layer has its own cleanup,
   and the standing goal is no removes for safety. It is a real trade, and
   the one place here where the answer is not computed.
2. **The 212 that answer first.** They follow from R132 as accepted on
   2026-10-12. They wait for a go-ahead like any build.
3. **The 77 of section 4.** Left as they are unless the author says
   otherwise.
4. **The 88 in the modifier family** (section 7). Leave them for a first
   build, or take them with the rest. My pick is to leave them: rocking is
   the most sensitive part of the layout, and 63 of the 88 have thin walk
   evidence. That build takes out 1,074 (1,078 in the alternative).

## Not verified on the Deck

All of it. The simulator holds a control or not, runs one array as one step,
and resets a pending delay on any bind that removes at all, whatever the
list names. If Steam disturbs a delay once per `remove_layer` command (A13),
shorter lists disturb less, not more.

## Files

| File | What it is |
|---|---|
| [`walk.py`](walk.py) | The whole-pad random walks and the counters |
| [`audit.py`](audit.py), [`audit.txt`](audit.txt) | One verdict per remove, and the tables |
| `removes-default.json`, `removes-alternative.json` | One row per remove: rule, chains, firings, verdict |
| [`trial.py`](trial.py), [`trial.txt`](trial.txt) | The trial layout and the walk-for-walk comparison |
| [`reductive.py`](reductive.py), [`reductive.txt`](reductive.txt) | Every difference between 90.57 and the trial, counted: removes taken out, nothing added |
| [`rocking.py`](rocking.py), [`rocking.txt`](rocking.txt) | Every short bumper sequence on both, log for log |
