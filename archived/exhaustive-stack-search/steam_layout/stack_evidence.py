"""Witnessed facts from a compatible HeldModel search, without loading SQLite.

These are lower bounds on reachability in the exported model. The model file
must match byte for byte; this does not establish fidelity to Steam's runtime.
Candidate seeds may be sampled, but ``facts`` always scans every stored stack.
Every witness retained for a fact is replayed from Base under the current
HeldModel, and its final stack is checked against the stored fact's stack.
"""
from collections import OrderedDict
from pathlib import Path
import struct
import tempfile

from .stackdb import LEVEL_META, META, NO_PARENT, Value


class EvidenceError(ValueError):
    """A search cannot safely be used as evidence for the requested model."""


class Evidence:
    def __init__(self, model, db=None):
        self.model, self.db = model, db
        self._facts = {}
        self._validated_states = {}
        self._successors = OrderedDict()
        if model.missed or hasattr(model, "k"):
            raise EvidenceError("Evidence requires the full HeldModel with missed releases disabled")
        self._values = {}
        for lid, title in enumerate(model.layer_names):
            for jid in model.blocks.get(lid, ()):
                self._values[lid, jid] = Value(blocked_by=title)
            for jid in model.binds.get(lid, ()):
                source, name = model.inputs[jid]
                self._values[lid, jid] = Value(
                    owner=title,
                    activators=model.layout.active(title)[source]["inputs"][name]["activators"],
                )
        if db is not None:
            self._validate()

    def _file(self, name):
        path = self.db.dir / name
        if not path.is_file():
            raise EvidenceError(f"Missing search evidence artifact: {path}")
        return path

    def _validate(self):
        db = self.db
        if not db.held:
            raise EvidenceError("Search evidence must have been generated with --held")
        if db.top:
            raise EvidenceError("Top-K search is an upper bound, not witnessed evidence")
        if db.summary.get("missed") is not False:
            raise EvidenceError("Search evidence must explicitly disable missed releases")
        try:
            actual = self._file("model.txt").read_bytes()
            with tempfile.TemporaryDirectory(prefix="stack-evidence-") as tmp:
                expected = Path(tmp, "model.txt")
                self.model.write_held(expected)
                if actual != expected.read_bytes():
                    raise EvidenceError("Stale or mismatched search evidence: model.txt differs from the current HeldModel")
            self._file("stacks.tsv")
            if db.layers != self.model.layer_names or db.inputs != self.model.inputs or db.controls != self.model.controls:
                raise EvidenceError("Search evidence layer, input, or control indexes differ from the current HeldModel")
            total = 0
            if db.levels:
                starts = db.starts
                if len(starts) < 2 or starts[0] != 0 or any(b < a for a, b in zip(starts, starts[1:])):
                    raise EvidenceError("Invalid search evidence level boundaries")
                for level, (start, stop) in enumerate(zip(starts, starts[1:])):
                    count = stop - start
                    prefix = f"levels/level_{level:03d}"
                    meta = self._file(prefix + ".meta")
                    records = self._file(prefix + ".rec")
                    if meta.stat().st_size != count * LEVEL_META.size or records.stat().st_size < count * 11:
                        raise EvidenceError(f"Truncated search evidence state artifacts: {prefix}")
                    total += count
            else:
                if db.shards < 1:
                    raise EvidenceError("Invalid search evidence shard count")
                for shard in range(db.shards):
                    prefix = f"shard_{shard}"
                    meta = self._file(prefix + ".meta")
                    records = self._file(prefix + ".stacks")
                    size = meta.stat().st_size
                    count = size // META.size
                    if size % META.size or records.stat().st_size < count * 11:
                        raise EvidenceError(f"Truncated search evidence state artifacts: {prefix}")
                    total += count
            if total != db.summary.get("states") or total < 1:
                raise EvidenceError("Search evidence state artifacts disagree with summary.json")
        except OSError as exc:
            raise EvidenceError(f"Cannot read search evidence: {exc}") from exc

    def _rows(self):
        try:
            for row in self.db.distinct_stacks():
                stack = row["stack"]
                if (not stack or stack[0] != self.model.layer_names[0]
                        or len(set(stack)) != len(stack)
                        or any(title not in self.model.index for title in stack)
                        or not row["clean"]):
                    raise EvidenceError("Invalid stack in search evidence stacks.tsv")
                yield row
        except (OSError, KeyError, IndexError, ValueError) as exc:
            if isinstance(exc, EvidenceError):
                raise
            raise EvidenceError(f"Cannot read search evidence stacks.tsv: {exc}") from exc

    def seed_states(self, limit=None):
        """Yield the start and representative numeric states for candidate pruning.

        ``limit`` caps additional distinct witness ids, never the facts scan.
        In-memory indexes provide representative witnesses; the disk format
        falls back to the witness for every distinct stack.
        """
        if limit is not None and limit < 0:
            raise ValueError("seed limit must be nonnegative")
        yield self.model.start()
        if self.db is None or limit == 0:
            return
        if self.db.levels:
            gids = (row["witness"] for row in self._rows())
        else:
            gids = (gid for index in (self.db._under, self.db._below, self.db._top)
                    for gid in index.values())
        seen = set()
        for gid in gids:
            if gid in seen:
                continue
            seen.add(gid)
            state = self._state(gid)
            if state != self.model.start():
                yield state
            if limit is not None and len(seen) >= limit:
                return

    def _state(self, gid):
        if gid in self._validated_states:
            return self._validated_states[gid]
        try:
            stack, held, missed = self.db.state(gid)
            state = (self.model.ids_of(stack), frozenset(self.model.cid[c] for c in held), missed)
            if (missed or not state[0] or state[0][0] != 0 or len(set(state[0])) != len(state[0])
                    or not self.model.valid(state[1]) or any(not self.model.owner[c] for c in state[1])):
                raise EvidenceError(f"Invalid HeldModel state in search evidence: {gid}")
            return state
        except (OSError, KeyError, IndexError, ValueError, struct.error) as exc:
            if isinstance(exc, EvidenceError):
                raise
            raise EvidenceError(f"Cannot read search evidence state {gid}: {exc}") from exc

    def _replay(self, gid):
        """Certify an event chain under today's model, reusing verified prefixes."""
        if self.db is None:
            raise EvidenceError("No search database is available for a witness")
        target, chain, visiting = gid, [], set()
        try:
            while gid not in self._validated_states:
                if gid in visiting:
                    raise EvidenceError(f"Cycle in search evidence witness ancestry at state {gid}")
                visiting.add(gid)
                state = self._state(gid)
                _, _, parent, event = self.db._locate(gid)
                if parent == NO_PARENT:
                    if state != self.model.start():
                        raise EvidenceError(f"Search evidence witness {gid} does not start at Base")
                    self._validated_states[gid] = state
                    break
                chain.append((gid, parent, event, state))
                gid = parent
            for child, parent, event, state in reversed(chain):
                if parent not in self._successors:
                    self._successors[parent] = self.model.successors(self._validated_states[parent])
                    if len(self._successors) > 256:
                        self._successors.popitem(last=False)
                else:
                    self._successors.move_to_end(parent)
                decoded = (event // 16 - 1, event % 16)
                if (state, decoded) not in self._successors[parent]:
                    raise EvidenceError(f"Search evidence witness replay failed at state {child}: "
                                        f"event {event} from state {parent} is not a current HeldModel transition")
                self._validated_states[child] = state
        except (OSError, KeyError, IndexError, ValueError, struct.error) as exc:
            if isinstance(exc, EvidenceError):
                raise
            raise EvidenceError(f"Cannot replay search evidence witness {target}: {exc}") from exc
        return self._validated_states[target]

    def facts(self, title):
        """All witnessed relations and inherited owners for a layer anywhere in a stack.

        Return ``below`` and ``above`` maps from layer name to witness id, and
        ``inherited`` from input tuple to ``{Value: witness id}``. A disabled
        source below the target is distinguished from an unbound input.
        """
        if title not in self.model.index:
            raise ValueError(f"unknown layer: {title}")
        if title in self._facts:
            return self._facts[title]
        lid = self.model.index[title]
        excluded = self.model.binds.get(lid, set()) | self.model.blocks.get(lid, set())
        inherited = {j: {} for jid, j in enumerate(self.model.inputs) if jid not in excluded}
        result = {"below": {}, "above": {}, "inherited": inherited}
        if self.db is not None:
            input_ids = set(range(len(self.model.inputs))) - excluded
            empty = Value()
            witnesses = {}

            def retain(mapping, key, gid, stack):
                if key not in mapping:
                    mapping[key] = gid
                    previous = witnesses.setdefault(gid, stack)
                    if previous != stack:
                        raise EvidenceError(f"Search evidence witness {gid} is assigned to different stacks")

            for row in self._rows():
                stack = row["stack"]
                try:
                    pos = stack.index(title)
                except ValueError:
                    continue
                gid = row["witness"]
                for other in stack[:pos]:
                    retain(result["below"], other, gid, stack)
                for other in stack[pos + 1:]:
                    retain(result["above"], other, gid, stack)
                remaining = input_ids.copy()
                for other in reversed(stack[:pos]):
                    owner = self.model.index[other]
                    bound = self.model.binds.get(owner, set()) | self.model.blocks.get(owner, set())
                    resolved = remaining & bound
                    for jid in resolved:
                        retain(inherited[self.model.inputs[jid]], self._values[owner, jid], gid, stack)
                    remaining -= resolved
                    if not remaining:
                        break
                for jid in remaining:
                    retain(inherited[self.model.inputs[jid]], empty, gid, stack)
            for gid, stack in witnesses.items():
                state = self._replay(gid)
                if self.model.names_of(state[0]) != stack:
                    raise EvidenceError(f"Search evidence witness {gid} ends at a different stack than stacks.tsv")
        self._facts[title] = result
        return result

    def witness(self, gid):
        """Return an event trace replayed against HeldModel, without hardware claims."""
        self._replay(gid)
        try:
            return self.db.witness(gid)
        except (OSError, KeyError, IndexError, ValueError, struct.error) as exc:
            raise EvidenceError(f"Cannot read search evidence witness {gid}: {exc}") from exc
