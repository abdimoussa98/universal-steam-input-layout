"""Replay stick touches against a held menu button on the working layouts, in the simulator.

Read-only. Run from the repository root:

    python3 findings/2026-10-06-menu-entry-point-stick-touches/sequences.py

Each line is one gesture: what is on the stack afterwards, what was typed, and the beeps. It runs
every sequence four ways: with an exposed bind firing or not (A9), and with two activators that
are due at the same moment taken in either order (A32).
"""
import itertools
import sys

sys.path.insert(0, '.')
from tests.scenario import Pad                                                         # noqa: E402

MENUS = (('Select', 'Menu Left'), ('Start', 'Menu Right'))


def state(pad):
    return f"stack {list(pad.names()[1:])} typed {pad.typed()} beeps {[d for _, d in pad.seen('beep')]}"


def sequences(menu, side, stick):
    """(label, steps): each step is (what, a function of the pad)."""
    return [
        ('thumb resting, then a 400 ms hold', [
            ('rest 300 ms', lambda p: p.touch(stick).wait(300)),
            ('hold 100 ms', lambda p: p.hold(menu).wait(100)),
            ('hold 400 ms', lambda p: p.wait(300)),
            ('let go', lambda p: p.let_go(menu).wait(400))]),
        ('thumb resting, a tap', [
            ('rest 300 ms', lambda p: p.touch(stick).wait(300)),
            ('tap', lambda p: p.tap(menu, 60).wait(400))]),
        ('thumb resting, hold, lift the thumb at 100 ms', [
            ('rest 300 ms', lambda p: p.touch(stick).wait(300)),
            ('hold 100 ms', lambda p: p.hold(menu).wait(100)),
            ('lift', lambda p: p.lift(stick).wait(50)),
            ('let go', lambda p: p.let_go(menu).wait(400))]),
        ('hold, then touch at 100 ms and keep it', [
            ('hold 100 ms', lambda p: p.hold(menu).wait(100)),
            ('touch', lambda p: p.touch(stick).wait(50)),
            ('to 400 ms', lambda p: p.wait(250)),
            ('let go, thumb stays', lambda p: p.let_go(menu).wait(400)),
            ('lift', lambda p: p.lift(stick).wait(400))]),
        ('hold, touch and lift inside 80 ms', [
            ('hold 50 ms', lambda p: p.hold(menu).wait(50)),
            ('touch 30 ms', lambda p: p.touch(stick).wait(30)),
            ('lift', lambda p: p.lift(stick).wait(20)),
            ('let go at 150 ms', lambda p: p.wait(50).let_go(menu).wait(400))]),
        ('a missed menu release, then a fresh touch', [
            ('hold 300 ms', lambda p: p.hold(menu).wait(300)),
            ('release missed', lambda p: p.miss(menu).wait(200)),
            ('touch', lambda p: p.touch(stick).wait(200)),
            ('lift', lambda p: p.lift(stick).wait(400))]),
    ]


def main():
    for variant in ('default', 'alternative'):
        for (menu, side), stick in itertools.product(MENUS, ('LS', 'RS')):
            for number in range(6):
                results = {}
                for exposed, reverse in itertools.product((True, False), (False, True)):
                    pad = Pad(variant, exposed_fires=exposed, reverse_ties=reverse)
                    label, steps = sequences(menu, side, stick)[number]
                    lines = []
                    for what, step in steps:
                        pad.mark()
                        step(pad)
                        lines.append(f'      {what:<22} {state(pad)}')
                    results.setdefault('\n'.join(lines), []).append((exposed, reverse))
                print(f'{variant} | {menu} | {stick} | {label}')
                for text, ways in results.items():
                    if len(results) > 1:
                        print(f'   A9 exposed fires / A32 reversed: {ways}')
                    print(text)


if __name__ == '__main__':
    main()
