use super::*;
use crate::buffer::Buffer;
fn fixture(text: &[u8], pattern: &[u8], regex: bool, back: bool) -> Editor {
    let mut conf = Config::new(false);
    conf.set(CASE_SENSITIVE, true);
    conf.set(USE_REGEXP, regex);
    conf.set(BACKWARDS_SEARCH, back);
    let mut editor = Editor::new(conf);
    editor.buffers.push(Buffer::new(
        Vec::new(),
        text.split(|b| *b == b'\n')
            .map(bytes::encode_nuls)
            .collect(),
    ));
    editor.search = pattern.to_vec();
    editor
}
#[test]
fn capture_and_zero_width_replacement() {
    let mut e = fixture(b"foo Foo FOO\n", b"(f)(o+)", true, false);
    e.conf.set(CASE_SENSITIVE, false);
    e.start_replace(b"<\\2\\1\\3>".to_vec());
    e.replace_answer(true, true);
    assert_eq!(e.b().raw(), b"<oof\\3> <ooF\\3> <OOF\\3>\n");
    let mut e = fixture(b"foo Foo FOO\nbar foo\nbaz\n", b"o*", true, false);
    e.conf.set(CASE_SENSITIVE, false);
    e.start_replace(b"-".to_vec());
    e.replace_answer(true, true);
    assert_eq!(e.b().raw(), b"-f- -F- -F-\n-b-a-r- -f-\n-b-a-z-\n");
    assert!(e.message.as_ref().unwrap().text.contains("16"));
}
#[test]
fn replacement_wrap_direction_region_and_undo() {
    for back in [false, true] {
        let text = b"foo foo foo\nfoo\n";
        let mut e = fixture(text, b"foo", false, back);
        e.bm().state.pos = Pos { line: 0, x: 4 };
        e.start_replace(b"longer".to_vec());
        e.replace_answer(true, true);
        assert_eq!(e.b().raw(), b"longer longer longer\nlonger\n");
        assert_eq!(e.b().pos(), Pos { line: 0, x: 7 });
        if !cfg!(feature = "tiny") {
            for _ in 0..4 {
                assert!(e.bm().undo(false).is_some());
            }
            assert_eq!(e.b().raw(), text);
            for _ in 0..4 {
                assert!(e.bm().undo(true).is_some());
            }
            assert_eq!(e.b().raw(), b"longer longer longer\nlonger\n");
        }
        let mut e = fixture(text, b"foo", false, back);
        e.bm().state.mark = Some(Pos { line: 0, x: 4 });
        e.bm().state.pos = Pos { line: 0, x: 11 };
        e.start_replace(b"z".to_vec());
        e.replace_answer(true, true);
        assert_eq!(e.b().raw(), b"foo z z\nfoo\n");
        assert_eq!(e.b().state.mark, Some(Pos { line: 0, x: 4 }));
    }
}
#[test]
fn interactive_skip_then_all_and_nul_captures() {
    let mut e = fixture(b"foo foo foo\n", b"foo", false, false);
    e.start_replace(b"barbar".to_vec());
    e.replace_answer(false, false);
    e.replace_answer(true, false);
    e.replace_answer(true, true);
    assert_eq!(e.b().raw(), b"foo barbar barbar\n");
    let mut e = fixture(b"x\0y x\0y\n", b"(x.y)", true, false);
    e.start_replace(b"<\\1>".to_vec());
    e.replace_answer(true, true);
    assert_eq!(e.b().raw(), b"<x\0y> <x\0y>\n");
}
#[test]
fn overlapping_backward_and_magic_line_find() {
    let mut e = fixture(b"ababa\n", b"aba", true, true);
    e.bm().state.pos = Pos { line: 0, x: 5 };
    e.find(false);
    assert_eq!(e.b().pos(), Pos { line: 0, x: 2 });
    e.find(false);
    assert_eq!(e.b().pos(), Pos { line: 0, x: 0 });
    let mut e = fixture(b"a\n", b"$", true, false);
    e.find(false);
    assert_eq!(e.b().pos(), Pos { line: 0, x: 1 });
    e.find(false);
    assert_eq!(e.b().pos(), Pos { line: 0, x: 1 });
}
#[test]
fn cancel_search_discards_pending_input_burst() {
    let mut e = fixture(&vec![b'a'; 65536], b"z", false, false);
    e.input.queue.extend([b'x' as i32, 3, b'y' as i32]);
    e.find(false);
    assert_eq!(e.b().pos(), Pos::default());
    assert!(e.input.queue.is_empty());
    assert_eq!(e.message.as_ref().unwrap().text, "Cancelled");
}
#[test]
fn cancel_all_keeps_completed_edits_and_undo_valid() {
    let mut e = fixture(b"a a a\n", b"a", false, false);
    e.start_replace(b"bb".to_vec());
    e.input.queue.push_back(3);
    e.replace_answer(true, true);
    // Cancellation can occur after the currently confirmed replacement.
    assert_eq!(e.b().raw(), b"bb a a\n");
    if !cfg!(feature = "tiny") {
        e.bm().undo(false);
        assert_eq!(e.b().raw(), b"a a a\n");
    }
}
#[test]
fn multiline_replacement_preserves_later_matches() {
    for back in [false, true] {
        let mut e = fixture(b"a a\na a\n", b"a", false, back);
        e.start_replace(b"x\ny".to_vec());
        e.replace_answer(true, true);
        assert_eq!(e.b().raw(), b"x\ny x\ny\nx\ny x\ny\n");
        if !cfg!(feature = "tiny") {
            for _ in 0..4 {
                e.bm().undo(false);
            }
            assert_eq!(e.b().raw(), b"a a\na a\n");
        }
    }
}
#[test]
#[ignore = "bounded resource fixture, run via tests/search/run.py"]
fn stress_find_literal() {
    let mut e = fixture(&vec![b'a'; 2 * 1024 * 1024], b"a", false, false);
    e.find(false);
    assert_eq!(e.b().pos().x, 1);
}
#[test]
#[ignore = "bounded resource fixture, run via tests/search/run.py"]
fn stress_find_regex() {
    let mut e = fixture(&vec![b'a'; 2 * 1024 * 1024], b"(a)", true, false);
    e.find(false);
    assert_eq!(e.b().pos().x, 1);
}
#[test]
#[ignore = "bounded resource fixture, run via tests/search/run.py"]
fn stress_replace_literal() {
    let mut text = vec![b'a'; 200000];
    text.push(b'\n');
    let mut e = fixture(&text, b"a", false, false);
    e.start_replace(b"bb".to_vec());
    e.replace_answer(true, true);
    assert_eq!(e.b().state.lines[0], vec![b'b'; 400000]);
}
#[test]
#[ignore = "bounded resource fixture, run via tests/search/run.py"]
fn stress_replace_regex() {
    let mut text = vec![b'a'; 200000];
    text.push(b'\n');
    let mut e = fixture(&text, b"(a)", true, false);
    e.start_replace(b"\\1\\1".to_vec());
    e.replace_answer(true, true);
    assert_eq!(e.b().state.lines[0], vec![b'a'; 400000]);
}

#[test]
fn multiline_all_after_interactive_and_midline_wrap() {
    for back in [false, true] {
        for interactive in [false, true] {
            let mut e = fixture(b"a a a\na a\n", b"a", false, back);
            e.bm().state.pos = Pos { line: 0, x: 2 };
            e.bm().state.anchors[0] = true;
            let first_gen = e.b().state.generations[0];
            e.start_replace(b"x\ny\nz".to_vec());
            if interactive {
                e.replace_answer(true, false);
            }
            e.replace_answer(true, true);
            assert_eq!(e.b().raw(), b"x\ny\nz x\ny\nz x\ny\nz\nx\ny\nz x\ny\nz\n");
            assert!(e.b().state.anchors[0]);
            assert_eq!(e.b().state.generations[0], first_gen);
            assert_eq!(e.b().state.anchors.iter().filter(|v| **v).count(), 1);
            if !cfg!(feature = "tiny") {
                for _ in 0..5 {
                    assert!(e.bm().undo(false).is_some());
                }
                assert_eq!(e.b().raw(), b"a a a\na a\n");
                for _ in 0..5 {
                    assert!(e.bm().undo(true).is_some());
                }
                assert_eq!(e.b().raw(), b"x\ny\nz x\ny\nz x\ny\nz\nx\ny\nz x\ny\nz\n");
            }
        }
    }
}
#[test]
#[ignore = "bounded resource fixture, run via tests/search/run.py"]
fn stress_replace_backward_regex() {
    let mut text = vec![b'a'; 200000];
    text.push(b'\n');
    let mut e = fixture(&text, b"(a)", true, true);
    e.start_replace(b"\\1\\1".to_vec());
    e.replace_answer(true, true);
    assert_eq!(e.b().state.lines[0], vec![b'a'; 400000]);
}
#[test]
#[ignore = "bounded resource fixture, run via tests/search/run.py"]
fn stress_replace_multiline() {
    let mut text = vec![b'a'; 100000];
    text.push(b'\n');
    let mut e = fixture(&text, b"a", false, false);
    e.start_replace(b"b\nc".to_vec());
    e.replace_answer(true, true);
    assert_eq!(e.b().state.lines.len(), 100002);
    assert_eq!(e.b().state.lines[0], b"b");
    assert!(
        e.b().state.lines[1..100000]
            .iter()
            .all(|line| line == b"cb")
    );
    assert_eq!(e.b().state.lines[100000], b"c");
}

#[test]
fn region_zero_width_restores_adjusted_mark() {
    let mut e = fixture(b"abc\n", b"^", true, false);
    e.bm().state.mark = Some(Pos { line: 0, x: 0 });
    e.bm().state.pos = Pos { line: 0, x: 3 };
    e.start_replace(b"-".to_vec());
    e.replace_answer(true, true);
    assert_eq!(e.b().raw(), b"-abc\n");
    assert_eq!(e.b().state.mark, Some(Pos { line: 0, x: 1 }));
}
