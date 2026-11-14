//! Formats counters without allocating twice.

/// Returns `n` followed by its unit.
pub fn with_unit(n: u64, unit: &str) -> String {
    let mut buf = itoa::Buffer::new();
    format!("{} {}", buf.format(n), unit)
}
