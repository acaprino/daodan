//! Ledger entries and their formatting.

use ledger_macros::Describe;

cfg_if::cfg_if! {
    if #[cfg(windows)] {
        /// Line ending used in exported ledgers.
        pub const EOL: &str = "\r\n";
    } else {
        /// Line ending used in exported ledgers.
        pub const EOL: &str = "\n";
    }
}

/// One ledger entry, amount in cents.
#[derive(Describe)]
pub struct Entry {
    pub amount: u64,
}

impl Entry {
    /// Formats the entry as one exported line.
    pub fn line(&self) -> String {
        let mut buf = itoa::Buffer::new();
        format!("{} {}{}", Self::describe(), buf.format(self.amount), EOL)
    }
}
