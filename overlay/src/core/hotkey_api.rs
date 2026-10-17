//! Registration and cleanup of native mode shortcuts.
pub trait HotkeyApi {
    fn register(&mut self, id: i32, key: u8) -> Result<(), String>;
    fn unregister(&mut self, id: i32);
}
