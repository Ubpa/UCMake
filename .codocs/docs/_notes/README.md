# codocs

Semantic mirror documentation system for source trees.
Every source file/directory has a paired `.codocs/*.md` that captures
meaning rather than syntax — interfaces, design decisions, algorithms, traps.

## Layout

```
.codocs/
├── config.json         ← roots, excludes, hook toggles
├── scripts/
│   ├── codocs.py       ← lint / missing-check / parent-sync
│   └── setup-hooks.py  ← (re-)install git hooks
├── hooks/              ← hook scripts (registered into .git via more-hooks)
│   ├── pre-commit
│   └── commit-msg
└── <mirror of source tree>
    ├── src.md          ← directory index
    └── src/
        └── Foo.cpp.md  ← file semantic doc
```

## Re-install hooks after cloning

```bash
python .codocs/scripts/setup-hooks.py
```

This registers `.codocs/hooks/pre-commit` and `.codocs/hooks/commit-msg`
through `more-hooks` (if `.more-hooks/more-hooks.py` exists in the project),
or installs them directly into `.git/hooks/` as a fallback.

## Lint

```bash
python .codocs/scripts/codocs.py . --lint
```

Reports `[MISSING]`, `[ORPHAN]`, `[BLOAT]`, `[THIN]` issues.

## Commit hooks behaviour

| Phase | Hook | What it checks | On failure |
|-------|------|----------------|------------|
| 1 | pre-commit | ORPHAN / MISSING lint | Hard block |
| 2 | pre-commit + commit-msg | Code changed, no doc updated | Soft — needs skip tag or `doc: updated` |
| 3 | pre-commit + commit-msg | `.codocs/` MD changed, parent MD not staged | Soft — needs skip tag |
| 4 | pre-commit + commit-msg | Dependency rules triggered | Soft — needs skip tag |

### Skip syntax (in commit message body)

```
## codocs-skip
- [all]: <reason>               ← global skip
- .codocs/src/Foo.md: <reason>  ← path-specific skip
```
