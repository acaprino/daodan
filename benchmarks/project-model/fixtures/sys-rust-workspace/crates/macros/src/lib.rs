//! Derive macros for ledger types, written on proc_macro alone.

use proc_macro::{TokenStream, TokenTree};

/// Derives `fn describe() -> &'static str` returning the type name.
#[proc_macro_derive(Describe)]
pub fn derive_describe(input: TokenStream) -> TokenStream {
    let mut tokens = input.into_iter();
    let mut name = None;
    while let Some(tt) = tokens.next() {
        if let TokenTree::Ident(id) = &tt {
            let s = id.to_string();
            if s == "struct" || s == "enum" {
                if let Some(TokenTree::Ident(n)) = tokens.next() {
                    name = Some(n.to_string());
                }
                break;
            }
        }
    }
    let name = name.expect("Describe needs a struct or an enum");
    format!("impl {name} {{ pub fn describe() -> &'static str {{ \"{name}\" }} }}")
        .parse()
        .expect("valid impl block")
}
