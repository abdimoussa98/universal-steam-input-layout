# Plan: an Ibex base layout, its conversions to the Deck and the DualSense Edge, and a release pipeline

**Status, 2026-10-15:** built the same day, on the author's "go ahead and
start implementing this"; untested on the devices. Parts 0 to 4 are in: the
registry, `ibex/` and `dse/`, `tools/release.py`, `CHANGELOG.md` and the
workflow; Ibex 1.0, Neptune 90.75 and DSE 1.0 with their snapshots
([record](../findings/2026-10-15-ibex-base/README.md)). Left for the author:
pushing `main` and the tags (step 2's backfill first, then step 7). Of the
three readings marked in [the author's answers](#the-authors-answers), the
author corrected 5: "Gyro always on" does not include Base. Readings 1 and 7
stand as written.

**Changed while building**, the plan below is as written:

- There is no layout input `center_trackpad_touch`: it is only a field of the
  Steam client's controller state message. On the Edge the two pad-touch
  switches, `left_trackpad_touch` and `right_trackpad_touch`, are the
  touchpad's halves, so R183 leaves them as they are and Base's mode shifts
  follow a thumb anywhere on the pad; neither is an absent input. The whole
  pad's touch chord is mask bit 27, as planned. A76 and R183 say so now.
- The Click Entry Point's ring press, a Soft Press past 23000 on the Deck, is
  a Regular Press on the whole pad's outer ring with its radius set to 23000.
- Each conversion ends with the fix pipeline, as a build does; the result is
  a fixed point of it. The audits read the exceptions register through a view
  of the layout's controller (R178 g).
- R185 takes the gyro enable mask off `Gyro` and its four modifiers only. The
  author, of reading 5: "no does not include base". Base keeps its mask, so
  with no stick touch Base has no gyro of its own on the Edge.
- `tools.release snapshot` saves a controller's snapshot (and refuses a tagged
  one), in place of the skill's copy loop.
- C4 is a recorded run, not a test in the suite: it repeats the whole scenario
  suite twice, about 25 minutes
  ([c4_scenarios.py](../findings/2026-10-15-ibex-base/c4_scenarios.py), with its
  results beside it). The Edge's own scenarios add E8: with no stick touch, a
  missed release clears at the next stick push to the edge.
- The CI's four test parts are balanced by the slow modules' measured times.

The author, 2026-10-15: "create a dse directory similar to the neptune dir.
[...] I also want a directory for the steam controller 2, but i want you to call
the directory Ibex. For the controller directories you should keep the json
files [...] versions are published changes. And finally i want you to add a
pipeline to publish the latest versions with proper semantic versioning so i
dont have to just dig through the version directory."

Revisions, same day:

1. "we'll keep the json files in the versions directory [...] the published
   artifacts will just be a bundle of all controller layout vdfs." Nothing is
   deleted.
2. "maybe the old folder order "versions/neptune/90.74/" made more sense."
   `versions/<controller>/<version>/` stays; no path in code or records changes.
3. The author asked whether semantic versioning makes sense and whether every
   controller should be bumped when one changes, then: "ok revise this plan and
   look for any issues with the simple pipeline." Both answers were no: each
   controller keeps its own two-part version, and only a controller that
   changed gets a release. What the review found is in
   [Issues found](#issues-found-with-the-simple-pipeline).
4. "This plan should port the deck layout to them."
5. The author's answers to the port questions: "1. copied and edited
   separately 2. no it didn't 3. the back button are the same but the order is
   swaped r4 & l4 are on the front of the controller and r5 & l5 are on the back
   of the controller, so we'll have to have shift and space on the back and crtl
   and alt on the front."
6. The author's answers to the two Edge questions: "1. delete them and delete
   the left and right trackpad. 2. gyro should always be on unless the gyro off
   layer is active but the mask should just always be on."
7. "another thing i want for the dse layout is the mute button should be middle
   mouse and the whole trackpad bind should be the same swipe gestures we are
   used to from the left trackpad and click should be arrow keys. [...] THe
   arrow click should not be a softpress though."
8. "These "the four swipes into Escape, Enter, Tab and Backspace" need to be
   new layers that utilize the whole pad since we are deleteing the left and
   right trackpads. it should follow the same rules and conventions of the
   current trackpad left and right rules. The only thing is that the arrow keys
   will not have a middle click so no capslock in the center."
9. "the last change is the for the neptune layouts we need to configure the
   gyro to no longer use player space gyro calculation. It needs to be
   yaw+roll." [Part 3](#part-3-the-decks-gyro-turns-by-yaw-and-roll-neptune-9075).
10. "One thing I also want is in the plan, to have some rules created around
    these new changes. That the IBEX controller is the base controller. That's
    the default for everything. And there should be rules for converting from
    IBEX to the other ones. [...] So from IBEX to DSE. IBEX to Neptune."
    [Part 4](#part-4-ibex-is-the-base-conversion-rules).

What revisions 4 to 8 decide is in [the author's answers](#the-authors-answers),
each with the rule that carries it.

## Terms

- **Controller directory:** a top-level folder holding one controller's working
  layouts, `<stem>_latest.json` and `.vdf`. Today only `neptune/` (Steam Deck).
  New: `dse/` (DualSense Edge) and `ibex/` (Steam Controller 2).
- **Base layout:** the Ibex layout. Every layout change is made there (R177).
- **Conversion:** a Deck or DualSense Edge layout made by a program from an
  Ibex release, by that controller's conversion rules; never edited by hand.
  For example, Neptune 90.75 and DSE 1.0 are both conversions of Ibex 1.0.
- **Bootstrap:** the one time a layout goes the other way. Ibex has no layout
  today, so Ibex 1.0 is made from Deck 90.74.
- **Version:** a controller's own number, written at the end of
  `controller_mappings.title`, such as `single-set-default :: always-gyro :: 90.75`.
  Neptune continues its line (90.75 next). DualSense Edge and Ibex start their
  own lines at 1.0. Two controllers' numbers say nothing about each other.
- **Snapshot:** one controller's files at one version,
  `versions/<controller>/<version>/`, JSON and VDF per variant, as today.
- **Release:** a version with a Git tag `<controller>-v<version>`, such as
  `neptune-v90.75`. Pushing the tag publishes it. A snapshot without a tag is
  not a release: trials like 90.53 and 90.69, and the 90.39 candidate.
- **A controller's latest release:** its highest-numbered tag. Compare numbers,
  not text: 90.10 is higher than 90.9.
- **Bundle:** the one file every release publishes, a zip of every controller's
  latest release VDFs, one folder per controller. JSONs are not in it.
- **Input:** a source and an input name together, as the audits name them:
  `(joystick, touch)` is the left stick's touch, `(switch, button_back_left)`
  is the L5 grip.
- **Absent input:** an input the Ibex layout binds and a converted layout
  doesn't: the controller lacks it (the Edge's stick touch), or the author left
  it out (the Edge's right trackpad). A bind on an absent input never fires.
- **Whole pad, `CTP`:** the Edge's touchpad as one pad, Steam's source
  `center_trackpad`. Its layers are titled `CTP: ...`, as the Deck's pads'
  layers are `LTP: ...` and `RTP: ...`.

## Part 0: before anything changes

90.71 to 90.74 are untracked and 15 files are modified (their builds, tests,
plans). The author, or the session that built them, commits them first. Then
check git status again for another session's work.

## Part 1: controller registry and the two new directories

New `steam_layout/controllers.py`, the one place that knows the controllers:

| Directory | Controller | `controller_type` (from the Steam client on this Mac) | File stems |
|---|---|---|---|
| `ibex/` | Steam Controller 2, **the base** | `controller_triton` (Steam's internal name; the directory is `ibex/` as asked, lowercase like `neptune/`) | `ibex_single-set-{default,alternative}_hold-gyro` |
| `neptune/` | Steam Deck | `controller_neptune` | `single-set-{default,alternative}_hold-gyro` (unchanged) |
| `dse/` | DualSense Edge | `controller_ps5_edge` | `dse_single-set-{default,alternative}_hold-gyro` |

The new stems start with the controller. Every controller's VDFs go into the
same Steam folder (`controller_base/templates/`). A Deck with a DualSense Edge
plugged in uses both, and equal file names would overwrite each other there.
Neptune's stems stay: renaming them would rewrite 382 paths in 215 files.

The registry names Ibex the base (R177) and gives each other controller its
conversion rules ([Part 4](#the-conversion-rules)): its absent inputs, its
input map (the Edge's grip swap) and its gyro style (the Deck Yaw + Roll, Ibex
and the Edge Player Space; [Part 3](#part-3-the-decks-gyro-turns-by-yaw-and-roll-neptune-9075)).
The audits read it too. Where a tool or a doc needs one controller, it is Ibex:
`tools.convert` reads Ibex, a new builder writes Ibex, and the docs' examples
use Ibex. Tools that check layouts (`audit_build`, `change_report`) still
default to every controller with a layout.

Only live code reads the registry instead of a `neptune` written into it:

- [steam_layout/changes.py:28](../steam_layout/changes.py#L28): the versions
  folder per controller.
- [tools/change_report.py:34](../tools/change_report.py#L34) and
  [tools/audit_build.py:49](../tools/audit_build.py#L49): default to every
  registry directory that has `*_latest.json`.
- The steam-layout-apply skill's snapshot copy.

Builders, tests and findings scripts that open `versions/neptune/<v>/...` stay
as they are. `ibex/` and `dse/` get a `README.md` each: the controller, its
`controller_type`, that Ibex is the base, and for the Edge its conversion rules
in short: no stick touch, the grip swap, the whole pad's `CTP:` layers, the
mute button as middle mouse, gyro always on.

## Part 2: the release pipeline

### How a release goes

1. The version goes into both titles: Ibex's builder writes it, as builders do
   today ([building](../docs/building.md)), and `tools.convert` writes the
   Deck's and the Edge's next versions.
2. steam-layout-apply exports both VDFs and writes the snapshot, for each
   controller that changed ([publishing](../docs/publishing.md)).
3. The author tests on the device. A trial ends here: it is never tagged.
4. Add a section to `CHANGELOG.md` at the repo root, newest first, headed
   `neptune 90.75`, with the summary and link of the findings record that built
   it. A conversion's section names the Ibex release it comes from.
5. `python3 -m tools.release check <controller>` passes for each controller
   being released (below).
6. Commit, push `main`, then tag each controller the change releases (an Ibex
   change usually releases all three) and push the tags. Pushing the tags
   publishes, so it is the author's step.

### `tools/release.py`

One script, run on this Mac before tagging and on GitHub after the push, so the
two can't drift apart.

`check <controller> [<version>]` (version defaults to the working titles') fails
unless:

1. The titles in every `<controller>/*_latest.json` and `.vdf` end with
   ` :: <version>`.
2. `versions/<controller>/<version>/` has a JSON and a VDF per variant, byte
   for byte the working files.
3. Every one of those JSONs, exported again with `tools/convert_vdf.mjs`, gives
   its VDF byte for byte. On this Mac it warns if the installed exporter
   extension isn't the pinned version (5.12.3).
4. The version is higher than the controller's latest release, and has no tag
   yet. On GitHub, where the tag exists, it must be the only tag at that
   version, and the highest.
5. `CHANGELOG.md` has a section for `<controller> <version>`.
6. No released snapshot changed: for every tag, `versions/<controller>/<version>/`
   is the same as at the tag. This also runs as a test.
7. For the Deck and the Edge: the working files are the conversion of the Ibex
   release their CHANGELOG section names ([check C1](#checks)).

`bundle <controller> <version> <out>` writes `universal-steam-input-layout.zip`:
one folder per controller with its latest release VDFs, the new version for the
controller being released, and a `RELEASE.md`: the CHANGELOG section and a table
of the version of each controller in the bundle. A controller with no release
yet is listed as "no release yet".

### `.github/workflows/release.yml`

Runs on a pushed tag matching `*-v*`, and by hand (`workflow_dispatch`) to
retry.

1. `permissions: contents: write`. `concurrency: release`, so two runs never
   publish at once.
2. Checkout with `fetch-depth: 0` (all tags are needed to find each
   controller's latest release). Each run publishes **every** `*-v*` tag that
   has no GitHub Release yet, oldest first, not only the tag that started it.
   So the three tags of an Ibex change can be pushed together: if GitHub
   cancels a waiting run (issue 9), the next run publishes its tag. Each tag
   must be on `origin/main`.
3. Python 3.9, as on this Mac. Node 26, as on this Mac. The VDF extension
   5.12.3 from Open VSX, checked against the SHA-256 of the copy downloaded on
   2026-10-15 (`8fd847e3f78e07dd3a4a45c9b9cba86d541b8afec629171735659533ed8d23c9`),
   its `extension/` folder unpacked as
   `~/.vscode/extensions/pfwobcke.vscode-vdf-5.12.3/`.
4. For each tag: `tools.release check`. Once per tagged commit:
   `tools.audit_build`, the Python tests and
   `node --test tests/test_convert_vdf.mjs`. The Python tests are split by
   module across four parallel jobs (issue 11); publishing waits for all of
   them.
5. For each tag: `tools.release bundle`, then `gh release create <tag>` with the
   zip attached, titled `<Controller> <version>`, `RELEASE.md` as the notes.

Every release's zip has the same file name, so this link always downloads the
newest one, with every controller's latest release in it:
`https://github.com/abdimoussa98/universal-steam-input-layout/releases/latest/download/universal-steam-input-layout.zip`.
The README's install section gets that link and the Releases page link, once.
No README edit per release.

What the workflow doesn't do: write a VDF or a snapshot (it only checks them),
judge the description (publishing step 1 stays manual), or upload anything to
Steam.

### Backfill

Tag `neptune-v90.74` and publish it, to try the pipeline on a known layout. GitHub
runs the workflow file of the tagged commit, so the tag goes on the commit that
adds the pipeline, not on the Part 0 commit. Neptune's working files are still
90.74 there, which check 2 confirms. Older versions aren't tagged.

### Doc changes

- publishing.md: steps 4 to 6 above. A tagged snapshot is never changed: a fix
  after the tag is a new version. Today's rule that follow-up edits in a batch
  refresh the snapshot holds only until the tag.
- The README's install section, directory map and quick start (`tools.convert`,
  `tools.release check`; the test suite's run time, 46 minutes, not about five).
- building.md: Ibex is the base (R177). A change is built on Ibex, and
  `tools.convert` makes the Deck and the Edge. The Deck's builder chain up to
  90.74 stays as the record. The steam-layout-apply skill: convert, then
  export and snapshot each controller that changed.
- The Definition of Done: rows R177 to R185 and their notes
  ([Part 4](#the-conversion-rules)).
- resources: the Edge facts from the author (no stick touch; L4 and R4 on the
  front, L5 and R5 on the back), the gyro style values (Part 3) and A72 to A76.

## Part 3: the Deck's gyro turns by yaw and roll (Neptune 90.75)

The author, 2026-10-15: "for the neptune layouts we need to configure the gyro
to no longer use player space gyro calculation. It needs to be yaw+roll. [...]
This is since neptune is a handheld console layout for my steamdeck and the
other are controllers where player space makes sense."

**The setting** is a gyro group's `gyro_to_2d_conversion_style`, "3DOF to 2D
Conversion Style" in Steam's editor. Its values, read from the Steam client on
this Mac on 2026-10-15:

| Value | Style | Steam's description, shortened |
|---|---|---|
| 0 | Yaw | Turn the controller around its own vertical axis |
| 1 | Roll | Lean it around its forward axis |
| **2** | **Yaw + Roll** | Adds the lean and the turn together; tilting up and down around its own lateral axis moves the mouse vertically |
| 3 | Local Space | (advanced) |
| **4** | **Player Space** | Yaw + Roll around the gravity axis for horizontal output, local pitch for vertical |
| 5 | World Space | All rotation around the gravity axis |
| 6 | Laser Pointer | Like a laser pointer |

**What 90.74 has:** eleven gyro groups per variant run gyro to mouse: Base,
`Gyro` and its four modifiers, `Cursor Gyro`, the two `Temp Cursor Gyro`
layers and the two `Temporary Gyro` layers. Only Base's states a style: 4,
Player Space, since 90.4 (commit 5bf46a7, 2026-09-29). The other ten leave it
unset, as every Deck layout before 90.4 did. No layout in the repo's history or
in Steam's folders on this Mac states 2, so there is no older bind to copy, only
the key. Steam's default for an unset style isn't in the client's UI code.

**Every layout states its style in all eleven groups,** so none depends on the
default: Ibex 1.0 writes 4, Player Space (the bootstrap); the Deck conversion
writes 2, Yaw + Roll (R179); the Edge keeps Ibex's 4 (R180).

**90.75** is the Deck conversion of Ibex 1.0. Its check is the round trip
([C3](#checks)): it is 90.74 apart from the title and these 22 settings, which
`tools.change_report` shows. Nothing for the simulator: it doesn't model gyro
output. On the Deck, with 90.75 in the configurator's title: turning and
leaning the Deck both move the aim. 90.75 is the first Neptune release
published by the pipeline after the backfill.

## Part 4: Ibex is the base; conversion rules

### The author's answers

1. **Ibex is the base; the others are converted from it** (revision 10). A
   change is made on Ibex, and each Ibex release is converted to the Deck and
   to the Edge by their rules. **Read as replacing answer 1** ("copied and
   edited separately"): a converted layout is made again from every Ibex
   release, so a change for the Deck or the Edge alone is written as a
   conversion rule, not as a hand edit. R177.
2. **The Edge has no stick touch:** touching a stick never did anything with the
   old Edge layouts. R182.
3. **The Edge's grips:** Steam uses the four grip names on the Edge too, but L4
   and R4 are on the front and L5 and R5 on the back. Shift and Space go on the
   back, Ctrl and Alt on the front. R181.
4. **The Edge deletes the eight stick-touch layers and both trackpads,** with
   every layer of the two pads. R178, R183.
5. **Gyro is always on** on the Edge: the enable masks come off. `Gyro Off Ramp
   Up`, which Base's right stick edge adds and whose gyro is disabled, still
   turns it off while it is active. So do the other layers whose gyro is
   disabled (`Gamepad`, the menu and Fn layers, the three Transition Sets).
   **Read as the whole layout, Base included,** though the question asked about
   `Gyro`: "always" says so, the gyro off layer is Base's, and on the Deck Base
   gets its gyro from a thumb on a stick, through the `Temporary Gyro` layers
   the Edge deletes. If only `Gyro` was meant, Base keeps its mask and the Edge
   has no gyro in Base. R185.
6. **The mute button is middle mouse.** R184.
7. **The whole pad has the left pad's gestures:** four swipes into the Escape,
   Enter, Tab and Backspace layers, and a click into the arrow keys. The arrow
   click is a Regular Press, not a Soft Press. **Read as every click on the
   whole pad:** all eleven are Regular Presses, not only the arrow chain's three
   (Base's click, the Click Entry Point's ring press, the arrow layer's
   self-hold), so the click works the same in every layer: the four key layers'
   click, the three ramp layers' click and `Gamepad`'s Select too. R183.
8. **New whole-pad layers, by the pad rules:** six `CTP:` layers replace the
   left pad's six and follow the rules and conventions those follow. The one
   difference: the arrow keys have no middle click, so no centre press and no
   Caps Lock. R183, [table](#the-new-whole-pad-layers).

### What each controller has

Checked on 2026-10-15 against the Steam client on this Mac, the repo's older
layouts and the author's answers. The Deck layout, and so Ibex 1.0, binds ten
sources: both sticks with `click`, `edge` and `touch`, both trackpads with
`click`, `touch` and D-pad directions, the right trackpad's scroll, both
triggers, the D-pad, the face buttons, gyro, and in `switch` the four grips,
`button_escape`, `button_menu`, the bumpers and both trackpad touches.

| Input | Steam Controller 2 (`ibex`, the base) | Steam Deck (`neptune`) | DualSense Edge (`dse`) |
|---|---|---|---|
| Both trackpads, click and touch | Yes: Valve's `chord_triton.vdf` has both pads as sources | Yes | One touchpad. The whole pad, `center_trackpad`, takes the left pad's gestures with six `CTP:` layers; its two halves are unbound (author). Valve's PS5 templates and the older Edge layouts bind `center_trackpad` |
| Stick touch | Expected yes: the exploratory layout (`findings/2026-07-11-layer-order-swap/`) binds it (A72) | Yes | **No** (author) |
| Four grips | Yes, on the back: Valve's `chord_triton.vdf` binds L4 and L5, the exploratory layout all four (A72) | Yes, on the back | Same names; L4 and R4 on the front, L5 and R5 on the back (author) |
| Mute button | Unbound | None | `button_capture` (A75): middle mouse |
| Chords | `chord_button`, as the Deck (A73) | `chord_button` for one button, a mask for several | As the Deck; a mask where there is no `chord_button` ID (the whole pad's touch, A76) |

### The bootstrap: Ibex 1.0 from the Deck

Ibex has no layout today. Ibex 1.0 is made once from Deck 90.74 by a builder in
`findings/<date>-ibex-base/`: `controller_type` `controller_triton`, the ibex
stems, version 1.0, Ibex's description, and `gyro_to_2d_conversion_style` 4
(Player Space) in all eleven gyro-to-mouse groups of both variants. If A72
holds, nothing is absent. Chords keep their encoding (A73). This is the last
change that goes from the Deck to Ibex: from Ibex 1.0 on, changes go the other
way (R177), and the Deck's builder chain up to 90.74 stays as the record.

If A73 fails, so that Steam reads `chord_button` wrong on the Steam Controller
2, Ibex writes masks instead, and the Deck and the Edge keep them: both read
masks, and the Deck layout already stores some.

### The conversion rules

New rows in the Definition of Done, beside R101 to R176. `tools.convert
<controller> <ibex version>` applies a controller's rules to an Ibex release and
writes `<controller>/<stem>_latest.json`. The library is
`steam_layout/convert.py`, with one function per rule.

**For every conversion:**

| ID | Rule |
|---|---|
| R177 | **Ibex is the base layout.** Every layout change is made on Ibex. The Deck and Edge layouts are made from an Ibex release by their rules below and never edited by hand (check C1). A change for one of them alone is a new conversion rule in this table. Example: Neptune 90.75 and DSE 1.0 are both conversions of Ibex 1.0 |
| R178 | **Absent inputs.** When a converted layout lacks an input Ibex binds: (a) a bind on it is dropped; (b) a chord or gyro enable mask that needs **any** of several buttons loses the absent ones, and with none left it is treated as (c); (c) a chord that needs **all** its buttons, or its one chord button, with one absent, is dropped, and a gyro enable mask like that is listed, not changed; (d) in a mask that needs all its buttons, a stick touch is dropped when the same stick's push is needed too, since a pushed stick is touched (A74); (e) an inverted chord on an absent button is listed, not rewritten: by A61 it runs while its own input is released and no chord button is held, which no plain bind does; (f) a layer the converted layout can no longer reach is deleted with every command that names it, on title tokens, keeping the list order (R104); (g) a rule about an absent input doesn't apply to that layout: R169's stick touches and R172's right pad on the Edge. Dropping a bind, rather than leaving it to Steam, keeps the result the same whatever Steam does with an input the controller lacks. Example: on the Edge, (f) deletes the eight `LST:` and `RST:` layers |

**Ibex to the Deck (`neptune`):**

| ID | Rule |
|---|---|
| R179 | `controller_type` `controller_neptune`, the Neptune stems, Neptune's next version in the title and Neptune's description. `gyro_to_2d_conversion_style` 2 (Yaw + Roll) in every gyro-to-mouse group (Part 3). Nothing is absent today (A72). Nothing else changes. Example: Ibex 1.0 converts back to 90.74 apart from the title and the 22 gyro styles (C3) |

**Ibex to the DualSense Edge (`dse`),** applied in the order R180, R181, R183,
R182, R184, R185, then R178 (f), so the `CTP:` layers are made from the left
pad's before anything is dropped:

| ID | Rule |
|---|---|
| R180 | **Type.** `controller_type` `controller_ps5_edge`, the dse stems, the Edge's next version in the title and the Edge's description. The gyro style stays Ibex's 4 (Player Space). Chords keep their encoding; a chord on an input with no `chord_button` ID is a mask (the whole pad's touch, bit 27) |
| R181 | **Grips.** Each side's two grips swap, with everything bound to them: L4 `button_back_left_upper` with L5 `button_back_left`, R4 with R5. Shift and Space then sit on the back paddles, Ctrl and Alt on the front buttons (author). Nine layers bind each grip; no chord or gyro mask names one |
| R182 | **No stick touch.** Both stick touches are absent inputs (R178): the Edge's sticks have no touch (author) |
| R183 | **The whole pad.** The left pad's role goes to the whole pad, `center_trackpad`. In every layer the left pad's binds move to it, its touch switch to `center_trackpad_touch`, and chords on its touch (`chord_button` 16, mask bit 19) to mask bit 27 (A76). The left pad's six layers are replaced by six `CTP:` layers made from them ([table](#the-new-whole-pad-layers)), whose arrow keys have no centre press: no middle click, no Caps Lock. Every click on the whole pad is a Regular Press, with its model's settings. The right pad is absent (R178): `right_trackpad`, `(switch, right_trackpad_touch)` and chords on its touch (`chord_button` 17, mask bit 20). On the Edge, R101's self-hold exception covers `CTP: Arrow Keys` with a Regular Press, R120's pad reset is `CTP: Click Entry Point`'s, and R149 and R172 hold for the whole pad as for the left pad |
| R184 | **Mute button.** Base binds `button_capture` (A75) to `mouse_button MIDDLE, , ` with a Regular Press. No other layer binds it, so it answers in every layer |
| R185 | **Gyro always on.** The enable mask (`gyro_ratchet_button_mask`, `gyro_ratchet_button_requireany_or_all`) comes off the gyro groups of Base, `Gyro` and its four modifiers. Layers whose gyro is disabled, `Gyro Off Ramp Up` among them, still turn it off |

### What the Edge conversion does

Computed on 2026-10-15 from the 90.74 snapshots, both variants alike, on a
scratch copy outside the repo. Ibex 1.0 is 90.74 apart from the type, the title
and the gyro style, so the counts hold for the Edge conversion of Ibex 1.0.

- **Stick touch (R182):** 426 activators go, 213 per stick. Eight layers can't
  be reached any more: `LST: Entry Point`, `LST: Tap Cover`, `LST: Double Tap`,
  `LST: Temporary Gyro`, and the same four `RST:` layers. Base's stick touch
  was their only way in.
- **22 layers are deleted:** the eight above; the right pad's seven
  (`RTP: Entry Point`, `RTP: Tap Cover`, `RTP: Double Tap`,
  `RTP: Circular Scroll`, `RTP: Click Entry Point`, `RTP: Mouse Buttons`,
  `RTP: Middle Click`); and the left pad's seven (`LTP: Click Entry Point`,
  `LTP: Arrow Keys`, `LTP: Middle Click`, `Escape`, `Tab`, `Backspace`,
  `Enter`), six of them replaced by `CTP:` layers. 69 layers stay and 6 come
  in: 75.
- **What goes:** Base's right pad (the mouse pointer; its click into the right
  pad's click layers, mouse buttons and middle click; its touch into
  `RTP: Entry Point` and its circular scroll), and the left pad's centre click
  (Caps Lock). Middle mouse moves to the mute button (R184).
- **What the whole pad has:** the swipes into its four key layers, the click
  into its arrow keys, Base's 2D scroll, the two mode shifts Base makes while a
  thumb is on the pad (the D-pad and the face buttons), and the left pad's
  binds in the 20 other layers that have them: the ramps, `Gamepad`, the menu
  Entry Points, the windows and `Steering | LS: Entry Guard`.
- **No layer left without a remove:** every layer that can still be reached is
  still named by some `remove_layer`. That is a rough count; the Cleanup audit
  is the real check (C2).
- `Gyro Off Ramp Up` stays reachable.

### The new whole-pad layers

Each is made from the left-pad layer it replaces (its model), so it follows the
rules and conventions that layer follows, with the pad changed to the whole pad
and the differences the author named. Settings not named here are the model's.

| New layer | Model | On the whole pad |
|---|---|---|
| `CTP: Click Entry Point` | `LTP: Click Entry Point` | D-pad pad. Its ring press (Regular Press, Hold to Repeat every 50 ms, not interruptible, 5 ms start delay, silent) hands over: it adds `CTP: Arrow Keys`, then removes the layer (arrays run bottom to top). **No centre press:** no middle click, no Caps Lock. The touch's Release removes the layer; R120's reset on the touch (Regular Press, Hold to Repeat, not interruptible, silent) removes `CTP: Arrow Keys` |
| `CTP: Arrow Keys` | `LTP: Arrow Keys` | D-pad pad without Requires Click (deadzone 23000, outer ring inverted). Each direction types its arrow key, silent, and its Release removes the layer; the ring's Release removes it; the click holds the layer (R101's self-hold, a Regular Press, with the model's bump); the touch's Release removes it |
| `CTP: Escape`, `CTP: Enter`, `CTP: Tab`, `CTP: Backspace` | `Escape`, `Enter`, `Tab`, `Backspace` | Single-button pad. The touch types the key, silent; the touch's Release removes the layer; the click (Regular Press, Hold to Repeat every 50 ms, not interruptible, silent) removes the layer, so Base's click goes on to the arrow keys (90.73) |

Each keeps its model's cleanup functions in R133's shape: on both stick edges,
the 90.72 copy guarded by the pad's touch, now the whole pad's (the Edge has no
stick touch, so these edges are its stick cleanups), and on every button it
retypes or blocks (R170, R171). They take their models' places in the layer
list (90.64's order by parent, R104). How they are reached, as their models
are:

- **Base:** the whole pad is a directional swipe. West adds `CTP: Escape`,
  east `CTP: Enter`, north `CTP: Tab`, south `CTP: Backspace`, each with the
  model's Low bump. The click (Regular Press, Hold to Repeat every 50 ms,
  silent) adds `CTP: Click Entry Point`. While a thumb is on the pad, Base
  mode-shifts the D-pad and the face buttons, on `center_trackpad_touch`.
- **The three ramp layers:** the whole pad's click adds `CTP: Click Entry Point`
  and removes the ramps, as their left pad's click does.
- **`Gamepad`:** the whole pad's click is Select; its touch blocks Base's mode
  shifts.
- **Windows and menu layers (R149, R172):** the whole pad takes the left pad's
  known replacements. Its swipes type the four keys directly and its click is
  blocked.
- **Every command that named a model names its new layer:** per variant,
  4 adds and 12 removes of the Click Entry Point, 1 add and 16 removes of each
  key layer, and 14 removes of the arrow layer.

### Checks

Each is a test.

- **C1:** each converted layout is what `tools.convert` makes from the Ibex
  release it names, so a hand edit fails. Ibex's own working layout is held to
  its newest builder, as Neptune's is today (R156).
- **C2:** `tools.audit_build` passes on every controller's layout, with R178 (g)
  for the Edge.
- **C3, the round trip:** Ibex 1.0 converted to the Deck is 90.74 apart from
  the title and the 22 gyro styles. It shows that the bootstrap and R179 lose
  nothing.
- **C4:** the Deck's scenario tests run on Ibex 1.0 (all pass) and on the Edge
  conversion stopped after R180 to R182, with the Deck's inputs translated
  through R181's swap: pressing L4 for Shift presses the Edge's L5 paddle. Those
  that need a stick touch are skipped by name. `tests/scenario.py` loads every
  working layout through `layout_path`
  ([tests/scenario.py:108](../tests/scenario.py#L108)), which C4 points at the
  layout under test; scenarios pinned to an older Deck release stay on the Deck.
- **C5:** each `CTP:` layer is its model with only the table's changes (a test
  reads both). The Edge conversion has its own scenarios: each swipe on the pad
  adds its key layer and its touch types the key; a click on the pad's ring
  gives the arrow key of that direction, with Regular Presses only; a click in
  the centre gives nothing; a click in a key layer ends it and goes on to the
  arrow keys; the mute button gives middle mouse in Base and in a modifier
  layer; gyro runs in Base and in `Gyro` with both sticks centred and stops
  while the right stick is at its edge (`Gyro Off Ramp Up`); Shift is on the
  left paddle and Ctrl on the left front button; nothing adds a deleted layer.
- Each rule has its own tests on small layouts.

### Building after the switch

- A change is built on Ibex: a builder in `findings/<date>-<slug>/` reads the
  Ibex snapshot before it, as builders read the release before them today, and
  writes `ibex/*_latest.json`.
- `python3 -m tools.convert neptune` and `tools.convert dse` write the Deck and
  the Edge from it. Each controller whose layout changed gets its next version,
  a snapshot and, when the author wants, a release.
- The test suite keeps running on Neptune, the Deck conversion, as today; C3
  keeps it a faithful copy of Ibex. New scenarios are written for Ibex and run
  on each conversion whose inputs they use.
- The author tests on the Deck and on the Edge, both conversions; Ibex itself
  on a Steam Controller 2 when one is at hand.

### Assumptions to add

| ID | Assumption | How it's checked |
|---|---|---|
| A72 | The Steam Controller 2 has the Deck's inputs: both trackpads, stick touch, four grips on the back | Valve's `chord_triton.vdf` and the exploratory layout; a Steam Controller 2's configurator when one is at hand |
| A73 | A `chord_button` chord works on the Steam Controller 2, though Steam's own exports for it write masks | The 2026-09-27 audit read the masks as the client's newer format, not a device limit. Checked by loading Ibex 1.0 and opening a chord in the configurator |
| A74 | A stick pushed off centre is also touched, so a mask needing both a stick's push and its touch means the same as one needing the push alone | How the thumb works the stick. R178 (d) relies on it; on the Edge today the only mask it would touch is Base's gyro mask, which R185 takes off |
| A75 | The DualSense Edge's mute button is `button_capture` | Steam's mask table labels that button's bit (29) "Mute" and relabels it "Capture" only for Switch controllers; the client's state message calls it `button_mute_capture`; Valve's own Edge layout binds `button_capture` to screenshot. Checked in the Edge's configurator, then by pressing mute with DSE 1.0 |
| A76 | The whole touchpad's touch is the switch input `center_trackpad_touch` and mask bit 27, and the Edge accepts a mask chord on it | The names sit beside the Deck's pad-touch names in the Steam client's library; Steam's mask table labels bits 27 and 28 the centre pad's touch and click. Checked by loading DSE 1.0 and opening a guarded stick-edge cleanup in the configurator |

## Issues found with the simple pipeline

"The simple pipeline" is: a tool bumps the version, the newest folder per
controller goes in the zip, a tag publishes. Checked on 2026-10-15.

| # | Issue | Evidence | What the plan does |
|---|---|---|---|
| 1 | The builder already writes the version, so a bump tool would fight it | [build_candidate.py:82](../findings/2026-10-15-fn-right-stick/build_candidate.py#L82) sets the title's version; [the R156 test](../tests/test_steering_rtp_menu_chords.py#L51) matches builders to layouts by it | No bump tool. `check` reads the version |
| 2 | The newest folder isn't the newest release | `versions/neptune/` holds two trials (90.53, 90.69) and the 90.39 candidate, whose files are named `...-fallback-window_hold-gyro_90.39`; sorted as text, 90.9 comes after 90.10 | Latest release = highest tag, compared as numbers. Trials are never tagged |
| 3 | A GitHub runner has no VDF exporter | `test_convert_vdf.mjs` fails by design without the VS Code extension; `convert_vdf.mjs` finds it under `~/.vscode/extensions` | Open VSX serves 5.12.3. Its serializer source map is byte for byte the installed one; only VS Code's install metadata in `package.json` differs |
| 4 | Nothing checks that a VDF matches its JSON | Today only the titles are compared, by hand | Check 3. All 140 JSONs today (138 snapshots, 2 working) export to their committed VDFs byte for byte |
| 5 | A published snapshot could still change | publishing.md: follow-up edits in a batch refresh the snapshot | Frozen once tagged; check 6 and a test |
| 6 | Tagging the 90.74 release commit wouldn't run the workflow | A tag runs the workflow file in its own commit | Backfill tag on the pipeline's commit |
| 7 | Two controllers' VDFs can overwrite each other on one machine | All templates share one Steam folder | New controllers' stems start with the controller |
| 8 | GitHub's "Latest" is one release for the whole repo, the newest by date | Per-controller releases would hide the others | Every release carries every controller's latest; a lower version than the latest is refused (check 4) |
| 9 | Tags pushed together can miss each other's version, or not publish at all | An Ibex change usually tags three controllers at once. Two runs at once each build a bundle without the other's new version. With a concurrency group, GitHub keeps one run going and one waiting, and cancels the waiting run when a third arrives | `concurrency: release`, and each run publishes every tag that has no release yet, oldest first, so a cancelled run's tag is published by the next |
| 10 | GitHub runs Linux; this repo has only run on this Mac | Python 3.9.6 and Apple clang here; this Mac's file system ignores case (`core.ignorecase true`), Linux doesn't; the chain engine has only been built with clang | Pin Python 3.9 and Node 26. Case and compiler only show on the first run: run the workflow on the backfill tag before any real release |
| 11 | The test suite takes 46 minutes, not the README's "about five" | A fresh clone of 87369af (90.70) with an empty home folder: 1,301 tests pass (25 expected failures) in 2,781 s on this Mac, so nothing depends on ignored files or the home folder. The exporter test fails there, as issue 3 says | The workflow splits the Python tests by module across four parallel jobs, once per tagged commit. The README's run time is corrected |
| 12 | The repo is public | `api.github.com` answers for it without a login | Releases are public downloads, as the VDFs on `main` already are |

## Order and checks

| Step | Done when |
|---|---|
| 0 | 90.71 to 90.74 committed; git status clean of other sessions' work |
| 1 | Registry in, with Ibex as the base. `ibex/`, `dse/`, `versions/ibex/`, `versions/dse/` exist. No `neptune` path left in live code outside the registry. Audits, change report and tests give the same results as before |
| 2 | `tools.release check neptune` passes on 90.74 and fails on a changed snapshot, a stale title, a VDF out of date and a missing CHANGELOG section. `neptune-v90.74` publishes a release whose zip holds Neptune 90.74's two VDFs and a `RELEASE.md`, and the permanent link downloads it |
| 3 | `steam_layout/convert.py` and `tools.convert` with R177 to R185, and the audits' controller rules. Each rule's tests pass |
| 4 | Ibex 1.0 built by the bootstrap builder; C2 and C4 pass |
| 5 | Neptune 90.75 converted from Ibex 1.0; C1, C2 and C3 pass |
| 6 | DSE 1.0 converted from Ibex 1.0; C1, C2, C4 and C5 pass |
| 7 | `ibex-v1.0`, `neptune-v90.75` and `dse-v1.0` pushed together and all three published; the bundle holds all three controllers |

Tests to add: `test_controllers.py` (every registry directory exists; every
`_latest.json` has its registry `controller_type`; new stems start with the
controller; every gyro-to-mouse group states its controller's gyro style),
`test_release.py` (version order as numbers, latest release from tags, each
`check` failure, the bundle's file list, released snapshots unchanged) and
`test_convert.py` (each rule, C1 to C5).

Not in this plan: running the checks on every push to `main`, not only on tags.
It would catch a broken state before tagging, at 46 minutes of tests per push,
split four ways.
