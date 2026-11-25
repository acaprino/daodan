fn main() {
    // The commands are named, so that a page has the ones its capability grants, and no other.
    let manifest = tauri_build::AppManifest::new().commands(&["start_state", "start_again"]);
    tauri_build::try_build(tauri_build::Attributes::new().app_manifest(manifest))
        .expect("the build of the window failed");
}
