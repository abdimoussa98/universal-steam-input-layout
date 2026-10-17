"""Clock regressions: renderer/driver latency must not change gesture durations."""
from pathlib import Path
import subprocess
import unittest


class DemoClockTests(unittest.TestCase):
    def test_slow_work_and_resuming_preserve_monotonic_gesture_time(self):
        fixture = Path(__file__).resolve().parents[1] / 'tests/fixtures/demo-clock.js'
        script = r'''
          const assert=require('node:assert/strict');
          let real=100;
          global.window=global;
          global.performance={now:()=>real};
          global.requestAnimationFrame=()=>1;
          new Function(require('node:fs').readFileSync(process.argv[1],'utf8'))();
          assert.equal(performance.now(),100);
          demoClock.begin();
          real+=500; // Rendering/driver work cannot lengthen the touch.
          assert.equal(performance.now(),100);
          demoClock.advance(60);
          real+=900;
          assert.equal(performance.now(),160);
          demoClock.end();
          assert.equal(performance.now(),160); // No jump on returning to real time.
          real+=20;
          assert.equal(performance.now(),180);
          demoClock.begin();
          demoClock.advance(600); // Tenfold wall duration still advances exactly 600.
          assert.equal(performance.now(),780);
          assert.throws(()=>demoClock.advance(-1));
          demoClock.end();
          real+=10;
          assert.equal(performance.now(),790);
        '''
        subprocess.run(['node', '-e', script, str(fixture)], check=True)


if __name__ == '__main__':
    unittest.main()
