mod util;

#[test]
fn counts_sample() {
    util::assert_words(util::sample(), 3);
}
