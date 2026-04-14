#!/usr/bin/env python3
"""
codocs setup-hooks script

Installs codocs git hooks into a project via the more-hooks framework.
Also installs README.md files for both .more-hooks/ and .codocs/ so that
collaborators understand what these directories are for.

Usage:
    python .codocs/scripts/setup-hooks.py [project_root]

If project_root is omitted, walks up from cwd to find .codocs/config.json.

Hook source: .codocs/hooks/ in the project (must exist).

more-hooks lookup order:
  1. <project_root>/.more-hooks/more-hooks.py  ← project-local (preferred)
  2. ~/agent-data/skills/more-hooks/scripts/more-hooks.py
  3. ~/.claude-internal/skills/more-hooks/scripts/more-hooks.py

If more-hooks is not found anywhere, falls back to copying hooks directly
into .git/hooks/.
"""

import shutil
import stat
import sys
from pathlib import Path


# ── Helpers ───────────────────────────────────────────────────────────────────

def find_project_root(start: Path) -> Path:
    current = start.resolve()
    while True:
        if (current / ".codocs" / "config.json").is_file():
            return current
        parent = current.parent
        if parent == current:
            raise FileNotFoundError(
                ".codocs/config.json not found in any parent directory. "
                "Run from inside a repo initialized with codocs."
            )
        current = parent


def _find_more_hooks_script(project_root: Path) -> Path | None:
    """
    Locate more-hooks.py.  Project-local copy takes priority so that the
    project is self-contained even without the global skill installed.
    """
    candidates = [
        project_root / ".more-hooks" / "more-hooks.py",                                   # 1. project-local
        Path.home() / "agent-data" / "skills" / "more-hooks" / "scripts" / "more-hooks.py",  # 2. agent-data skill
        Path.home() / ".claude-internal" / "skills" / "more-hooks" / "scripts" / "more-hooks.py",  # 3. symlink
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _import_more_hooks(project_root: Path):
    """Dynamically import more_hooks module.  Returns module or None."""
    script = _find_more_hooks_script(project_root)
    if script is None:
        return None, None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("more_hooks", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, script
    except Exception as e:
        print(f"[codocs setup-hooks] WARNING: could not load more-hooks from {script}: {e}", file=sys.stderr)
        return None, script


def _ensure_readme(dest_dir: Path, readme_src: Path | None) -> None:
    """Copy README.md into dest_dir if a source exists and dest doesn't yet."""
    if readme_src is None or not readme_src.is_file():
        return
    dest = dest_dir / "README.md"
    shutil.copy2(readme_src, dest)


# ── Fallback: direct copy into .git/hooks/ ───────────────────────────────────

def _setup_hooks_direct(project_root: Path, hooks_src_dir: Path) -> None:
    git_dir = project_root / ".git"
    if git_dir.is_file():
        content = git_dir.read_text(encoding="utf-8").strip()
        if content.startswith("gitdir:"):
            git_dir = Path(content[len("gitdir:"):].strip()).resolve()
    if not git_dir.is_dir():
        print("[codocs setup-hooks] ERROR: not a git repo", file=sys.stderr)
        sys.exit(1)

    hooks_target = git_dir / "hooks"
    hooks_target.mkdir(exist_ok=True)

    installed, updated = [], []
    for hook_src in sorted(hooks_src_dir.iterdir()):
        if not hook_src.is_file():
            continue
        hook_dst = hooks_target / hook_src.name
        existed = hook_dst.exists()
        shutil.copy2(hook_src, hook_dst)
        hook_dst.chmod(hook_dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        (updated if existed else installed).append(hook_src.name)

    if installed:
        print(f"[codocs setup-hooks] installed (direct): {', '.join(installed)}", file=sys.stderr)
    if updated:
        print(f"[codocs setup-hooks] updated (direct): {', '.join(updated)}", file=sys.stderr)
    if not installed and not updated:
        print("[codocs setup-hooks] no hook files found in .codocs/hooks/", file=sys.stderr)


# ── Main ──────────────────────────────────────────────────────────────────────

def setup_hooks(project_root: Path) -> None:
    hooks_src_dir = project_root / ".codocs" / "hooks"
    if not hooks_src_dir.is_dir():
        print("[codocs setup-hooks] ERROR: .codocs/hooks/ not found", file=sys.stderr)
        sys.exit(1)

    # ── Install more-hooks into project if not already there ─────────────────
    project_more_hooks = project_root / ".more-hooks" / "more-hooks.py"
    if not project_more_hooks.exists():
        # Bootstrap: copy from skill directory
        skill_script = _find_more_hooks_script(project_root)  # will skip project-local since absent
        if skill_script is not None and skill_script != project_more_hooks:
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("more_hooks_tmp", skill_script)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                dest = mod.install_to_project(project_root)
                print(f"[codocs setup-hooks] bootstrapped more-hooks into project: {dest}", file=sys.stderr)
            except Exception as e:
                print(f"[codocs setup-hooks] WARNING: could not bootstrap more-hooks: {e}", file=sys.stderr)

    # ── Install codocs README into .codocs/ ───────────────────────────────────
    codocs_readme_src = Path(__file__).resolve().parent.parent / "docs" / "README.md"
    codocs_readme_dst = project_root / ".codocs" / "README.md"
    if codocs_readme_src.is_file() and not codocs_readme_dst.exists():
        shutil.copy2(codocs_readme_src, codocs_readme_dst)
        print(f"[codocs setup-hooks] installed .codocs/README.md", file=sys.stderr)

    # ── Load more-hooks (prefer project-local now that we may have just installed it) ──
    more_hooks, mh_script = _import_more_hooks(project_root)

    if more_hooks is not None:
        print(f"[codocs setup-hooks] using more-hooks from: {mh_script}", file=sys.stderr)
        for hook_src in sorted(hooks_src_dir.iterdir()):
            if not hook_src.is_file():
                continue
            hook_name = hook_src.name
            try:
                dest = more_hooks.register_hook(
                    project_root=project_root,
                    hook_name=hook_name,
                    script_id="codocs",
                    script_path=hook_src,
                    priority=50,
                    copy=False,   # symlink → always reflects .codocs/hooks/ as-is
                )
                print(f"[codocs setup-hooks] registered: {dest}", file=sys.stderr)
            except Exception as e:
                print(f"[codocs setup-hooks] WARNING: more-hooks failed for {hook_name}: {e}", file=sys.stderr)
                print("[codocs setup-hooks] falling back to direct install", file=sys.stderr)
                _setup_hooks_direct(project_root, hooks_src_dir)
                return
    else:
        print("[codocs setup-hooks] more-hooks not available, using direct install", file=sys.stderr)
        _setup_hooks_direct(project_root, hooks_src_dir)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).resolve()
        if not root.is_dir():
            print(f"Error: '{sys.argv[1]}' is not a directory", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            root = find_project_root(Path.cwd())
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"[codocs setup-hooks] project root: {root}", file=sys.stderr)
    setup_hooks(root)
