Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

# Inventory data

All CSVs use UTF-8, a header row and Python csv quoting. Row counts exclude the
header. Each row is a fact extracted from this pinned source or its executable;
not every row has a runtime assertion. Column names are the authoritative schema.
Empty fields mean not applicable or not populated, not verified absence.

| File | Rows at audit | Meaning / provenance |
|---|---:|---|
| keybindings.csv | 921 | Effective binding rows merged across 13 gdb profiles; context, key/code, function, profiles, restrictions, source |
| functions.csv | 122 | Registered functions, help tags/descriptions, context and profile availability |
| bindable-functions.csv | 113 | Rc function names/aliases and availability |
| helplines-80cols.csv | 1093 | Computed help-line slot/row/column/width, key and tag per profile/context |
| cli-options.csv | 60 | Short/long options, argument shape, handler/build conditions and help |
| nanorc-options.csv | 70 | Rc option types/defaults, validation and diagnostics |
| nanorc-commands.csv | 15 | Command grammar, contexts and source |
| color-names.csv | 34 | Named colors and terminal-dependent mapping |
| messages.csv | 682 | POT msgids, plurals, format flags/substitutions, channels, source/comments |
| translation-catalogs.csv | 41 | PO locale/completeness and plural formula |
| build-features.csv | 32 | Configure switches/macros and impacted behavior |
| menus.csv | 16 | Dispatch contexts and rc menu names |
| escape-sequences.csv | 154 | Nano decoder patterns/codes, conditions and source |
| toggles.csv | 15 | Flag, description and default keys |
| syntaxes.csv | 44 | Bundled syntax selectors, strings, rule counts and license headers |
| undo-types.csv | 22 | Native history kinds, behavior references |
| test-runs.csv | 309 | Scenario ID/file/argv, recorded state, exit/signal, snapshot count and citing docs |
| requirements.csv | generated | Requirement headings, owning doc, nearby explicit test references, and baseline/follow-up phase; coarse traceability, not a coverage proof |
| follow-up-tests.csv | maintained | Planned test ID, requirement IDs, area, scenario, oracle, method, release gate, status and evidence path; every row pins the reference hash |

Regenerate from `spec/`:

```sh
python3 tools/build_inventories.py
python3 tools/gen_key_tables.py
python3 tools/test_inventory.py
python3 tools/audit_spec.py
```

The first commands depend on the reference source/build paths recorded in 00;
gdb table re-dumps use `tools/dump_all_tables.sh`. Run those only with harness
fixtures/private debugger fixtures. `build_inventories.py` writes its known CSVs;
`test_inventory.py` writes test-runs; audit writes requirements and audit JSON.
Do not hand-edit generated inventories. Stable IDs/profile names provide joins;
`source` citations always refer to the pinned tree, not Naro's native bridge.

CSV requirement/test columns inherited from extraction are sometimes empty.
Use 97, document evidence tables and scenario definitions together; counts alone
do not establish complete behavior. Complete raw evidence is retained outside
these compact inventories.


Follow-up matrix schema: `requirement_ids` joins IDs with semicolons; `release_gate`
is required/conditional/optional; `status` is planned/recorded/verified/blocked/
deferred. `evidence` is a path relative to `spec/` and is mandatory for recorded
or verified cases. The audit checks identity, coverage, status/gate values and
path presence, not the semantic correctness of an evidence file. Review actual
reference/candidate results before assigning verified. Planned cases never count
as executed baseline scenarios. The requirement inventory's `phase` column
separates the original contract from document 19's follow-up requirements.


Follow-up matrix status is evidence-linked independently from requirement origin.
The requirements CSV `phase` is `baseline` or `follow-up`; phase is not a passing
status. The original 309 reference recordings remain unchanged. New paired
scenario revisions live in `../../tests/follow-up/scenarios`; compact reports
are in `../../validation/follow-up`. The audit counts 248 baseline and 38
follow-up requirements separately (22 in doc 19, nine in doc 20 and seven in
doc 21). Doc 21 uses `closure-tests.csv`. Its statuses advance only after final
binary-linked evidence is reviewed, independently of historical phase results.


`root-console-tests.csv` adds doc 20 cases using the common identity, requirement,
status, gate and evidence columns. Its eight verified automated rows and two
deferred physical-console rows are audited alongside the earlier matrix.
Namespace backend hashes and actual uid/NSS/device observations are retained in
`../../validation/root-console`. See doc 20 for the explicit oracle build flags.
