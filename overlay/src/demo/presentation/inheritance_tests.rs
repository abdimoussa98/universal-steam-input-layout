use super::*;
use crate::demo::Input;

fn button(e: &mut Engine, control: &str, down: bool) {
    e.input(&Input::Button {
        control: control.into(),
        down,
    });
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn cursor_cancellation_shows_the_exposed_modifier_binding() {
    for layout in Layout::catalog().unwrap() {
        let primary = if layout.variant == "alternative" {
            "left_trigger/edge"
        } else {
            "switch/left_bumper"
        };
        let mut e = Engine::new(layout);
        button(&mut e, primary, true);
        e.advance_to(210);
        assert!(
            e.stack_titles()
                .iter()
                .any(|t| t.ends_with("Temp Cursor Gyro"))
        );
        let before = e.snapshot();
        assert_eq!(
            e.display_label("button_diamond/button_a"),
            "G",
            "{}",
            e.layout.label()
        );
        assert_eq!(
            e.snapshot(),
            before,
            "Rendering must not execute cancellation"
        );
        button(&mut e, "button_diamond/button_a", true);
        assert!(e.output.down.contains("G"));
        assert_eq!(e.display_label("button_diamond/button_a"), "G");
        assert!(e.stack_titles().iter().any(|t| t.ends_with("Tap Cover")));
        button(&mut e, "button_diamond/button_a", false);
        button(&mut e, primary, false);
        assert_eq!(e.display_label("button_diamond/button_a"), "F");
    }
}

fn stack(e: &mut Engine, titles: &[&str]) {
    e.stack = titles
        .iter()
        .map(|title| {
            e.layout
                .layers
                .iter()
                .position(|l| &l.title == title)
                .unwrap()
        })
        .collect();
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn both_cursor_overlays_preserve_all_parent_labels_and_pad_inheritance() {
    for layout in Layout::catalog().unwrap() {
        for side in ["left", "right"] {
            let owner = if layout.variant == "alternative" {
                format!("{side}_trigger/edge")
            } else {
                format!("switch/{side}_bumper")
            };
            let mut e = Engine::new(layout.clone());
            button(&mut e, &owner, true);
            let controls = [
                "button_diamond/button_a",
                "button_diamond/button_b",
                "button_diamond/button_x",
                "button_diamond/button_y",
                "dpad/dpad_north",
                "dpad/dpad_east",
                "dpad/dpad_south",
                "dpad/dpad_west",
                "joystick/click",
                "right_joystick/click",
                "switch/button_menu",
                "switch/button_escape",
            ];
            let labels = controls.map(|c| e.display_label(c));
            assert!(labels.iter().all(|l| l != "—"));
            let source = if layout.controller == "dse" {
                "center_trackpad"
            } else {
                "right_trackpad"
            };
            let pad = e.pad_view(source, true);
            e.advance_to(210);
            assert!(
                e.stack_titles()
                    .iter()
                    .any(|t| t.ends_with("Temp Cursor Gyro"))
            );
            assert_eq!(
                controls.map(|c| e.display_label(c)),
                labels,
                "{} {side}",
                layout.label()
            );
            assert_eq!(e.pad_view(source, true).directions, pad.directions);
            assert_eq!(e.pad_view(source, true).center, pad.center);
        }
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn inherited_outputs_obey_chord_guards_and_explicit_window_blocks() {
    let mut e = Engine::new(Layout::catalog().unwrap()[0].clone());
    stack(&mut e, &["Base", "L1: Modifier 0", "L1: Tap Cover"]);
    e.held.insert("switch/left_bumper".into());
    assert_eq!(e.display_label("button_diamond/button_a"), "G");
    stack(&mut e, &["Base", "L1!R1: Modifier 2"]);
    e.held.clear();
    e.held.insert("switch/right_bumper".into());
    assert_eq!(
        e.display_label("button_diamond/button_a"),
        "—",
        "Empty chord must suppress recovery"
    );
    stack(
        &mut e,
        &[
            "Base",
            "L1: Modifier 0",
            "L1: Temp Cursor Gyro",
            "RTP: Double Tap",
        ],
    );
    e.held.insert("switch/left_bumper".into());
    assert_eq!(
        e.display_label("button_diamond/button_a"),
        "—",
        "Timed window must not expose G"
    );
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test::wasm_bindgen_test)]
#[test]
fn absent_inputs_inherit_but_disabled_modes_and_delayed_exits_do_not() {
    let mut e = Engine::new(Layout::catalog().unwrap()[0].clone());
    stack(&mut e, &["Base", "L1: Modifier 0", "L1: Temp Cursor Gyro"]);
    e.held.insert("switch/left_bumper".into());
    let top = *e.stack.last().unwrap();
    let gid = e.layout.layers[top].sources["button_diamond"];
    let group = &mut std::sync::Arc::make_mut(&mut e.layout).groups[gid];
    group.inputs.get_mut("button_a").unwrap()[0]
        .settings
        .insert("delay_start".into(), "50".into());
    assert_eq!(e.display_label("button_diamond/button_a"), "—");
    std::sync::Arc::make_mut(&mut e.layout).groups[gid]
        .inputs
        .clear();
    assert_eq!(e.display_label("button_diamond/button_a"), "G");
    for mode in ["disabled", "dpad"] {
        std::sync::Arc::make_mut(&mut e.layout).groups[gid].mode = mode.into();
        assert_eq!(e.display_label("button_diamond/button_a"), "—");
    }
}
