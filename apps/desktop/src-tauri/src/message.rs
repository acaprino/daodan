//! A native message, for when there is no page that could say it.
use windows_sys::Win32::UI::WindowsAndMessaging::{MessageBoxW, MB_ICONERROR, MB_SETFOREGROUND};

/// Says `text` and blocks until it is closed.
pub fn tell(text: &str) {
    let wide = |text: &str| -> Vec<u16> { text.encode_utf16().chain(Some(0)).collect() };
    let (title, text) = (wide("Daodan"), wide(text));
    // SAFETY: both texts end with a zero and live through the call; the message has no owner.
    unsafe {
        MessageBoxW(
            std::ptr::null_mut(),
            text.as_ptr(),
            title.as_ptr(),
            MB_ICONERROR | MB_SETFOREGROUND,
        );
    }
}
