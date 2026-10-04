"""The capped walk: every stack the bindings can build with at most N layers on at once.

The backward chains (chains.py) follow one layer's chain and allow one extra
layer of each kind: one arrival, one bystander, one landing. This walk has no
such limit. From the action set it fires every binding the chains follow, on
every stack, in every order, until no new stack appears. The only limit is how
many layers may be on at once:

    walk = Walk(layout, max_layers=6).run()
    walk.settled                 # True: every stack with at most 6 layers on was built
    walk.count, walk.presses     # how many stacks, and the longest shortest press sequence
    walk.path(stack)             # the bindings that built a stack, shortest first

Rules:

- It follows the same bindings as the chains: every binding that adds a layer
  (not recovery, reset, hold_layer or mode shifts) and every removal-only
  binding the chains settle on. A binding fires only when its layer answers
  that input on the stack (flow_model.resolve).
- A stack with more than `max_layers` layers on, the action set not counted,
  is not built. `MAX_SIMULTANEOUS` (10) is the author's ceiling of 2026-10-03.
  Without a cap the walk does not settle: on 90.22 it had 71 million stacks
  after 12 presses and was still growing.
- Chords and time are ignored, as in the chains: a stack here can be one a
  person can't produce.
- Nothing is stored on disk. A stack is kept in memory as bytes of layer
  numbers, with the stack it came from, so every stack has a shortest path.
- `memory` (bytes) stops the walk when the process has used that much; the
  walk is then not settled.
- It uses every core. Once a press has `POOL_MIN` stacks to test, they are
  split over worker processes; the main process keeps the one table of known
  stacks, so the result is the same as on one core, in the same order.

The cost grows about four times per extra layer. On 90.22: 4 layers 47
thousand stacks, 5 layers 243 thousand, 6 layers 1.1 million (17 s), 7 layers
4.2 million (67 s), 10 layers 80 million (40 minutes, 7 GB). Those are for
one core; every core is about 3.5 times faster. native.py runs the same walk
in a compiled engine (10 layers in 25 s), and this module is its reference.
Record: findings/2026-10-03-simultaneous-cap/README.md.
"""
import multiprocessing
import os
import resource

from .chains import NOT_FOLLOWED, SETTLE
from .flow_model import Inventory
from .model import defined, entries

MAX_SIMULTANEOUS = 10      # layers on at once, the action set not counted (author, 2026-10-03)
POOL_MIN = 20000           # stacks in one press before the work is split over processes
CHUNK = 4000               # stacks per task
_STOP = object()
_ACTIVE = None             # (walk, test) of the run in progress; the forked workers inherit it


def _expand(stacks):
    """One task: ([(next stack, the stack it came from)], [(test result, the first stack that gave it)])."""
    walk, test = _ACTIVE
    children, results = {}, {}
    for stack in stacks:
        found, stops = walk.answers(stack)
        if test:
            for item in test(stack, found, stops):
                if item not in results:
                    results[item] = stack
        for nxt, _ in walk.successors(stack, found):
            if nxt not in children:
                children[nxt] = stack
    return list(children.items()), list(results.items())


class Walk:
    def __init__(self, layout, max_layers=MAX_SIMULTANEOUS, inventory=None):
        if len(layout.presets) > 255:
            raise ValueError("the walk keeps a stack as bytes: at most 255 layers")
        self.layout, self.max_layers = layout, max_layers
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
        self.moves = [[] for _ in self.titles]   # per layer: (control, ops, binding) for every binding followed
        for t in (inventory or Inventory.of(layout)).transitions:
            adds = t.role not in NOT_FOLLOWED and any(op == "add_layer" for op, _ in t.ops)
            settles = t.role in SETTLE and t.ops and all(op == "remove_layer" for op, _ in t.ops)
            if adds or settles:
                ops = tuple((op != "remove_layer", self.ident[target]) for op, target in t.ops)
                self.moves[self.ident[t.layer]].append((self.control(t.source, t.input), ops, t))
        self.parents = {}                        # stack -> the stack it was first built from
        self.settled, self.stopped, self.presses, self.longest = False, None, 0, 0
        self.engine = None                       # the compiled engine's result, when it ran this walk (native.py)

    def control(self, source, name):
        return self.controls.setdefault((source, name), len(self.controls))

    def stack(self, titles):
        return bytes(self.ident[t] for t in titles)

    def named(self, stack):
        return tuple(self.titles[i] for i in stack)

    @property
    def count(self):
        return self.engine["stacks"] if self.engine else len(self.parents)

    def answers(self, stack):
        """({control: the layer that answers it}, {source: why its lookup stopped}) for a stack.

        The same lookup as flow_model.resolve, for every input at once. A stop is ("disabled", layer) or
        ("mode", the top layer of that source): nothing below it answers on that source.
        """
        found, state, stops = {}, {}, {}
        for layer in reversed(stack):
            for source, mode, bound in self.groups[layer]:
                seen = state.get(source)
                if seen is _STOP:
                    continue
                if mode is None:
                    state[source], stops[source] = _STOP, ("disabled", layer)
                    continue
                if seen is None:
                    state[source] = seen = (mode, layer)
                elif seen[0] != mode:
                    state[source], stops[source] = _STOP, ("mode", seen[1])
                    continue
                for control in bound:
                    if control not in found:
                        found[control] = layer
        return found, stops

    def successors(self, stack, found):
        """[(next stack, binding)] for every followed binding that answers on `stack`, within the cap."""
        result = []
        for layer in stack:
            for control, ops, binding in self.moves[layer]:
                if found.get(control) != layer:
                    continue
                new = list(stack)
                for add, target in ops:
                    if add:
                        if target not in new:
                            new.append(target)
                    elif target != self.base and target in new:
                        new.remove(target)
                if self.max_layers is None or len(new) - 1 <= self.max_layers:
                    result.append((bytes(new), binding))
        return result

    def run(self, test=None, collect=None, memory=None, progress=None, workers=None):
        """Build every stack, breadth first.

        `test(stack, found, stops)` returns hashable results for one stack. It runs in the worker processes,
        so it must not change anything. `collect(result, stack)` is called in the main process, once per
        distinct result of a task, with the first stack that gave it, in walk order.
        `progress(presses, tested at this depth, new stacks, stacks in all)` is called after each depth.
        `workers`: how many processes (default: every core). Small walks stay in this process.
        """
        global _ACTIVE
        workers = workers or os.cpu_count() or 1
        start = bytes([self.base])
        self.parents = {start: None}
        frontier, pool = [start], None
        _ACTIVE = (self, test)
        try:
            while frontier:
                tasks = [frontier[i:i + CHUNK] for i in range(0, len(frontier), CHUNK)]
                if workers > 1 and len(frontier) >= POOL_MIN:
                    if pool is None:
                        pool = multiprocessing.get_context("fork").Pool(workers)
                    outputs = pool.imap(_expand, tasks)
                else:
                    outputs = map(_expand, tasks)
                new = []
                for children, results in outputs:
                    if collect:
                        for item, stack in results:
                            collect(item, stack)
                    for nxt, parent in children:
                        if nxt not in self.parents:
                            self.parents[nxt] = parent
                            new.append(nxt)
                            if len(nxt) - 1 > self.longest:
                                self.longest = len(nxt) - 1
                    if memory and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > memory:
                        self.stopped = f"the memory limit was reached after {self.presses} presses"
                        return self
                if progress:
                    progress(self.presses, len(frontier), len(new), len(self.parents))
                if new:
                    self.presses += 1
                frontier = new
        finally:
            _ACTIVE = None
            if pool is not None:
                pool.terminate()
                pool.join()
        self.settled = True
        return self

    def path(self, stack):
        """The bindings that built `stack` from the action set, as text: a shortest sequence."""
        steps = []
        while self.parents.get(stack) is not None:
            before = self.parents[stack]
            binding = next(b for nxt, b in self.successors(before, self.answers(before)[0]) if nxt == stack)
            steps.append(binding.describe())
            stack = before
        return list(reversed(steps))
