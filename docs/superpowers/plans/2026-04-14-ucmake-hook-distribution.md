# UCMake Hook Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** UCMake becomes the single authority for codocs and more-hooks tooling; downstream libraries (UCommon etc.) get all hooks auto-registered at `cmake configure` time with zero manual steps.

**Architecture:** A new `infra/` directory in UCMake holds static copies of `more-hooks.py`, `codocs.py`, and all hook scripts under `.codocs/hooks/` and `.ucmake/hooks/`. These are installed alongside `cmake/` on `cmake --install`. `Ubpa_InitProject()` locates the installed `infra/`, generates `.ucmake/project.env`, then calls `more-hooks.py register` via `execute_process` to symlink all three hooks into `.git/hooks.d/`. Every `cmake configure` re-registers (self-healing on UCMake version upgrades).

**Tech Stack:** CMake 3.16+, Python 3, Bash

---

## File Map

**New files (UCMake source):**
- `infra/.codocs/codocs.py` — codocs lint/stale engine (copy from skill source)
- `infra/.codocs/hooks/pre-commit` — static codocs pre-commit hook (self-locating)
- `infra/.codocs/hooks/commit-msg` — static codocs commit-msg hook (self-locating)
- `infra/.more-hooks/more-hooks.py` — hook dispatcher framework (copy from skill source)
- `infra/.ucmake/hooks/pre-commit` — static UCMake pre-commit hook (sources project.env)

**Modified files (UCMake source):**
- `CMakeLists.txt` — add `install(DIRECTORY infra/ DESTINATION infra)`
- `cmake/UbpaInit.cmake` — replace `configure_file` block with `project.env` + auto-register logic

**Deleted files (UCMake source):**
- `cmake/hooks/pre-commit.in`
- `cmake/hooks/` directory

**codocs skill (`~/agent-data/skills/codocs/`):**
- `hooks/pre-commit` — replace hardcoded `.codocs/scripts/codocs.py` path with self-location
- `hooks/commit-msg` — same
- `INIT.md` — update path references from `.codocs/scripts/codocs.py` → `.codocs/codocs.py`
- `scripts/setup-hooks.py` — update codocs.py source path reference

**UCommon cleanup (after UCMake install + reconfigure):**
- Delete `.codocs/hooks/` (local copies replaced by infra/ symlinks)
- Delete `.codocs/scripts/codocs.py`

---

## Task 1: Create infra/.more-hooks/more-hooks.py

Copy the authoritative `more-hooks.py` from the skill into UCMake's new `infra/` directory.

**Files:**
- Create: `infra/.more-hooks/more-hooks.py`

- [ ] **Step 1: Create directory and copy file**

```bash
mkdir -p /data/data/com.termux/files/home/UCMake/infra/.more-hooks
cp /data/data/com.termux/files/home/agent-data/skills/more-hooks/scripts/more-hooks.py \
   /data/data/com.termux/files/home/UCMake/infra/.more-hooks/more-hooks.py
```

- [ ] **Step 2: Verify**

```bash
head -5 /data/data/com.termux/files/home/UCMake/infra/.more-hooks/more-hooks.py
```

Expected: `#!/usr/bin/env python3` and `more-hooks` in first few lines.

- [ ] **Step 3: Commit**

```bash
cd /data/data/com.termux/files/home/UCMake
git add infra/.more-hooks/more-hooks.py
git commit -m "feat: add infra/.more-hooks/more-hooks.py

## codocs-skip
- [all]: 仅新增 infra/ 目录，不在 cmake/ roots 范围内"
```

---

## Task 2: Create infra/.codocs/codocs.py

Copy the authoritative `codocs.py` from the skill into `infra/.codocs/`.

**Files:**
- Create: `infra/.codocs/codocs.py`

- [ ] **Step 1: Create directory and copy file**

```bash
mkdir -p /data/data/com.termux/files/home/UCMake/infra/.codocs
cp /data/data/com.termux/files/home/agent-data/skills/codocs/scripts/codocs.py \
   /data/data/com.termux/files/home/UCMake/infra/.codocs/codocs.py
```

- [ ] **Step 2: Verify the file runs**

```bash
python /data/data/com.termux/files/home/UCMake/infra/.codocs/codocs.py --help 2>&1 | head -5
```

Expected: usage/help output, no import errors.

- [ ] **Step 3: Commit**

```bash
cd /data/data/com.termux/files/home/UCMake
git add infra/.codocs/codocs.py
git commit -m "feat: add infra/.codocs/codocs.py

## codocs-skip
- [all]: 仅新增 infra/ 目录，不在 cmake/ roots 范围内"
```

---

## Task 3: Create infra/.codocs/hooks/ with self-locating scripts

Create static codocs hook scripts that locate `codocs.py` by resolving their own symlink path (`dirname dirname $0`). Replace the hardcoded `.codocs/scripts/codocs.py` path in the current skill hooks.

**Files:**
- Create: `infra/.codocs/hooks/pre-commit`
- Create: `infra/.codocs/hooks/commit-msg`

- [ ] **Step 1: Create directory**

```bash
mkdir -p /data/data/com.termux/files/home/UCMake/infra/.codocs/hooks
```

- [ ] **Step 2: Write infra/.codocs/hooks/pre-commit**

Take the current skill pre-commit and replace the `INIT_PY` assignment. Open:
```
/data/data/com.termux/files/home/agent-data/skills/codocs/hooks/pre-commit
```

Copy it to `infra/.codocs/hooks/pre-commit`, then replace this block:

Old (around line 44):
```bash
# ── Shared variables (needed by multiple phases) ──────────────────────────
INIT_PY="$ROOT/.codocs/scripts/codocs.py"
```

New:
```bash
# ── Shared variables (needed by multiple phases) ──────────────────────────
# Self-locate codocs.py: resolve symlink → infra/.codocs/hooks/pre-commit
# → two dirname levels up → infra/.codocs/ → codocs.py
_hook_self="$(readlink -f "$0")"
INIT_PY="$(dirname "$(dirname "$_hook_self")")/codocs.py"
```

Also replace all occurrences of `.codocs/scripts/codocs.py` in error messages with `.codocs/codocs.py`:
```bash
# In Phase 1 STALE_FILE hint:
#   python .codocs/scripts/codocs.py . review-stale <md-path>
# Replace with:
#   python .codocs/codocs.py . review-stale <md-path>
```

Full command sequence:
```bash
cp /data/data/com.termux/files/home/agent-data/skills/codocs/hooks/pre-commit \
   /data/data/com.termux/files/home/UCMake/infra/.codocs/hooks/pre-commit

# Replace INIT_PY line
sed -i 's|INIT_PY="\$ROOT/.codocs/scripts/codocs.py"|_hook_self="$(readlink -f "$0")"\nINIT_PY="$(dirname "$(dirname "$_hook_self")")/codocs.py"|' \
    /data/data/com.termux/files/home/UCMake/infra/.codocs/hooks/pre-commit

# Replace error message paths
sed -i 's|python .codocs/scripts/codocs.py|python .codocs/codocs.py|g' \
    /data/data/com.termux/files/home/UCMake/infra/.codocs/hooks/pre-commit

chmod +x /data/data/com.termux/files/home/UCMake/infra/.codocs/hooks/pre-commit
```

- [ ] **Step 3: Verify INIT_PY line was replaced correctly**

```bash
grep -n "INIT_PY\|_hook_self\|readlink" \
    /data/data/com.termux/files/home/UCMake/infra/.codocs/hooks/pre-commit
```

Expected: lines containing `_hook_self`, `readlink -f`, and `INIT_PY=` using `dirname dirname`.

- [ ] **Step 4: Write infra/.codocs/hooks/commit-msg**

The commit-msg hook does not call `codocs.py` directly (it only reads flag files and parses commit messages), so no path substitution is needed — just copy and make executable:

```bash
cp /data/data/com.termux/files/home/agent-data/skills/codocs/hooks/commit-msg \
   /data/data/com.termux/files/home/UCMake/infra/.codocs/hooks/commit-msg
chmod +x /data/data/com.termux/files/home/UCMake/infra/.codocs/hooks/commit-msg
```

- [ ] **Step 5: Verify commit-msg is executable**

```bash
ls -la /data/data/com.termux/files/home/UCMake/infra/.codocs/hooks/
```

Expected: both files shown with `x` permission bits.

- [ ] **Step 6: Commit**

```bash
cd /data/data/com.termux/files/home/UCMake
git add infra/.codocs/hooks/
git commit -m "feat: add infra/.codocs/hooks with self-locating codocs.py path

## codocs-skip
- [all]: 仅新增 infra/ 目录，不在 cmake/ roots 范围内"
```

---

## Task 4: Create infra/.ucmake/hooks/pre-commit (static, sources project.env)

Replace the `configure_file`-expanded template with a static script that reads `.ucmake/project.env` at runtime.

**Files:**
- Create: `infra/.ucmake/hooks/pre-commit`

- [ ] **Step 1: Create directory**

```bash
mkdir -p /data/data/com.termux/files/home/UCMake/infra/.ucmake/hooks
```

- [ ] **Step 2: Write the static script**

```bash
cat > /data/data/com.termux/files/home/UCMake/infra/.ucmake/hooks/pre-commit << 'EOF'
#!/usr/bin/env bash
# UCMake pre-commit hook — static script, project values loaded from .ucmake/project.env
# Generated/registered by Ubpa_InitProject() at cmake configure time. Do NOT edit manually.

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
ENV_FILE="$ROOT/.ucmake/project.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "[UCMake/pre-commit] .ucmake/project.env not found, skipping (re-run cmake configure)"
    exit 0
fi

# shellcheck source=/dev/null
source "$ENV_FILE"

if [ ! -d "$UCMAKE_BUILD_DIR" ]; then
    echo "[UCMake/pre-commit] build dir not found at $UCMAKE_BUILD_DIR, skipping"
    exit 0
fi

echo "[UCMake/pre-commit] Building and running tests for $UCMAKE_PROJECT_NAME..."
if ! cmake --build "$UCMAKE_BUILD_DIR" --config "$UCMAKE_DEFAULT_CONFIG" \
           --target "${UCMAKE_PROJECT_NAME}_Check" 2>&1; then
    echo "[UCMake/pre-commit] Build or tests failed. Commit aborted."
    exit 1
fi

echo "[UCMake/pre-commit] Build and tests passed."
EOF
chmod +x /data/data/com.termux/files/home/UCMake/infra/.ucmake/hooks/pre-commit
```

- [ ] **Step 3: Verify**

```bash
head -10 /data/data/com.termux/files/home/UCMake/infra/.ucmake/hooks/pre-commit
ls -la /data/data/com.termux/files/home/UCMake/infra/.ucmake/hooks/pre-commit
```

Expected: shebang line visible, file is executable.

- [ ] **Step 4: Commit**

```bash
cd /data/data/com.termux/files/home/UCMake
git add infra/.ucmake/hooks/pre-commit
git commit -m "feat: add static infra/.ucmake/hooks/pre-commit (sources project.env)

## codocs-skip
- [all]: 仅新增 infra/ 目录，不在 cmake/ roots 范围内"
```

---

## Task 5: Update CMakeLists.txt to install infra/

**Files:**
- Modify: `CMakeLists.txt`

- [ ] **Step 1: Read current CMakeLists.txt**

```bash
cat /data/data/com.termux/files/home/UCMake/CMakeLists.txt
```

- [ ] **Step 2: Add install(DIRECTORY) for infra/**

The current `Ubpa_Export` call is:
```cmake
Ubpa_Export(
  DIRECTORIES
    "cmake"
)
```

Add the install directive after `Ubpa_AddSubDirsRec(src)` and before `Ubpa_Export`:

```cmake
# Install infra/ (hook tooling: more-hooks, codocs, ucmake hooks)
install(DIRECTORY infra/ DESTINATION infra)
```

Use the Edit tool to insert this line. After the change, `CMakeLists.txt` should read:

```cmake
cmake_minimum_required(VERSION 3.16 FATAL_ERROR)

project (UCMake VERSION 0.7.3)
message(STATUS "[Project] ${PROJECT_NAME} ${PROJECT_VERSION}")

list(APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake")
include(UbpaInit)

Ubpa_InitProject(CXX_STANDARD 20)

Ubpa_AddSubDirsRec(src)

# Install infra/ (hook tooling: more-hooks, codocs, ucmake hooks)
install(DIRECTORY infra/ DESTINATION infra)

Ubpa_Export(
  DIRECTORIES
    "cmake"
)
```

- [ ] **Step 3: Verify cmake configure picks up the change**

```bash
cd /data/data/com.termux/files/home/UCMake
cmake -B build 2>&1 | tail -5
```

Expected: configure succeeds, no errors.

- [ ] **Step 4: Commit**

```bash
cd /data/data/com.termux/files/home/UCMake
git add CMakeLists.txt
git commit -m "feat: install infra/ directory alongside cmake/

## codocs-skip
- [all]: CMakeLists.txt 不在 cmake/ roots 范围内"
```

---

## Task 6: Update UbpaInit.cmake — replace configure_file with project.env + auto-register

This is the core change. Replace the existing `configure_file` + comment block with logic that:
1. Generates `.ucmake/project.env`
2. Locates `infra/` relative to `UBPA_UCMAKE_LIST_DIR`
3. Calls `more-hooks.py register` for all three hooks via `execute_process`

**Files:**
- Modify: `cmake/UbpaInit.cmake`

- [ ] **Step 1: Identify the block to replace**

Read lines ~140–175 of `cmake/UbpaInit.cmake`. The block starts at:
```cmake
  # generate a pre-commit hook script into <source_dir>/.cmake/hooks/pre-commit
```
and ends after:
```cmake
  unset(_hook_template)
  unset(_hook_output)
```

- [ ] **Step 2: Replace the block**

Replace this entire block (from the comment through `unset(_hook_output)`):

```cmake
  # generate a pre-commit hook script into <source_dir>/.cmake/hooks/pre-commit
  # this file is a build artifact (not tracked by git) that users can register
  # with their hook framework of choice, e.g.:
  #   python .more-hooks/more-hooks.py register . \
  #     --hook pre-commit --id <project>-ci --script .cmake/hooks/pre-commit --symlink
  string(TOLOWER "${PROJECT_NAME}" PROJECT_NAME_LOWER)
  set(UCMAKE_DEFAULT_CONFIG "Release")
  set(_hook_template "${UBPA_UCMAKE_LIST_DIR}/hooks/pre-commit.in")
  set(_hook_output "${CMAKE_SOURCE_DIR}/.ucmake/hooks/pre-commit")
  if(EXISTS "${_hook_template}")
    configure_file("${_hook_template}" "${_hook_output}" @ONLY NEWLINE_STYLE LF)
    # generate .gitignore to prevent build artifacts from being tracked
    file(WRITE "${CMAKE_SOURCE_DIR}/.ucmake/.gitignore" "*\n")
    message(STATUS "[UCMake] Generated hook: ${_hook_output}")
  endif()
  unset(_hook_template)
  unset(_hook_output)
```

With this new block:

```cmake
  # ── Hook tooling: generate project.env + auto-register via more-hooks ──────
  # infra/ sits alongside cmake/ in the UCMake install tree
  get_filename_component(_ucmake_infra "${UBPA_UCMAKE_LIST_DIR}/../infra" ABSOLUTE)

  # Generate .ucmake/project.env (runtime values for the static ucmake hook script)
  set(UCMAKE_DEFAULT_CONFIG "Release")
  file(MAKE_DIRECTORY "${CMAKE_SOURCE_DIR}/.ucmake")
  file(WRITE "${CMAKE_SOURCE_DIR}/.ucmake/project.env"
    "UCMAKE_PROJECT_NAME=${PROJECT_NAME}\n"
    "UCMAKE_BUILD_DIR=${CMAKE_BINARY_DIR}\n"
    "UCMAKE_DEFAULT_CONFIG=${UCMAKE_DEFAULT_CONFIG}\n"
  )
  # Gitignore for .ucmake/ (project.env is a configure artifact, not tracked)
  file(WRITE "${CMAKE_SOURCE_DIR}/.ucmake/.gitignore" "*\n")
  message(STATUS "[UCMake] Generated .ucmake/project.env")

  # Auto-register hooks via more-hooks (symlinks point into installed infra/)
  set(_more_hooks_py "${_ucmake_infra}/.more-hooks/more-hooks.py")
  if(EXISTS "${_more_hooks_py}")
    find_package(Python3 COMPONENTS Interpreter QUIET)
    if(Python3_FOUND)
      # codocs pre-commit (priority 50)
      execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${_more_hooks_py}" register "${CMAKE_SOURCE_DIR}"
          --hook pre-commit
          --id codocs
          --script "${_ucmake_infra}/.codocs/hooks/pre-commit"
          --priority 50
          --symlink
        RESULT_VARIABLE _mh_rc
        OUTPUT_QUIET ERROR_QUIET
      )
      # codocs commit-msg (priority 50)
      execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${_more_hooks_py}" register "${CMAKE_SOURCE_DIR}"
          --hook commit-msg
          --id codocs
          --script "${_ucmake_infra}/.codocs/hooks/commit-msg"
          --priority 50
          --symlink
        RESULT_VARIABLE _mh_rc
        OUTPUT_QUIET ERROR_QUIET
      )
      # ucmake pre-commit (priority 80)
      execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${_more_hooks_py}" register "${CMAKE_SOURCE_DIR}"
          --hook pre-commit
          --id ucmake
          --script "${_ucmake_infra}/.ucmake/hooks/pre-commit"
          --priority 80
          --symlink
        RESULT_VARIABLE _mh_rc
        OUTPUT_QUIET ERROR_QUIET
      )
      message(STATUS "[UCMake] Registered hooks via more-hooks (infra: ${_ucmake_infra})")
    else()
      message(WARNING "[UCMake] Hook registration skipped: Python3 not found")
    endif()
  else()
    message(WARNING "[UCMake] Hook registration skipped: infra not found at ${_ucmake_infra} (run cmake --install first)")
  endif()
  unset(_ucmake_infra)
  unset(_more_hooks_py)
  unset(_mh_rc)
```

- [ ] **Step 3: Verify cmake configure runs without error**

```bash
cd /data/data/com.termux/files/home/UCMake
cmake -B build 2>&1 | grep -E "UCMake\]|WARNING|ERROR"
```

Expected output contains:
```
[UCMake] Generated .ucmake/project.env
[UCMake] Registered hooks via more-hooks (infra: ...)
```

(On first run before install, you'll see the WARNING about infra not found — that's expected until Task 7.)

- [ ] **Step 4: Commit**

```bash
cd /data/data/com.termux/files/home/UCMake
git add cmake/UbpaInit.cmake
git commit -m "feat: auto-register hooks at configure time via more-hooks

Replace configure_file template with project.env + execute_process
calls to more-hooks.py. Symlinks point into installed infra/ directory.
Self-healing: re-configure updates symlinks to current UCMake version."
```

---

## Task 7: Delete cmake/hooks/ and install + verify full flow

**Files:**
- Delete: `cmake/hooks/pre-commit.in`
- Delete: `cmake/hooks/` directory

- [ ] **Step 1: Delete cmake/hooks/**

```bash
cd /data/data/com.termux/files/home/UCMake
rm -rf cmake/hooks/
```

- [ ] **Step 2: Run cmake --install to deploy infra/**

```bash
cmake --build build --target install 2>&1 | tail -20
```

Expected: `infra/` files appear in install output:
```
-- Installing: /data/data/com.termux/files/home/.local/Ubpa/UCMake_0_7_3/infra/.codocs/codocs.py
-- Installing: /data/data/com.termux/files/home/.local/Ubpa/UCMake_0_7_3/infra/.codocs/hooks/pre-commit
...
```

- [ ] **Step 3: Re-run cmake configure to trigger auto-registration**

```bash
cmake -B build 2>&1 | grep -E "\[UCMake\]|WARNING"
```

Expected:
```
[UCMake] Generated .ucmake/project.env
[UCMake] Registered hooks via more-hooks (infra: /data/data/com.termux/files/home/.local/Ubpa/UCMake_0_7_3/infra)
```

No WARNING about infra not found.

- [ ] **Step 4: Verify symlinks are correct**

```bash
ls -la /data/data/com.termux/files/home/UCMake/.git/hooks.d/pre-commit/
ls -la /data/data/com.termux/files/home/UCMake/.git/hooks.d/commit-msg/
```

Expected:
```
50-codocs -> /data/data/com.termux/files/home/.local/Ubpa/UCMake_0_7_3/infra/.codocs/hooks/pre-commit
80-ucmake -> /data/data/com.termux/files/home/.local/Ubpa/UCMake_0_7_3/infra/.ucmake/hooks/pre-commit
50-codocs -> /data/data/com.termux/files/home/.local/Ubpa/UCMake_0_7_3/infra/.codocs/hooks/commit-msg
```

- [ ] **Step 5: Smoke-test the pre-commit hook**

```bash
cd /data/data/com.termux/files/home/UCMake
bash .git/hooks/pre-commit
echo "exit code: $?"
```

Expected: exits 0 (no staged files or lint passes).

- [ ] **Step 6: Commit**

```bash
cd /data/data/com.termux/files/home/UCMake
git add cmake/
git commit -m "chore: remove cmake/hooks/ (replaced by infra/.ucmake/hooks/)

## codocs-skip
- [all]: 删除 cmake/hooks/ 目录，该目录不含文档追踪文件"
```

---

## Task 8: Update codocs skill — align paths

Update the skill's own hooks and docs to use `.codocs/codocs.py` (not `.codocs/scripts/codocs.py`) so the self-location pattern works for direct-install projects too.

**Files:**
- Modify: `~/agent-data/skills/codocs/hooks/pre-commit`
- Modify: `~/agent-data/skills/codocs/INIT.md`
- Modify: `~/agent-data/skills/codocs/scripts/setup-hooks.py`

- [ ] **Step 1: Update skill pre-commit hook — INIT_PY line**

```bash
SKILL_HOOK=/data/data/com.termux/files/home/agent-data/skills/codocs/hooks/pre-commit
```

Replace:
```bash
INIT_PY="$ROOT/.codocs/scripts/codocs.py"
```

With:
```bash
_hook_self="$(readlink -f "$0")"
INIT_PY="$(dirname "$(dirname "$_hook_self")")/codocs.py"
```

Also replace error message paths in that file:
```bash
sed -i 's|python .codocs/scripts/codocs.py|python .codocs/codocs.py|g' "$SKILL_HOOK"
```

- [ ] **Step 2: Verify skill pre-commit hook**

```bash
grep -n "INIT_PY\|_hook_self\|codocs.py" \
    /data/data/com.termux/files/home/agent-data/skills/codocs/hooks/pre-commit
```

Expected: `_hook_self` and `readlink` lines present; no reference to `scripts/codocs.py`.

- [ ] **Step 3: Update INIT.md path references**

In `~/agent-data/skills/codocs/INIT.md`, replace all occurrences of:
```
~/agent-data/skills/codocs/scripts/codocs.py
```
with:
```
~/agent-data/skills/codocs/.codocs/codocs.py
```

And replace project-local references:
```
.codocs/scripts/codocs.py
```
with:
```
.codocs/codocs.py
```

- [ ] **Step 4: Update setup-hooks.py**

In `~/agent-data/skills/codocs/scripts/setup-hooks.py`, find where it references `scripts/codocs.py` as a source to copy (if any). Search:

```bash
grep -n "codocs.py\|scripts/" \
    /data/data/com.termux/files/home/agent-data/skills/codocs/scripts/setup-hooks.py
```

If found, update references from `scripts/codocs.py` to `.codocs/codocs.py` accordingly (setup-hooks.py installs hooks, not codocs.py itself — verify the grep result before editing).

- [ ] **Step 5: Move codocs.py in skill source to .codocs/ layout**

The skill's `scripts/codocs.py` should be mirrored at `.codocs/codocs.py` for direct-install projects. Create the `.codocs/` subdirectory in the skill and symlink or copy:

```bash
mkdir -p /data/data/com.termux/files/home/agent-data/skills/codocs/.codocs
cp /data/data/com.termux/files/home/agent-data/skills/codocs/scripts/codocs.py \
   /data/data/com.termux/files/home/agent-data/skills/codocs/.codocs/codocs.py
```

`scripts/codocs.py` stays as-is (referenced by INIT.md and other tooling), `.codocs/codocs.py` is what gets installed into projects.

- [ ] **Step 6: Update setup-hooks.py to install .codocs/codocs.py into projects**

In `setup-hooks.py`, find the section that installs files into the project's `.codocs/`. Add logic to copy `codocs.py` from the skill's `.codocs/codocs.py` into the project's `.codocs/codocs.py` (sibling of `hooks/`):

```python
# In setup_hooks() function, after installing README.md:
codocs_py_src = Path(__file__).resolve().parent.parent / ".codocs" / "codocs.py"
codocs_py_dst = project_root / ".codocs" / "codocs.py"
if codocs_py_src.is_file() and not codocs_py_dst.exists():
    shutil.copy2(codocs_py_src, codocs_py_dst)
    print(f"[codocs setup-hooks] installed .codocs/codocs.py", file=sys.stderr)
```

- [ ] **Step 7: Commit skill changes**

```bash
cd /data/data/com.termux/files/home/agent-data
git add skills/codocs/
git commit -m "feat(codocs): align hook self-location pattern, add .codocs/codocs.py layout"
```

---

## Task 9: Migrate UCommon — clean up local copies, reconfigure

Remove UCommon's local hook copies and let UCMake configure re-register everything.

**Files:**
- Delete: `~/UCommon/.codocs/hooks/`
- Delete: `~/UCommon/.codocs/scripts/codocs.py` (or `scripts/` if empty after removal)

- [ ] **Step 1: Remove local hook copies from UCommon**

```bash
rm -rf /data/data/com.termux/files/home/UCommon/.codocs/hooks/
```

- [ ] **Step 2: Remove local codocs.py copy**

```bash
rm -f /data/data/com.termux/files/home/UCommon/.codocs/scripts/codocs.py
# If scripts/ is now empty, remove it too:
rmdir /data/data/com.termux/files/home/UCommon/.codocs/scripts/ 2>/dev/null || true
```

- [ ] **Step 3: Run cmake configure on UCommon**

```bash
cmake -B /data/data/com.termux/files/home/UCommon/build \
      -S /data/data/com.termux/files/home/UCommon 2>&1 | grep -E "\[UCMake\]|WARNING|ERROR"
```

Expected:
```
[UCMake] Generated .ucmake/project.env
[UCMake] Registered hooks via more-hooks (infra: .../UCMake_0_7_3/infra)
```

- [ ] **Step 4: Verify UCommon symlinks point to infra/**

```bash
ls -la /data/data/com.termux/files/home/UCommon/.git/hooks.d/pre-commit/
ls -la /data/data/com.termux/files/home/UCommon/.git/hooks.d/commit-msg/
```

Expected:
```
50-codocs -> /data/data/com.termux/files/home/.local/Ubpa/UCMake_0_7_3/infra/.codocs/hooks/pre-commit
80-ucmake -> /data/data/com.termux/files/home/.local/Ubpa/UCMake_0_7_3/infra/.ucmake/hooks/pre-commit
50-codocs -> /data/data/com.termux/files/home/.local/Ubpa/UCMake_0_7_3/infra/.codocs/hooks/commit-msg
```

- [ ] **Step 5: Smoke-test hooks in UCommon**

```bash
cd /data/data/com.termux/files/home/UCommon
bash .git/hooks/pre-commit
echo "exit code: $?"
```

Expected: exits 0.

- [ ] **Step 6: Commit UCommon cleanup**

```bash
cd /data/data/com.termux/files/home/UCommon
git add .codocs/
git commit -m "chore: remove local hook copies, hooks now managed by UCMake infra/

Hooks are auto-registered at cmake configure time via UCMake's infra/.
symlinks point to ~/.local/Ubpa/UCMake_x_y_z/infra/.

## codocs-skip
- [all]: 删除 .codocs/hooks/ 和 scripts/codocs.py，这些是工具文件非文档内容"
```

---

## Self-Review

**Spec coverage check:**
- ✅ Section 1 (infra/ structure) → Tasks 1–4
- ✅ Section 2 (Ubpa_InitProject auto-register) → Task 6
- ✅ Section 3 (self-locating codocs.py path) → Task 3 (infra hooks) + Task 8 (skill hooks)
- ✅ Section 4 (migration) → Tasks 7 (UCMake install), 9 (UCommon cleanup), 8 (skill align)
- ✅ CMakeLists.txt install → Task 5
- ✅ cmake/hooks/ deletion → Task 7

**No placeholders found.**

**Type/name consistency:** `UCMAKE_PROJECT_NAME`, `UCMAKE_BUILD_DIR`, `UCMAKE_DEFAULT_CONFIG` used consistently in Task 4 (writing project.env) and Task 6 (generating it from CMake).
