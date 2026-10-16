"""Pure selectors over completed observations; these never run audits or chains."""
from dataclasses import dataclass


@dataclass(frozen=True)
class WindowObservation:
    """All independent Window assertions, detached from the large mutable trace report."""

    variant: str
    targets: frozenset
    expected_windows: frozenset
    undecided: tuple
    without_chain_stacks: tuple
    ok: bool


def window_observation(report, expected_windows):
    """Keep every route/coverage obligation in an immutable, inexpensive class fixture."""
    return WindowObservation(
        variant=report["variant"],
        targets=frozenset(report["targets"]),
        expected_windows=frozenset(expected_windows),
        undecided=tuple((title, route["source"], route["input"], route["status"])
                        for title, row in report["targets"].items()
                        for route in row["routes"] if route["status"] == "open"),
        without_chain_stacks=tuple(title for title, row in report["targets"].items()
                                   if not row["chain_stacks"]),
        ok=report["ok"],
    )


def finding_pairs(report, check=None):
    """Return failing (check, layer, removed or hiding layer) triples."""
    return {(finding["check"], finding["layer"], finding["target"])
            for finding in report["findings"] if check in (None, finding["check"])}
