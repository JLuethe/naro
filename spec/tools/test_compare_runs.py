#!/usr/bin/env python3
"""Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c: comparator regressions."""
import copy
import json
from pathlib import Path
import unittest
import compare_runs as c

class CompareTests(unittest.TestCase):
    def setUp(self):
        self.ref = json.loads((Path(__file__).resolve().parents[1] / 'evidence/runs/TEST-SMOKE-001/result.json').read_text())
        self.cand = copy.deepcopy(self.ref)

    def test_identical(self):
        self.assertEqual(c.compare(self.ref, self.cand), [])

    def test_missing_row_and_mode(self):
        self.cand['snapshots']['start']['rows'].pop()
        self.cand['snapshots']['start']['modes']['mouse_any'] = 1
        fields = [d['field'] for d in c.compare(self.ref, self.cand)]
        self.assertIn('snapshot.start.height', fields)
        self.assertIn('snapshot.start.modes', fields)

    def test_wide_and_combining_attributes(self):
        a = {'text': '日e\u0301 x ', 'attrs': [{'start': 4, 'end': 5, 'attr': 'fg=1'}]}
        b = copy.deepcopy(a)
        b['attrs'][0].update(start=3, end=4)
        self.assertNotEqual(c.norm_row(a, 6), c.norm_row(b, 6))
        # Index 3 is a space; invisible foreground has no effect.
        self.assertEqual(c.norm_row(b, 6), c.norm_row(dict(text=a['text'], attrs=[]), 6))

    def test_blanks_preserve_visible_attributes(self):
        def row(attr):
            return c.norm_row({'text': ' ', 'attrs': [{'start': 0, 'end': 1, 'attr': attr}]}, 1)
        self.assertEqual(row('bold=True,fg=1'), row(''))
        self.assertNotEqual(row('underline=True'), row(''))
        self.assertNotEqual(row('reverse=True,fg=1'), row('reverse=True,fg=2'))

    def test_files_exact_and_symlink_target(self):
        a = {'x': {'type': 'file', 'mode': '0o600', 'b64': 'bmFuby5hYmNkZWY='}}
        b = copy.deepcopy(a); b['x']['b64'] = 'bmFuby5naGlqa2w='
        self.assertNotEqual(c.norm_manifest(a), c.norm_manifest(b))
        self.assertNotEqual(c.norm_manifest({'x': {'type': 'link', 'target': 'a'}}),
                            c.norm_manifest({'x': {'type': 'link', 'target': 'b'}}))

    def test_lock_identity_but_not_version_or_modified(self):
        a = bytearray(1024); a[:2] = b'b0'
        b = a.copy(); b[24:28] = b'abcd'
        self.assertEqual(c.norm_lock(a), c.norm_lock(b))
        b[1007] = 0x55
        self.assertNotEqual(c.norm_lock(a), c.norm_lock(b))
        b = a.copy(); b[2] = ord('x')
        self.assertNotEqual(c.norm_lock(a), c.norm_lock(b))

    def test_final_cursor_and_stdout(self):
        self.cand['after_exit_screen']['cursor']['visible'] ^= True
        self.assertEqual(c.compare(self.ref, self.cand), [])
        self.cand['stdout'] = 'extra'
        self.assertTrue(c.compare(self.ref, self.cand))

    def test_temp_tokens(self):
        self.assertEqual(c.norm_text('nano.12345.save nano.abcDEF.txt'),
                         'nano.<PID>.save nano.XXXXXX.txt')

    def test_dead_banner_time(self):
        self.assertEqual(c.norm_text("Pane is dead (status 0, Fri Oct 23 22:48:55 2026)"),
                         c.norm_text("Pane is dead (status 0, Sat Oct 24 01:02:03 2026)"))
        self.assertNotEqual(c.norm_text("Pane is dead (status 1, date)"),
                            c.norm_text("Pane is dead (status 0, date)"))

    def test_tool_temp_logs_are_narrowly_normalized(self):
        def manifest(raw):
            import base64
            return {'home/fmt-args': {'type': 'file', 'mode': '0o644', 'b64': base64.b64encode(raw).decode()}}
        r={'scenario':'TEST-FEAT-007','env':{}}
        s={'scenario':'TEST-FEAT-007','env':{'TMPDIR':'/scratch/tmp'}}
        self.assertEqual(c.norm_manifest(manifest(b'-x /tmp/nano.abcdef.txt\n'),run=r),
                         c.norm_manifest(manifest(b'-x /scratch/tmp/nano.qrstuv.txt\n'),run=s))
        self.assertNotEqual(c.norm_manifest(manifest(b'-x /tmp/nano.abcdef.txt\n'),run=r),
                            c.norm_manifest(manifest(b'/scratch/tmp/nano.qrstuv.txt\n'),run=s))

    def test_timeout_fails(self):
        self.cand['notes'].append('settle timed out after 5.0s')
        self.assertTrue(c.compare(self.ref, self.cand))

if __name__ == '__main__':
    unittest.main()
