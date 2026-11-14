//! Small helpers kept in a local crate.

/// Clamps `x` to the range 0..=100.
pub fn percent(x: i32) -> i32 {
    x.clamp(0, 100)
}
