use std::env;
use std::fs;
use std::path::Path;

fn main() {
    println!("cargo:rerun-if-changed=opcodes.txt");
    let spec = fs::read_to_string("opcodes.txt").expect("read opcodes.txt");
    let mut out = String::from(
        "/// Opcodes generated from opcodes.txt.\n#[derive(Debug, Clone, Copy, PartialEq, Eq)]\npub enum Opcode {\n",
    );
    for line in spec.lines().map(str::trim) {
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let (name, code) = line.split_once('=').expect("NAME=code");
        out.push_str(&format!("    {} = {},\n", name.trim(), code.trim()));
    }
    out.push_str("}\n");
    let dest = Path::new(&env::var("OUT_DIR").expect("OUT_DIR")).join("opcodes.rs");
    fs::write(dest, out).expect("write opcodes.rs");

    let modern = version_check::is_min_version("1.80.0").unwrap_or(false);
    println!("cargo:rustc-env=OPCODES_MODERN_RUSTC={modern}");
}
