# Issue 10 packaging validation

Base revision: `f5e79cf`. Tests ran in disposable synthetic Git repositories;
the real checkout had unrelated untracked review files and concurrent changes,
so no release package was created from it.

| Command | Result | Evidence |
| --- | --- | --- |
| `python3 -m unittest discover -s tools -p 'test_package_provenance.py' -v` | 6 passed | [unit.log](unit.log) |
| `python3 -m unittest discover -s tools -p 'test_package_docs.py' -v` | 3 passed | [docs-unit.log](docs-unit.log) |
| `git diff --check` | passed | Command output was empty. |
| `python3 target/issue-10-old-proof/check.py` | expected old-policy failure reproduced | [old-regression.json](old-regression.json) |

The provenance fixture packages a clean commit, checks its source archive members
against `build.json` hashes and modes, and confirms an unrelated untracked review
file is excluded. Separate fixtures reject modified tracked, staged, untracked,
Git-ignored untracked source inputs, and tracked symlinks before creating an
output directory.

The old packager was loaded from `f5e79cf` and run with a valid synthetic binary
and uncommitted tracked README change. It produced release archives; the new
preflight refuses this input. This proves the policy regression independently
of the missing-binary shortcut used to test early rejection.
