"""The author's suspicion of 2026-10-11, carried over to the pad clicks: after a remove_layer call, an activator
with Invert Activation fires once although its input is held. Each final click layer ends on an inverted
Soft Press on the click, so that one firing takes the layer off under a held click.

Two readings: `real` counts only a call that takes a layer off, `any` counts every call. The model is
switched on once the click has landed. It has to be: a click lands by a removal (the Click Entry Point
removes itself), and clicks do land on the Deck, so the suspicion can't hold for every removal. A9 is
"silent" here: Base's click doesn't fire again under the held click, so a dropped click stays dropped.

    PYTHONPATH=.:tests python3 findings/2026-10-11-pad-click-audit/suspicion.py [default|alternative]
"""
from collections import defaultdict
from pathlib import Path
import sys

sys.path.insert(0, '.')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import steam_layout.simulator as simulator  # noqa: E402
import probe  # noqa: E402

plain = simulator.Simulator._run
state = {'mode': None, 'busy': False}


def run(self, entry, act=None, tap=False, commands=True):
    before = self.stack
    plain(self, entry, act, tap, commands)
    if not state['mode'] or state['busy'] or not commands:
        return
    called = any(op == 'remove_layer' for op, _ in entry.ops)
    took_off = any(title not in self.stack for title in before)
    if (state['mode'] == 'real' and took_off) or (state['mode'] == 'any' and called):
        state['busy'] = True
        for control in sorted(self.held):
            if control[1] == 'click' and 'trackpad' in control[0]:
                for e in self.binding(control)[1]:
                    if e.kind == 'Soft_Press' and e.inverted and e.ops:
                        plain(self, e)
        state['busy'] = False


simulator.Simulator._run = run


def cases(click):
    for name, action in probe.actions(click[0]).items():
        yield name, action, 'click first'
        if name.startswith('stick: touch'):
            stick = name.split()[2]
            yield f'stick: lift {stick}, thumbs rested before the click', (lambda p, s=stick: p.lift(s).wait(60)), 'thumbs first'


if __name__ == '__main__':
    for mode, label in (('real', 'only a call that takes a layer off'), ('any', 'every call, also one that finds nothing')):
        table = defaultdict(lambda: defaultdict(set))
        for start in probe.STARTS:
            for click in probe.CLICKS:
                for name, action, order in cases(click):
                    def switched(p, action=action):
                        state['mode'] = mode
                        return action(p)
                    result = probe.run(start, click, name, switched, order, False)
                    state['mode'] = None
                    table[name]['drops' if 'taken off' in result else 'holds'].add(f'{start}/{click[0]} {click[1]}')
        print(f'\nsuspicion, {label}: of 16 cases (4 starting layers, 4 clicks)')
        for name, found in table.items():
            drops = found['drops']
            where = '' if len(drops) in (0, 16) else (f'   in {", ".join(sorted({c.split("/")[0] for c in drops}))}; '
                                                        f'{", ".join(sorted({c.split("/")[1] for c in drops}))}')
            print(f'  {name:48} drops {len(drops):2d}{where}')
