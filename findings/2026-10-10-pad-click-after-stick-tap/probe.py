import sys
sys.path.insert(0,'.')
from tests.scenario import Pad
def show(label, pad):
    print(f"  {label:52} down={pad.down()} stack={[n for n in pad.stack if n not in ('Base','Steering')]} typed={pad.typed()}")
for start in (None, ('Base','Steering')):
  for stick in ('RS','LS'):
    for padname, where in (('LP','left'),('RP','left'),('LP','centre'),('RP','centre')):
      print(f"\n## start={start} stick={stick} pad={padname} {where}")
      # a: long touch, click, lift
      p=Pad('default', start=start); p.mark(); p.touch(stick).wait(400); p.press_pad(padname, where).wait(200); show('a held, thumb long on stick',p); p.lift(stick).wait(10); show('a after lift +10',p); p.wait(300); show('a after lift +310',p)
      # b: short touch, click, lift inside 150
      p=Pad('default', start=start); p.mark(); p.touch(stick).wait(40); p.press_pad(padname, where).wait(40); p.lift(stick).wait(10); show('b short touch, lift +10',p); p.wait(300); show('b +310',p)
      # c: click first, touch, lift
      p=Pad('default', start=start); p.mark(); p.press_pad(padname, where).wait(200); p.touch(stick).wait(60); show('c touch after click',p); p.lift(stick).wait(10); show('c lift +10',p); p.wait(300); show('c +310',p)
      # d: tap the stick, then click inside the window
      p=Pad('default', start=start); p.mark(); p.touch(stick).wait(60); p.lift(stick).wait(30); p.press_pad(padname, where).wait(30); show('d click 30 ms after a stick tap',p); p.wait(300); show('d +300',p)
      # e: long touch, lift, click 30 ms later
      p=Pad('default', start=start); p.mark(); p.touch(stick).wait(400); p.lift(stick).wait(30); p.press_pad(padname, where).wait(30); show('e click 30 ms after a long touch ends',p)
