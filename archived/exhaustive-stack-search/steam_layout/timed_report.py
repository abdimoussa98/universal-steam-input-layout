"""Layer relationships and inherited raw bindings from a timed search.

Witnesses are replayed through the caller's verifier before being reported.
Only an exhausted timed search excludes an unobserved fact; untimed search
results and HeldModel invariants are deliberately not used here.
"""

from .stackdb import Value, describe


MODEL_SCOPE = (
    "Results describe the versioned TimedModel and its recorded search assumptions; "
    "they do not establish Steam hardware behavior. Inheritance means raw bindings "
    "below the requested layer, irrespective of layers above it or active mode shifts."
)


def _definitions(model, target):
    """Each inherited raw input's statically available owners or source blockers."""
    names = model.spec.layer_names
    groups = {index: model.layout.active(name) for index, name in enumerate(names)}
    result = {}
    for control in model.spec.controls:
        source, name = control
        own = groups[target].get(source, {})
        if (own.get("mode") == "disabled" or
                own.get("inputs", {}).get(name, {}).get("activators")):
            continue
        definitions = {}
        for owner, sources in groups.items():
            group = sources.get(source, {})
            if group.get("mode") == "disabled":
                definitions[owner] = Value(blocked_by=names[owner])
            else:
                activators = group.get("inputs", {}).get(name, {}).get("activators")
                if activators:
                    definitions[owner] = Value(owner=names[owner], activators=activators)
        result[control] = definitions
    return result


def timed_layer_report(model, store, title, *, verify_witness, verify_complete=None):
    """Report every layer order and lower binding seen with ``title`` present.

    ``store`` must belong to ``model`` and expose ``iter_states()`` yielding
    ``(id, TimedState)`` pairs plus a ``complete`` flag. The required verifier
    accepts a state ID, replays its stored trace through this model and raises
    or returns False on failure. Every retained unique witness is verified.

    An incomplete search leaves all unobserved static alternatives possible.
    Once the frontier is exhausted, ``verify_complete()`` must independently
    verify graph closure and return a certificate with ``verified=True`` before
    those alternatives are excluded. This includes all alternatives if the
    requested layer was never reached.
    """
    if title not in model.spec.index:
        raise ValueError(f"Unknown layer: {title}")
    if store.model is not model:
        raise ValueError("Timed store and report must share the same TimedModel instance")
    if not callable(verify_witness):
        raise ValueError("A timed witness replay verifier is required")
    complete = bool(store.complete)
    certificate = None
    if complete:
        if not callable(verify_complete):
            raise ValueError("A completed timed search requires an independent closure verifier")
        certificate = verify_complete()
        if not isinstance(certificate, dict) or certificate.get("verified") is not True:
            raise ValueError("Timed search closure verification failed")
    target = model.spec.index[title]
    names = model.spec.layer_names
    definitions = _definitions(model, target)
    observed = {"below": {}, "above": {}, "inherited": {}}
    seen_stacks = set()
    states_scanned = target_states = 0
    for state_id, state in store.iter_states():
        states_scanned += 1
        stack = state.stack
        if target not in stack:
            continue
        target_states += 1
        if stack in seen_stacks:
            continue
        seen_stacks.add(stack)
        position = stack.index(target)
        lower = stack[:position]
        for direction, layers in (("below", lower), ("above", stack[position + 1:])):
            for owner in layers:
                observed[direction].setdefault(names[owner], state_id)
        for control, definers in definitions.items():
            value = next((definers[owner] for owner in reversed(lower) if owner in definers), Value())
            observed["inherited"].setdefault(control, {}).setdefault(value, state_id)

    # Check witnesses before returning any reachability claim. Many facts share
    # one witness; one replay per state is enough even when it supports all three
    # projections or several different inherited bindings.
    witnesses = set(observed["below"].values()) | set(observed["above"].values())
    for values in observed["inherited"].values():
        witnesses.update(values.values())
    for witness in sorted(witnesses):
        if verify_witness(witness) is False:
            raise ValueError(f"Timed witness replay failed for state {witness}")

    report = {
        "layer": title,
        "model_family": "TimedModel",
        "scope": MODEL_SCOPE,
        "semantics": model.semantics,
        "identity": store.identity,
        "search_complete": complete,
        "complete_for_model": complete,
        "closure_certificate": certificate,
        "below": [],
        "above": [],
        "inherited": [],
        "excluded": {"below": [], "above": [], "inherited": []},
        "search": {"states_scanned": states_scanned, "states_with_layer": target_states,
                   "distinct_stacks_with_layer": len(seen_stacks),
                   "verified_witnesses": len(witnesses)},
    }

    def classification(witness):
        if witness is not None:
            return {"status": "proven", "witness": witness}
        if not complete:
            return {"status": "possible", "witness": None}
        return None

    for direction in ("below", "above"):
        for owner, name in enumerate(names):
            if owner == target:
                continue
            info = classification(observed[direction].get(name))
            if info is None:
                report["excluded"][direction].append(name)
            else:
                report[direction].append({"layer": name, **info})

    for (source, name), definers in definitions.items():
        values = []
        seen = observed["inherited"].get((source, name), {})
        for value in (*definers.values(), Value()):
            row = {"owner": value.owner, "blocked_by": value.blocked_by,
                   "activators": value.activators, "summary": describe(value.activators)}
            info = classification(seen.get(value))
            if info is None:
                report["excluded"]["inherited"].append({"source": source, "input": name, **row})
            else:
                values.append({**row, **info})
        report["inherited"].append({"source": source, "input": name, "values": values})
    rows = report["below"] + report["above"] + [value for row in report["inherited"]
                                              for value in row["values"]]
    report["counts"] = {
        "proven": sum(row["status"] == "proven" for row in rows),
        "possible": sum(row["status"] == "possible" for row in rows),
        "excluded": sum(len(rows) for rows in report["excluded"].values()),
    }
    return report


def format_timed_report(report):
    """Compact text presentation shared by the timed search/report CLI."""
    lines = [report["layer"], report["scope"],
             "proven = replayed timed witness; possible = unobserved static alternative.",
             f"Complete for model: {str(report['complete_for_model']).lower()}"]
    for direction in ("below", "above"):
        lines.append(f"\n{direction.capitalize()}:")
        lines.extend(f"  [{row['status']}] {row['layer']}" for row in report[direction])
    lines.append("\nInherited raw inputs:")
    for row in report["inherited"]:
        lines.append(f"  {row['source']}/{row['input']}")
        for value in row["values"]:
            owner = value["owner"] or (f"blocked by {value['blocked_by']}" if value["blocked_by"] else "unbound")
            summary = f": {value['summary']}" if value["summary"] else ""
            lines.append(f"    [{value['status']}] {owner}{summary}")
    counts = report["counts"]
    lines.append(f"\n{counts['proven']} witnessed; {counts['possible']} unresolved; "
                 f"{counts['excluded']} excluded by exhausted timed search.")
    return "\n".join(lines)
