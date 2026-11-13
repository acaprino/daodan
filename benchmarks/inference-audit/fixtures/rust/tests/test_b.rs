mod util;

#[test]
fn b() {
    util::assert_len("ab", 2);
    let n = util::version("x");
    assert_eq!(n, 1);
}
