//! Helpers shared by the integration tests. This file is not a test
//! target: Cargo only turns files directly under tests/ into targets.

/// A fixed sample text.
pub fn sample() -> &'static str {
    "one two  three"
}

/// Asserts that `text` has `n` words.
pub fn assert_words(text: &str, n: usize) {
    assert_eq!(tally::words(text), n, "{text:?}");
}
