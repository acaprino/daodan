//! Byte scanning with optional fast paths.
#![cfg_attr(not(feature = "std"), no_std)]

/// Position of the first newline in `haystack`.
pub fn first_newline(haystack: &[u8]) -> Option<usize> {
    #[cfg(feature = "fast")]
    {
        memchr::memchr(b'\n', haystack)
    }
    #[cfg(not(feature = "fast"))]
    {
        haystack.iter().position(|&b| b == b'\n')
    }
}

/// Writes `n` in decimal into `buf` and returns the text.
#[cfg(feature = "itoa")]
pub fn int_text(buf: &mut itoa::Buffer, n: i64) -> &str {
    buf.format(n)
}

/// Writes `x` in shortest decimal form into `buf` and returns the text.
#[cfg(feature = "float")]
pub fn float_text(buf: &mut ryu::Buffer, x: f64) -> &str {
    buf.format(x)
}
