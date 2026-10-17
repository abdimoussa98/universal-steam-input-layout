use super::*;

fn frame() -> FrameData {
    FrameData {
        state: State::default(),
        profile: Profile::parse(crate::BUNDLED_PROFILE).unwrap(),
        settings: HostSettings::default(),
        preferences: Preferences::default(),
        native: false,
        remote: false,
        recovery_available: false,
        hud: false,
        companion_url: None,
        browser_connection: None,
        error: None,
    }
}

fn sample(data: &mut FrameData, input: &InputFrame, logical_ms: u64) {
    let wall_ms = logical_ms * u64::from(data.state.timing_scale());
    data.state
        .sample_input("test", input.clone(), &data.profile, wall_ms);
}

fn render(data: &FrameData) -> (Vec<String>, f32, serde_json::Value) {
    let ctx = egui::Context::default();
    let mut bottom = 0.0;
    let output = ctx.run(
        egui::RawInput {
            screen_rect: Some(egui::Rect::from_min_size(
                egui::Pos2::ZERO,
                egui::vec2(760.0, 200.0),
            )),
            ..Default::default()
        },
        |ctx| {
            egui::CentralPanel::default().show(ctx, |ui| {
                draw(ui, data, data.state.gestures.clock_ms);
                bottom = ui.cursor().top();
            });
        },
    );
    let text = output
        .shapes
        .iter()
        .filter_map(|shape| match &shape.shape {
            egui::epaint::Shape::Text(text) => Some(text.galley.text().to_owned()),
            _ => None,
        })
        .collect();
    let diagnostic = ctx
        .data(|data| data.get_temp::<serde_json::Value>(egui::Id::new("keybind.timeline")))
        .unwrap();
    (text, bottom, diagnostic)
}

#[test]
fn idle_history_output_unknown_and_interrupted_timelines_have_no_text() {
    let mut data = frame();
    data.state.status = InputStatus::Live;
    data.state.gestures.history.push(GestureMark {
        lane: 0,
        at_ms: 10,
        label: "Previous tap".into(),
    });
    for phase in [
        Phase::Idle,
        Phase::Output,
        Phase::Unknown,
        Phase::Interrupted,
    ] {
        data.state.gestures.lanes[0].phase = phase;
        let (text, _, diagnostic) = render(&data);
        assert!(text.is_empty(), "Painted text in {phase:?}: {text:?}");
        assert_eq!(diagnostic["active"], false);
        assert_eq!(diagnostic["text"], "");
    }
    data.profile.dashboard = None;
    assert!(render(&data).0.is_empty());
}

#[test]
fn lifecycle_text_never_changes_the_controller_position() {
    let mut data = frame();
    data.state.status = InputStatus::Live;
    let (_, idle_bottom, _) = render(&data);
    for phase in [
        Phase::Pressed,
        Phase::Window,
        Phase::Second,
        Phase::Hold,
        Phase::Cover,
        Phase::Consumed,
        Phase::Combined,
        Phase::CombinedCover,
    ] {
        data.state.gestures.lanes[0].phase = phase;
        let (text, bottom, diagnostic) = render(&data);
        assert!(text.iter().any(|text| text.contains(" :: ")));
        assert_eq!(bottom, idle_bottom, "Timeline moved controls in {phase:?}");
        assert_eq!(diagnostic["active"], true);
    }
}

#[test]
fn missing_or_uncertain_input_never_displays_a_stale_countdown() {
    let mut data = frame();
    data.state.gestures.lanes[0] = Lane {
        phase: Phase::Pressed,
        started_ms: 100,
        deadline_ms: Some(300),
        ..Default::default()
    };
    for status in [
        InputStatus::SelectDevice,
        InputStatus::Disconnected,
        InputStatus::Paused,
        InputStatus::UnsupportedMapping,
        InputStatus::Unavailable,
    ] {
        data.state.status = status;
        assert!(render(&data).0.is_empty());
    }
    data.state.status = InputStatus::Live;
    data.state.gestures.uncertainty = Some("Timing interrupted".into());
    assert!(render(&data).0.is_empty());
}

#[test]
fn progress_uses_logical_time_and_countdown_uses_slowed_wall_time() {
    for scale in [1, 2, 5, 10] {
        let mut data = frame();
        data.state.set_timing_scale(scale);
        let mut input = InputFrame::default();
        sample(&mut data, &input, 0);
        input.buttons[Control::L1 as usize] = true;
        sample(&mut data, &input, 10);
        sample(&mut data, &input, 110);
        let timeline = Timeline::active(&data).unwrap();
        assert_eq!(timeline.progress(110), 0.5);
        assert_eq!(timeline.remaining_ms(110), Some(100 * u64::from(scale)));
        sample(&mut data, &input, 210);
        let timeline = Timeline::active(&data).unwrap();
        assert_eq!(timeline.lane.phase, Phase::Hold);
        assert_eq!(timeline.progress(210), 1.0);
        assert_eq!(timeline.remaining_ms(210), None);
        input.buttons[Control::L1 as usize] = false;
        sample(&mut data, &input, 220);
        assert!(Timeline::active(&data).is_none());
    }
}

#[test]
fn release_window_and_second_hold_remain_visible_until_the_lifecycle_ends() {
    let mut data = frame();
    data.state.set_timing_scale(10);
    let mut input = InputFrame::default();
    sample(&mut data, &input, 0);
    input.buttons[Control::L1 as usize] = true;
    sample(&mut data, &input, 10);
    input.buttons[Control::L1 as usize] = false;
    sample(&mut data, &input, 20);
    let timeline = Timeline::active(&data).unwrap();
    let window_ms = timeline.recipe.window_ms;
    assert_eq!(timeline.lane.phase, Phase::Window);
    assert_eq!(timeline.remaining_ms(20), Some(window_ms * 10));
    sample(&mut data, &input, 70);
    assert!(data.state.gestures.lanes[0].output_seen);
    assert!(Timeline::active(&data).is_some());
    input.buttons[Control::L1 as usize] = true;
    sample(&mut data, &input, 80);
    assert_eq!(Timeline::active(&data).unwrap().lane.phase, Phase::Second);
    sample(&mut data, &input, 230);
    assert_eq!(Timeline::active(&data).unwrap().lane.phase, Phase::Cover);
    input.buttons[Control::L1 as usize] = false;
    sample(&mut data, &input, 240);
    assert!(Timeline::active(&data).is_none());
    input.buttons[Control::L1 as usize] = true;
    sample(&mut data, &input, 250);
    input.buttons[Control::L1 as usize] = false;
    sample(&mut data, &input, 260);
    sample(&mut data, &input, 260 + window_ms);
    assert!(Timeline::active(&data).is_none());
}

#[test]
fn steering_and_combined_gestures_use_their_own_durations() {
    let mut data = frame();
    data.state.select_mode(Mode::Steering);
    let mut input = InputFrame::default();
    sample(&mut data, &input, 0);
    input.buttons[Control::L1 as usize] = true;
    sample(&mut data, &input, 10);
    input.stick_positions[0] = Some([0, -1000]);
    sample(&mut data, &input, 20);
    let timeline = Timeline::active(&data).unwrap();
    assert!(timeline.steering);
    assert_eq!(timeline.owner(), "Left stick up");
    assert_eq!(
        timeline.duration(),
        timeline.profile.steering.as_ref().unwrap().hold_ms
    );
    assert_eq!(timeline.summary(), "Scroll up :: Tap Cover");
    input.buttons[Control::R1 as usize] = true;
    sample(&mut data, &input, 30);
    assert!(Timeline::active(&data).is_none());
    data.state.select_mode(Mode::Base);
    input = InputFrame::default();
    sample(&mut data, &input, 40);
    input.buttons[Control::L1 as usize] = true;
    sample(&mut data, &input, 50);
    input.buttons[Control::R1 as usize] = true;
    sample(&mut data, &input, 60);
    let timeline = Timeline::active(&data).unwrap();
    assert!(timeline.combined());
    assert_eq!(timeline.owner(), "L1 + R1");
    assert_eq!(timeline.duration(), timeline.profile.combined_hold_ms);
}

#[test]
fn replacement_output_does_not_take_the_active_windows_timeline() {
    let mut data = frame();
    let mut input = InputFrame::default();
    sample(&mut data, &input, 0);
    input.buttons[Control::L1 as usize] = true;
    sample(&mut data, &input, 10);
    input.buttons[Control::L1 as usize] = false;
    sample(&mut data, &input, 20);
    input.buttons[Control::R1 as usize] = true;
    sample(&mut data, &input, 30);
    let timeline = Timeline::active(&data).unwrap();
    assert_eq!(timeline.control, Control::L1);
    assert_eq!(timeline.lane.phase, Phase::Window);
    assert_eq!(timeline.lane.started_ms, 20);
    assert_eq!(data.state.gestures.lanes[1].phase, Phase::Output);
}
