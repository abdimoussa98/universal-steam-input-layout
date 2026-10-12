"""When is a menu stick guard or `Menu Buttons: Tap Cover` under a Steering Modifier 2 quick tap?

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/menu_layers.py

The walks of walks.py on both working layouts, 12,000 per layout, once with no button release missed and
once with one in ten missed (let go with the Steam menu open, A25). Counts the quick taps, and how many
fired with one of the three `Menu Buttons` layers on the stack.
"""
import random
from multiprocessing import Pool

from steam_layout.model import Layout
from steam_layout.simulator import Simulator
from scenario import Pad, layout_data
import walks as probe

MENU = (("switch", "button_escape"), ("switch", "button_menu"))


class Watcher(Simulator):
    def __init__(self, layout, taps, **options):
        self.taps = taps
        super().__init__(layout, **options)

    def _run(self, entry, act=None, tap=False, commands=True):
        if entry.kind == "release" and commands and entry.layer.startswith("Steering | ") and "Modifier 2" in entry.layer:
            self.taps.append((any(t.startswith("Menu Buttons") for t in self.stack), any(c in self.held for c in MENU)))
        return super()._run(entry, act=act, tap=tap, commands=commands)


def batch(job):
    variant, seed, missed = job
    layout, rng, taps = Layout(layout_data(variant)), random.Random(seed), []
    for _ in range(1500):
        pad = Pad.__new__(Pad)
        pad.variant, pad.options, pad.layout = variant, {}, layout
        pad.sim = Watcher(layout, taps, exposed_fires=rng.random() < 0.5, reverse_ties=rng.random() < 0.5)
        pad._mark, pad._began = 0, tuple(pad.sim.stack)
        try:
            if rng.random() < 0.5:
                pad.hold("L1").wait(20).hold("R1").wait(40).let_go("R1").wait(20).let_go("L1").wait(400)
            if rng.random() < 0.5:
                pad.touch("RS").wait(20)
            pad.hold("Start").click("LS").let_go("Start")
            if rng.random() < 0.7:
                pad.flick("LS", "left").wait(300)
            if rng.random() < 0.5:
                pad.lift("LS").wait(50)
            for _ in range(probe.EVENTS):
                probe.step(pad, rng, missed, probe.WAITS)
        except (RuntimeError, NotImplementedError):
            pass
    return missed, taps


def main():
    jobs = [(variant, seed, missed) for variant in ("default", "alternative") for seed in range(1, 9) for missed in (0.0, 0.10)]
    with Pool() as pool:
        done = pool.map(batch, jobs)
    for missed in (0.0, 0.10):
        taps = [tap for found, rows in done if found == missed for tap in rows]
        print(f"{int(missed * 100)}% of button releases missed: {len(taps)} quick taps; "
              f"{sum(1 for menu, _ in taps if menu)} with a Menu Buttons layer on the stack, "
              f"{sum(1 for menu, held in taps if menu and held)} of them with Start or Select held")


if __name__ == "__main__":
    main()
