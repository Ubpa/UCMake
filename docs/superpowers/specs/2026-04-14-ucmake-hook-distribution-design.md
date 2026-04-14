# UCMake Hook Distribution Design

**Date:** 2026-04-14  
**Status:** Approved  
**Scope:** UCMake, UCommon, codocs skill

---

## Problem

Currently, every downstream library (UCommon, etc.) must independently maintain local copies of codocs hooks and more-hooks.py. When the codocs skill is updated, each library must be manually redeployed. This is unsustainable as the number of downstream libraries grows.

**Goal:** UCMake becomes the single authority for codocs hooks and more-hooks. Downstream libraries get hooks automatically at cmake configure time, with no per-library manual steps after initial setup.

---

## Architecture

### Core Principle

UCMake's installed `infra/` directory is the canonical source for all hook tooling. Downstream libraries symlink directly into it. UCMake version upgrades are self-healing: the next `cmake configure` re-registers symlinks pointing to the new version.

### infra/ Directory Structure

New top-level directory in UCMake source (tracked in git, UCMake is the authority):

```
infra/
    .codocs/
        codocs.py               ← codocs lint/stale engine
        hooks/
            pre-commit          ← static script
            commit-msg          ← static script
    .more-hooks/
        more-hooks.py           ← hook dispatcher framework
    .ucmake/
        hooks/
            pre-commit          ← static script (sources project.env)
```

After `cmake --install`:

```
~/.local/Ubpa/UCMake_x_y_z/infra/
    .codocs/
        codocs.py
        hooks/
            pre-commit
            commit-msg
    .more-hooks/
        more-hooks.py
    .ucmake/
        hooks/
            pre-commit
```

`CMakeLists.txt` addition:
```cmake
install(DIRECTORY infra/ DESTINATION infra)
```

### Hook Self-Location Pattern

All hooks use the same path resolution — no hardcoded paths, no configuration needed:

```bash
_self="$(readlink -f "$0")"
_codocs_py="$(dirname "$(dirname "$_self")")/codocs.py"
```

This works identically in both scenarios:

| Scenario | symlink target | resolved codocs.py |
|----------|---------------|-------------------|
| Direct install (codocs skill) | `.codocs/hooks/pre-commit` | `.codocs/codocs.py` |
| UCMake downstream | `infra/.codocs/hooks/pre-commit` | `infra/.codocs/codocs.py` |

If `_codocs_py` does not exist (broken install), the hook prints a warning and `exit 0` — never blocks commits due to environment issues.

### project.env for UCMake Hook

UCMake's pre-commit hook needs project-specific values. Instead of `configure_file` expanding a `.in` template, configure generates a minimal env file:

```
.ucmake/project.env          ← configure artifact, gitignored
    UCMAKE_PROJECT_NAME=UCommon
    UCMAKE_BUILD_DIR=/path/to/build
    UCMAKE_DEFAULT_CONFIG=Release
```

`infra/.ucmake/hooks/pre-commit` is a static script that `source`s this file at runtime. This means all files in `infra/` are static and can be symlinked directly — no per-project expansion needed.

---

## Ubpa_InitProject() Changes

At the end of `Ubpa_InitProject()`, replace the current `configure_file` + manual-register comment with:

```
1. Locate infra/ directory:
   get_filename_component(_ucmake_infra "${UBPA_UCMAKE_LIST_DIR}/../infra" ABSOLUTE)

2. Generate .ucmake/project.env (configure_file or file(WRITE))
   Generate .ucmake/.gitignore (already exists, keep as-is)

3. find_package(Python3 COMPONENTS Interpreter QUIET)

4. If Python3 found AND _ucmake_infra/.more-hooks/more-hooks.py exists:
   execute_process × 3:
     a. register codocs pre-commit  → priority 50, symlink → infra/.codocs/hooks/pre-commit
     b. register codocs commit-msg  → priority 50, symlink → infra/.codocs/hooks/commit-msg
     c. register ucmake pre-commit  → priority 80, symlink → infra/.ucmake/hooks/pre-commit

5. If Python3 not found or infra/ missing:
   message(WARNING "[UCMake] Hook registration skipped: Python3 not found or infra/ missing at ${_ucmake_infra}")
```

Every `cmake configure` re-registers (overwrites symlinks), providing self-healing on UCMake version upgrades.

---

## codocs Skill Alignment

The codocs skill (`~/agent-data/skills/codocs/`) must align its directory structure with the new layout so the hook self-location pattern works for direct-install projects too:

| Before | After |
|--------|-------|
| `.codocs/scripts/codocs.py` | `.codocs/codocs.py` |
| `.codocs/hooks/pre-commit` (hardcoded path) | `.codocs/hooks/pre-commit` (self-resolving) |

Files to update in the skill:
- `INIT.md` — update `codocs.py` path references
- `scripts/setup-hooks.py` — update source path when copying codocs.py to project
- `hooks/pre-commit` and `hooks/commit-msg` — replace hardcoded `.codocs/scripts/codocs.py` calls with self-location pattern

---

## Migration Path

### UCMake (one-time)
1. Create `infra/` with the structure above
2. Move `codocs.py` content into `infra/.codocs/codocs.py`
3. Copy `more-hooks.py` into `infra/.more-hooks/more-hooks.py`
4. Create static `infra/.ucmake/hooks/pre-commit` (sources `.ucmake/project.env`)
5. Delete `cmake/hooks/pre-commit.in` and `cmake/hooks/` directory
6. Update `CMakeLists.txt`: add `install(DIRECTORY infra/ DESTINATION infra)`
7. Update `UbpaInit.cmake`: replace configure_file block with new logic above
8. Run `cmake --install` to deploy new infra/

### UCommon (one-time, then never again)
1. Delete `.codocs/hooks/` (local copies no longer needed)
2. Delete `.codocs/scripts/codocs.py` (or entire `.codocs/scripts/` if setup-hooks.py not needed)
3. Re-run `cmake configure` → hooks auto-registered pointing to UCMake install

### Any New Downstream Library (zero steps)
- `cmake configure` gives all hooks automatically

### codocs Skill (align with new layout)
- Move `scripts/codocs.py` → `.codocs/codocs.py` in skill source
- Update INIT.md and setup-hooks.py references accordingly
- Update hook scripts to use self-location pattern

---

## Invariants

- `infra/` contains only static files — no per-project content, no build artifacts
- `.ucmake/project.env` is the only configure-time generated artifact for hook purposes
- Hook symlinks always point to the currently installed UCMake version (self-healing)
- No downstream library ever needs to run a manual hook setup command
- codocs skill remains independent — it handles doc initialization; UCMake handles hook lifecycle
