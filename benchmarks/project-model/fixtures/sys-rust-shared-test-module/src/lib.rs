//! Counts words.

/// Number of whitespace-separated words in `text`.
pub fn words(text: &str) -> usize {
    text.split_whitespace().count()
}
