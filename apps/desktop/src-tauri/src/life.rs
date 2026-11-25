//! The life of the server behind the window. While there is no server to show, the page inside the
//! program says so; a server that dies is started again, and the window goes back to the screen the
//! person was on.
use crate::server::{Fault, Output, Server, ANSWER, GRACE};
use imago_shell::Origins;
use std::{
    collections::VecDeque,
    fs::{self, OpenOptions},
    path::{Path, PathBuf},
    process::Command,
    sync::{Mutex, MutexGuard, PoisonError},
    thread,
    time::{Duration, Instant},
};
use tauri::{AppHandle, Emitter, Manager, Url};

/// The port of the last start, in the data folder: the same origin again, so that what the pages
/// keep in the browser's storage is there at the next start.
const PORT_FILE: &str = "server-port";

/// What the server says of itself, in the data folder.
const LOG_FILE: &str = "server.log";

/// The page inside the program.
const START: &str = "http://tauri.localhost/";

/// The event that tells that page to ask for the state again.
const CHANGED: &str = "server-state";

/// How many times a server that died is started again by itself in one [`PERIOD`].
const LIMIT: usize = 3;
const PERIOD: Duration = Duration::from_secs(60);

/// What the page inside the program says, and the address of the server's page once there is one.
enum Phase {
    Starting,
    /// It died, and is being started again.
    Restarting(String),
    /// It did not start: the person is asked.
    Failed(String),
    /// It died too often: the person is asked.
    Stopped(String),
    Up(Url),
}

impl Phase {
    fn told(&self) -> (&'static str, String) {
        match self {
            Self::Starting | Self::Up(_) => ("starting", String::new()),
            Self::Restarting(cause) => ("restarting", cause.clone()),
            Self::Failed(cause) => ("failed", cause.clone()),
            Self::Stopped(cause) => ("stopped", cause.clone()),
        }
    }
}

struct Life {
    phase: Phase,
    /// Whoever takes it out ends it.
    server: Option<Server>,
    /// Where the person was when the server died.
    place: Option<Url>,
    closing: bool,
}

pub struct Daodan {
    data: PathBuf,
    origins: Origins,
    life: Mutex<Life>,
}

impl Daodan {
    /// `origins` are those of the window: the server's is added once it has answered.
    pub fn new(data: PathBuf, origins: Origins) -> Self {
        let life = Life {
            phase: Phase::Starting,
            server: None,
            place: None,
            closing: false,
        };
        Self {
            data,
            origins,
            life: Mutex::new(life),
        }
    }

    pub fn data(&self) -> &Path {
        &self.data
    }

    /// Never held while the window is asked something: its thread takes it too.
    fn life(&self) -> MutexGuard<'_, Life> {
        self.life.lock().unwrap_or_else(PoisonError::into_inner)
    }

    /// Starts the server and waits for the address of its page.
    fn start(&self) -> Result<(Output, Url), Fault> {
        // Appended: what a server that died said stays, until Daodan is started again.
        let log = fs::create_dir_all(&self.data)
            .and_then(|()| {
                OpenOptions::new()
                    .create(true)
                    .append(true)
                    .open(self.data.join(LOG_FILE))
            })
            .map_err(Fault::NotStarted)?;
        let python = std::env::current_exe()
            .map(|program| program.with_file_name("runtime").join("python.exe"))
            .map_err(Fault::NotStarted)?;
        let port = fs::read_to_string(self.data.join(PORT_FILE))
            .ok()
            .and_then(|kept| kept.trim().parse::<u16>().ok())
            .unwrap_or(0);
        // `-I`: the server imports nothing from the folder it is started in, from the environment or
        // from the person's own Python packages. The programs it starts get the same from the variables.
        let (server, output) = Server::start(
            Command::new(python)
                .args(["-I", "-m", "daodan", "app", "--desktop", "--port"])
                .arg(port.to_string())
                .current_dir(&self.data)
                .env_remove("PYTHONHOME")
                .env_remove("PYTHONPATH")
                .env("PYTHONNOUSERSITE", "1")
                .stderr(log),
        )?;
        {
            let mut life = self.life();
            if life.closing {
                return Err(Fault::Ended(None));
            }
            life.server = Some(server);
        }
        let page = output.address(ANSWER)?;
        if let Some(port) = page.port() {
            // A port that cannot be kept costs the next start its storage, never this one.
            let _ = fs::write(self.data.join(PORT_FILE), port.to_string());
        }
        Ok((output, page))
    }

    /// The server answers: the window goes to its page, where the person was if it is started again.
    fn up(&self, app: &AppHandle, page: &Url) {
        self.origins.allow(page.as_str());
        let page = {
            let mut life = self.life();
            let page = match life.place.take() {
                Some(place) => again(&place, page),
                None => page.clone(),
            };
            life.phase = Phase::Up(page.clone());
            page
        };
        show(app, page);
    }

    /// There is no server: the window goes to the page inside the program. False when Daodan is
    /// closing, which is why there is none.
    fn down(&self, app: &AppHandle, phase: Phase) -> bool {
        let at = app
            .get_webview_window("main")
            .and_then(|window| window.url().ok());
        let server = {
            let mut life = self.life();
            if life.closing {
                return false;
            }
            if let (Phase::Up(page), Some(at)) = (&life.phase, &at) {
                if at.origin() == page.origin() {
                    life.place = Some(at.clone());
                }
            }
            life.phase = phase;
            life.server.take()
        };
        // One that is silent, or says too much, still runs.
        if let Some(server) = server {
            server.stop(GRACE);
        }
        if let Ok(start) = Url::parse(START) {
            if at.is_some_and(|at| at.origin() != start.origin()) {
                show(app, start);
            }
        }
        let _ = app.emit_to("main", CHANGED, ());
        true
    }

    /// The program closes: the server ends.
    pub fn close(&self) {
        let server = {
            let mut life = self.life();
            life.closing = true;
            life.server.take()
        };
        if let Some(server) = server {
            server.stop(GRACE);
        }
    }
}

fn show(app: &AppHandle, page: Url) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.navigate(page);
    }
}

/// Empties the log, for a start of the program.
pub fn new_log(data: &Path) {
    let _ = fs::write(data.join(LOG_FILE), "");
}

/// Starts the server, shows it, and starts it again when it dies, until it does not start, dies too
/// often or the program closes. It blocks until then.
pub fn keep(app: &AppHandle) {
    let daodan = app.state::<Daodan>();
    let mut restarts = Restarts::default();
    loop {
        let output = match daodan.start() {
            Ok((output, page)) => {
                daodan.up(app, &page);
                output
            }
            Err(fault) => {
                daodan.down(app, Phase::Failed(said(&fault, &daodan.data)));
                return;
            }
        };
        let fault = output.fault();
        let goes_on = restarts.allow(Instant::now());
        let phase = if goes_on {
            Phase::Restarting(fault.to_string())
        } else {
            Phase::Stopped(said(&fault, &daodan.data))
        };
        if !daodan.down(app, phase) || !goes_on {
            return;
        }
    }
}

/// What the page inside the program says: the state, and its cause. With the server there, the
/// window goes to it: it may have answered before there was a window.
#[tauri::command(async)]
pub fn start_state(app: AppHandle) -> (&'static str, String) {
    let daodan = app.state::<Daodan>();
    let (told, page) = {
        let life = daodan.life();
        let page = match &life.phase {
            Phase::Up(page) => Some(page.clone()),
            _ => None,
        };
        (life.phase.told(), page)
    };
    if let Some(page) = page {
        show(&app, page);
    }
    told
}

/// The person asked for the server again.
#[tauri::command(async)]
pub fn start_again(app: AppHandle) {
    {
        let daodan = app.state::<Daodan>();
        let mut life = daodan.life();
        if !matches!(life.phase, Phase::Failed(_) | Phase::Stopped(_)) {
            return;
        }
        life.phase = Phase::Starting;
    }
    let _ = app.emit_to("main", CHANGED, ());
    thread::spawn(move || keep(&app));
}

fn said(fault: &Fault, data: &Path) -> String {
    let log = data.join(LOG_FILE);
    format!("{fault}\n\nIl registro è in:\n{}", log.display())
}

/// Where the person was, at the address the server has now: its port and its token.
fn again(place: &Url, page: &Url) -> Url {
    let mut again = page.clone();
    again.set_path(place.path());
    again.set_fragment(place.fragment());
    let others = place.query_pairs().filter(|(name, _)| name != "token");
    again.query_pairs_mut().extend_pairs(others);
    again
}

/// The times the server was started again by itself in the last minute.
#[derive(Default)]
struct Restarts(VecDeque<Instant>);

impl Restarts {
    /// Whether it may be started again at `now`. If it may, it is counted.
    fn allow(&mut self, now: Instant) -> bool {
        self.0.retain(|at| now.duration_since(*at) < PERIOD);
        let allowed = self.0.len() < LIMIT;
        if allowed {
            self.0.push_back(now);
        }
        allowed
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn four_deaths_in_a_minute_stop_at_the_question() {
        let mut restarts = Restarts::default();
        let start = Instant::now();
        let mut dies = |second| restarts.allow(start + Duration::from_secs(second));
        assert!(dies(0) && dies(1) && dies(2), "three are started again");
        assert!(!dies(3), "the fourth is asked about");
        assert!(dies(60), "a minute after the first, one more is");
        assert!(!dies(60));
    }

    #[test]
    fn the_same_screen_has_the_port_and_the_token_of_now() {
        let page = Url::parse("http://127.0.0.1:50124/app/?token=new").unwrap();
        for (place, wanted) in [
            (
                "http://127.0.0.1:50123/app/?token=old",
                "http://127.0.0.1:50124/app/?token=new",
            ),
            (
                "http://127.0.0.1:50123/?token=old&run=a%20b#c",
                "http://127.0.0.1:50124/?token=new&run=a+b#c",
            ),
        ] {
            let place = Url::parse(place).unwrap();
            assert_eq!(again(&place, &page).as_str(), wanted);
        }
    }

    #[test]
    fn a_fault_says_where_the_log_is() {
        let said = said(&Fault::Silent, Path::new(r"C:\dati"));
        assert!(said.contains("60 secondi") && said.contains(r"C:\dati\server.log"));
    }

    #[test]
    fn the_address_of_the_server_is_not_told_to_the_page() {
        let page = Url::parse("http://127.0.0.1:50124/app/?token=secret").unwrap();
        assert_eq!(Phase::Up(page).told(), ("starting", String::new()));
        let stopped = Phase::Stopped("perché".into());
        assert_eq!(stopped.told(), ("stopped", "perché".into()));
    }
}
