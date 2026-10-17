use super::*;

// Display wording stays separate from profile semantics and source bindings.
pub(super) fn compact_binding(label: &str) -> String {
    label
        .replace(" / Function layer", " :: Fn")
        .replace(" / Cursor gyro", " :: Gyro")
        .replace("Function layer", "Fn")
        .replace("Cursor gyro", "Gyro")
        .replace("Mouse left", "Left click")
        .replace("Mouse right", "Right click")
        .replace("Mouse middle", "Middle click")
        .replace("CAPSLOCK", "Caps Lock")
        .replace("UP_ARROW", "↑")
        .replace("RIGHT_ARROW", "→")
        .replace("DOWN_ARROW", "↓")
        .replace("LEFT_ARROW", "←")
        .replace("_ARROW", "")
        .replace("Unbound", "—")
}

pub(super) fn gesture_binding(tap: &str, hold: &str) -> String {
    format!("{} :: {}", compact_binding(tap), compact_binding(hold))
}

pub(super) fn recipe_binding(recipe: &Recipe) -> String {
    match &recipe.modifier_label {
        Some(modifier) => gesture_binding(modifier, &recipe.tap_label),
        None => gesture_binding(&recipe.tap_label, &recipe.hold_label),
    }
}

pub(super) fn timed_gesture_outcomes(recipe: &Recipe) -> [String; 3] {
    [
        format!(
            "HOLD  {}",
            recipe
                .modifier_label
                .as_deref()
                .unwrap_or(&recipe.hold_label)
        ),
        format!("TAP  {}", recipe.tap_label),
        format!("TAP, THEN HOLD  {} while held", recipe.tap_label),
    ]
}

#[cfg(test)]
mod timed_gesture_wording_tests {
    use super::*;

    #[test]
    fn outcomes_keep_single_tap_distinct_from_second_hold() {
        let profile = Profile::parse(crate::BUNDLED_PROFILE).unwrap();
        let dashboard = profile.dashboard.unwrap();
        let bumper = dashboard.recipe(Mode::Base, Control::L1).unwrap();
        assert_eq!(
            timed_gesture_outcomes(bumper),
            [
                "HOLD  Mod 0",
                "TAP  Scroll down",
                "TAP, THEN HOLD  Scroll down while held"
            ]
        );
        let menu = dashboard.recipe(Mode::Base, Control::Select).unwrap();
        assert_eq!(
            timed_gesture_outcomes(menu),
            [
                "HOLD  Function layer",
                "TAP  Escape",
                "TAP, THEN HOLD  Escape while held"
            ]
        );
    }
}
