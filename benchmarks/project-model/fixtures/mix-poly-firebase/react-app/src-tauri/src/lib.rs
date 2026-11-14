#[tauri::command]
fn save_receipt(order_id: String) -> Result<String, String> {
    Ok(format!("receipt-{order_id}.pdf"))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![save_receipt])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
