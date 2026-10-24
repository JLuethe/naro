"""Track the preprocessor condition that guards each line of a C file.

Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c

conditions(path) -> list where index i (1-based line number) holds a string
such as "ENABLE_NANORC && !NANO_TINY" (empty string = unconditional).
Only #if/#ifdef/#ifndef/#elif/#else/#endif are interpreted; the expression
text of #if/#elif is kept verbatim.
"""

import re

_DIRECTIVE = re.compile(r"^\s*#\s*(ifdef|ifndef|if|elif|else|endif)\b(.*)$")


def _clean(expr):
    expr = re.sub(r"/\*.*?\*/", "", expr).strip()
    expr = re.sub(r"defined\s*\(\s*(\w+)\s*\)", r"\1", expr)
    expr = re.sub(r"defined\s+(\w+)", r"\1", expr)
    return expr


def _neg(expr):
    if re.fullmatch(r"!?\w+", expr):
        return expr[1:] if expr.startswith("!") else "!" + expr
    return "!(%s)" % expr


def conditions(path):
    stack = []          # list of [current_expr, list_of_previous_branch_exprs]
    out = [""]
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")
    for line in lines:
        m = _DIRECTIVE.match(line)
        if m:
            kind, rest = m.group(1), _clean(m.group(2))
            if kind == "ifdef":
                stack.append([rest, []])
            elif kind == "ifndef":
                stack.append(["!" + rest, []])
            elif kind == "if":
                stack.append([rest, []])
            elif kind == "elif":
                top = stack[-1]
                top[1].append(top[0])
                top[0] = " && ".join([_neg(e) for e in top[1]] + [rest])
            elif kind == "else":
                top = stack[-1]
                top[1].append(top[0])
                top[0] = " && ".join(_neg(e) for e in top[1])
            elif kind == "endif":
                if stack:
                    stack.pop()
            out.append(" && ".join("(%s)" % s[0] if " " in s[0] else s[0] for s in stack))
        else:
            out.append(" && ".join("(%s)" % s[0] if " " in s[0] else s[0] for s in stack))
    return out


if __name__ == "__main__":
    import sys
    conds = conditions(sys.argv[1])
    for n in map(int, sys.argv[2:]):
        print(n, conds[n])
