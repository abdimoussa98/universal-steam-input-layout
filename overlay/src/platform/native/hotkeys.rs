use super::*;
use windows::Win32::UI::{Input::KeyboardAndMouse::*, WindowsAndMessaging::*};

pub(super) struct WinHotkeys;
impl HotkeyApi for WinHotkeys {
    fn register(&mut self, id: i32, key: u8) -> Result<(), String> {
        // Thread-scoped registration; this object is used and dropped on main.
        unsafe {
            RegisterHotKey(
                None,
                id,
                MOD_NOREPEAT,
                u32::from(VK_F1.0) + u32::from(key) - 1,
            )
        }
        .map_err(|e| e.to_string())
    }
    fn unregister(&mut self, id: i32) {
        let _ = unsafe { UnregisterHotKey(None, id) };
    }
}
pub(super) struct RecoveryHotkey(pub(super) bool);
impl RecoveryHotkey {
    pub(super) fn new() -> Self {
        Self(
            unsafe {
                RegisterHotKey(
                    None,
                    100,
                    MOD_CONTROL | MOD_ALT | MOD_NOREPEAT,
                    u32::from(b'O'),
                )
            }
            .is_ok(),
        )
    }
}
impl Drop for RecoveryHotkey {
    fn drop(&mut self) {
        if self.0 {
            let _ = unsafe { UnregisterHotKey(None, 100) };
        }
    }
}

pub(super) fn process_messages(h: &mut Hub) {
    let mut message = MSG::default();
    while unsafe { PeekMessageW(&mut message, None, WM_HOTKEY, WM_HOTKEY, PM_REMOVE) }.as_bool() {
        match message.wParam.0 {
            1..=3 => {
                if h.data.state.select_mode(Mode::ALL[message.wParam.0 - 1]) {
                    h.changed();
                }
            }
            100 => h.window(false, false),
            _ => {}
        }
    }
}
