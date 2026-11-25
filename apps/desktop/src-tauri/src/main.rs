//! Daodan's window: its own server, started hidden from the Python beside this program, and the page
//! the server serves in a window that `imago-shell` opens and watches.
#![cfg_attr(not(test), windows_subsystem = "windows")]

mod message;
mod server;

use imago_shell::{
    on_run_event, open_main, plugin, show_main,
    single_instance::{launch, Launch, Quitting},
    Material, Options, DARK_GROUND, LIGHT_GROUND,
};
use server::{Fault, Output, Server, ANSWER, GRACE};
use std::{
    error::Error,
    fs::{self, File},
    path::{Path, PathBuf},
    process::{exit, Command},
    sync::{Mutex, PoisonError},
    thread,
};
use tauri::{App, AppHandle, Manager, RunEvent, Url, WebviewUrl};

/// The port of the last start, in the data folder: the same origin again, so that what the pages
/// keep in the browser's storage is there at the next start.
const PORT_FILE: &str = "server-port";

/// What the server says of itself, in the data folder.
const LOG_FILE: &str = "server.log";

/// The server while the window shows it. Whoever takes it out ends it.
struct Running {
    server: Mutex<Option<Server>>,
    data: PathBuf,
}

impl Running {
    fn take(&self) -> Option<Server> {
        self.server
            .lock()
            .unwrap_or_else(PoisonError::into_inner)
            .take()
    }
}

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
    let (server, output, page) = match serve(&data) {
        Ok(served) => served,
        Err(fault) => {
            message::tell(&said(&fault, &data));
            exit(1);
        }
    };
    options.material = Material::Opaque {
        dark: DARK_GROUND,
        light: LIGHT_GROUND,
    };
    options.origins.allow(page.as_str());
    options.window.url = WebviewUrl::External(page);
    options.data_dir = Some(data.clone());
    options.reload_label = "Ricarica l'interfaccia".into();
    options.stopped_message = "L'interfaccia non risponde. Ricaricarla?".into();
    options.lost_message = "La finestra non si può ripristinare. Daodan si chiude.".into();
    app.manage(Running {
        server: Mutex::new(Some(server)),
        data,
    });
    open_main(app.handle(), options)?;
    let watched = app.handle().clone();
    thread::spawn(move || watch(&watched, &output));
    Ok(())
}

/// Starts the server and waits for the address of its page.
fn serve(data: &Path) -> Result<(Server, Output, Url), Fault> {
    let log = fs::create_dir_all(data)
        .and_then(|()| File::create(data.join(LOG_FILE)))
        .map_err(Fault::NotStarted)?;
    let python = std::env::current_exe()
        .map(|program| program.with_file_name("runtime").join("python.exe"))
        .map_err(Fault::NotStarted)?;
    let port = fs::read_to_string(data.join(PORT_FILE))
        .ok()
        .and_then(|kept| kept.trim().parse::<u16>().ok())
        .unwrap_or(0);
    // `-I`: the server imports nothing from the folder it is started in, from the environment or
    // from the person's own Python packages. The programs it starts get the same from the variables.
    let (server, output) = Server::start(
        Command::new(python)
            .args(["-I", "-m", "daodan", "app", "--desktop", "--port"])
            .arg(port.to_string())
            .current_dir(data)
            .env_remove("PYTHONHOME")
            .env_remove("PYTHONPATH")
            .env("PYTHONNOUSERSITE", "1")
            .stderr(log),
    )?;
    let page = output.address(ANSWER)?;
    if let Some(port) = page.port() {
        // A port that cannot be kept costs the next start its storage, never this one.
        let _ = fs::write(data.join(PORT_FILE), port.to_string());
    }
    Ok((server, output, page))
}

/// Waits for the server to fail. One that was told to stop is not a failure.
fn watch(app: &AppHandle, output: &Output) {
    let fault = output.fault();
    let running = app.state::<Running>();
    if let Some(server) = running.take() {
        message::tell(&said(&fault, &running.data));
        server.stop(GRACE);
        app.exit(1);
    }
}

fn said(fault: &Fault, data: &Path) -> String {
    let log = data.join(LOG_FILE);
    format!("{fault}\n\nIl registro è in:\n{}", log.display())
}

/// The window is gone: the server ends, and a copy started meanwhile waits for it.
fn close(app: &AppHandle) {
    let Some(running) = app.try_state::<Running>() else {
        return;
    };
    let _quitting = Quitting::mark(&running.data);
    if let Some(server) = running.take() {
        server.stop(GRACE);
    }
}

fn main() {
    // A program on WebView2 that starts this one would hand its own profile down.
    std::env::remove_var("WEBVIEW2_USER_DATA_FOLDER");
    tauri::Builder::default()
        .plugin(plugin())
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
    use super::*;
    use std::collections::BTreeSet;
    use tauri::utils::acl::{capability::Capability, RemoteUrlPattern};

    fn capability() -> Capability {
        serde_json::from_str(include_str!("../capabilities/main.json")).unwrap()
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
        let granted: BTreeSet<&str> = capability
            .permissions
            .iter()
            .map(|permission| permission.identifier().get())
            .collect();
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
        assert_eq!(granted, wanted);
    }

    #[test]
    fn a_fault_says_where_the_log_is() {
        let said = said(&Fault::Silent, Path::new(r"C:\dati"));
        assert!(said.contains("60 secondi") && said.contains(r"C:\dati\server.log"));
    }
}
