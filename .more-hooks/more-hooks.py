#!/usr/bin/env python3
"""
more-hooks — git hook dispatcher framework

Allows multiple tools/skills to register their own hook scripts
independently, without overwriting each other.

Layout:
  .git/hooks/<hook-name>         ← dispatcher (installed by this script)
  .git/hooks.d/<hook-name>/      ← registered hook scripts
      50-codocs                  ← symlink or copy to actual script

  .more-hooks/                   ← project-local copy of more-hooks (installed via install-to-project)
      more-hooks.py              ← this script, copied into the project

Usage:
  # Copy more-hooks.py into a project (run once per project)
  python more-hooks.py install-to-project /path/to/repo

  # Install dispatcher only
  python more-hooks.py install /path/to/repo

  # Register a hook script (called by tools like codocs)
  python more-hooks.py register /path/to/repo \\
      --hook pre-commit --id codocs --script /path/to/script [--priority 50]

  # Unregister
  python more-hooks.py unregister /path/to/repo --hook pre-commit --id codocs
  # or unregister all hooks for an id:
  python more-hooks.py unregister /path/to/repo --id codocs

  # List registered hooks
  python more-hooks.py list /path/to/repo

Python API (import as module):
  from more_hooks import register_hook, unregister_hook, install_dispatcher
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
from pathlib import Path


# ── Dispatcher template ──────────────────────────────────────────────────────

DISPATCHER_TEMPLATE = """\
#!/usr/bin/env bash
# more-hooks dispatcher — DO NOT EDIT MANUALLY
# Managed by: https://github.com/user/agent-data (more-hooks skill)
#
# Executes all scripts in .git/hooks.d/{hook_name}/ in sorted order.
# Any script returning non-zero aborts the chain immediately.

HOOK_NAME="{hook_name}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOKS_D="$(git rev-parse --git-dir)/../.git/hooks.d/$HOOK_NAME"

# Resolve to absolute path (handles worktrees etc.)
HOOKS_D="$(cd "$REPO_ROOT" && git rev-parse --git-dir)/hooks.d/$HOOK_NAME"

if [ ! -d "$HOOKS_D" ]; then
  exit 0
fi

# Execute scripts in sorted order, passing all args through
for script in $(ls "$HOOKS_D" | sort); do
  script_path="$HOOKS_D/$script"
  if [ ! -f "$script_path" ] || [ ! -x "$script_path" ]; then
    continue
  fi
  "$script_path" "$@"
  rc=$?
  if [ $rc -ne 0 ]; then
    exit $rc
  fi
done

exit 0
"""


# ── Helpers ──────────────────────────────────────────────────────────────────

def find_git_dir(project_root: Path) -> Path:
    """Return the .git directory (handles worktrees where .git is a file)."""
    git_path = project_root / ".git"
    if git_path.is_file():
        # worktree: .git is a file containing "gitdir: /path/to/actual/.git"
        content = git_path.read_text(encoding="utf-8").strip()
        if content.startswith("gitdir:"):
            return Path(content[len("gitdir:"):].strip()).resolve()
    if git_path.is_dir():
        return git_path
    raise FileNotFoundError(f"No .git found in {project_root}")


def make_executable(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def is_dispatcher(path: Path) -> bool:
    """Return True if the hook file was installed by more-hooks."""
    if not path.exists():
        return False
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        return "more-hooks dispatcher" in content
    except OSError:
        return False


# ── Public API ───────────────────────────────────────────────────────────────

def install_dispatcher(project_root: str | Path, hook_name: str) -> bool:
    """
    Install the dispatcher into .git/hooks/<hook_name>.

    Returns True if installed/updated, False if a non-dispatcher hook already
    exists there (caller should decide what to do).
    """
    project_root = Path(project_root).resolve()
    git_dir = find_git_dir(project_root)
    hook_path = git_dir / "hooks" / hook_name

    (git_dir / "hooks").mkdir(exist_ok=True)

    if hook_path.exists() and not is_dispatcher(hook_path):
        return False  # foreign hook, don't overwrite

    dispatcher_content = DISPATCHER_TEMPLATE.format(hook_name=hook_name)
    hook_path.write_text(dispatcher_content, encoding="utf-8", newline="\n")
    make_executable(hook_path)
    return True


def register_hook(
    project_root: str | Path,
    hook_name: str,
    script_id: str,
    script_path: str | Path,
    priority: int = 50,
    copy: bool = True,
) -> Path:
    """
    Register a hook script under .git/hooks.d/<hook_name>/<priority>-<id>.

    Args:
        project_root: Root of the git repository.
        hook_name:    Git hook name, e.g. "pre-commit".
        script_id:    Unique identifier for the registering tool, e.g. "codocs".
        script_path:  Path to the actual hook script to register.
        priority:     Execution order (lower = earlier). Default 50.
        copy:         If True (default), copy the script into hooks.d/.
                      If False, create a symlink instead.

    Returns:
        Path to the registered script inside hooks.d/.
    """
    project_root = Path(project_root).resolve()
    script_path = Path(script_path).resolve()
    git_dir = find_git_dir(project_root)

    hooks_d = git_dir / "hooks.d" / hook_name
    hooks_d.mkdir(parents=True, exist_ok=True)

    # Remove any existing registration for this id under this hook
    _remove_registration(hooks_d, script_id)

    dest = hooks_d / f"{priority:02d}-{script_id}"

    if copy:
        shutil.copy2(script_path, dest)
        make_executable(dest)
    else:
        if dest.is_symlink() or dest.exists():
            dest.unlink()
        dest.symlink_to(script_path)

    # Install dispatcher if not already present (or update if it is ours)
    installed = install_dispatcher(project_root, hook_name)
    if not installed:
        print(
            f"[more-hooks] WARNING: .git/hooks/{hook_name} already exists and is not "
            f"a more-hooks dispatcher. Registered script in hooks.d/ but dispatcher "
            f"is NOT active. Remove or rename the existing hook manually.",
            file=sys.stderr,
        )

    return dest


def unregister_hook(
    project_root: str | Path,
    script_id: str,
    hook_name: str | None = None,
) -> list[Path]:
    """
    Remove registration(s) for script_id.

    If hook_name is given, only removes from that hook's hooks.d/ dir.
    Otherwise removes from all hooks.

    Returns list of removed paths.
    """
    project_root = Path(project_root).resolve()
    git_dir = find_git_dir(project_root)
    hooks_d_root = git_dir / "hooks.d"
    removed = []

    if hook_name:
        dirs = [hooks_d_root / hook_name]
    else:
        dirs = list(hooks_d_root.iterdir()) if hooks_d_root.is_dir() else []

    for d in dirs:
        if d.is_dir():
            removed.extend(_remove_registration(d, script_id))

    return removed


def list_hooks(project_root: str | Path) -> dict[str, list[tuple[str, str]]]:
    """
    Return a dict mapping hook_name → list of (filename, resolved_path).
    """
    project_root = Path(project_root).resolve()
    git_dir = find_git_dir(project_root)
    hooks_d_root = git_dir / "hooks.d"
    result: dict[str, list[tuple[str, str]]] = {}

    if not hooks_d_root.is_dir():
        return result

    for hook_dir in sorted(hooks_d_root.iterdir()):
        if not hook_dir.is_dir():
            continue
        entries = []
        for f in sorted(hook_dir.iterdir()):
            if f.is_symlink():
                target = str(f.resolve())
            else:
                target = str(f)
            entries.append((f.name, target))
        result[hook_dir.name] = entries

    return result


# ── Internal helpers ─────────────────────────────────────────────────────────

def _remove_registration(hooks_d: Path, script_id: str) -> list[Path]:
    """Remove all files in hooks_d whose name ends with '-<script_id>'."""
    removed = []
    if not hooks_d.is_dir():
        return removed
    for f in hooks_d.iterdir():
        parts = f.name.split("-", 1)
        if len(parts) == 2 and parts[1] == script_id:
            f.unlink()
            removed.append(f)
    return removed


# ── CLI ──────────────────────────────────────────────────────────────────────

def install_to_project(project_root: str | Path) -> Path:
    """
    Copy more-hooks.py (and README.md if present) into <project_root>/.more-hooks/.

    This makes the project self-contained: anyone who clones it can run
    python .more-hooks/more-hooks.py without needing the global skill installed.

    Returns the path of the installed script.
    """
    project_root = Path(project_root).resolve()
    dest_dir = project_root / ".more-hooks"
    dest_dir.mkdir(exist_ok=True)

    this_script = Path(__file__).resolve()
    dest = dest_dir / "more-hooks.py"
    shutil.copy2(this_script, dest)
    make_executable(dest)

    # Also copy README.md from the skill's docs/ directory if present
    readme_src = this_script.parent.parent / "docs" / "README.md"
    if readme_src.is_file():
        shutil.copy2(readme_src, dest_dir / "README.md")

    return dest


def cmd_install_to_project(args: argparse.Namespace) -> int:
    dest = install_to_project(args.project_root)
    print(f"[more-hooks] installed to project: {dest}", file=sys.stderr)
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    hooks = args.hooks or ["pre-commit", "commit-msg", "pre-push", "post-checkout"]
    for hook in hooks:
        ok = install_dispatcher(root, hook)
        if ok:
            print(f"[more-hooks] installed dispatcher: .git/hooks/{hook}", file=sys.stderr)
        else:
            print(
                f"[more-hooks] SKIPPED .git/hooks/{hook} (non-dispatcher file exists)",
                file=sys.stderr,
            )
    return 0


def cmd_register(args: argparse.Namespace) -> int:
    dest = register_hook(
        project_root=args.project_root,
        hook_name=args.hook,
        script_id=args.id,
        script_path=args.script,
        priority=args.priority,
        copy=not args.symlink,
    )
    print(f"[more-hooks] registered: {dest}", file=sys.stderr)
    return 0


def cmd_unregister(args: argparse.Namespace) -> int:
    removed = unregister_hook(
        project_root=args.project_root,
        script_id=args.id,
        hook_name=getattr(args, "hook", None),
    )
    if removed:
        for p in removed:
            print(f"[more-hooks] removed: {p}", file=sys.stderr)
    else:
        print(f"[more-hooks] nothing to remove for id={args.id}", file=sys.stderr)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    hooks = list_hooks(args.project_root)
    if not hooks:
        print("(no hooks registered)", file=sys.stderr)
        return 0
    for hook_name, entries in hooks.items():
        print(f"{hook_name}/")
        for fname, target in entries:
            print(f"  {fname}  →  {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="more-hooks",
        description="Git hook dispatcher framework",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # install-to-project
    pip = sub.add_parser("install-to-project", help="Copy more-hooks.py into .more-hooks/ in a project")
    pip.add_argument("project_root", help="Git repository root")

    # install
    pi = sub.add_parser("install", help="Install dispatcher(s) into .git/hooks/")
    pi.add_argument("project_root", help="Git repository root")
    pi.add_argument("--hooks", nargs="+", help="Hook names to install (default: common set)")

    # register
    pr = sub.add_parser("register", help="Register a hook script")
    pr.add_argument("project_root", help="Git repository root")
    pr.add_argument("--hook", required=True, help="Hook name, e.g. pre-commit")
    pr.add_argument("--id", required=True, help="Unique id for this registration, e.g. codocs")
    pr.add_argument("--script", required=True, help="Path to the hook script")
    pr.add_argument("--priority", type=int, default=50, help="Execution order (default: 50)")
    pr.add_argument("--symlink", action="store_true", help="Symlink instead of copy")

    # unregister
    pu = sub.add_parser("unregister", help="Remove a registered hook")
    pu.add_argument("project_root", help="Git repository root")
    pu.add_argument("--id", required=True, help="Id to remove")
    pu.add_argument("--hook", help="Limit removal to this hook name")

    # list
    pl = sub.add_parser("list", help="List registered hooks")
    pl.add_argument("project_root", help="Git repository root")

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {
        "install-to-project": cmd_install_to_project,
        "install": cmd_install,
        "register": cmd_register,
        "unregister": cmd_unregister,
        "list": cmd_list,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
