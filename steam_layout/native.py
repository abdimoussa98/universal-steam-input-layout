"""The compiled engine for the chain walk with extra presses (engine/chain_engine.cpp).

    native.available()                         # the engine's path, built on first use
    tables = native.Tables(layout)             # the layout as the engine reads it
    result = native.run(tables, exits, extras=6)

The chains (chains.py) follow one layer's chain and allow one extra press (arrival)
along it. The engine does the same walk with up to `extras` of them, tests every stack
for lost exits, and tests every stack one landing past it. It is what the Cleanup
audit's hidden-exit check reads (cleanups.covered_exits). chains.py is its reference:
tests/test_native.py checks that both give the same stacks and the same findings.

- The engine is built with a C++ compiler (clang++, c++ or g++) into engine/build/,
  which git ignores, and rebuilt when its source changes. Without a compiler `run`
  raises: the check does not fall back to anything else (author, 2026-10-04).
- The layout's tables go to the engine through a pipe and the result comes back
  through one. Every stack lives in the engine's memory for the length of the run;
  nothing is stored on disk.
- With `paths` each finding has the bindings that built its example stack, with the
  fewest extra presses. It costs twice the memory, so past `PATHS_UP_TO` extra presses
  cleanups.py runs the walk without them and takes the paths from a second run.

`exits` is {layer number: [(exit number, control number, source, on the keeper, the
layer's mode on that source)]}. The result is the engine's JSON as a dict: settled,
stopped, states, stacks, extras, longest, landings, seconds, memory_mb, threads,
by_cost, and pairs with who, lower, exits, cost, stack and path ([binding number, how];
how: 0 step, 1 settle, 2 arrival, 3 landing).

On 90.22, 14 cores: 4 extra presses 1 s; 6: 15 s and 1 GB (2 GB with paths); 7: 50 s
and 6 GB; 8: 8 minutes and 11 GB. Record: findings/2026-10-03-simultaneous-cap/README.md.
"""
import json
from pathlib import Path
import shutil
import subprocess
import threading

from .chains import NOT_FOLLOWED, SETTLE
from .flow_model import Inventory
from .model import defined, entries

SOURCE = Path(__file__).with_name("engine") / "chain_engine.cpp"
BINARY = SOURCE.parent / "build" / "chain_engine"
HOW = ("", "settle: ", "arrival: ", "landing: ")
PATHS_UP_TO = 6            # extra presses up to which one run keeps the paths
NO_COMPILER = ("the hidden-exit check needs a C++ compiler to build its engine "
               "(steam_layout/engine/chain_engine.cpp): clang++, c++ or g++ was not found")
_checked = None


def available():
    """The engine's path, building it when it is missing or older than its source. Raises without a compiler."""
    global _checked
    if _checked is None:
        if not (BINARY.exists() and BINARY.stat().st_mtime >= SOURCE.stat().st_mtime):
            compiler = shutil.which("clang++") or shutil.which("c++") or shutil.which("g++")
            if not compiler:
                raise RuntimeError(NO_COMPILER)
            BINARY.parent.mkdir(exist_ok=True)
            done = subprocess.run([compiler, "-O3", "-std=c++17", "-pthread", "-o", str(BINARY), str(SOURCE)],
                                  capture_output=True, text=True)
            if done.returncode:
                raise RuntimeError("the chain engine did not build: " + (done.stderr.strip().splitlines() or ["no output"])[0])
        _checked = BINARY
    return _checked


class Tables:
    """A layout as the engine reads it: layers, inputs and bindings as small numbers.

    It follows the same bindings as the chains: every binding that adds a layer (not recovery, reset,
    hold_layer or mode shifts) and every removal-only binding the chains settle on.
    """

    def __init__(self, layout, inventory=None):
        if len(layout.presets) > 126:
            raise ValueError("the engine keeps a layer in seven bits: at most 126 layers")
        self.layout = layout
        self.titles = list(layout.presets)
        self.ident = {title: i for i, title in enumerate(self.titles)}
        self.base = self.ident[layout.base]
        self.controls = {}                       # (source, input) -> small number
        self.groups = []                         # per layer: (source, mode or None when disabled, bound controls)
        self.removes = {}                        # (layer, control) -> the layers any entry on that input removes
        for title in self.titles:
            rows = []
            for source, group in layout.active(title).items():
                if group["mode"] == "disabled":
                    rows.append((source, None, ()))
                    continue
                bound = []
                for name, value in group.get("inputs", {}).items():
                    if not defined(group, name):
                        continue
                    control = self.control(source, name)
                    bound.append(control)
                    removed = {self.ident[t] for _, e in entries(value["activators"]) for op, t in layout.layer_ops(e)
                               if op == "remove_layer" and t in self.ident}
                    if removed:
                        self.removes[(self.ident[title], control)] = frozenset(removed)
                rows.append((source, group["mode"], tuple(bound)))
            self.groups.append(tuple(rows))
        self.bindings = []                       # binding number -> the binding
        self.moves = [[] for _ in self.titles]   # per layer: (binding number, control, ops)
        for t in (inventory or Inventory.of(layout)).transitions:
            adds = t.role not in NOT_FOLLOWED and any(op == "add_layer" for op, _ in t.ops)
            settles = t.role in SETTLE and t.ops and all(op == "remove_layer" for op, _ in t.ops)
            if adds or settles:
                ops = tuple((op != "remove_layer", self.ident[target]) for op, target in t.ops)
                self.moves[self.ident[t.layer]].append((len(self.bindings), self.control(t.source, t.input), ops))
                self.bindings.append(t)

    def control(self, source, name):
        return self.controls.setdefault((source, name), len(self.controls))

    def named(self, stack):
        return tuple(self.titles[i] for i in stack)

    def text(self, exits, extras, landings, threads, memory_mb, paths, batch):
        """The engine's input: whole numbers, in the order chain_engine.cpp reads them."""
        sources, modes = {}, {}
        out = []
        for rows in self.groups:
            out.append(len(rows))
            for source, mode, bound in rows:
                out += [sources.setdefault(source, len(sources)),
                        -1 if mode is None else modes.setdefault(mode, len(modes)), len(bound), *bound]
        for rows in self.moves:
            out.append(len(rows))
            for number, control, ops in rows:
                out += [number, control, int(any(add for add, _ in ops)), len(ops)]
                for add, target in ops:
                    out += [int(add), target]
        out.append(len(self.removes))
        for (layer, control), removed in self.removes.items():
            out += [layer, control, len(removed), *sorted(removed)]
        for layer in range(len(self.titles)):
            rows = exits.get(layer, ())
            out.append(len(rows))
            for number, control, source, on_keeper, mine in rows:
                out += [number, control, sources.setdefault(source, len(sources)), int(on_keeper),
                        -1 if mine is None else modes.setdefault(mine, len(modes))]
        head = [len(self.titles), self.base, len(self.controls), len(sources), extras, int(landings), threads or 0,
                memory_mb, int(paths), batch or 0]
        return " ".join(map(str, head + out)) + "\n"


def run(tables, exits, extras, landings=True, threads=None, memory=None, progress=None, paths=True, batch=None):
    """Run the engine: the chain walk with `extras` extra presses per chain, and the lost exits it meets.

    `memory` (bytes) stops the walk when its tables pass it; the result is then not settled.
    `progress(extra presses done, states so far)` is called as each cost is finished.
    `batch`: how many waiting states are taken up at a time (the tests set it low).
    """
    if not 0 <= extras <= 14:
        raise ValueError("the engine walks 0 to 14 extra presses")
    text = tables.text(exits, extras, landings, threads, max(1, memory // (1024 * 1024)) if memory else 0, paths, batch)
    with subprocess.Popen([str(available())], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True) as process:
        def follow():
            for line in process.stderr:
                words = line.replace(",", "").split()
                if progress and line.startswith("walk:") and len(words) >= 5:
                    progress(int(words[1]), int(words[3]))

        reader = threading.Thread(target=follow, daemon=True)
        reader.start()
        process.stdin.write(text)
        process.stdin.close()
        output = process.stdout.read()
        code = process.wait()
        reader.join()
    if code:
        raise RuntimeError(f"the chain engine stopped with exit code {code}")
    return json.loads(output)


def describe(tables, path):
    """A path of the engine as text, like `Why.describe()`."""
    return [HOW[how] + tables.bindings[number].describe() for number, how in path]
