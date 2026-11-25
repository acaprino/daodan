//! A server that behaves as `FAKE_SERVER` says, in place of Daodan's: for the tests of `src/server.rs`,
//! and for the smoke of the whole program (`apps/desktop/smoke.ps1`), as its `runtime/python.exe`.
use std::{
    env, fs,
    io::{self, Read, Write},
    net::TcpListener,
    os::windows::process::CommandExt,
    process::{exit, id, Command, Stdio},
    thread,
    time::Duration,
};

const CREATE_BREAKAWAY_FROM_JOB: u32 = 0x0100_0000;
const CREATE_NO_WINDOW: u32 = 0x0800_0000;

/// Longer than any test, so that a process that is not ended is seen; not for ever.
const LONG: Duration = Duration::from_secs(150);

/// A page on a free port, and the line that says its address.
fn serve() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    thread::spawn(move || {
        for mut stream in listener.incoming().flatten() {
            let page = "<!doctype html><title>fake</title><p>fake";
            let _ = stream.read(&mut [0; 4096]);
            let _ = write!(
                stream,
                "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {}\r\n\r\n{page}",
                page.len()
            );
        }
    });
    println!("http://127.0.0.1:{port}/app/?token=fake");
}

/// This program again, which only waits, started with `flags` more.
fn child(flags: u32) -> u32 {
    Command::new(env::current_exe().unwrap())
        .env("FAKE_SERVER", "wait")
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .creation_flags(CREATE_NO_WINDOW | flags)
        .spawn()
        .unwrap()
        .id()
}

/// Names the processes to look at in the file `FAKE_PIDS`.
fn name(pids: &[u32]) {
    let pids: Vec<String> = pids.iter().map(u32::to_string).collect();
    fs::write(env::var_os("FAKE_PIDS").unwrap(), pids.join(" ")).unwrap();
}

fn main() {
    match env::var("FAKE_SERVER").as_deref() {
        Ok("wait") => return thread::sleep(LONG),
        Ok("never") => {}
        Ok("die") => exit(3),
        Ok("other") => println!("Traceback (most recent call last):"),
        Ok("late") => {
            thread::sleep(Duration::from_millis(700));
            serve();
        }
        Ok("twice") => {
            serve();
            thread::sleep(Duration::from_secs(2));
            println!("one line more");
        }
        Ok("children") => {
            name(&[id(), child(0), child(CREATE_BREAKAWAY_FROM_JOB)]);
            serve();
        }
        Ok("deaf") => {
            name(&[id()]);
            serve();
            thread::sleep(LONG);
        }
        other => panic!("FAKE_SERVER: {other:?}"),
    }
    let _ = io::copy(&mut io::stdin(), &mut io::sink());
}
