//! Daodan's window: its own server, started hidden from the Python beside this program, and the page
//! the server serves in a window that `imago-shell` opens and watches. Until the server answers, and
//! when it dies, the window shows the page inside this program (`viewer/start`).
#![cfg_attr(not(test), windows_subsystem = "windows")]

mod life;
mod message;
mod server;

use imago_shell::{
    on_run_event, open_main, plugin, show_main,
    single_instance::{launch, Launch, Quitting},
    Material, Options, DARK_GROUND, LIGHT_GROUND,
};
use life::Daodan;
use std::{error::Error, process::exit, thread};
use tauri::{App, AppHandle, Manager, RunEvent};

fn setup(app: &mut App) -> Result<(), Box<dyn Error>> {
    let mut options = Options::for_app(app)?;
    let data = app.path().app_data_dir()?;
    match launch(&data, false) {
        Ok(Launch::First(instance)) => {
            let app = app.handle().clone();
            instance.on_raise(move || show_main(&app));
        }
        Ok(Launch::Running | Launch::Closing) => exit(0),
        // Without the signal Daodan still runs; two of them are two servers.
        Err(error) => eprintln!("daodan: single instance: {error}"),
    }
    life::new_log(&data);
    options.material = Material::Opaque {
        dark: DARK_GROUND,
        light: LIGHT_GROUND,
    };
    options.data_dir = Some(data.clone());
    options.reload_label = "Ricarica l'interfaccia".into();
    options.stopped_message = "L'interfaccia non risponde. Ricaricarla?".into();
    options.lost_message = "La finestra non si può ripristinare. Daodan si chiude.".into();
    app.manage(Daodan::new(data, options.origins.clone()));
    // Before the window, which takes its time: the server starts meanwhile.
    let kept = app.handle().clone();
    thread::spawn(move || life::keep(&kept));
    open_main(app.handle(), options)?;
    Ok(())
}

/// The window is gone: the server ends, and a copy started meanwhile waits for it.
fn close(app: &AppHandle) {
    let Some(daodan) = app.try_state::<Daodan>() else {
        return;
    };
    let _quitting = Quitting::mark(daodan.data());
    daodan.close();
}

fn main() {
    // A program on WebView2 that starts this one would hand its own profile down.
    std::env::remove_var("WEBVIEW2_USER_DATA_FOLDER");
    tauri::Builder::default()
        .plugin(plugin())
        .invoke_handler(tauri::generate_handler![life::start_state, life::start_again])
        .setup(|app| {
            setup(app).inspect_err(|error| {
                message::tell(&format!("Daodan non si avvia: {error}."));
            })
        })
        .build(tauri::generate_context!())
        .expect("Daodan failed to start")
        .run(|app, event| {
            // Not before: the window may go to be built again, after its browser process was lost.
            if matches!(event, RunEvent::Exit) {
                close(app);
            }
            on_run_event(app, event);
        });
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeSet;
    use tauri::utils::acl::{capability::Capability, RemoteUrlPattern};

    fn capability() -> Capability {
        serde_json::from_str(include_str!("../capabilities/main.json")).unwrap()
    }

    fn granted(capability: &Capability) -> BTreeSet<&str> {
        capability
            .permissions
            .iter()
            .map(|permission| permission.identifier().get())
            .collect()
    }

    #[test]
    fn the_page_inside_has_two_commands_more_and_no_address_has_them() {
        let start: Capability =
            serde_json::from_str(include_str!("../capabilities/start.json")).unwrap();
        assert!(start.local && start.remote.is_none());
        assert_eq!(start.windows, ["main"]);
        let main = capability();
        let mut wanted = granted(&main);
        wanted.extend(["allow-start-state", "allow-start-again"]);
        assert_eq!(granted(&start), wanted);
    }

    #[test]
    fn the_capability_is_for_the_server_on_the_loopback_alone() {
        let capability = capability();
        assert!(!capability.local);
        let urls: Vec<RemoteUrlPattern> = capability
            .remote
            .unwrap()
            .urls
            .iter()
            .map(|url| url.parse().unwrap())
            .collect();
        let allows = |url: &str| {
            let url = url.parse().unwrap();
            urls.iter().any(|pattern| pattern.test(&url))
        };
        assert!(allows("http://127.0.0.1:50123/"));
        assert!(allows("http://127.0.0.1:50123/app/?token=x"));
        for other in [
            "https://127.0.0.1:50123/",
            "http://localhost:50123/",
            "http://localhost.evil:50123/",
            "http://127.0.0.2:50123/",
            "http://127.0.0.1.evil.test:50123/",
            "http://evil.test/?http://127.0.0.1:50123/",
            "http://tauri.localhost/",
        ] {
            assert!(!allows(other), "{other}");
        }
    }

    #[test]
    fn the_capability_grants_the_window_and_nothing_else() {
        let capability = capability();
        assert_eq!(capability.windows, ["main"]);
        let wanted = BTreeSet::from([
            "core:event:allow-listen",
            "core:event:allow-unlisten",
            "core:webview:allow-set-webview-zoom",
            "core:window:allow-close",
            "core:window:allow-internal-toggle-maximize",
            "core:window:allow-is-maximized",
            "core:window:allow-minimize",
            "core:window:allow-start-dragging",
            "core:window:allow-toggle-maximize",
            "imago-shell:default",
        ]);
        assert_eq!(granted(&capability), wanted);
    }
}
