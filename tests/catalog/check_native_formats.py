#!/usr/bin/env python3
"""Require literal-only format arguments at native printf-family call sites.

GCC treats gettext's format_arg annotation as preserving a literal's format.
That checks shipped source types but cannot validate an external catalog, so
strict compiler warnings alone do not enforce this stronger source rule.
"""
import argparse
import json
from pathlib import Path
import re

LEXEME = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\[\s\S]|[^"\\])*"|'
                    r"'(?:\\[\s\S]|[^'\\])*'|[A-Za-z_][A-Za-z_0-9]*|[^\s]")
FORMAT_INDEX = {
    'printf': 0, 'vprintf': 0, 'wprintf': 0, 'vwprintf': 0,
    'fprintf': 1, 'vfprintf': 1, 'fwprintf': 1, 'vfwprintf': 1,
    'sprintf': 1, 'vsprintf': 1, 'asprintf': 1, 'vasprintf': 1,
    'dprintf': 1, 'vdprintf': 1,
    'snprintf': 2, 'vsnprintf': 2, 'swprintf': 2, 'vswprintf': 2,
    'printw': 0, 'wprintw': 1, 'mvprintw': 2, 'mvwprintw': 3,
}


def check(source):
    tokens = [m.group() for m in LEXEME.finditer(source)
              if not m.group().startswith(('//', '/*'))]
    failures = []
    calls = 0
    for index, token in enumerate(tokens[:-1]):
        if token not in FORMAT_INDEX or tokens[index + 1] != '(':
            continue
        calls += 1
        args = [[]]
        depth = 0
        for part in tokens[index + 2:]:
            if part == ')' and depth == 0:
                break
            if part == ',' and depth == 0:
                args.append([])
                continue
            if part in ('(', '[', '{'):
                depth += 1
            elif part in (')', ']', '}'):
                depth -= 1
            args[-1].append(part)
        else:
            failures.append(f'{token}: unterminated call')
            continue
        slot = FORMAT_INDEX[token]
        if slot >= len(args) or not args[slot] or not all(
                part.startswith('"') for part in args[slot]):
            failures.append(f'{token}: format argument is not exclusively string literals')
    return {'pass': not failures, 'printf_calls': calls, 'failures': failures}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    result = check(args.source.read_text())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['pass'] else 1)
