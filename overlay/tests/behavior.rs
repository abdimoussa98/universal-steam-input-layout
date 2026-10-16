use keybind_overlay::core::*;
#[cfg(target_arch = "wasm32")]
use wasm_bindgen_test::wasm_bindgen_test;
#[cfg(target_arch = "wasm32")]
wasm_bindgen_test::wasm_bindgen_test_configure!(run_in_browser);

fn profile() -> Profile {
    Profile::parse(include_str!("fixtures/profile.json")).unwrap()
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn all_twelve_contexts_have_independent_labels() {
    let p = profile();
    let mut s = State::default();
    for (mode, prefix) in [
        (Mode::Base, "base"),
        (Mode::Steering, "steering"),
        (Mode::Menu, "menu"),
    ] {
        s.select_mode(mode);
        for (held, context) in [
            ([false, false], "none"),
            ([true, false], "left"),
            ([false, true], "right"),
            ([true, true], "both"),
        ] {
            s.snapshot("pad", held);
            let view = s.view(&p);
            assert_eq!(
                view.labels,
                ["south", "east", "west", "north"].map(|b| format!("{prefix}/{context}/{b}"))
            );
        }
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn release_orders_repeats_and_mode_changes() {
    for first in [0, 1] {
        let mut s = State::default();
        s.snapshot("pad", [false, false]);
        s.modifier(first, true);
        assert!(!s.modifier(first, true));
        s.modifier(1 - first, true);
        s.select_mode(Mode::Steering);
        assert_eq!(s.view(&profile()).labels[0], "steering/both/south");
        s.modifier(first, false);
        assert!(s.held[1 - first]);
        s.modifier(1 - first, false);
        assert!(!s.modifier(1 - first, false));
        assert_eq!(s.mode, Mode::Steering);
        assert_eq!(s.view(&profile()).labels[0], "steering/none/south");
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn selected_device_snapshots_disconnect_and_resume() {
    let mut t = InputTracker::default();
    let mut s = State::default();
    s.select_mode(Mode::Menu);
    let a = Device {
        input: InputFrame::default(),
        id: "a".into(),
        name: "Physical".into(),
        standard: true,
        held: [true, false],
    };
    let b = Device {
        input: InputFrame::default(),
        id: "b".into(),
        name: "Virtual".into(),
        standard: true,
        held: [false, true],
    };
    t.sample(&mut s, &[a.clone(), b.clone()], false);
    assert_eq!(s.status, InputStatus::SelectDevice);
    t.select(Some("a".into()));
    assert!(t.sample(&mut s, &[a.clone(), b.clone()], false));
    assert_eq!(s.held, [true, false]);
    assert!(!t.sample(&mut s, &[a.clone(), b.clone()], false));
    t.sample(&mut s, &[b], false);
    assert_eq!(s.held, [false, false]);
    assert_eq!(s.status, InputStatus::Disconnected);
    assert_eq!(s.mode, Mode::Menu);
    t.sample(&mut s, std::slice::from_ref(&a), true);
    assert_eq!(s.status, InputStatus::Paused);
    t.sample(
        &mut s,
        &[Device {
            input: InputFrame::default(),
            held: [false, true],
            ..a
        }],
        false,
    );
    assert_eq!(s.held, [false, true]);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn unknown_mapping_never_assumes_standard_indices() {
    let mut t = InputTracker::default();
    t.select(Some("x".into()));
    let mut s = State::default();
    t.sample(
        &mut s,
        &[Device {
            input: InputFrame::default(),
            id: "x".into(),
            name: "x".into(),
            standard: false,
            held: [true, true],
        }],
        false,
    );
    assert_eq!(s.status, InputStatus::UnsupportedMapping);
    assert_eq!(s.held, [false, false]);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn rejects_invalid_profiles_and_retains_last_good_reload() {
    let good = include_str!("fixtures/profile.json");
    let mut slot = ProfileSlot::new(good).unwrap();
    for bad in [
        "{}".to_string(),
        good.replace("\"schema_version\": 1", "\"schema_version\": 99"),
        good.replace("\"context\": \"left\"", "\"context\": \"none\""),
    ] {
        assert!(slot.reload(&bad).is_err());
        assert_eq!(slot.profile.name, "Behavior fixture");
    }
    let mut p = profile();
    p.contexts.pop();
    assert!(p.validate().is_err());
    p = profile();
    p.modifiers = ["L1".into(), "L1".into()];
    assert!(p.validate().is_err());
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn explicit_unbound_unavailable_and_inheritance() {
    let mut p = profile();
    p.contexts[1].bindings[0] = Binding::Inherit;
    p.contexts[1].bindings[1] = Binding::Unbound;
    p.contexts[1].bindings[2] = Binding::Unavailable {
        reason: "Ambiguous".into(),
    };
    assert!(p.validate().is_ok());
    let mut s = State::default();
    s.snapshot("pad", [true, false]);
    assert_eq!(
        s.view(&p).labels,
        [
            "base/none/south",
            "Unbound",
            "Unavailable: Ambiguous",
            "base/left/north"
        ]
    );
    p.contexts[0].bindings[0] = Binding::Inherit;
    assert!(p.validate().is_err());
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn preferences_shortcuts_and_hud_recovery_are_validated() {
    let mut p = Preferences::default();
    assert!(p.validate().is_ok());
    p.hotkeys = [1, 1, 3];
    assert!(p.validate().is_err());
    p = Preferences::default();
    p.opacity = 0.0;
    assert!(p.validate().is_err());
    assert_eq!(
        page_shortcut(&[1, 2, 3], 2, false, false),
        Some(Mode::Steering)
    );
    assert_eq!(page_shortcut(&[1, 2, 3], 2, true, false), None);
    assert_eq!(page_shortcut(&[1, 2, 3], 2, false, true), None);
    assert_eq!(page_shortcut(&[1, 2, 3], 4, false, false), None);
    assert!(!can_enter_hud(false));
    assert!(can_enter_hud(true));
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn bridge_requires_matching_session_profile_and_increasing_sequences() {
    let p = profile();
    let mut c = BridgeClient::new("secret".into());
    let mut snapshot = BridgeSnapshot {
        version: 1,
        session: "secret".into(),
        sequence: 1,
        state: State::default(),
        profile_digest: p.digest(),
        profile: Some(p.clone()),
        settings: HostSettings::default(),
    };
    assert!(c.accept(snapshot.clone()).unwrap());
    assert!(!c.accept(snapshot.clone()).unwrap());
    snapshot.sequence = 2;
    snapshot.state.select_mode(Mode::Menu);
    snapshot.profile = None;
    assert!(c.accept(snapshot.clone()).unwrap());
    assert_eq!(c.state.mode, Mode::Menu);
    snapshot.sequence = 1;
    snapshot.state.select_mode(Mode::Base);
    assert!(!c.accept(snapshot.clone()).unwrap());
    assert_eq!(c.state.mode, Mode::Menu);
    snapshot.sequence = 3;
    snapshot.profile_digest = "wrong".into();
    assert!(c.accept(snapshot.clone()).is_err());
    snapshot.profile_digest = p.digest();
    snapshot.session = "old".into();
    assert!(c.accept(snapshot.clone()).is_err());
    snapshot.session = "secret".into();
    snapshot.version = 2;
    assert!(c.accept(snapshot).is_err());
    c.disconnect();
    assert_eq!(c.state.status, InputStatus::Unavailable);
    assert_eq!(c.state.held, [false, false]);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn bridge_commands_and_origins_are_scoped() {
    assert!(validate_request(
        "127.0.0.1:1234",
        Some("http://127.0.0.1:1234"),
        "token",
        "127.0.0.1:1234",
        "token"
    ));
    assert!(!validate_request(
        "evil.test",
        None,
        "token",
        "127.0.0.1:1234",
        "token"
    ));
    assert!(!validate_request(
        "127.0.0.1:1234",
        Some("http://evil.test"),
        "token",
        "127.0.0.1:1234",
        "token"
    ));
    assert!(!validate_request(
        "127.0.0.1:1234",
        None,
        "bad",
        "127.0.0.1:1234",
        "token"
    ));
    assert!(serde_json::from_str::<ModeCommand>(r#"{"mode":"menu"}"#).is_ok());
    assert!(serde_json::from_str::<ModeCommand>(r#"{"mode":"menu","file":"secret"}"#).is_err());
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn hotkey_conflicts_rebind_and_shutdown_release_registrations() {
    use std::cell::RefCell;
    use std::rc::Rc;
    #[derive(Clone)]
    struct Fake(Rc<RefCell<Vec<(i32, u8)>>>);
    impl HotkeyApi for Fake {
        fn register(&mut self, id: i32, key: u8) -> Result<(), String> {
            if key == 5 {
                return Err("reserved by another app".into());
            }
            self.0.borrow_mut().push((id, key));
            Ok(())
        }
        fn unregister(&mut self, id: i32) {
            self.0.borrow_mut().retain(|(i, _)| *i != id);
        }
    }
    let registrations = Rc::new(RefCell::new(vec![]));
    {
        let mut keys = Hotkeys::new(Fake(registrations.clone()));
        assert!(keys.rebind([1, 2, 3]).is_empty());
        assert_eq!(registrations.borrow().len(), 3);
        assert_eq!(keys.rebind([4, 5, 6]).len(), 1);
        assert_eq!(*registrations.borrow(), vec![(1, 4), (3, 6)]);
        assert!(keys.rebind([1, 2, 3]).is_empty());
    }
    assert!(registrations.borrow().is_empty());
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn stalled_remote_input_expires_and_resumes_only_after_fresh_data() {
    let mut clock = InputFreshness::default();
    clock.received(100.0);
    assert!(!clock.expired(2100.0));
    assert!(clock.expired(3101.0));
    clock.received(3200.0);
    assert!(!clock.expired(3201.0));
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn reconnect_uses_unique_physical_path_and_never_guesses_between_devices() {
    let mut selection = DeviceSelection::default();
    selection.choose("old-instance".into(), Some("usb:path-a".into()));
    let devices = vec![
        ("other".into(), Some("usb:path-b".into())),
        ("new-instance".into(), Some("usb:path-a".into())),
    ];
    assert_eq!(selection.resolve(&devices), Some("new-instance".into()));
    assert_eq!(
        selection.resolve(&[
            ("second".into(), Some("usb:path-a".into())),
            ("third".into(), Some("usb:path-a".into()))
        ]),
        None
    );
    selection.choose("unknown".into(), None);
    assert_eq!(selection.resolve(&devices), None);
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn headless_selection_waits_for_one_device_and_never_switches_to_another() {
    let mut selection = DeviceSelection::default();
    let a = ("a".into(), Some("usb:a".into()));
    let b = ("b".into(), Some("usb:b".into()));
    assert_eq!(selection.resolve_single(&[]), None);
    assert_eq!(selection.resolve_single(&[a.clone(), b.clone()]), None);
    assert_eq!(
        selection.resolve_single(std::slice::from_ref(&a)),
        Some("a".into())
    );
    assert_eq!(selection.resolve_single(&[]), None);
    assert_eq!(selection.resolve_single(&[b]), None);
    assert_eq!(
        selection.resolve_single(&[("new-a".into(), a.1)]),
        Some("new-a".into())
    );
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen_test)]
#[cfg_attr(not(target_arch = "wasm32"), test)]
fn native_reconnect_survives_macos_path_changes_with_serial_identity() {
    let identity =
        |serial, path| physical_device_identity(Some(0x28de), Some(0x1302), serial, path);
    let original = identity(Some("test-controller-a"), Some("DevSrvsID:100"));
    let reconnected = identity(Some("test-controller-a"), Some("DevSrvsID:200"));
    let other = identity(Some("test-controller-b"), Some("DevSrvsID:300"));
    assert_eq!(original, reconnected);
    assert_ne!(original, other);
    assert!(!original.as_ref().unwrap().contains("test-controller-a"));
    let mut selection = DeviceSelection::default();
    selection.choose("1".into(), original);
    assert_eq!(selection.resolve_single(&[]), None);
    assert_eq!(selection.resolve_single(&[("2".into(), other)]), None);
    assert_eq!(
        selection.resolve_single(&[("3".into(), reconnected.clone())]),
        Some("3".into())
    );
    assert_eq!(
        selection.resolve_single(&[("4".into(), reconnected.clone()), ("5".into(), reconnected)]),
        None
    );
    assert_eq!(identity(None, None), None);
    assert_eq!(
        identity(Some(""), Some("usb:path")),
        Some("path:usb:path".into())
    );
}
