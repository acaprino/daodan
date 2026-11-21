#[tauri::command]
fn persist() {}

#[tauri::command]
fn only_in_tests() {}

#[tauri::command]
fn on_idle_builder() {}

#[allow(dead_code)]
fn idle() -> tauri::Builder<tauri::Wry> {
    tauri::Builder::default().invoke_handler(tauri::generate_handler![on_idle_builder])
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![persist])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    #[test]
    fn registers() {
        let _ = tauri::Builder::<tauri::Wry>::default()
            .invoke_handler(tauri::generate_handler![super::only_in_tests]);
    }
}
