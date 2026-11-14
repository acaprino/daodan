use std::sync::LazyLock;

// LazyLock is stable since Rust 1.80, hence rust-version = "1.80".
static GREETING: LazyLock<String> = LazyLock::new(|| format!("pinned {}", env!("CARGO_PKG_VERSION")));

fn main() {
    println!("{}", *GREETING);
}
