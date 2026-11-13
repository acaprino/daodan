mod util;

use crate::util::assert_len;

#[test]
fn a() {
    assert_len("ab", 2);
    let n = util::version("abc");
    assert_eq!(n, 3);
}
