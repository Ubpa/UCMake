# more-hooks

Git hook dispatcher — allows multiple tools to each register their own hook
scripts without overwriting each other.

## Layout

```
.more-hooks/
├── more-hooks.py   ← dispatcher framework (this directory)
└── README.md       ← this file

.git/hooks/
├── pre-commit      ← dispatcher (delegates to hooks.d/)
└── commit-msg      ← dispatcher (delegates to hooks.d/)

.git/hooks.d/
├── pre-commit/
│   └── 50-codocs   ← symlink → .codocs/hooks/pre-commit
└── commit-msg/
    └── 50-codocs   ← symlink → .codocs/hooks/commit-msg
```

## Re-install hooks after cloning

```bash
python .more-hooks/more-hooks.py install-to-project .   # update .more-hooks/ itself
python .codocs/scripts/setup-hooks.py                   # re-register codocs hooks
```

## CLI reference

```bash
# Register a hook script under hooks.d/
python .more-hooks/more-hooks.py register . \
    --hook pre-commit --id mytool --script path/to/script [--priority 50]

# List registered hooks
python .more-hooks/more-hooks.py list .

# Remove a registration
python .more-hooks/more-hooks.py unregister . --id mytool [--hook pre-commit]

# Install dispatcher shims only (without registering anything)
python .more-hooks/more-hooks.py install . [--hooks pre-commit commit-msg]
```

## Execution order

Scripts in `hooks.d/<hook-name>/` run in filename sort order.
Naming convention: `<priority>-<id>` — lower priority number runs first.

| Range | Convention |
|-------|-----------|
| 10–20 | Security (secret scanning, etc.) |
| 50    | Default (most tools) |
| 80–90 | Post-checks |
