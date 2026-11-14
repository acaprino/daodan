cfg_if::cfg_if! {
    if #[cfg(debug_assertions)] {
        const MODE: &str = "debug";
    } else {
        const MODE: &str = "release";
    }
}

fn main() {
    println!("{MODE}: {}%", helper::percent(140));
}
