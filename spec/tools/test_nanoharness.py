#!/usr/bin/env python3
"""Harness regressions for reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c."""
import unittest
from unittest.mock import patch
import nanoharness as h


class HarnessTests(unittest.TestCase):
    def test_rows_keep_independent_sgr_in_one_capture(self):
        with patch.object(h, 'tmux', return_value='\x1b[31mred\nplain\n') as capture:
            grid = h.capture_grid(5, 2)
        self.assertEqual(capture.call_count, 1)
        self.assertEqual(grid[0][0]['attr'], {'fg': 1})
        self.assertEqual(grid[1][0]['attr'], {})
        self.assertEqual(''.join(c['ch'] for c in grid[1]), 'plain')

    def test_exit_waits_for_reaped_status(self):
        states = [{'dead': 1, 'exit_status': None, 'exit_signal': None},
                  {'dead': 1, 'exit_status': 0, 'exit_signal': None}]
        with patch.object(h, 'pane_state', side_effect=states) as state, \
             patch.object(h.time, 'sleep'):
            self.assertTrue(h.Run.__new__(h.Run).wait_dead(1))
        self.assertEqual(state.call_count, 2)

    def test_tmux_signal_names(self):
        fields = ['' for _ in h.PANE_KEYS]
        fields[h.PANE_KEYS.index('exit_signal')] = 'TERM'
        with patch.object(h, 'tmux', return_value='\t'.join(fields) + '\n'):
            self.assertEqual(h.pane_state()['exit_signal'], 15)


if __name__ == '__main__':
    unittest.main()
