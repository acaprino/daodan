mod util;

#[test]
fn counts_empty() {
    util::assert_words("", 0);
    assert!(!util::sample().is_empty());
}
