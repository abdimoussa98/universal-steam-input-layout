"""Resolve exported source geometry without inventing Steam defaults.

Valve describes layers as consecutive setting modifications and ring bindings
as active outside a configured radius, or inside when inverted:
https://partner.steamgames.com/doc/features/steam_controller/action_set_layers
https://partner.steamgames.com/doc/features/steam_controller/input_source_modes

Those descriptions do not specify equality, sensor/deadzone transforms, omitted
JSON defaults, or the interaction between Soft Press and the source ring. This
module therefore resolves configuration and proposes sample boundaries; it is
not a physical-controller simulator. Ring evaluation takes a logical position
already expressed in the configured radius's coordinate space.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext

from .model import MODE_SHIFT, actions, entries


MAX_POSITION = Decimal(32767)
RADIUS_KEYS = frozenset(("edge_binding_radius", "deadzone", "deadzone_inner_radius",
                         "deadzone_outer_radius", "activation_threshold"))


class UnresolvedGeometry(ValueError):
    """A runtime choice is not specified by the exported configuration."""


def position(value, field="position"):
    if isinstance(value, bool):
        raise ValueError(f"{field}: expected a finite number between 0 and 32767")
    try:
        number = Decimal(str(value))
    except (ValueError, InvalidOperation):
        raise ValueError(f"{field}: expected a finite number between 0 and 32767") from None
    if not number.is_finite() or not 0 <= number <= MAX_POSITION:
        raise ValueError(f"{field}: expected a finite number between 0 and 32767")
    return number


@dataclass(frozen=True)
class RingRegion:
    radius: Decimal
    inverted: bool

    def __post_init__(self):
        object.__setattr__(self, "radius", position(self.radius, "edge_binding_radius"))
        if type(self.inverted) is not bool:
            raise ValueError("inverted must be a boolean")

    def contains(self, value, *, equality_outside=None):
        """Classify a logical position; equality requires an explicit choice.

        The complement gives inversion. This does not apply deadzones, axis
        scaling, saturation, hysteresis, touch gates, or Soft Press thresholds.
        """
        value = position(value)
        if equality_outside is not None and type(equality_outside) is not bool:
            raise ValueError("equality_outside must be a boolean or None")
        if value == self.radius:
            if equality_outside is None:
                raise UnresolvedGeometry("ring equality boundary requires an explicit policy")
            outside = equality_outside
        else:
            outside = value > self.radius
        return not outside if self.inverted else outside


@dataclass(frozen=True)
class ResolvedSource:
    source: str
    mode: object
    settings: tuple
    owners: tuple
    mode_changes: tuple
    shift_policy: object = None

    def ring(self, *, defaults=None):
        """Read radius and inversion, requiring explicit omitted defaults."""
        settings = dict(defaults or {})
        settings.update(self.settings)
        if self.mode is None or self.mode == "disabled":
            raise UnresolvedGeometry(f"{self.source}: absent or disabled sources have no active ring")
        required = ("edge_binding_radius", "edge_binding_invert")
        missing = [key for key in required if key not in settings]
        if missing:
            raise UnresolvedGeometry(f"{self.source}: missing explicit settings {', '.join(missing)}")
        invert = settings["edge_binding_invert"]
        if isinstance(invert, bool) or str(invert) not in ("0", "1"):
            raise ValueError(f"{self.source}: edge_binding_invert must be 0 or 1")
        return RingRegion(position(settings["edge_binding_radius"], "edge_binding_radius"),
                          str(invert) == "1")


class SourceGeometry:
    """Per-field overlay of exported settings, with origins retained.

    The newest group supplies the mode. A mode change is recorded, rather than
    treated as proof that a previous mode's deadzone coordinates stay valid.
    Mode-specific interpretation belongs to the caller's runtime contract.
    """

    def __init__(self, layout):
        self.layout = layout
        self.titles = tuple(layout.presets)

    def resolve(self, stack, source, *, shift_group=None, inherit_shift_settings=None):
        settings, owners, mode_changes = {}, {}, []
        mode = None

        def overlay(group, owner):
            nonlocal mode
            following_mode = group.get("mode")
            if following_mode != mode:
                mode_changes.append((owner, mode, following_mode))
                mode = following_mode
            for key, value in group.get("settings", {}).items():
                settings[key], owners[key] = value, owner

        for layer in stack:
            if type(layer) is int and not 0 <= layer < len(self.titles):
                raise ValueError(f"invalid layer index: {layer}")
            title = self.titles[layer] if type(layer) is int else layer
            group = self.layout.active(title).get(source)
            if group is not None:
                overlay(group, title)
        policy = None
        if shift_group is not None:
            if type(inherit_shift_settings) is not bool:
                raise UnresolvedGeometry("mode-shift settings require an explicit inheritance policy")
            policy = "inherit-explicit-layer-settings" if inherit_shift_settings else "shift-group-only"
            if not inherit_shift_settings:
                settings.clear()
                owners.clear()
                mode_changes.clear()
                mode = None
            overlay(self.layout.groups[str(shift_group)], f"shift:{source}:{shift_group}")
        return ResolvedSource(source, mode, tuple(sorted(settings.items())),
                              tuple(sorted(owners.items())), tuple(mode_changes), policy)

    def candidate_boundaries(self, source):
        """All explicit radial/activator boundaries, including hidden groups.

        No bound is inferred for an omitted setting. Mode-shift groups are
        associated by both preset declarations and explicit shift commands.
        Bounds outside the replay coordinate range cannot split that range.
        """
        groups = set()
        for preset in self.layout.presets.values():
            for group_id, binding in preset["group_source_bindings"].items():
                if binding.split(" ", 1)[0] == source:
                    groups.add(group_id)
        for group in self.layout.groups.values():
            for input_value in group.get("inputs", {}).values():
                for _, entry in entries(input_value.get("activators", {})):
                    for command in actions(entry):
                        shifted = MODE_SHIFT.search(command)
                        if shifted and shifted.group(1) == source:
                            groups.add(shifted.group(2))
        bounds = {Decimal(0), MAX_POSITION}
        for group_id in groups:
            group = self.layout.groups[group_id]
            candidates = [value for key, value in group.get("settings", {}).items()
                          if key in RADIUS_KEYS]
            for input_value in group.get("inputs", {}).values():
                candidates.extend(entry.get("settings", {})["activation_threshold"]
                                  for _, entry in entries(input_value.get("activators", {}))
                                  if "activation_threshold" in entry.get("settings", {}))
            for raw in candidates:
                try:
                    number = Decimal(str(raw))
                except InvalidOperation:
                    raise ValueError(f"group {group_id}: invalid geometry boundary {raw!r}") from None
                if not number.is_finite() or number < 0:
                    raise ValueError(f"group {group_id}: invalid geometry boundary {raw!r}")
                if number <= MAX_POSITION:
                    bounds.add(number)
        return tuple(sorted(bounds))


def boundary_representatives(boundaries):
    """Keep every boundary singleton and a sample in every open interval.

    This preserves both strict and inclusive predicates. Upper-end-only bins
    cannot simultaneously preserve ``x > a`` and ``x >= b`` at their bounds.
    These are candidate samples, not a completeness claim for hysteresis or
    other unmodeled source processing.
    """
    bounds = sorted({Decimal(0), MAX_POSITION, *(position(value) for value in boundaries)})
    with localcontext() as context:
        context.prec = max(28, max(value.adjusted() for value in bounds) -
                           min(value.as_tuple().exponent for value in bounds) + 3)
        return tuple(sorted({*bounds, *((left + right) / 2
                                       for left, right in zip(bounds, bounds[1:]))}))
