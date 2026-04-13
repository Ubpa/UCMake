#!/usr/bin/env python3
"""
codocs — code documentation mirror tool

Usage:
    python codocs.py [project_root]          # list missing MDs (for AI to create)
    python codocs.py [project_root] --lint   # check ORPHAN + MISSING

If project_root is omitted, walks up from cwd to find .codocs/config.json.

Init behavior:
  1. Reads .codocs/config.json for tracked roots and exclude patterns
  2. Scans each root recursively
  3. Prints missing MD paths to stdout in bottom-up order
     (deepest files first, then dirs) — ready for AI to create in sequence
  4. Installs git hooks + copies self to .codocs/scripts/

Lint behavior:
  1. Scans source tree → reports [MISSING] if MD does not exist
  2. Scans .codocs/ MDs → reports [ORPHAN] if source no longer exists
"""

import os
import sys
import json
import stat
import shutil
import fnmatch
from pathlib import Path


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def find_project_root(start: Path) -> Path:
    """Walk up directory tree to find the project root containing .codocs/config.json."""
    current = start.resolve()
    while True:
        if (current / ".codocs" / "config.json").exists():
            return current
        parent = current.parent
        if parent == current:
            raise FileNotFoundError(
                ".codocs/config.json not found in any parent directory. "
                "Run 'python codocs.py <project_root>' or create .codocs/config.json first."
            )
        current = parent


def load_config(project_root: Path) -> dict:
    config_path = project_root / ".codocs" / "config.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def get_hook_enabled(config: dict, name: str) -> bool:
    """Return whether a hook phase is enabled (default: True)."""
    return bool(config.get("hooks", {}).get(name, True))


def get_lint_enabled(config: dict, name: str) -> bool:
    """Return whether a lint check is enabled (default: True)."""
    return bool(config.get("lint", {}).get(name, True))


# ---------------------------------------------------------------------------
# Exclude logic
# ---------------------------------------------------------------------------

def is_excluded(path: Path, exclude_patterns: list[str]) -> bool:
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(path.name, pattern):
            return True
    return False


def is_excluded_path(path: Path, project_root: Path, exclude_paths: list[str]) -> bool:
    """Check if path matches any excluded path prefix (relative to project root)."""
    try:
        rel = path.relative_to(project_root)
    except ValueError:
        return False
    rel_str = str(rel).replace("\\", "/")
    for excl in exclude_paths:
        excl = excl.strip("/")
        if rel_str == excl or rel_str.startswith(excl + "/"):
            return True
    return False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent  # codocs/scripts/ -> codocs/


# ---------------------------------------------------------------------------
# Main scan
# ---------------------------------------------------------------------------

def scan(project_root: Path, config: dict) -> list[tuple[int, bool, Path, Path, str]]:
    """
    Scan tracked roots and return entries as:
        (depth, is_dir, source_path, md_path, name)
    """
    roots = config.get("roots", [])
    exclude = config.get("exclude", [])
    exclude_paths = config.get("exclude_paths", [])
    codocs_dir = project_root / ".codocs" / "docs"

    entries: list[tuple[int, bool, Path, Path, str]] = []

    for root_rel in roots:
        # Support glob patterns in roots (e.g. "*.py" to track root-level py files only)
        if any(c in root_rel for c in ("*", "?", "[")):
            matched = sorted(project_root.glob(root_rel))
            if not matched:
                print(f"[WARN] glob '{root_rel}' matched no files, skipping", file=sys.stderr)
            for root_path in matched:
                if root_path.is_file():
                    if not is_excluded(root_path, exclude) and not is_excluded_path(root_path, project_root, exclude_paths):
                        rel_file = root_path.relative_to(project_root)
                        depth = len(rel_file.parts)
                        md_path = codocs_dir / (str(rel_file).replace("\\", "/") + ".md")
                        entries.append((depth, False, root_path, md_path, root_path.name))
            continue

        root_path = (project_root / root_rel).resolve()
        if not root_path.exists():
            print(f"[WARN] root '{root_rel}' does not exist, skipping", file=sys.stderr)
            continue

        # Support single-file roots (e.g. "opt.py" in the project root)
        if root_path.is_file():
            if not is_excluded(root_path, exclude) and not is_excluded_path(root_path, project_root, exclude_paths):
                rel_file = root_path.relative_to(project_root)
                depth = len(rel_file.parts)
                md_path = codocs_dir / (str(rel_file).replace("\\", "/") + ".md")
                entries.append((depth, False, root_path, md_path, root_path.name))
            continue

        for dirpath_str, dirnames, filenames in os.walk(root_path):
            dirpath = Path(dirpath_str)

            # Prune excluded dirs in-place so os.walk won't descend into them
            dirnames[:] = sorted(
                d for d in dirnames
                if not is_excluded(Path(d), exclude)
                and not is_excluded_path(dirpath / d, project_root, exclude_paths)
            )
            filenames = sorted(filenames)

            # Skip this directory itself if it's excluded by path
            if is_excluded_path(dirpath, project_root, exclude_paths):
                continue

            rel_dir = dirpath.relative_to(project_root)
            depth = len(rel_dir.parts)

            # Files
            for filename in filenames:
                filepath = dirpath / filename
                if is_excluded(filepath, exclude):
                    continue
                if is_excluded_path(filepath, project_root, exclude_paths):
                    continue
                rel_file = filepath.relative_to(project_root)
                md_path = codocs_dir / (str(rel_file).replace("\\", "/") + ".md")
                entries.append((depth + 1, False, filepath, md_path, filename))

            # Directory itself
            md_path = codocs_dir / (str(rel_dir).replace("\\", "/") + ".md")
            entries.append((depth, True, dirpath, md_path, dirpath.name))

    return entries


def bottom_up_order(entries: list) -> list:
    """
    Sort entries deepest-first.
    Within the same depth: files before directories
    (so when we fill a dir's MD, its children's MDs are already done).
    """
    return sorted(entries, key=lambda e: (-e[0], e[1]))  # is_dir False(0) < True(1)


# ---------------------------------------------------------------------------
# Hook / script install
# ---------------------------------------------------------------------------

def install_hooks(project_root: Path):
    """Install codocs git hooks and supporting scripts into the project.

    Copies:
    - hooks/pre-commit, hooks/commit-msg → .git/hooks/
    - scripts/codocs.py → .codocs/scripts/codocs.py  (so hooks can reference it locally)

    Non-destructive: skips files that already exist.
    Returns (installed, skipped) lists of item names.
    """
    hooks_src = SKILL_DIR / "hooks"
    git_hooks_dir = project_root / ".git" / "hooks"
    codocs_scripts_dir = project_root / ".codocs" / "scripts"

    installed, skipped = [], []

    # Copy codocs.py to .codocs/scripts/
    local_script = codocs_scripts_dir / "codocs.py"
    self_path = Path(__file__).resolve()
    if local_script.resolve() != self_path:  # avoid copying onto self
        if local_script.exists():
            skipped.append(".codocs/scripts/codocs.py")
        else:
            codocs_scripts_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self_path, local_script)
            installed.append(".codocs/scripts/codocs.py")

    # Copy hooks
    if not hooks_src.exists():
        return installed, skipped
    if not git_hooks_dir.exists():
        print("[codocs hooks] .git/hooks/ not found, skipping hook install", file=sys.stderr)
        return installed, skipped

    for hook_file in sorted(hooks_src.iterdir()):
        if hook_file.is_file():
            dest = git_hooks_dir / hook_file.name
            if dest.exists():
                skipped.append(hook_file.name)
            else:
                shutil.copy2(hook_file, dest)
                dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                installed.append(hook_file.name)

    return installed, skipped


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

def init(project_root: Path):
    config = load_config(project_root)
    entries = scan(project_root, config)
    ordered = bottom_up_order(entries)

    missing = [e for e in ordered if not e[3].exists()]
    existing = [e for e in ordered if e[3].exists()]

    # Install git hooks
    hooks_installed, hooks_skipped = install_hooks(project_root)
    if hooks_installed:
        print(f"[codocs hooks] installed: {', '.join(hooks_installed)}", file=sys.stderr)
    if hooks_skipped:
        print(f"[codocs hooks] skipped (already exist): {', '.join(hooks_skipped)}", file=sys.stderr)

    # Summary
    print(f"[codocs init] missing={len(missing)}  existing={len(existing)}", file=sys.stderr)

    if not missing:
        print("[codocs init] all MDs exist — nothing to do", file=sys.stderr)
        return

    print("=== codocs paths (bottom-up) — create in this order ===")
    for _, is_dir, _, md_path, _ in missing:
        try:
            rel = md_path.relative_to(project_root)
            tag = " [dir]" if is_dir else ""
            print(f"{str(rel).replace(chr(92), '/')}{tag}")
        except ValueError:
            print(str(md_path))


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------

def lint(project_root: Path) -> int:
    """Check codocs health: MISSING source→MD mappings, ORPHAN MDs, and BLOAT.

    [MISSING] — source file/dir exists but corresponding MD does not.
    [ORPHAN]  — MD exists but the corresponding source file/dir does not.
    [BLOAT]   — MD size exceeds 20% of the corresponding source size.
                For file MDs: MD size vs source file size.
                For dir MDs: MD size vs sum of all child file MDs under that dir.

    Returns the number of issues found (0 = clean).
    """
    codocs_dir = project_root / ".codocs" / "docs"

    if not codocs_dir.exists():
        print("[codocs lint] .codocs/ directory not found", file=sys.stderr)
        return 0

    issues: list[tuple[str, str, str]] = []

    # Phase 1: check for MISSING (source exists, MD does not)
    config = load_config(project_root)
    entries = scan(project_root, config)
    if get_lint_enabled(config, "missing"):
        for _, _, _, md_path, _ in entries:
            if not md_path.exists():
                try:
                    rel = md_path.relative_to(project_root)
                    issues.append(("MISSING", str(rel).replace("\\", "/"), "MD not found"))
                except ValueError:
                    issues.append(("MISSING", str(md_path), "MD not found"))

    # Phase 2: check for ORPHAN (MD exists, source does not or is excluded)
    if get_lint_enabled(config, "orphan"):
        exclude_paths = config.get("exclude_paths", [])
        for md_path in sorted(codocs_dir.rglob("*.md")):
            rel_md = md_path.relative_to(codocs_dir)

            # Skip _notes/ and scripts/
            if rel_md.parts[0] in ("_notes", "scripts"):
                continue

            rel_str = str(rel_md).replace("\\", "/")
            if not rel_str.endswith(".md"):
                continue
            rel_source_str = rel_str[:-3]

            source_path = project_root / rel_source_str
            if not source_path.exists():
                issues.append(("ORPHAN", f".codocs/docs/{rel_str}", f"{rel_source_str} not found"))
            elif is_excluded_path(source_path, project_root, exclude_paths):
                issues.append(("ORPHAN", f".codocs/docs/{rel_str}", f"{rel_source_str} is excluded by exclude_paths"))

    # Phase 3: check for BLOAT / THIN (MD size should be 10%–24% of source)
    # Uses a smooth threshold that accounts for fixed overhead in small files:
    #   BLOAT upper limit = BASE + (size - BASE) * 24%   (for size > BASE)
    #   THIN  lower limit = (size - BASE) * 10%          (for size > BASE, else 0)
    # This means files near the BASE threshold get generous allowance, converging
    # to the standard ratio as files grow larger.
    if get_lint_enabled(config, "bloat"):
        BLOAT_RATIO_LO = 0.10  # below this → [THIN]
        BLOAT_RATIO_HI = 0.24  # above this → [BLOAT]
        BLOAT_MIN_SRC = 1024   # base threshold for file MD
        BLOAT_MIN_DIR = 4096   # base threshold for dir MD

        def bloat_upper(size: int, base: int) -> float:
            """Max allowed MD size before BLOAT triggers."""
            if size <= base:
                return float('inf')  # skip check
            return base + (size - base) * BLOAT_RATIO_HI

        def thin_lower(size: int, base: int) -> float:
            """Min required MD size before THIN triggers."""
            if size <= base:
                return 0  # skip check
            return (size - base) * BLOAT_RATIO_LO

        for _, is_dir, source_path, md_path, _ in entries:
            if not md_path.exists():
                continue  # MISSING already reported

            md_size = md_path.stat().st_size
            if md_size == 0:
                continue

            if not is_dir:
                # File MD: compare against source file size
                if not source_path.exists():
                    continue
                src_size = source_path.stat().st_size
                if src_size <= BLOAT_MIN_SRC:
                    continue  # too small to enforce ratio
                upper = bloat_upper(src_size, BLOAT_MIN_SRC)
                lower = thin_lower(src_size, BLOAT_MIN_SRC)
                try:
                    rel = md_path.relative_to(project_root)
                    rel_str_md = str(rel).replace("\\", "/")
                except ValueError:
                    continue
                ratio = md_size / src_size
                if md_size > upper:
                    issues.append((
                        "BLOAT",
                        rel_str_md,
                        f"MD {md_size}B > smooth limit {upper:.0f}B of source {src_size}B "
                        f"({ratio*100:.0f}%)",
                    ))
                elif md_size < lower:
                    issues.append((
                        "THIN",
                        rel_str_md,
                        f"MD {md_size}B < smooth limit {lower:.0f}B of source {src_size}B "
                        f"({ratio*100:.0f}%)",
                    ))
            else:
                # Dir MD: compare against sum of all child file MDs under this dir
                try:
                    rel_dir = source_path.relative_to(project_root)
                except ValueError:
                    continue
                child_md_dir = codocs_dir / str(rel_dir).replace("\\", "/")
                child_md_total = sum(
                    p.stat().st_size
                    for p in child_md_dir.rglob("*.md")
                    if p.is_file() and p.resolve() != md_path.resolve()
                    and p.relative_to(codocs_dir).parts[0] not in ("_notes", "scripts")
                )
                if child_md_total == 0:
                    continue
                if child_md_total <= BLOAT_MIN_DIR:
                    continue  # too small; index table alone will exceed ratio
                upper = bloat_upper(child_md_total, BLOAT_MIN_DIR)
                lower = thin_lower(child_md_total, BLOAT_MIN_DIR)
                try:
                    rel = md_path.relative_to(project_root)
                    rel_str_md = str(rel).replace("\\", "/")
                except ValueError:
                    continue
                ratio = md_size / child_md_total
                if md_size > upper:
                    issues.append((
                        "BLOAT",
                        rel_str_md,
                        f"dir MD {md_size}B > smooth limit {upper:.0f}B of child MDs total "
                        f"{child_md_total}B ({ratio*100:.0f}%)",
                    ))
                elif md_size < lower:
                    issues.append((
                        "THIN",
                        rel_str_md,
                        f"dir MD {md_size}B < smooth limit {lower:.0f}B of child MDs total "
                        f"{child_md_total}B ({ratio*100:.0f}%)",
                    ))

    # Phase 4: validate codocs.json structure
    if get_lint_enabled(config, "config"):
        KNOWN_HOOKS = {"lint", "doc_change", "parent_sync", "dependencies"}
        KNOWN_LINT  = {"missing", "orphan", "bloat", "config"}

        hooks_val = config.get("hooks")
        if hooks_val is not None:
            if not isinstance(hooks_val, dict):
                issues.append(("CONFIG", "codocs.json", "hooks must be an object"))
            else:
                for k, v in hooks_val.items():
                    if k not in KNOWN_HOOKS:
                        issues.append(("CONFIG", "codocs.json", f"hooks.{k}: unknown key"))
                    elif not isinstance(v, bool):
                        issues.append(("CONFIG", "codocs.json", f"hooks.{k}: must be a bool"))

        lint_val = config.get("lint")
        if lint_val is not None:
            if not isinstance(lint_val, dict):
                issues.append(("CONFIG", "codocs.json", "lint must be an object"))
            else:
                for k, v in lint_val.items():
                    if k not in KNOWN_LINT:
                        issues.append(("CONFIG", "codocs.json", f"lint.{k}: unknown key"))
                    elif not isinstance(v, bool):
                        issues.append(("CONFIG", "codocs.json", f"lint.{k}: must be a bool"))

        deps_val = config.get("dependencies")
        if deps_val is not None:
            if not isinstance(deps_val, list):
                issues.append(("CONFIG", "codocs.json", "dependencies must be an array"))
            else:
                for i, entry in enumerate(deps_val):
                    if not isinstance(entry, dict):
                        issues.append(("CONFIG", "codocs.json", f"dependencies[{i}]: must be an object"))
                        continue
                    when = entry.get("when")
                    update = entry.get("update")
                    # validate when
                    if not isinstance(when, list) or len(when) == 0:
                        issues.append(("CONFIG", "codocs.json",
                                        f"dependencies[{i}].when: must be a non-empty array"))
                    elif not all(isinstance(w, str) for w in when):
                        issues.append(("CONFIG", "codocs.json",
                                        f"dependencies[{i}].when: all items must be strings"))
                    else:
                        for w in when:
                            if w.startswith(".codocs/docs/"):
                                issues.append(("CONFIG", "codocs.json",
                                               f"dependencies[{i}].when: .codocs/docs/ paths are unusual; "
                                               f"consider using update instead ({w})"))
                            wp = project_root / w
                            if not wp.exists():
                                issues.append(("CONFIG", "codocs.json",
                                               f"dependencies[{i}].when: path not found: {w}"))
                    # validate update
                    if not isinstance(update, list) or len(update) == 0:
                        issues.append(("CONFIG", "codocs.json",
                                        f"dependencies[{i}].update: must be a non-empty array"))
                    elif not all(isinstance(u, str) for u in update):
                        issues.append(("CONFIG", "codocs.json",
                                        f"dependencies[{i}].update: all items must be strings"))
                    else:
                        for u in update:
                            if not (u.startswith(".codocs/docs/") and u.endswith(".md")):
                                issues.append(("CONFIG", "codocs.json",
                                               f"dependencies[{i}].update: must start with .codocs/docs/ "
                                               f"and end with .md ({u})"))
                            else:
                                up = project_root / u
                                if not up.exists():
                                    issues.append(("CONFIG", "codocs.json",
                                                   f"dependencies[{i}].update: path not found: {u}"))

    if not issues:
        print("[codocs lint] OK no issues found")
        return 0

    THIN_HINT = (
        "→ 检查源文件是否有遗漏内容（隐性约定、算法选择、坑、跨文件关联等）；"
        "确认无遗漏后在 commit message 中加 ## codocs-skip 跳过"
    )
    BLOAT_HINT = (
        "→ 精简 MD，删除冗余描述或直接照搬源码的内容"
    )

    print(f"=== codocs lint: {len(issues)} issue(s) ===")
    for kind, path, reason in issues:
        print(f"[{kind}]  {path}  ({reason})")
        if kind == "THIN":
            print(f"         {THIN_HINT}")
        elif kind == "BLOAT":
            print(f"         {BLOAT_HINT}")

    return len(issues)


# ---------------------------------------------------------------------------
# Parent sync
# ---------------------------------------------------------------------------

def parent_sync(project_root: Path, changed_md_paths: list[str]) -> int:
    """
    Given a list of changed .codocs/ MD paths (relative to project root,
    e.g. '.codocs/src/Entity.cpp.md'), output the parent directory MDs that
    also need updating but are NOT in the changed set.

    Returns the count of missing parent MDs (0 = all covered).
    """
    codocs_dir = project_root / ".codocs" / "docs"

    # Resolve changed paths to absolute
    changed_abs: set[Path] = set()
    for p in changed_md_paths:
        abs_p = (project_root / p.replace("\\", "/")).resolve()
        changed_abs.add(abs_p)

    # Walk up from each changed MD to find required parent directory MDs
    required: set[Path] = set()
    for md_abs in changed_abs:
        try:
            rel = md_abs.relative_to(codocs_dir)  # e.g. src/Entity.cpp.md
        except ValueError:
            continue
        current = rel.parent  # e.g. src
        while str(current) not in (".", ""):
            parent_md = codocs_dir / (str(current).replace("\\", "/") + ".md")
            if parent_md.exists():
                required.add(parent_md)
            current = current.parent

    missing = sorted(required - changed_abs)

    for p in missing:
        try:
            print(str(p.relative_to(project_root)).replace("\\", "/"))
        except ValueError:
            print(str(p))

    return len(missing)


# ---------------------------------------------------------------------------
# Check deps
# ---------------------------------------------------------------------------

def check_deps(project_root: Path, staged_files: list[str]) -> int:
    """
    Given a list of staged file paths (relative to project root),
    print the .codocs/ MD paths that are required by dependency rules
    but not yet staged.

    Returns the count of missing paths (capped at 125), 0 if none.
    """
    if not staged_files:
        return 0

    config = load_config(project_root)
    deps = config.get("dependencies", [])
    if not deps:
        return 0

    def normalize(p: str) -> str:
        return p.lstrip("./").replace("\\", "/")

    staged_set = {normalize(f) for f in staged_files}

    missing: set[str] = set()
    for rule in deps:
        if not isinstance(rule, dict):
            continue
        when = rule.get("when")
        update = rule.get("update")
        if not isinstance(when, list) or not isinstance(update, list):
            continue
        triggered = any(normalize(w) in staged_set for w in when if isinstance(w, str))
        if triggered:
            for u in update:
                if isinstance(u, str) and normalize(u) not in staged_set:
                    missing.add(u)

    for path in sorted(missing):
        print(path)

    return min(len(missing), 125)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]
    do_lint = "--lint" in args
    do_parent_sync = "--parent-sync" in args
    do_check_deps = "--check-deps" in args
    args = [a for a in args if a not in ("--lint", "--parent-sync", "--check-deps")]

    if args:
        root = Path(args[0]).resolve()
        if not root.is_dir():
            print(f"Error: '{args[0]}' is not a directory", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            root = find_project_root(Path.cwd())
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"[codocs] project root: {root}", file=sys.stderr)

    if do_parent_sync:
        # Remaining args (after root) are the changed MD paths
        md_paths = args[1:]
        count = parent_sync(root, md_paths)
        sys.exit(min(count, 125))
    elif do_lint:
        issue_count = lint(root)
        sys.exit(min(issue_count, 125))
    elif do_check_deps:
        staged = args[1:]
        count = check_deps(root, staged)
        sys.exit(min(count, 125))
    else:
        init(root)
