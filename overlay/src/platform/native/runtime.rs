use super::super::sdl_input::{Sample, SdlInput};
use super::*;

pub(super) struct NativeLoop {
    input: SdlInput,
    keys: Hotkeys<WinHotkeys>,
    registered: [u8; 3],
    diagnostic: bool,
    last_diagnostic: Vec<Device>,
    last_input_error: Option<String>,
    selection: DeviceSelection,
}
impl NativeLoop {
    pub fn new(
        input: SdlInput,
        keys: Hotkeys<WinHotkeys>,
        registered: [u8; 3],
        diagnostic: bool,
    ) -> Self {
        Self {
            input,
            keys,
            registered,
            diagnostic,
            last_diagnostic: vec![],
            last_input_error: None,
            selection: DeviceSelection::default(),
        }
    }
    pub fn run(&mut self, hub: &Arc<Mutex<Hub>>, running: &AtomicBool) {
        while running.load(Ordering::Acquire) {
            let Some((sample, input_error)) = self.poll(hub, running) else {
                break;
            };
            self.report_diagnostic(&sample.devices);
            let mut h = hub.lock().expect("hub");
            self.update_metadata(&mut h, &input_error);
            hotkeys::process_messages(&mut h);
            self.select_device(&mut h, &sample.identities);
            apply_sample(&mut h, sample, input_error.is_some());
            drop(h);
            thread::sleep(Duration::from_millis(8));
        }
    }
    fn poll(
        &mut self,
        hub: &Arc<Mutex<Hub>>,
        running: &AtomicBool,
    ) -> Option<(Sample, Option<String>)> {
        let (sample, input_error) = match self.input.poll() {
            Ok(sample) => (sample, None),
            Err(error) => (
                Sample {
                    devices: vec![],
                    events: vec![],
                    now_ms: sdl3::timer::ticks(),
                    identities: vec![],
                },
                Some(error),
            ),
        };
        if self.input.quit_requested {
            running.store(false, Ordering::Release);
            if let Some(ctx) = &hub.lock().expect("hub").context {
                ctx.send_viewport_cmd(egui::ViewportCommand::Close);
            }
            return None;
        }
        Some((sample, input_error))
    }
    fn report_diagnostic(&mut self, devices: &[Device]) {
        if self.diagnostic && devices != self.last_diagnostic.as_slice() {
            println!("{}", serde_json::to_string(&devices).expect("devices"));
            self.last_diagnostic = devices.to_vec();
        }
    }
    fn update_metadata(&mut self, h: &mut Hub, input_error: &Option<String>) {
        if input_error != &self.last_input_error {
            if input_error.is_some() || h.data.error == self.last_input_error {
                h.data.error = input_error.clone();
            }
            self.last_input_error = input_error.clone();
            h.changed();
        }
        if h.data.settings.hotkeys != self.registered {
            self.registered = h.data.settings.hotkeys;
            let conflicts = self.keys.rebind(self.registered);
            h.data.settings.error = if conflicts.is_empty() {
                None
            } else {
                Some(conflicts.join("; "))
            };
            h.changed();
        }
    }
    fn select_device(&mut self, h: &mut Hub, identities: &[(String, Option<String>)]) {
        if h.data.settings.selected != self.selection.current {
            self.selection = DeviceSelection::default();
            if let Some(id) = &h.data.settings.selected {
                self.selection.choose(id.clone(), None);
            }
        }
        if let Some(id) = self.selection.resolve(identities)
            && h.data.settings.selected.as_ref() != Some(&id)
        {
            h.data.settings.selected = Some(id);
            h.changed();
        }
    }
}

fn apply_sample(h: &mut Hub, sample: Sample, unavailable: bool) {
    let tracker = InputTracker {
        selected: h.data.settings.selected.clone(),
    };
    let changed = if unavailable {
        let changed = h.data.state.status != InputStatus::Unavailable;
        h.data.state.unavailable(InputStatus::Unavailable);
        changed
    } else {
        {
            let FrameData { state, profile, .. } = &mut h.data;
            tracker.sample_timed(
                state,
                &sample.devices,
                &sample.events,
                sample.now_ms,
                profile,
            )
        }
    };
    let metadata: Vec<_> = sample
        .devices
        .into_iter()
        .map(|mut d| {
            d.held = [false, false];
            d.input = InputFrame::default();
            d
        })
        .collect();
    if changed || metadata != h.data.settings.devices {
        h.data.settings.devices = metadata;
        h.changed();
    }
}
