pub fn version(text: &str) -> usize {
    fxrs::parse(text)
}

pub fn assert_len(text: &str, len: usize) {
    assert_eq!(version(text), len);
}
