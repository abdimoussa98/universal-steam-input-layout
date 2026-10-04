"""The compiled walk engines: the walks of walk.py and chains.py in C++, on every core.

    native.available()                    # a program's path, built on first use; None without a compiler
    native.run(walk, exits, max_layers=8) # the capped walk, with the hidden-exit test on every stack
    native.run(walk, exits, extras=3)     # the chain walk with 3 extra presses per chain
    native.run(walk, exits, extras=8, program=native.CHAIN)   # the same, for large press counts

Two programs, built with clang++ into engine/build/, which git ignores:

    walk_engine    both walks. It keeps the stack every stack came from, so each finding has a
                   shortest path. 84 bytes a state: 6 extra presses take 4.6 GB.
    chain_engine   the chain walk only, for large press counts. A state is (stack, the chain's
                   layer) at its lowest cost, 18 bytes, and the table is filled one part at a
                   time so the part fits in the cache. No paths. 8 extra presses take 11 GB.

Both read the layout's tables from stdin, keep every stack in memory and print their
result; nothing is stored on disk. The Python walks stay the reference, and
tests/test_native.py checks that all of them give the same stacks and the same findings.

`walk` is a `walk.Walk` (only its tables are used). `exits` is
{layer number: [(exit number, control number, source, on the keeper, the layer's mode there)]}.
The result is the engine's JSON as a dict: settled, stopped, nodes, stacks, presses, longest,
landings, seconds, levels, and pairs with who, lower, exits, stack and path
([binding number, kind]; kind 0 step, 1 settle, 2 arrival, 3 landing).

Record: findings/2026-10-03-simultaneous-cap/README.md.
"""
import json
from pathlib import Path
import shutil
import subprocess
import threading

FOLDER = Path(__file__).with_name("engine")
WALK, CHAIN = "walk_engine", "chain_engine"          # the two programs; see their sources' first lines
KINDS = ("", "settle: ", "arrival: ", "landing: ")
_checked = {}


def available(program=WALK):
    """A program's path, building it when it is missing or older than its source. None if it can't be built."""
    if program not in _checked:
        source, binary = FOLDER / f"{program}.cpp", FOLDER / "build" / program
        fresh = binary.exists() and binary.stat().st_mtime >= source.stat().st_mtime
        compiler = shutil.which("clang++") or shutil.which("c++") or shutil.which("g++")
        if not fresh and compiler:
            binary.parent.mkdir(exist_ok=True)
            done = subprocess.run([compiler, "-O3", "-std=c++17", "-pthread", "-o", str(binary), str(source)],
                                  capture_output=True, text=True)
            fresh = done.returncode == 0
        _checked[program] = binary if fresh else None
    return _checked[program]


def tables(walk, exits, max_layers, mode, extras, landings, threads, memory_mb):
    """The engine's input: whole numbers, in the order walk_engine.cpp reads them."""
    sources, modes = {}, {}
    out = []
    for rows in walk.groups:
        out.append(len(rows))
        for source, group_mode, bound in rows:
            out += [sources.setdefault(source, len(sources)),
                    -1 if group_mode is None else modes.setdefault(group_mode, len(modes)), len(bound), *bound]
    bindings = []
    for rows in walk.moves:
        out.append(len(rows))
        for control, ops, binding in rows:
            out += [len(bindings), control, int(any(add for add, _ in ops)), len(ops)]
            for add, target in ops:
                out += [int(add), target]
            bindings.append(binding)
    out.append(len(walk.removes))
    for (layer, control), removed in walk.removes.items():
        out += [layer, control, len(removed), *sorted(removed)]
    for layer in range(len(walk.titles)):
        rows = exits.get(layer, ())
        out.append(len(rows))
        for number, control, source, on_keeper, mine in rows:
            out += [number, control, sources.setdefault(source, len(sources)), int(on_keeper),
                    -1 if mine is None else modes.setdefault(mine, len(modes))]
    head = [len(walk.titles), walk.base, len(walk.controls), len(sources), max_layers or 0, mode, extras,
            int(landings), threads or 0, memory_mb or 0]
    return " ".join(map(str, head + out)) + "\n", bindings


def run(walk, exits, max_layers=None, extras=None, landings=False, threads=None, memory=None, progress=None,
        program=WALK):
    """Run an engine. `extras` (not None) selects the chain walk; else the capped walk at `max_layers`.

    `program`: WALK keeps a path to every stack. CHAIN only walks chains, in a quarter of the memory, and
    gives no paths: its pairs carry `cost`, the extra presses their example needs.
    """
    binary = available(program)
    if not binary:
        raise RuntimeError("the walk engine isn't built: no C++ compiler was found")
    mode = 0 if extras is None else 1
    text, bindings = tables(walk, exits, max_layers, mode, extras or 0, landings, threads,
                            max(1, memory // (1024 * 1024)) if memory else 0)
    with subprocess.Popen([str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True) as process:
        def follow():
            for line in process.stderr:
                words = line.replace(",", "").split()
                if progress and line.startswith("walk:") and len(words) >= 5:
                    progress(int(words[1]), None, None, int(words[3]))

        reader = threading.Thread(target=follow, daemon=True)
        reader.start()
        process.stdin.write(text)
        process.stdin.close()
        output = process.stdout.read()
        code = process.wait()
        reader.join()
    if code:
        raise RuntimeError(f"the walk engine stopped with exit code {code}")
    result = json.loads(output)
    result["bindings"] = bindings
    return result


def describe(result, path):
    """A path of the engine as text, like `Why.describe()`."""
    return [KINDS[kind] + result["bindings"][number].describe() for number, kind in path]
