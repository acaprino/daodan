//! Daodan's own server as a child process. It prints one line, the address of its page with the
//! token in it, and it ends when its input ends.
//!
//! It runs in a job that ends with this process, so whatever the server started ends too, also when
//! this process is killed. The job lets a process leave it on purpose: the analysis does
//! (`CREATE_BREAKAWAY_FROM_JOB`, `daodan/core/engine_pass.py`), and goes on when the window closes.
use std::{
    fmt, io,
    io::{BufRead, BufReader},
    os::windows::{
        io::{AsRawHandle, FromRawHandle, OwnedHandle},
        process::CommandExt,
    },
    process::{Child, ChildStdin, Command, Stdio},
    sync::mpsc::{channel, Receiver, RecvTimeoutError},
    thread,
    time::Duration,
};
use tauri::Url;
use windows_sys::Win32::System::{
    JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation,
        SetInformationJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
        JOB_OBJECT_LIMIT_BREAKAWAY_OK, JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    },
    Threading::CREATE_NO_WINDOW,
};

/// How long the server may take to print its address.
pub const ANSWER: Duration = Duration::from_secs(60);

/// How long the server may take to end once its input has ended.
pub const GRACE: Duration = Duration::from_secs(5);

/// Why there is no server to show.
#[derive(Debug)]
pub enum Fault {
    NotStarted(io::Error),
    /// It printed nothing in time.
    Silent,
    /// It printed something that is not the address of its page.
    NotAnAddress,
    /// It printed more than its address.
    Twice,
    /// It ended; with its exit code, if it has one.
    Ended(Option<i32>),
}

impl fmt::Display for Fault {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotStarted(error) => write!(f, "Il server di Daodan non si avvia: {error}."),
            Self::Silent => write!(
                f,
                "Il server di Daodan non ha risposto in {} secondi.",
                ANSWER.as_secs()
            ),
            Self::NotAnAddress => f.write_str("Il server di Daodan non ha dato il suo indirizzo."),
            Self::Twice => f.write_str("Il server di Daodan ha dato più del suo indirizzo."),
            Self::Ended(Some(code)) => {
                write!(f, "Il server di Daodan si è chiuso (codice {code}).")
            }
            Self::Ended(None) => f.write_str("Il server di Daodan si è chiuso."),
        }
    }
}

enum Event {
    Line(String),
    Ended(Option<i32>),
}

/// The running server. Dropping it ends the server and what it started at once; [`Server::stop`]
/// lets it end by itself first.
pub struct Server {
    input: ChildStdin,
    ended: Receiver<()>,
    job: OwnedHandle,
}

impl Server {
    /// Starts `command` in a job of its own, with a console that has no window, so that the programs
    /// the server starts open none either.
    pub fn start(command: &mut Command) -> Result<(Self, Output), Fault> {
        let mut child = command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .creation_flags(CREATE_NO_WINDOW)
            .spawn()
            .map_err(Fault::NotStarted)?;
        // The server starts nothing before its interpreter has started: the job comes in time.
        let job = job_of(&child).map_err(|error| {
            let _ = child.kill();
            Fault::NotStarted(error)
        })?;
        let (Some(input), Some(output)) = (child.stdin.take(), child.stdout.take()) else {
            unreachable!("both were asked for");
        };
        let (said, events) = channel();
        let reader = said.clone();
        thread::spawn(move || {
            for line in BufReader::new(output).lines().map_while(Result::ok) {
                if reader.send(Event::Line(line)).is_err() {
                    break;
                }
            }
        });
        let (ending, ended) = channel();
        thread::spawn(move || {
            let code = child.wait().ok().and_then(|status| status.code());
            let _ = said.send(Event::Ended(code));
            let _ = ending.send(());
        });
        Ok((Self { input, ended, job }, Output(events)))
    }

    /// Ends the server's input, and after `grace` whatever of it is left in the job.
    pub fn stop(self, grace: Duration) {
        drop(self.input);
        let _ = self.ended.recv_timeout(grace);
        drop(self.job);
    }
}

/// What the server says: its address, then nothing until it ends.
pub struct Output(Receiver<Event>);

impl Output {
    /// The address of the page, waited for at most `limit`.
    pub fn address(&self, limit: Duration) -> Result<Url, Fault> {
        match self.0.recv_timeout(limit) {
            Ok(Event::Line(line)) => page(&line).ok_or(Fault::NotAnAddress),
            Ok(Event::Ended(code)) => Err(Fault::Ended(code)),
            Err(RecvTimeoutError::Timeout) => Err(Fault::Silent),
            Err(RecvTimeoutError::Disconnected) => Err(Fault::Ended(None)),
        }
    }

    /// Blocks until the server ends or says something more.
    pub fn fault(&self) -> Fault {
        match self.0.recv() {
            Ok(Event::Line(_)) => Fault::Twice,
            Ok(Event::Ended(code)) => Fault::Ended(code),
            Err(_) => Fault::Ended(None),
        }
    }
}

/// `line` as the address of the App's page, `http://127.0.0.1:<port>/app/?token=…`, and no other.
fn page(line: &str) -> Option<Url> {
    let url = Url::parse(line).ok()?;
    let token = url.query()?.strip_prefix("token=")?;
    let own = url.scheme() == "http"
        && url.host_str() == Some("127.0.0.1")
        && url.port().is_some_and(|port| port != 0)
        && url.username().is_empty()
        && url.password().is_none()
        && url.path() == "/app/"
        && url.fragment().is_none();
    (own && !token.is_empty() && !token.contains('&')).then_some(url)
}

/// A job with `child` in it, which ends with its handle.
fn job_of(child: &Child) -> io::Result<OwnedHandle> {
    // SAFETY: `info` is a plain structure that lives through the call, of the size that is said;
    // the job's handle is owned here from the moment it is known to be one.
    unsafe {
        let job = CreateJobObjectW(std::ptr::null(), std::ptr::null());
        if job.is_null() {
            return Err(io::Error::last_os_error());
        }
        let owned = OwnedHandle::from_raw_handle(job);
        let mut info: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = std::mem::zeroed();
        info.BasicLimitInformation.LimitFlags =
            JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_BREAKAWAY_OK;
        let set = SetInformationJobObject(
            job,
            JobObjectExtendedLimitInformation,
            (&raw const info).cast(),
            std::mem::size_of_val(&info) as u32,
        );
        if set == 0 || AssignProcessToJobObject(job, child.as_raw_handle()) == 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(owned)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::{fs, path::Path, time::Instant};
    use windows_sys::Win32::{
        Foundation::{CloseHandle, WAIT_TIMEOUT},
        System::Threading::{
            OpenProcess, TerminateProcess, WaitForSingleObject, PROCESS_SYNCHRONIZE,
            PROCESS_TERMINATE,
        },
    };

    const SOON: Duration = Duration::from_secs(20);

    /// The fake server (`examples/fake_server.rs`), which Cargo builds with the tests, doing `what`.
    fn fake(what: &str) -> Command {
        let tests = std::env::current_exe().unwrap();
        let built = tests.parent().and_then(Path::parent).unwrap();
        let mut command = Command::new(built.join("examples").join("fake_server.exe"));
        command.env("FAKE_SERVER", what);
        command
    }

    /// Whether the process `pid` still runs, waited for at most `limit` to end.
    fn runs(pid: u32, limit: Duration) -> bool {
        // SAFETY: the handle is closed here and used only before that.
        unsafe {
            let handle = OpenProcess(PROCESS_SYNCHRONIZE, 0, pid);
            if handle.is_null() {
                return false;
            }
            let waited = WaitForSingleObject(handle, limit.as_millis() as u32);
            CloseHandle(handle);
            waited == WAIT_TIMEOUT
        }
    }

    fn end(pid: u32) {
        // SAFETY: as above.
        unsafe {
            let handle = OpenProcess(PROCESS_TERMINATE, 0, pid);
            TerminateProcess(handle, 0);
            CloseHandle(handle);
        }
    }

    /// The processes the fake server named in `file`.
    fn pids(file: &Path) -> Vec<u32> {
        let said = fs::read_to_string(file).unwrap();
        said.split_whitespace()
            .map(|pid| pid.parse().unwrap())
            .collect()
    }

    #[test]
    fn only_the_page_of_the_app_on_the_loopback_is_an_address() {
        let own = "http://127.0.0.1:50123/app/?token=a-b_c";
        assert_eq!(page(own).unwrap().as_str(), own);
        for other in [
            "",
            "Traceback (most recent call last):",
            "https://127.0.0.1:50123/app/?token=x",
            "http://localhost:50123/app/?token=x",
            "http://127.0.0.2:50123/app/?token=x",
            "http://127.0.0.1.evil.test:50123/app/?token=x",
            "http://127.0.0.1@evil.test:50123/app/?token=x",
            "http://user@127.0.0.1:50123/app/?token=x",
            "http://127.0.0.1/app/?token=x",
            "http://127.0.0.1:0/app/?token=x",
            "http://127.0.0.1:50123/?token=x",
            "http://127.0.0.1:50123/app/",
            "http://127.0.0.1:50123/app/?token=",
            "http://127.0.0.1:50123/app/?token=x&y=1",
            "http://127.0.0.1:50123/app/?token=x#y",
        ] {
            assert!(page(other).is_none(), "{other}");
        }
    }

    #[test]
    fn a_server_that_answers_late_is_waited_for() {
        let (server, output) = Server::start(&mut fake("late")).unwrap();
        assert!(output.address(SOON).is_ok());
        server.stop(GRACE);
        assert!(matches!(output.fault(), Fault::Ended(Some(0))));
    }

    #[test]
    fn a_server_that_prints_nothing_is_silent() {
        let (server, output) = Server::start(&mut fake("never")).unwrap();
        let answer = output.address(Duration::from_millis(500));
        assert!(matches!(answer, Err(Fault::Silent)), "{answer:?}");
        server.stop(GRACE);
    }

    #[test]
    fn a_server_that_dies_is_told_with_its_code() {
        let (_server, output) = Server::start(&mut fake("die")).unwrap();
        let answer = output.address(SOON);
        assert!(matches!(answer, Err(Fault::Ended(Some(3)))), "{answer:?}");
    }

    #[test]
    fn a_server_that_prints_something_else_has_no_address() {
        let (_server, output) = Server::start(&mut fake("other")).unwrap();
        let answer = output.address(SOON);
        assert!(matches!(answer, Err(Fault::NotAnAddress)), "{answer:?}");
    }

    #[test]
    fn a_server_that_prints_twice_is_told() {
        let (_server, output) = Server::start(&mut fake("twice")).unwrap();
        assert!(output.address(SOON).is_ok());
        assert!(matches!(output.fault(), Fault::Twice));
    }

    #[test]
    fn a_program_that_is_not_there_is_not_started() {
        let started = Server::start(&mut Command::new(r"C:\no\such\python.exe"));
        assert!(matches!(started, Err(Fault::NotStarted(_))));
    }

    // Not under `cargo test`: the job Cargo puts its tests in lets nothing leave it, so the fake
    // server could not start the child that does. The workflow starts the test program by itself.
    #[test]
    fn stopping_ends_the_server_and_what_it_started_and_not_what_left_the_job() {
        let folder = tempfile::tempdir().unwrap();
        let said = folder.path().join("pids");
        let (server, output) = Server::start(fake("children").env("FAKE_PIDS", &said)).unwrap();
        output.address(SOON).unwrap();
        let pids = pids(&said);
        let &[own, kept, left] = pids.as_slice() else {
            panic!("{pids:?}");
        };
        for pid in [own, kept, left] {
            assert!(runs(pid, Duration::ZERO), "{pid} of {pids:?}");
        }
        server.stop(GRACE);
        assert!(!runs(own, SOON), "the server");
        assert!(!runs(kept, SOON), "what it started");
        let lives = runs(left, Duration::from_secs(1));
        end(left);
        assert!(lives, "what left the job on purpose");
    }

    #[test]
    fn a_server_that_does_not_end_by_itself_is_ended() {
        let folder = tempfile::tempdir().unwrap();
        let said = folder.path().join("pids");
        let (server, output) = Server::start(fake("deaf").env("FAKE_PIDS", &said)).unwrap();
        output.address(SOON).unwrap();
        let own = pids(&said)[0];
        let (grace, before) = (Duration::from_millis(500), Instant::now());
        server.stop(grace);
        assert!(before.elapsed() >= grace);
        assert!(!runs(own, SOON));
    }
}
