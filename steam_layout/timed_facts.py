"""Finite layer-query facts and independently replayable timed witnesses.

Facts are projections of complete ordered stacks, not states in a pair-based
reachability search. Every below/above relation and every raw inherited binding
has a finite catalogue alternative, including disabled sources and no binding.
The optional solver is imported only when a fact's formula is requested.
"""
from dataclasses import dataclass, field
from copy import deepcopy
from types import MappingProxyType

from .stackdb import Value
from .timed_search import TimedQuotient, compact_trace
from .timed_store import encode_state
from .timed_trace import parse_trace


@dataclass(frozen=True, order=True)
class Fact:
    """A full-stack predicate; ``y`` is below ``x`` or owns inherited input j.

    An inheritance fact uses ``y=-1`` for no lower binding. ``definers`` lists
    every layer defining or disabling that raw input. It is catalogue context,
    not part of the fact's identity within one layout/model.
    """
    kind: str
    x: int
    y: int
    j: int = -1
    definers: object = field(default=None, compare=False, repr=False)

    def __post_init__(self):
        if self.kind not in ("below", "inherit"):
            raise ValueError(f"unknown fact kind: {self.kind!r}")

    def formula(self, ranks):
        """Z3 predicate over all stack ranks; zero means an absent layer."""
        import z3
        present = ranks[self.x] > 0
        if self.kind == "below":
            return z3.And(present, ranks[self.y] > 0, ranks[self.y] < ranks[self.x])
        if self.definers is None:
            raise ValueError("inheritance predicates require catalogue definer context")
        if self.y == -1:
            return z3.And(present, *(z3.Or(ranks[d] == 0, ranks[d] >= ranks[self.x])
                                     for d in self.definers))
        return z3.And(present, ranks[self.y] > 0, ranks[self.y] < ranks[self.x],
                      *(z3.Or(ranks[d] == 0, ranks[d] <= ranks[self.y],
                              ranks[d] >= ranks[self.x]) for d in self.definers
                        if d != self.y))

    def holds(self, stack):
        if self.x not in stack:
            return False
        lower = stack[:stack.index(self.x)]
        if self.kind == "below":
            return self.y in lower
        if self.definers is None:
            raise ValueError("inheritance predicates require catalogue definer context")
        owner = next((d for d in reversed(lower) if d in self.definers), -1)
        return self.y == owner


class FactCatalogue:
    """All alternatives for the three questions for one TimedModel.

    ``controls`` retains raw aliases, as in the original layout's bindings.
    For each layer, inputs it defines or disables are omitted from inheritance.
    An above relation for X is the same fact as X below the requested upper
    layer; no duplicate ``above`` predicates are necessary.
    """

    def __init__(self, model):
        self.model = model
        self.names = tuple(model.spec.layer_names)
        self.controls = tuple(model.spec.controls)
        self.inputs = self.controls
        self.definitions = {j: {} for j in range(len(self.controls))}
        self.defined_by_layer = {x: [] for x in range(len(self.names))}
        for owner, title in enumerate(self.names):
            groups = model.layout.active(title)
            for j, (source, name) in enumerate(self.controls):
                group = groups.get(source, {})
                if group.get("mode") == "disabled":
                    value = Value(blocked_by=title)
                else:
                    activators = group.get("inputs", {}).get(name, {}).get("activators")
                    if not activators:
                        continue
                    value = Value(owner=title, activators=activators)
                self.definitions[j][owner] = value
                self.defined_by_layer[owner].append(j)
        self.inherited_by_layer = {
            x: tuple(j for j, definitions in self.definitions.items() if x not in definitions)
            for x in range(len(self.names))}

        facts = [Fact("below", x, y) for x in range(len(self.names))
                 for y in range(len(self.names)) if x != y]
        for x, inputs in self.inherited_by_layer.items():
            for j in inputs:
                definers = tuple(self.definitions[j])
                facts.extend(Fact("inherit", x, y, j, definers) for y in (*definers, -1))
        self.facts = tuple(facts)
        self._lookup = {(fact.kind, fact.x, fact.y, fact.j): fact for fact in self.facts}

    def facts_of(self, stack):
        """Compute every true catalogue fact using one prefix-owner scan."""
        if not stack or stack[0] != 0 or len(set(stack)) != len(stack):
            raise ValueError("a stack must start with Base and contain no duplicate layers")
        if any(type(x) is not int or not 0 <= x < len(self.names) for x in stack):
            raise ValueError("stack contains an unknown layer")
        result, lower = set(), []
        owners = [-1] * len(self.controls)
        for x in stack:
            result.update(self._lookup[("below", x, y, -1)] for y in lower)
            result.update(self._lookup[("inherit", x, owners[j], j)]
                          for j in self.inherited_by_layer[x])
            for j in self.defined_by_layer[x]:
                owners[j] = x
            lower.append(x)
        return result

    def valuesmetadata(self, fact):
        """Return the original owner/blocker/activators for an inherited value."""
        if fact.kind != "inherit" or (fact.kind, fact.x, fact.y, fact.j) not in self._lookup:
            raise ValueError("expected an inheritance fact from this catalogue")
        value = Value() if fact.y == -1 else self.definitions[fact.j][fact.y]
        return {"owner": value.owner, "blocked_by": value.blocked_by,
                "activators": deepcopy(value.activators)}


class FactWitnesses:
    """A shared parent forest proving positive facts through public timed APIs.

    Every recorded edge is checked, and ``verify`` separately replays retained
    parent paths before a proof report uses them. Relative-time normalization
    is TimedQuotient's exact quotient. Distinct command-order branches remain
    separate nodes unless their complete normalized states are identical.
    """

    def __init__(self, model, catalogue):
        if catalogue.model is not model:
            raise ValueError("catalogue and witnesses must share the same TimedModel")
        self.model, self.catalogue = model, catalogue
        self.quotient = TimedQuotient(model)
        self.identity = self.quotient.identity
        self._states, self._parents, self._events, self._ids = {}, {}, {}, {}
        self.node_states = MappingProxyType(self._states)
        self.witness_nodes = {}
        self.facts = set()
        self._fact_stacks = set()
        self._verified = set()
        self._last_edge = None
        self._last_following = frozenset()
        roots = sorted(self.quotient.initial(), key=encode_state)
        self.roots = tuple(self._retain(None, state, None) for state in roots)

    def _retain(self, parent, state, event):
        if state in self._ids:
            return self._ids[state]
        node = len(self._states)
        self._states[node] = state
        self._parents[node] = parent
        self._events[node] = deepcopy(event)
        self._ids[state] = node
        if state.stack not in self._fact_stacks:
            self._fact_stacks.add(state.stack)
            for fact in self.catalogue.facts_of(state.stack) - self.facts:
                self.witness_nodes[fact] = node
                self.facts.add(fact)
        return node

    def record(self, parent_id, state, event):
        """Retain a successor only after validating this complete timed edge."""
        if parent_id not in self._states:
            raise ValueError("unknown witness parent")
        event = parse_trace([event])[0]
        state = self.quotient.normalize(state)
        edge = (parent_id, event)
        if edge != self._last_edge:
            self._last_following = self.quotient.step(self._states[parent_id], event)
            self._last_edge = deepcopy(edge)
        if state not in self._last_following:
            raise ValueError("witness edge does not replay to the supplied state")
        return self._retain(parent_id, state, event)

    def add_trace(self, events):
        """Replay all branches from every root; return the final node IDs."""
        current = set(self.roots)
        for event in parse_trace(events):
            following = set()
            for parent in sorted(current):
                outcomes = self.quotient.step(self._states[parent], event)
                # These results already came from the same public runtime
                # methods used by record, so do not compute the batch twice.
                self._last_edge, self._last_following = deepcopy((parent, event)), outcomes
                for state in sorted(outcomes, key=encode_state):
                    following.add(self.record(parent, state, event))
            current = following
        return frozenset(current)

    def _path(self, node):
        path = []
        while node is not None:
            path.append(node)
            node = self._parents[node]
        return tuple(reversed(path))

    def trace(self, fact):
        """Return a compact JSON-safe event trace reaching this positive fact."""
        if fact not in self.witness_nodes:
            raise ValueError("fact has no timed witness")
        events = [self._events[node] for node in self._path(self.witness_nodes[fact])
                  if self._events[node] is not None]
        return deepcopy(compact_trace(events))

    def verify(self, fact):
        """Independently replay a retained witness and check its final fact."""
        if fact not in self.witness_nodes:
            raise ValueError("fact has no timed witness")
        node = self.witness_nodes[fact]
        for current in self._path(node):
            if current in self._verified:
                continue
            parent = self._parents[current]
            if parent is None:
                valid = self._states[current] in self.quotient.initial()
            else:
                valid = self._states[current] in self.quotient.step(
                    self._states[parent], self._events[current])
            if not valid:
                raise ValueError(f"timed witness replay failed at node {current}")
            self._verified.add(current)
        canonical = self.catalogue._lookup[(fact.kind, fact.x, fact.y, fact.j)]
        if not canonical.holds(self._states[node].stack):
            raise ValueError("timed witness does not establish the claimed fact")
        return True
