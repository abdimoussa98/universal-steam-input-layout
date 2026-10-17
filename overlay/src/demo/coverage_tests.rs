use super::{Engine, Input, Layout, Session};

fn button(e: &mut Engine, control: &str, down: bool) {
    e.input(&Input::Button {
        control: control.into(),
        down,
    });
}
fn route(e: &mut Engine, menu: &str, stick: &str) {
    button(e, menu, true);
    button(e, stick, true);
    button(e, stick, false);
    button(e, menu, false);
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn swipes_gamepad_axes_and_stateful_exits_work_for_every_variant() {
    for layout in Layout::catalog().unwrap() {
        let mut e = Engine::new(layout.clone());
        let source = if layout.controller == "dse" {
            "center_trackpad"
        } else {
            "left_trackpad"
        };
        for (position, touching) in [([0., 0.], true), ([0.8, 0.], true), ([0.8, 0.], false)] {
            e.input(&Input::Surface {
                source: source.into(),
                position,
                touching,
                click: false,
            });
        }
        assert_eq!(e.output.text, "\n", "{}", e.snapshot());
        assert!(e.output.down.is_empty(), "{}", e.snapshot());
        route(&mut e, "switch/button_escape", "right_joystick/click");
        assert_eq!(e.mode(), "Gamepad", "{}", e.snapshot());
        e.input(&Input::Surface {
            source: "joystick".into(),
            position: [0.8, 0.],
            touching: false,
            click: false,
        });
        e.advance_to(20);
        assert!(
            e.output.axes.values().any(|xy| xy[0] > 0.5),
            "{}",
            e.snapshot()
        );
        e.input(&Input::Surface {
            source: "joystick".into(),
            position: [0.; 2],
            touching: false,
            click: false,
        });
        route(&mut e, "switch/button_escape", "right_joystick/click");
        e.advance_to(300);
        assert_ne!(e.mode(), "Gamepad");
        assert!(e.output.down.is_empty(), "{}", e.snapshot());
    }
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn scroll_rejects_center_expired_window_and_long_first_touch() {
    let layout = Layout::catalog().unwrap()[0].clone();
    for (hold, gap, position) in [
        (60, 50, [0.; 2]),
        (60, 151, [0., -0.9]),
        (151, 50, [0., -0.9]),
    ] {
        let mut e = Engine::new(layout.clone());
        let pad = |e: &mut Engine, p, t| {
            e.input(&Input::Surface {
                source: "right_trackpad".into(),
                position: p,
                touching: t,
                click: false,
            })
        };
        pad(&mut e, [0.; 2], true);
        e.advance_to(hold);
        pad(&mut e, [0.; 2], false);
        e.advance_to(hold + gap);
        pad(&mut e, position, true);
        assert!(
            !e.stack_titles().contains(&"RTP: Circular Scroll"),
            "{}",
            e.snapshot()
        );
        assert_eq!(e.output.wheel, 0);
        pad(&mut e, position, false);
        e.advance_to(1000);
        assert!(e.output.down.is_empty());
    }
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn release_window_obeys_exact_deadline_and_step() {
    let mut s = Session::new(Layout::catalog().unwrap()[0].clone());
    s.tick(0.);
    s.input(Input::Button {
        control: "right_trackpad/touch".into(),
        down: true,
    });
    s.tick(60.);
    s.input(Input::Button {
        control: "right_trackpad/touch".into(),
        down: false,
    });
    s.tick(209.);
    assert!(s.engine.stack_titles().contains(&"RTP: Double Tap"));
    s.step();
    assert_eq!(s.engine.now, 210);
    assert_eq!(s.engine.stack_titles(), ["Base"]);
}
#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn held_stick_output_is_independent_of_render_frequency() {
    let layout = Layout::catalog().unwrap()[0].clone();
    let mut a = Session::new(layout.clone());
    let mut b = Session::new(layout);
    b.scale = 10;
    a.tick(0.);
    b.tick(0.);
    let stick = Input::Surface {
        source: "right_joystick".into(),
        position: [0.8, 0.],
        touching: false,
        click: false,
    };
    a.input(stick.clone());
    b.input(stick);
    for n in 1..=100 {
        a.tick(f64::from(n));
    }
    for n in 1..=10 {
        b.tick(f64::from(n) * 100.);
    }
    assert_eq!(a.engine.snapshot(), b.engine.snapshot());
}
