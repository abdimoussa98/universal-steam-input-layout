//! Registration and cleanup of native mode shortcuts.
use super::HotkeyApi;

pub struct Hotkeys<A: HotkeyApi> {
    api: A,
    registered: Vec<i32>,
}
impl<A: HotkeyApi> Hotkeys<A> {
    pub fn new(api: A) -> Self {
        Self {
            api,
            registered: vec![],
        }
    }
    pub fn rebind(&mut self, keys: [u8; 3]) -> Vec<String> {
        for id in self.registered.drain(..) {
            self.api.unregister(id);
        }
        let mut errors = vec![];
        for (i, key) in keys.into_iter().enumerate() {
            let id = i as i32 + 1;
            match self.api.register(id, key) {
                Ok(()) => self.registered.push(id),
                Err(e) => errors.push(format!("F{key}: {e}")),
            }
        }
        errors
    }
}
impl<A: HotkeyApi> Drop for Hotkeys<A> {
    fn drop(&mut self) {
        for id in self.registered.drain(..) {
            self.api.unregister(id);
        }
    }
}
