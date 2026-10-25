//! Unavailable full-profile operations have no implementation in tiny.
//! Tiny bindings cannot dispatch these commands; shared prompt/state code
//! references the same methods, keeping retained behavior in one place.
use crate::editor::*;
impl Editor {
    pub fn scroll_horizontal(&mut self, _right: bool) {}
    pub fn paragraph_move(&mut self, _down: bool) {}
    pub fn chop(&mut self, _right: bool) {}
    pub fn indent(&mut self, _unindent: bool) {}
    pub fn comment(&mut self) {}
    pub fn complete_word(&mut self) {}
    pub fn anchor(&mut self, _next: bool) {}
    pub fn word_count(&mut self) {}
    pub fn hard_wrap(&mut self) {}
    pub fn justify(&mut self, _full: bool) {}
    pub fn help_key(&mut self, _h: HelpState, _key: crate::input::Key, _fun: &str) {}
    pub fn help_find(&mut self, _h: HelpState, _back: bool) {}
    pub fn open_browser(&mut self, _p: Prompt) {}
    pub fn refresh_browser(&mut self) {}
    pub fn browser_key(&mut self, _b: BrowserState, _key: crate::input::Key, _fun: &str) {}
    pub fn mouse(&mut self) {}
    pub fn load_history(&mut self) {}
    pub fn save_history(&mut self) {}
    pub fn restore_position(&mut self) {}
    pub fn record_position(&mut self) {}
    pub fn execute(&mut self, _command: Vec<u8>) {}
    pub fn format_tool(&mut self) {}
    pub fn spell(&mut self) {}
    pub fn next_spell(&mut self) {}
    pub fn restore_spell_position(&mut self) {}
    pub fn finish_spell(&mut self) {}
    pub fn lint(&mut self) {}
    pub fn lint_run(&mut self) {}
    pub fn lint_key(&mut self, _l: LintState, _key: crate::input::Key, _fun: &str) {}
    pub fn open_help(&mut self, previous: Mode) {
        self.mode = previous;
        self.msg("^W = Ctrl+W    M-W = Alt+W", 1);
    }
}
