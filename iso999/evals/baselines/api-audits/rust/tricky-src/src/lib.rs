//! Probe crate with item names chosen to exercise index filing rules.
#![allow(non_camel_case_types, non_snake_case, non_upper_case_globals, dead_code, uncommon_codepoints, confusable_idents, mixed_script_confusables)]

// ---- case variants (8.1-01) ----
pub struct Zebra;
pub struct apple_t;
pub struct Apple;
pub struct APPLE;
pub fn apple() {}
pub fn Apple_fn() {}
pub fn zebra() {}
pub fn aardvark() {}
pub fn Mango() {}
pub const APPLE_C: u8 = 0;
pub const apple_c: u8 = 1;

// ---- digits (8.3-04) ----
pub struct Foo;
pub struct Foo1;
pub struct Foo2;
pub struct Foo9;
pub struct Foo10;
pub struct Foo100;
pub struct FooBar;
pub struct Foo_Bar;
pub fn v2() {}
pub fn v10() {}
pub fn v9_1() {}
pub fn v10_1() {}
pub fn route_9() {}
pub fn route_66() {}
pub fn route_101() {}

// ---- underscores / word boundaries (8.2) ----
pub fn sea_horse() {}
pub fn seaboard() {}
pub fn sea_gull() {}
pub fn seagrass() {}
pub fn foo_bar() {}
pub fn foobar() {}
pub fn foo__baz() {}
pub fn foo() {}
pub fn _leading() {}
pub struct SeaHorse;
pub struct Seaboard;
pub struct Sea_Lion;

// ---- non-ASCII identifiers (8.1-02) ----
pub fn émigré() {}
pub fn école() {}
pub fn ezine() {}
pub fn eagle() {}
pub fn über() {}
pub fn zèbre() {}
pub struct Émigré;
pub struct Ørsted;
pub struct Über;
pub struct Ω;
pub fn ωmega() {}

// ---- raw identifiers ----
pub fn r#match() {}
pub fn r#type() {}

// ---- same name in different modules ----
pub mod alpha {
    /// alpha's widget
    pub struct Widget;
    /// alpha's parse
    pub fn parse() {}
    pub mod inner { pub fn parse() {} pub struct Widget; }
}
pub mod beta {
    /// beta's widget
    pub struct Widget;
    pub fn parse() {}
}
pub mod Gamma { pub fn parse() {} }
pub mod gamma2 { pub fn parse() {} }
pub mod gamma10 { pub fn parse() {} }

// ---- re-exports ----
pub use alpha::Widget as AlphaWidget;
pub use beta::Widget as BetaWidget;
pub use beta::parse as beta_parse;
#[doc(no_inline)]
pub use alpha::inner::parse as inner_parse;
mod hidden { pub struct Hidden; pub fn hidden_fn() {} }
pub use hidden::Hidden;
pub use hidden::hidden_fn;

// ---- deprecated ----
#[deprecated(note = "use apple")]
pub fn old_apple() {}
#[deprecated]
pub struct OldThing;
#[doc(hidden)]
pub fn doc_hidden_fn() {}

// ---- same name, different kinds ----
pub trait Thing {}
pub struct ThingImpl;
pub fn thing() {}
#[macro_export]
macro_rules! thing { () => {}; }
#[macro_export]
macro_rules! Zmacro { () => {}; }
pub type Alias2 = u8;
pub type Alias10 = u8;
pub enum Kind { A, B }
pub union U1 { a: u8 }
pub static STATIC_Z: u8 = 0;
pub static static_a: u8 = 0;
