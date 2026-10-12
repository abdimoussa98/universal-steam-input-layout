"""What each other input does to a pad click that is already held (press simulator, 90.56).

For every case it reads the log of the hold: was the final click layer taken off, did the output go up,
and is the bind that carries the bump still the one answering when the pad is let go. Each case runs with
A9 both ways (a bind exposed under a held input fires, or stays silent).

    PYTHONPATH=.:tests python3 findings/2026-10-11-pad-click-audit/probe.py [default|alternative]
"""
import sys, json
from collections import defaultdict
sys.path.insert(0, '.')
from tests.scenario import Pad, SOURCES, DIRECTIONS

VARIANT = sys.argv[1] if len(sys.argv) > 1 else 'default'
data = json.load(open(f'neptune/single-set-{VARIANT}_hold-gyro_latest.json'))

# pad, where, final layer, output that must stay down, the input that carries the bump
CLICKS = (('LP', 'centre', 'LTP: Middle Click', 'CAPSLOCK', 'click'),
          ('LP', 'left', 'LTP: Arrow Keys', 'LEFT_ARROW', 'dpad_west'),
          ('RP', 'centre', 'RTP: Middle Click', 'mouse_button MIDDLE', 'click'),
          ('RP', 'left', 'RTP: Mouse Buttons', 'mouse_button BACK', 'dpad_west'))
STARTS = {'Base': None, 'Gyro': ('Base', 'Gyro'), 'Cursor Gyro': ('Base', 'Cursor Gyro'), 'Steering': ('Base', 'Steering')}


def bump_live(pad, source, part, final):
    return any(k[0] == (source, part) and k[1] == 'down' and a.entry.kind == 'Full_Press' and a.entry.layer == pad.title(final)
               and int(a.entry.settings.get('haptic_intensity') or 0) > 0 for k, a in pad.sim.acts.items())


def other(pad_name):
    return 'RP' if pad_name == 'LP' else 'LP'


def actions(pad_name):
    o = other(pad_name)
    return {
        'nothing for 400 ms': lambda p: p.wait(400),
        'stick: touch LS 400 ms and lift': lambda p: p.touch('LS').wait(400).lift('LS').wait(60),
        'stick: touch RS 400 ms and lift': lambda p: p.touch('RS').wait(400).lift('RS').wait(60),
        'stick: tap LS 60 ms': lambda p: p.touch('LS').wait(60).lift('LS').wait(60),
        'stick: tap RS 60 ms': lambda p: p.touch('RS').wait(60).lift('RS').wait(60),
        'stick: push LS up 300 ms': lambda p: p.push('LS', 'up').wait(300).lift('LS').wait(60),
        'stick: push RS 300 ms': lambda p: p.push('RS').wait(300).lift('RS').wait(60),
        'stick: click LS': lambda p: p.click('LS', 60).lift('LS').wait(60),
        'stick: click RS': lambda p: p.click('RS', 60).lift('RS').wait(60),
        'bumper: L1 tap 40 ms': lambda p: p.tap('L1', 40).wait(20),
        'bumper: R1 tap 40 ms': lambda p: p.tap('R1', 40).wait(20),
        'bumper: L1 hold 400 ms': lambda p: p.hold('L1').wait(400).let_go('L1').wait(20),
        'bumper: R1 hold 400 ms': lambda p: p.hold('R1').wait(400).let_go('R1').wait(20),
        'bumper: L1 then R1, R1 let go first': lambda p: p.hold('L1').wait(100).hold('R1').wait(300).let_go('R1').wait(30).let_go('L1').wait(20),
        'bumper: R1 then L1, L1 let go first': lambda p: p.hold('R1').wait(100).hold('L1').wait(300).let_go('L1').wait(30).let_go('R1').wait(20),
        'bumper: R1 held, LS up 60 ms': lambda p: p.hold('R1').wait(150).flick('LS', 'up', 60).wait(250).lift('LS').let_go('R1').wait(20),
        'bumper: R1 held, LS up 400 ms': lambda p: p.hold('R1').wait(150).push('LS', 'up').wait(400).lift('LS').wait(30).let_go('R1').wait(20),
        'trigger: LF tap': lambda p: p.tap('LF', 60).wait(20),
        'trigger: RF tap': lambda p: p.tap('RF', 60).wait(20),
        'button: A tap': lambda p: p.tap('A', 60).wait(20),
        'button: D-pad Up tap': lambda p: p.tap('Up', 60).wait(20),
        'button: L4 tap': lambda p: p.tap('L4', 60).wait(20),
        'menu: Select tap': lambda p: p.tap('Select', 60).wait(20),
        'menu: Start tap': lambda p: p.tap('Start', 60).wait(20),
        'menu: Select hold 400 ms': lambda p: p.hold('Select').wait(400).let_go('Select').wait(20),
        'menu: Start hold 400 ms': lambda p: p.hold('Start').wait(400).let_go('Start').wait(20),
        'other pad: touch 60 ms': lambda p: p.touch(o).wait(60).lift(o).wait(20),
        'other pad: touch 400 ms': lambda p: p.touch(o).wait(400).lift(o).wait(20),
        'other pad: click centre 200 ms': lambda p: p.click_pad(o, 'centre', 200).wait(20),
        'other pad: click ring 200 ms': lambda p: p.click_pad(o, 'left', 200).wait(20),
        'same pad: slide to the centre': lambda p: p.slide_pad(pad_name, 'centre').wait(200),
        'same pad: slide to the ring (up)': lambda p: p.slide_pad(pad_name, 'up').wait(200),
    }


def run(start, click, name, action, order, exposed):
    pad_name, where, final, output, part = click
    source = SOURCES[pad_name]
    p = Pad(VARIANT, start=STARTS[start], data=data, exposed_fires=exposed)
    began = p.stack
    if order == 'thumbs first':
        p.touch('LS').touch('RS').wait(400)
    p.press_pad(pad_name, where).wait(200)
    ok = p.has(final) and output in p.down()
    mark = len(p.sim.log)
    try:
        action(p)
        p.wait(400)
    except Exception as error:
        return f'ERROR {str(error)[:70]}'
    log = p.sim.log[mark:]
    took_off = [d for _, w, d in log if w == 'remove' and d == p.title(final)]
    back = [d for _, w, d in log if w == 'add' and d == p.title(final)]
    cut = [w for _, w, d in log if w in ('up', 'handover') and d == output]
    covered = sorted({d for _, w, d in log if w == 'add' and d.endswith('Double Tap')})
    at_end = (p.has(final), output in p.down(), bump_live(p, source, part, final))
    p.let_go_pad(pad_name)
    for stick in ('LS', 'RS'):
        p.lift(stick)
    p.wait(700)
    stuck = [t for t in p.stack if t not in began] + p.down()
    if not ok:
        return 'the click never started'
    words = []
    if took_off:
        words.append(f'final layer taken off {len(took_off)}x' + (f', back {len(back)}x' if back else ', never back'))
    if cut and not took_off:
        words.append(f'output cut {len(cut)}x' + (f' under {", ".join(covered)}' if covered else ''))
    if not at_end[0]:
        words.append('at let-go: layer off')
    elif not at_end[1]:
        words.append('at let-go: layer on, output up')
    elif not at_end[2]:
        words.append('at let-go: output down, bump bind not live')
    if stuck:
        words.append(f'left after: {stuck}')
    return '; '.join(words) or 'holds'


def under_a_window():
    """Let go of the pad while a window that a tap opened is still on top."""
    found = defaultdict(set)
    for exposed in (True, False):
        for start in STARTS:
            for pad_name, where, final, output, part in CLICKS:
                for opener in ('L1', 'R1', 'Select', 'Start'):
                    for gap in (10, 60, 120):
                        p = Pad(VARIANT, start=STARTS[start], data=data, exposed_fires=exposed)
                        began = p.stack
                        p.press_pad(pad_name, where).wait(200)
                        p.tap(opener, 40).wait(gap)
                        window = [t for t in p.stack if t.endswith('Double Tap')]
                        live = bump_live(p, SOURCES[pad_name], part, final)
                        p.let_go_pad(pad_name).wait(1000)
                        late = [t for t in p.stack if t not in began] + p.down()
                        found[('a window is on top' if window else 'no window', 'bump bind live' if live else 'bump bind not live',
                               'clean 1 s later' if not late else f'left 1 s later: {late}')].add(f'{start}/{pad_name} {where}/{opener}')
    print('\nletting go of the pad 10, 60 or 120 ms after a 40 ms tap of L1, R1, Select or Start')
    for key, cases in sorted(found.items(), key=lambda kv: -len(kv[1])):
        print(f'   {len(cases):3d}  {", ".join(key)}')
        print(f'        in: {", ".join(sorted({c.split("/")[0] for c in cases}))} | clicks: {", ".join(sorted({c.split("/")[1] for c in cases}))}'
              f' | taps: {", ".join(sorted({c.split("/")[2] for c in cases}))}')


if __name__ == '__main__':
    table = defaultdict(lambda: defaultdict(list))            # action -> outcome -> [case]
    total = 0
    for exposed in (True, False):
        for start in STARTS:
            for click in CLICKS:
                for order in ('click first', 'thumbs first'):
                    for name, action in actions(click[0]).items():
                        if order == 'thumbs first':
                            if not name.startswith('stick: touch'):
                                continue
                            stick = name.split()[2]
                            action = (lambda s: (lambda p: p.lift(s).wait(60)))(stick)
                            name = f'stick: lift {stick}, thumbs rested before the click'
                        total += 1
                        table[name][run(start, click, name, action, order, exposed)].append(
                            f'{start}/{click[0]} {click[1]}/A9 {"fires" if exposed else "silent"}')
    print(f'{total} runs, {VARIANT}')
    for name, outcomes in table.items():
        print(f'\n{name}')
        for outcome, cases in sorted(outcomes.items(), key=lambda kv: -len(kv[1])):
            print(f'   {len(cases):3d}  {outcome}')
            if outcome != 'holds':
                starts = sorted({c.split('/')[0] for c in cases}); clicks = sorted({c.split('/')[1] for c in cases}); a9 = sorted({c.split('/')[2] for c in cases})
                print(f'        in: {", ".join(starts)} | clicks: {", ".join(clicks)} | {", ".join(a9)}')
    under_a_window()
