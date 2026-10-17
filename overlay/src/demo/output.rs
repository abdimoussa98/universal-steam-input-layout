use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet, VecDeque};

#[derive(Default, Serialize)]
pub(crate) struct Output {
    pub down: BTreeSet<String>,
    pub text: String,
    pub pointer: [f64; 2],
    pub wheel: i64,
    pub axes: BTreeMap<String, [f64; 2]>,
    pub events: VecDeque<Event>,
    pub sequence: u64,
    pub feedback: u64,
}
#[derive(Serialize)]
pub(crate) struct Event {
    pub sequence: u64,
    pub at: u64,
    pub kind: String,
    pub detail: String,
}
impl Output {
    pub fn note(&mut self, at: u64, kind: &str, detail: String) {
        if matches!(kind, "down" | "tap") {
            self.apply_key(&detail);
        }
        self.sequence += 1;
        if matches!(kind, "beep" | "gyro_tick" | "haptic") {
            self.feedback += 1;
        }
        self.events.push_back(Event {
            sequence: self.sequence,
            at,
            kind: kind.into(),
            detail,
        });
        if self.events.len() > 512 {
            self.events.pop_front();
        }
    }
    fn apply_key(&mut self, key: &str) {
        match key {
            "mouse_wheel SCROLL_UP" => self.wheel -= 1,
            "mouse_wheel SCROLL_DOWN" => self.wheel += 1,
            "BACKSPACE" => {
                self.text.pop();
            }
            "RETURN" => self.text.push('\n'),
            "SPACE" => self.text.push(' '),
            "TAB" => self.text.push_str("    "),
            key if key.len() == 1 => {
                if self
                    .down
                    .iter()
                    .any(|k| k.ends_with("CONTROL") || k.ends_with("ALT") || k.ends_with("WINDOWS"))
                {
                    return;
                }
                if self.down.iter().any(|k| k.ends_with("SHIFT")) {
                    self.text.push_str(key);
                } else {
                    self.text.push_str(&key.to_lowercase());
                }
            }
            _ => {}
        }
        if self.text.len() > 2000 {
            self.text.drain(..1000);
        }
    }
}
