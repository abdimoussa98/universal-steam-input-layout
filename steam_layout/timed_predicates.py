"""Higher-order predicates for checked timed-envelope induction.

These objects are hypotheses until initialization and preservation have been
checked.  Sampling can suggest members; it never certifies the predicate.
"""
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, order=True)
class RequiresBelowAny:
    """Whenever x is present, at least one member is present below x."""

    x: int
    members: tuple
    kind: ClassVar[str] = "requires_below_any"

    def __post_init__(self):
        if type(self.x) is not int or self.x < 0:
            raise ValueError("predicate target must be a nonnegative integer layer ID")
        if not isinstance(self.members, (tuple, list)):
            raise ValueError("predicate members must be a list or tuple of layer IDs")
        if not self.members or any(type(layer) is not int or layer < 0 or layer == self.x
                                   for layer in self.members):
            raise ValueError("predicate members must be nonempty, nonnegative and distinct from its target")
        object.__setattr__(self, "members", tuple(sorted(set(self.members))))

    def formula(self, ranks, held=()):
        import z3
        return z3.Or(ranks[self.x] == 0,
                     *(z3.And(ranks[layer] > 0, ranks[layer] < ranks[self.x]) for layer in self.members))

    def holds(self, ranks, held=()):
        return not ranks[self.x] or any(0 < ranks[layer] < ranks[self.x] for layer in self.members)

    def dependencies(self):
        return {self.x, *self.members}, set()

    def describe(self, model):
        names = ", ".join(model.layer_names[layer] for layer in self.members)
        return f"{model.layer_names[self.x]} requires at least one of [{names}] below it"

    def to_data(self):
        return {"kind": self.kind, "x": self.x, "members": list(self.members)}

    @classmethod
    def from_data(cls, value):
        if not isinstance(value, dict) or set(value) != {"kind", "x", "members"}:
            raise ValueError("invalid requires_below_any predicate fields")
        if value["kind"] != cls.kind:
            raise ValueError("unsupported timed predicate kind")
        return cls(value["x"], value["members"])


@dataclass(frozen=True, order=True)
class RequiresBetweenAny:
    """Whenever y is below x, at least one member lies strictly between."""

    x: int
    y: int
    members: tuple
    kind: ClassVar[str] = "requires_between_any"

    def __post_init__(self):
        if (type(self.x) is not int or type(self.y) is not int or
                self.x < 0 or self.y < 0 or self.x == self.y):
            raise ValueError("between predicate endpoints must be distinct nonnegative integer layer IDs")
        if not isinstance(self.members, (tuple, list)):
            raise ValueError("between predicate members must be a list or tuple of layer IDs")
        if not self.members or any(type(layer) is not int or layer < 0 or layer in (self.x, self.y)
                                   for layer in self.members):
            raise ValueError("between predicate members must be nonempty, nonnegative and distinct from endpoints")
        object.__setattr__(self, "members", tuple(sorted(set(self.members))))

    def formula(self, ranks, held=()):
        import z3
        return z3.Or(ranks[self.x] == 0, ranks[self.y] == 0, ranks[self.y] >= ranks[self.x],
                     *(z3.And(ranks[layer] > ranks[self.y], ranks[layer] < ranks[self.x])
                       for layer in self.members))

    def holds(self, ranks, held=()):
        return (not ranks[self.x] or not ranks[self.y] or ranks[self.y] >= ranks[self.x] or
                any(ranks[self.y] < ranks[layer] < ranks[self.x] for layer in self.members))

    def dependencies(self):
        return {self.x, self.y, *self.members}, set()

    def describe(self, model):
        names = ", ".join(model.layer_names[layer] for layer in self.members)
        return (f"{model.layer_names[self.y]} below {model.layer_names[self.x]} "
                f"requires at least one of [{names}] between them")

    def to_data(self):
        return {"kind": self.kind, "x": self.x, "y": self.y, "members": list(self.members)}

    @classmethod
    def from_data(cls, value):
        if not isinstance(value, dict) or set(value) != {"kind", "x", "y", "members"}:
            raise ValueError("invalid requires_between_any predicate fields")
        if value["kind"] != cls.kind:
            raise ValueError("unsupported timed predicate kind")
        return cls(value["x"], value["y"], value["members"])


@dataclass(frozen=True, order=True)
class FactExclusion:
    """Negate one catalogue fact; induction must establish its exclusion."""

    fact: object
    kind: ClassVar[str] = "fact_exclusion"

    def __post_init__(self):
        from .timed_facts import Fact
        if not isinstance(self.fact, Fact):
            raise ValueError("fact exclusion requires a catalogue Fact")
        if self.fact.kind == "inherit" and self.fact.definers is None:
            raise ValueError("inheritance exclusion requires catalogue definer context")

    @property
    def x(self):
        return self.fact.x

    def formula(self, ranks, held=()):
        import z3
        return z3.Not(self.fact.formula(ranks))

    def holds(self, ranks, held=()):
        stack = tuple(sorted((layer for layer, rank in enumerate(ranks) if rank > 0), key=ranks.__getitem__))
        return not self.fact.holds(stack)

    def dependencies(self):
        layers = {self.fact.x}
        if self.fact.y >= 0:
            layers.add(self.fact.y)
        if self.fact.kind == "inherit":
            layers.update(self.fact.definers)
        return layers, set()

    def describe(self, model):
        x = model.layer_names[self.fact.x]
        if self.fact.kind == "below":
            return f"{model.layer_names[self.fact.y]} is never below {x}"
        if self.fact.y == -1:
            return f"{x} never has raw input {self.fact.j} unbound below it"
        return f"{x} never inherits raw input {self.fact.j} from {model.layer_names[self.fact.y]}"

    def to_data(self):
        return {"kind": self.kind, "fact": {"kind": self.fact.kind, "x": self.fact.x,
                                           "y": self.fact.y, "j": self.fact.j}}

    @classmethod
    def from_data(cls, value, catalogue):
        from .timed_facts import FactCatalogue
        if not isinstance(catalogue, FactCatalogue):
            raise ValueError("fact exclusions must be resolved through a FactCatalogue")
        if not isinstance(value, dict) or set(value) != {"kind", "fact"} or value["kind"] != cls.kind:
            raise ValueError("invalid fact_exclusion predicate fields")
        fact = value["fact"]
        if not isinstance(fact, dict) or set(fact) != {"kind", "x", "y", "j"}:
            raise ValueError("invalid excluded fact fields")
        if fact["kind"] not in ("below", "inherit") or any(type(fact[key]) is not int for key in ("x", "y", "j")):
            raise ValueError("invalid excluded fact identity")
        key = (fact["kind"], fact["x"], fact["y"], fact["j"])
        try:
            canonical = catalogue._lookup[key]
        except KeyError:
            raise ValueError("excluded fact does not belong to the supplied catalogue") from None
        return cls(canonical)
