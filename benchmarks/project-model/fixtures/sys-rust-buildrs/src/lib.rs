//! Bytecode opcodes; the enum itself is written by build.rs.

include!(concat!(env!("OUT_DIR"), "/opcodes.rs"));

/// "true" when the compiler that built this crate is 1.80 or newer.
pub const MODERN_RUSTC: &str = env!("OPCODES_MODERN_RUSTC");

impl Opcode {
    /// The numeric code of the opcode.
    pub fn code(self) -> u8 {
        self as u8
    }
}
