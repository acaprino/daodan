pub fn invoice_total(lines: &[(u32, u64)]) -> u64 {
    lines.iter().map(|(qty, cents)| u64::from(*qty) * cents).sum()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sums_lines() {
        assert_eq!(invoice_total(&[(2, 150), (1, 100)]), 400);
    }
}
