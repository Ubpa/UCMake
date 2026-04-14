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

# Fix Windows console encoding for Unicode output (GBK console crashes on non-BMP chars).
# Strategy: try reconfigure() first (respects environment), fall back to TextIOWrapper
# which directly replaces the stream and always works, even when stdout is a pipe.
def _fix_stream_encoding(stream, attr_name: str):
    try:
        enc = getattr(stream, "encoding", None)
        if enc and enc.lower() in ("utf-8", "utf_8", "utf8"):
            return  # already UTF-8, nothing to do
        # Try reconfigure first (preferred, non-destructive)
        stream.reconfigure(encoding="utf-8", errors="replace")
        if getattr(stream, "encoding", "").lower() in ("utf-8", "utf_8", "utf8"):
            return  # reconfigure succeeded
    except Exception:
        pass
    # reconfigure failed or had no effect — replace with a UTF-8 TextIOWrapper
    import io
    buf = getattr(stream, "buffer", None)
    if buf is not None:
        try:
            setattr(sys, attr_name,
                    io.TextIOWrapper(buf, encoding="utf-8", errors="replace",
                                     line_buffering=True))
        except Exception:
            pass  # last resort: give up, individual print sites handle it

_fix_stream_encoding(sys.stdout, "stdout")
_fix_stream_encoding(sys.stderr, "stderr")
import stat
import shutil
import fnmatch
import hashlib
import datetime
import tempfile
from pathlib import Path
from urllib.parse import quote

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


# ---------------------------------------------------------------------------
# Front matter helpers
# ---------------------------------------------------------------------------

def parse_md_frontmatter(text: str) -> "tuple[dict | None, str]":
    """Parse YAML front matter from Markdown text.

    Returns (metadata_dict, body_text).
    If no front matter, returns (None, full_text).
    The body_text does NOT include the leading '---...---' block.
    """
    if not text.startswith("---"):
        return None, text

    # The opening '---' must be exactly on its own line
    first_newline = text.find("\n")
    if first_newline == -1:
        return None, text
    first_line = text[:first_newline].rstrip("\r")
    if first_line != "---":
        return None, text

    # Find closing '---'
    rest = text[first_newline + 1:]
    closing = -1
    for i, line in enumerate(rest.splitlines(keepends=True)):
        stripped = line.rstrip("\r\n")
        if stripped == "---":
            closing = i
            break

    if closing == -1:
        return None, text

    lines = rest.splitlines(keepends=True)
    yaml_lines = lines[:closing]
    body_lines = lines[closing + 1:]

    yaml_text = "".join(yaml_lines)
    body_text = "".join(body_lines)

    # Strip a single leading newline from body to avoid double blank line
    if body_text.startswith("\n"):
        body_text = body_text[1:]

    if _YAML_AVAILABLE:
        try:
            metadata = _yaml.safe_load(yaml_text)
        except Exception:
            return None, text
    else:
        # Minimal fallback: just return raw string as metadata (not a dict)
        return None, text

    if not isinstance(metadata, dict):
        return None, text

    return metadata, body_text


def render_md_frontmatter(metadata: dict, body: str) -> str:
    """Render updated front matter back into a Markdown file.

    Preserves body exactly. Returns the full file content as:
        ---
        <yaml>
        ---
        <body>
    """
    if _YAML_AVAILABLE:
        yaml_text = _yaml.dump(metadata, allow_unicode=True, default_flow_style=False, sort_keys=False)
    else:
        raise RuntimeError("PyYAML is required for render_md_frontmatter")

    # Ensure body doesn't start with blank line (avoid double blank after ---)
    # Strip at most ONE leading newline to match parse_md_frontmatter's single-strip behavior.
    body_out = body[1:] if body.startswith("\n") else body

    return f"---\n{yaml_text}---\n{body_out}"


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def normalize_text_bytes(data: bytes) -> bytes:
    """Normalize CRLF to LF. Returns bytes."""
    return data.replace(b"\r\n", b"\n")


def compute_file_hash(path: Path) -> str:
    """Compute sha256 hash of a file.
    - For .md files: strip YAML front matter, hash only body (text-lf-sha256)
    - For other files: hash full content with CRLF->LF normalization
    Returns 'sha256:<hex>'.
    Raises FileNotFoundError if path does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    raw = path.read_bytes()

    if path.suffix.lower() == ".md":
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        _, body = parse_md_frontmatter(text)
        normalized = normalize_text_bytes(body.encode("utf-8"))
    else:
        normalized = normalize_text_bytes(raw)

    digest = hashlib.sha256(normalized).hexdigest()
    return f"sha256:{digest}"


def compute_dependency_hash(project_root: Path, dep_paths: list[str]) -> str:
    """Compute dep_hash from a list of dependency paths (relative to project_root).
    Procedure: normalize paths, deduplicate, sort, compute per-file hash,
    serialize as 'path\\0hash', concatenate, hash with sha256.
    Returns 'sha256:<hex>'. Returns 'sha256:<hash-of-empty>' if dep_paths is empty.
    Raises FileNotFoundError if any dependency path does not exist on disk.
    """
    normalized = list({p.replace("\\", "/") for p in dep_paths})
    normalized.sort()

    parts = []
    for rel_path in normalized:
        abs_path = project_root / rel_path
        file_hash = compute_file_hash(abs_path)
        parts.append(f"{rel_path}\x00{file_hash}")

    payload = "".join(parts).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return f"sha256:{digest}"


# Required fields shared by both source types
_REQUIRED_COMMON = ("schema", "source_type", "source_path", "explicit_deps", "dep_hash", "hash_mode", "verified_at")
_REQUIRED_FILE   = ("source_hash",)
_REQUIRED_DIR    = ("entries_hash",)


def validate_frontmatter(metadata: dict, source_type: str) -> "list[str]":
    """Validate that all required fields are present and schema=1.

    Returns a list of reason strings (empty list = valid).
    source_type is 'file' or 'dir'.
    """
    reasons: list[str] = []

    codocs = metadata.get("codocs")
    if not isinstance(codocs, dict):
        reasons.append("missing 'codocs' key in front matter")
        return reasons

    for field in _REQUIRED_COMMON:
        if field not in codocs:
            reasons.append(f"missing required field: codocs.{field}")

    if source_type == "file":
        for field in _REQUIRED_FILE:
            if field not in codocs:
                reasons.append(f"missing required field for file doc: codocs.{field}")
    elif source_type == "dir":
        for field in _REQUIRED_DIR:
            if field not in codocs:
                reasons.append(f"missing required field for dir doc: codocs.{field}")
    else:
        reasons.append(f"unknown source_type: {source_type!r}")

    # Validate schema version
    schema = codocs.get("schema")
    if schema != 1:
        reasons.append(f"schema must be 1 (got {schema!r})")

    return reasons


# ---------------------------------------------------------------------------
# Staleness
# ---------------------------------------------------------------------------

def compute_entries_hash(codocs_docs_dir: Path, source_dir_rel: str) -> str:
    """Compute entries_hash for a directory doc.

    Hashes the direct child MD bodies under codocs_docs_dir / source_dir_rel.
    - child file MD: F\\0<rel-md-path>\\0<sha256(md-body)>
    - child subdir MD present: D\\0<rel-md-path>\\0<sha256(md-body)>
    - child subdir MD absent: D\\0<subdir-name>
    Records sorted lexicographically, joined with \\n, then sha256'd.
    Returns 'sha256:<hex>'.

    codocs_docs_dir: path to the .codocs/docs/ directory
    source_dir_rel: path of source directory relative to project root (e.g. 'src/Runtime')
    """
    child_md_dir = codocs_docs_dir / source_dir_rel.replace("\\", "/")

    if not child_md_dir.exists():
        digest = hashlib.sha256(b"").hexdigest()
        return f"sha256:{digest}"

    records: list[str] = []

    all_items = list(child_md_dir.iterdir())
    # Names of direct subdirectories (used to detect "dir MD with sibling dir")
    dir_names = {c.name for c in all_items if c.is_dir()}

    for child in all_items:
        if child.is_file() and child.suffix.lower() == ".md":
            stem = child.stem  # e.g. "foo.cpp" or "Runtime"
            # Directory docs: stem has no dot, OR there is a sibling directory with that name
            is_dir_doc = ("." not in stem) or (stem in dir_names)
            rel_path = str(child.relative_to(codocs_docs_dir)).replace("\\", "/")
            body_hash = compute_file_hash(child)
            prefix = "D" if is_dir_doc else "F"
            records.append(f"{prefix}\x00{rel_path}\x00{body_hash}")
        elif child.is_dir():
            # Only add a D-absent record when there is NO sibling .md for this dir;
            # if Runtime.md exists, it was already added in the file loop above.
            subdir_md = child_md_dir / (child.name + ".md")
            if not subdir_md.exists():
                records.append(f"D\x00{child.name}")

    records.sort()
    payload = "\n".join(records).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return f"sha256:{digest}"


def classify_file_doc_stale(
    project_root: Path,
    md_path: Path,
) -> list[str]:
    """Check if a file doc MD is stale. Returns list of reason strings (empty = fresh).

    Reads the MD, validates front matter, computes current hashes, compares.
    dep_hash is computed from explicit_deps only (implicit/rule-based deps not in scope for A3).
    """
    if not md_path.exists():
        return ["metadata missing"]

    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception:
        return ["metadata missing"]

    meta, _ = parse_md_frontmatter(text)
    if meta is None:
        return ["metadata missing"]

    reasons: list[str] = []

    # Schema / field validation
    schema_reasons = validate_frontmatter(meta, "file")
    if schema_reasons:
        reasons.append("schema outdated")
        return reasons

    codocs = meta["codocs"]
    source_path_rel: str = codocs.get("source_path", "")
    source_path = project_root / source_path_rel

    # source_path existence
    if not source_path.exists():
        reasons.append("source_path not found")
        return reasons

    # source_hash check
    try:
        current_source_hash = compute_file_hash(source_path)
        if current_source_hash != codocs.get("source_hash"):
            reasons.append("source_hash mismatch")
    except Exception as exc:
        reasons.append(f"source hash error: {exc}")

    # dep_hash check (explicit_deps only)
    explicit_deps: list[str] = codocs.get("explicit_deps") or []
    try:
        current_dep_hash = compute_dependency_hash(project_root, explicit_deps)
        if current_dep_hash != codocs.get("dep_hash"):
            reasons.append("dep_hash mismatch")
    except FileNotFoundError as exc:
        reasons.append(f"dep file not found: {exc}")
    except Exception as exc:
        reasons.append(f"dep hash error: {exc}")

    return reasons


def classify_dir_doc_stale(
    project_root: Path,
    md_path: Path,
) -> list[str]:
    """Check if a directory doc MD is stale. Returns list of reason strings (empty = fresh).

    Reads the MD, validates front matter, computes current hashes, compares.
    dep_hash is computed from explicit_deps only.
    """
    if not md_path.exists():
        return ["metadata missing"]

    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception:
        return ["metadata missing"]

    meta, _ = parse_md_frontmatter(text)
    if meta is None:
        return ["metadata missing"]

    reasons: list[str] = []

    # Schema / field validation
    schema_reasons = validate_frontmatter(meta, "dir")
    if schema_reasons:
        reasons.append("schema outdated")
        return reasons

    codocs = meta["codocs"]
    source_path_rel: str = codocs.get("source_path", "")
    source_path = project_root / source_path_rel

    # source_path existence (must be a directory)
    if not source_path.exists():
        reasons.append("source_path not found")
        return reasons
    if not source_path.is_dir():
        reasons.append("source_path is not a directory")
        return reasons

    # entries_hash check
    codocs_docs_dir = project_root / ".codocs" / "docs"
    try:
        current_entries_hash = compute_entries_hash(codocs_docs_dir, source_path_rel)
        if current_entries_hash != codocs.get("entries_hash"):
            reasons.append("entries_hash mismatch")
    except Exception as exc:
        reasons.append(f"entries hash error: {exc}")

    # dep_hash check (explicit_deps only)
    explicit_deps: list[str] = codocs.get("explicit_deps") or []
    try:
        current_dep_hash = compute_dependency_hash(project_root, explicit_deps)
        if current_dep_hash != codocs.get("dep_hash"):
            reasons.append("dep_hash mismatch")
    except FileNotFoundError as exc:
        reasons.append(f"dep file not found: {exc}")
    except Exception as exc:
        reasons.append(f"dep hash error: {exc}")

    return reasons


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
        codocs_scripts_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self_path, local_script)
        installed.append(".codocs/scripts/codocs.py")

    # Copy README.md to .codocs/README.md (always overwrite)
    readme_src = SKILL_DIR / "docs" / "README.md"
    readme_dst = project_root / ".codocs" / "README.md"
    if readme_src.exists():
        shutil.copy2(readme_src, readme_dst)
        installed.append(".codocs/README.md")

    # Copy hooks
    if not hooks_src.exists():
        return installed, skipped
    if not git_hooks_dir.exists():
        print("[codocs hooks] .git/hooks/ not found, skipping hook install", file=sys.stderr)
        return installed, skipped

    for hook_file in sorted(hooks_src.iterdir()):
        if hook_file.is_file():
            dest = git_hooks_dir / hook_file.name
            # Write with LF line endings to avoid CRLF issues on Windows
            content = hook_file.read_text(encoding="utf-8", errors="replace")
            dest.write_text(content, encoding="utf-8", newline="\n")
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
    all_codocs_mds = sorted(codocs_dir.rglob("*.md"))  # compute once, reused in Phase 5
    if get_lint_enabled(config, "orphan"):
        exclude_paths = config.get("exclude_paths", [])
        for md_path in all_codocs_mds:
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
        KNOWN_LINT  = {"missing", "orphan", "bloat", "config", "stale"}

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

    # Phase 5: Stale checks (STALE_FILE, STALE_DIR)
    if get_lint_enabled(config, "stale"):
        # Build set of tracked MD paths (resolved)
        tracked_md_set = {e[3].resolve() for e in entries}

        if codocs_dir.exists():
            for md_path in all_codocs_mds:
                rel_md = md_path.relative_to(codocs_dir)
                # Skip _notes/ and scripts/
                if rel_md.parts[0] in ("_notes", "scripts"):
                    continue
                # Only check tracked MDs
                if md_path.resolve() not in tracked_md_set:
                    continue

                # Determine source_type from front matter
                try:
                    text = md_path.read_text(encoding="utf-8")
                    meta, _ = parse_md_frontmatter(text)
                except Exception:
                    meta = None

                if meta is not None and isinstance(meta, dict) and "codocs" in meta:
                    source_type = meta["codocs"].get("source_type", "file")
                else:
                    source_type = "file"  # no front matter → treat as stale file doc

                try:
                    rel = str(md_path.relative_to(project_root)).replace("\\", "/")
                except ValueError:
                    rel = str(md_path)

                if source_type == "dir":
                    reasons = classify_dir_doc_stale(project_root, md_path)
                    if reasons:
                        issues.append(("STALE_DIR", rel, "; ".join(reasons)))
                else:
                    reasons = classify_file_doc_stale(project_root, md_path)
                    if reasons:
                        issues.append(("STALE_FILE", rel, "; ".join(reasons)))

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
    STALE_DIR_HINT = (
        "→ 目录文档不只是索引，还应包含架构说明、设计决策、模块关系等。\n"
        "         请 Read 该文档，确认内容（不只是索引表）是否仍准确，然后 review-stale + refresh-hash"
    )

    print(f"=== codocs lint: {len(issues)} issue(s) ===")
    for kind, path, reason in issues:
        print(f"[{kind}]  {path}  ({reason})")
        if kind == "THIN":
            print(f"         {THIN_HINT}")
        elif kind == "BLOAT":
            print(f"         {BLOAT_HINT}")
        elif kind == "STALE_DIR":
            print(f"         {STALE_DIR_HINT}")

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

    # Walk up ONE level from each changed MD to find the direct parent directory MD.
    # We only require the immediate parent — if that parent is also committed, the
    # grandparent check is deferred to the commit that updates the parent MD itself.
    required: set[Path] = set()
    for md_abs in changed_abs:
        try:
            rel = md_abs.relative_to(codocs_dir)  # e.g. src/Entity.cpp.md
        except ValueError:
            continue
        parent = rel.parent  # e.g. src
        if str(parent) in (".", ""):
            continue  # already at root level, no parent MD to require
        parent_md = codocs_dir / (str(parent).replace("\\", "/") + ".md")
        if parent_md.exists():
            required.add(parent_md)

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
# Explain hash
# ---------------------------------------------------------------------------

def explain_hash(project_root: Path, md_path: Path) -> None:
    """Print a human-readable hash breakdown for a given MD file.

    Usage:
        python codocs.py [project_root] --explain-hash .codocs/docs/src/Foo.cpp.md
    """
    try:
        rel_display = str(md_path.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        rel_display = str(md_path)

    print(f"=== explain-hash: {rel_display} ===")
    print()

    if not md_path.exists():
        print(f"ERROR: file not found: {md_path}")
        return

    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"ERROR: could not read file: {exc}")
        return

    meta, _ = parse_md_frontmatter(text)
    if meta is None or not isinstance(meta, dict) or "codocs" not in meta:
        print(f"ERROR: no codocs front matter found in {md_path.name}")
        return

    codocs = meta["codocs"]
    source_type = codocs.get("source_type", "file")
    source_path_rel = codocs.get("source_path", "")
    source_path = project_root / source_path_rel

    if source_type == "file":
        print("Source:")
        print(f"  source_type : file")
        print(f"  source_path : {source_path_rel}")

        stored_hash = codocs.get("source_hash", "<missing>")
        print(f"  source_hash (stored)  : {stored_hash}")
        try:
            current_hash = compute_file_hash(source_path)
        except Exception as exc:
            current_hash = f"<error: {exc}>"
        print(f"  source_hash (current) : {current_hash}")
        if current_hash == stored_hash:
            print("  status: MATCH")
        else:
            print("  status: MISMATCH")
        print()

        # Explicit deps
        explicit_deps: list[str] = codocs.get("explicit_deps") or []
        print("Explicit deps:")
        if not explicit_deps:
            print("  (none)")
        else:
            stored_dep_hash = codocs.get("dep_hash", "<missing>")
            for dep_rel in explicit_deps:
                dep_path = project_root / dep_rel
                print(f"  {dep_rel}")
                try:
                    current_per_file = compute_file_hash(dep_path)
                    print(f"    current file hash : {current_per_file}")
                except Exception as exc:
                    print(f"    current file hash : <error: {exc}>")
            # Show overall dep_hash
            try:
                current_dep_hash = compute_dependency_hash(project_root, explicit_deps)
            except Exception as exc:
                current_dep_hash = f"<error: {exc}>"
            print(f"  stored dep_hash  : {stored_dep_hash}")
            print(f"  current dep_hash : {current_dep_hash}")
            if current_dep_hash == stored_dep_hash:
                print("  status: MATCH")
            else:
                print("  status: MISMATCH")
        print()

        # Stale reasons (built inline from already-computed values)
        reasons: list[str] = []
        if current_hash != stored_hash:
            reasons.append("source_hash mismatch")
        _stored_dep = codocs.get("dep_hash", "<missing>")
        try:
            _current_dep = compute_dependency_hash(project_root, explicit_deps)
            if _current_dep != _stored_dep:
                reasons.append("dep_hash mismatch")
        except FileNotFoundError as exc:
            reasons.append(f"dep file not found: {exc}")
        except Exception as exc:
            reasons.append(f"dep hash error: {exc}")

    else:  # dir
        print("Source:")
        print(f"  source_type : dir")
        print(f"  source_path : {source_path_rel}")
        print()

        print("Entries:")
        stored_entries_hash = codocs.get("entries_hash", "<missing>")
        codocs_docs_dir = project_root / ".codocs" / "docs"
        try:
            current_entries_hash = compute_entries_hash(codocs_docs_dir, source_path_rel)
        except Exception as exc:
            current_entries_hash = f"<error: {exc}>"

        print(f"  entries_hash (stored)  : {stored_entries_hash}")
        print(f"  entries_hash (current) : {current_entries_hash}")
        if current_entries_hash == stored_entries_hash:
            print("  status: MATCH")
        else:
            print("  status: MISMATCH")
        print()

        # Explicit deps
        explicit_deps = codocs.get("explicit_deps") or []
        print("Explicit deps:")
        if not explicit_deps:
            print("  (none)")
        else:
            stored_dep_hash = codocs.get("dep_hash", "<missing>")
            for dep_rel in explicit_deps:
                dep_path = project_root / dep_rel
                print(f"  {dep_rel}")
                try:
                    current_per_file = compute_file_hash(dep_path)
                    print(f"    current file hash : {current_per_file}")
                except Exception as exc:
                    print(f"    current file hash : <error: {exc}>")
            try:
                current_dep_hash = compute_dependency_hash(project_root, explicit_deps)
            except Exception as exc:
                current_dep_hash = f"<error: {exc}>"
            print(f"  stored dep_hash  : {stored_dep_hash}")
            print(f"  current dep_hash : {current_dep_hash}")
            if current_dep_hash == stored_dep_hash:
                print("  status: MATCH")
            else:
                print("  status: MISMATCH")
        print()

        # Stale reasons (built inline from already-computed values)
        reasons = []
        if current_entries_hash != stored_entries_hash:
            reasons.append("entries_hash mismatch")
        _stored_dep_dir = codocs.get("dep_hash", "<missing>")
        try:
            _current_dep_dir = compute_dependency_hash(project_root, explicit_deps)
            if _current_dep_dir != _stored_dep_dir:
                reasons.append("dep_hash mismatch")
        except FileNotFoundError as exc:
            reasons.append(f"dep file not found: {exc}")
        except Exception as exc:
            reasons.append(f"dep hash error: {exc}")

    print("Stale reasons:")
    if not reasons:
        print("  (none)")
    else:
        for r in reasons:
            print(f"  {r}")


# ---------------------------------------------------------------------------
# Review & Refresh
# ---------------------------------------------------------------------------

def find_git_root(start: Path) -> Path:
    """Walk up from start to find the .git directory. Raises if not found."""
    current = start.resolve()
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            raise FileNotFoundError(
                ".git directory not found in any parent directory."
            )
        current = parent


def get_state_dir(git_root: "Path | None", project_root: Path) -> Path:
    """Return the directory to store codocs state files.

    In a git repo, uses .git/.codocs-state/ (invisible to git, never committed).
    Outside a git repo, falls back to .codocs/state/ to avoid creating stray .git/.
    """
    if git_root is not None:
        return git_root / ".git" / ".codocs-state"
    else:
        return project_root / ".codocs" / "state"


def get_receipt_path(state_dir: Path, md_path: Path, project_root: Path) -> Path:
    """Return the receipt file path under state_dir.

    Percent-encodes '/' so the full relative path is a single filename component,
    avoiding collisions from path components that contain '__'.
    Example: .codocs/docs/src/Foo.cpp.md -> %2Ecodocs%2Fdocs%2Fsrc%2FFoo.cpp.md.json
    """
    try:
        rel_str = str(md_path.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        rel_str = str(md_path).replace("\\", "/")
    # Percent-encode '/' (and only '/') so the whole path is one filename
    safe_name = quote(rel_str, safe="") + ".json"
    return state_dir / safe_name


def _compute_md_body_hash(md_path: Path) -> str:
    """Compute sha256 of the MD body (front matter stripped)."""
    text = md_path.read_text(encoding="utf-8")
    _, body = parse_md_frontmatter(text)
    normalized = normalize_text_bytes(body.encode("utf-8"))
    digest = hashlib.sha256(normalized).hexdigest()
    return f"sha256:{digest}"


def write_receipt(state_dir: Path, project_root: Path, md_path: Path, stale_reasons: list) -> Path:
    """Compute current hashes, write receipt JSON, return receipt path."""
    text = md_path.read_text(encoding="utf-8")
    meta, _ = parse_md_frontmatter(text)
    codocs = meta["codocs"] if (meta and "codocs" in meta) else {}
    source_type = codocs.get("source_type", "file")

    source_path_rel = codocs.get("source_path", "")
    explicit_deps = codocs.get("explicit_deps") or []

    # Compute current hashes at review time
    try:
        source_hash_at_review = compute_file_hash(project_root / source_path_rel)
    except Exception:
        source_hash_at_review = None

    try:
        dep_hash_at_review = compute_dependency_hash(project_root, explicit_deps)
    except Exception:
        dep_hash_at_review = None

    entries_hash_at_review = None
    if source_type == "dir":
        codocs_docs_dir = project_root / ".codocs" / "docs"
        try:
            entries_hash_at_review = compute_entries_hash(codocs_docs_dir, source_path_rel)
        except Exception:
            entries_hash_at_review = None

    md_body_hash_at_review = _compute_md_body_hash(md_path)

    # Derive md_path relative to project_root for storage
    try:
        md_rel_str = str(md_path.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        md_rel_str = str(md_path).replace("\\", "/")

    reviewed_at = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()

    receipt = {
        "md_path": md_rel_str,
        "reviewed_at": reviewed_at,
        "stale_reasons": stale_reasons,
        "source_hash_at_review": source_hash_at_review,
        "dep_hash_at_review": dep_hash_at_review,
        "entries_hash_at_review": entries_hash_at_review,
        "md_body_hash_at_review": md_body_hash_at_review,
    }

    receipt_path = get_receipt_path(state_dir, md_path, project_root)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    return receipt_path


def read_receipt(state_dir: Path, md_path: Path, project_root: Path) -> "dict | None":
    """Read receipt JSON. Returns None if not found."""
    receipt_path = get_receipt_path(state_dir, md_path, project_root)
    if not receipt_path.exists():
        return None
    try:
        text = receipt_path.read_text(encoding="utf-8")
        return json.loads(text)
    except Exception:
        return None


def review_stale(project_root: Path, md_path: Path) -> None:
    """Implements the review-stale command."""
    # Determine source type from front matter
    try:
        text = md_path.read_text(encoding="utf-8")
        meta, body = parse_md_frontmatter(text)
    except Exception as exc:
        print(f"Error reading {md_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    source_type = "file"
    if meta and isinstance(meta, dict) and "codocs" in meta:
        source_type = meta["codocs"].get("source_type", "file")

    if source_type == "dir":
        reasons = classify_dir_doc_stale(project_root, md_path)
    else:
        reasons = classify_file_doc_stale(project_root, md_path)

    try:
        rel_display = str(md_path.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        rel_display = str(md_path)

    print(f"=== review-stale: {rel_display} ===")
    print()

    if not reasons:
        print("Not stale — no review needed.")
        return

    print("Stale reasons:")
    for r in reasons:
        print(f"  - {r}")
    print()

    print("--- Markdown body for review ---")
    text_to_print = body if body is not None else ""
    try:
        print(text_to_print)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((text_to_print + "\n").encode("utf-8", errors="replace"))
    print("--- end ---")
    print()

    # Find git root and write receipt
    try:
        git_root = find_git_root(project_root)
    except FileNotFoundError:
        git_root = None

    state_dir = get_state_dir(git_root, project_root)
    receipt_path = write_receipt(state_dir, project_root, md_path, reasons)

    try:
        receipt_display = str(receipt_path.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        receipt_display = str(receipt_path)

    print(f"Review receipt stored at: {receipt_display}")
    print()
    print("  如果你打算编辑此 MD，编辑完成后直接运行：")
    print(f"    python .codocs/scripts/codocs.py . refresh-hash --after-edit {rel_display}")
    print("  （--after-edit 表示 MD 已由你亲自编辑，跳过 body hash 校验）")


def refresh_hash(project_root: Path, md_path: Path, after_edit: bool = False) -> None:
    """Implements the refresh-hash command. Exits non-zero on failure.

    after_edit: if True, skip the MD body hash check. Use this when you have
    intentionally edited the MD body after review-stale and want to refresh
    without re-running review-stale again.
    """
    try:
        git_root = find_git_root(project_root)
    except FileNotFoundError:
        git_root = None

    state_dir = get_state_dir(git_root, project_root)
    receipt = read_receipt(state_dir, md_path, project_root)
    if receipt is None:
        print(f"Error: no review receipt found for {md_path}. "
              f"Run 'review-stale' first.", file=sys.stderr)
        sys.exit(1)

    # Read current MD
    try:
        text = md_path.read_text(encoding="utf-8")
        meta, body = parse_md_frontmatter(text)
    except Exception as exc:
        print(f"Error reading {md_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    if meta is None or "codocs" not in meta:
        print(f"Error: no codocs front matter in {md_path}", file=sys.stderr)
        sys.exit(1)

    codocs = meta["codocs"]
    source_type = codocs.get("source_type", "file")
    source_path_rel = codocs.get("source_path", "")
    explicit_deps = codocs.get("explicit_deps") or []

    # Check 1: MD body has not changed since review
    # --after-edit skips this check: it signals that the user intentionally
    # edited the MD body after review-stale and is responsible for the content.
    if after_edit:
        print("(--after-edit: skipping body hash check, assuming intentional edit)")
    else:
        current_body_hash = _compute_md_body_hash(md_path)
        if current_body_hash != receipt.get("md_body_hash_at_review"):
            print("Error: MD body has changed since review. "
                  "If you intentionally edited the MD, use --after-edit flag. "
                  "Otherwise run 'review-stale' again.", file=sys.stderr)
            sys.exit(1)

    # Check 2: source has not changed since review
    # Dir MDs don't have a source_hash (directories can't be hashed as files),
    # so skip this check for dir source type.
    if source_type == "dir":
        current_source_hash = None  # dirs have no file hash
    else:
        try:
            current_source_hash = compute_file_hash(project_root / source_path_rel)
        except Exception as exc:
            print(f"Error computing source hash: {exc}", file=sys.stderr)
            sys.exit(1)

        if current_source_hash != receipt.get("source_hash_at_review"):
            print("Error: source file has changed since review. "
                  "Run 'review-stale' again.", file=sys.stderr)
            sys.exit(1)

    # Check 3: dep has not changed since review
    try:
        current_dep_hash = compute_dependency_hash(project_root, explicit_deps)
    except Exception as exc:
        print(f"Error computing dep hash: {exc}", file=sys.stderr)
        sys.exit(1)

    if current_dep_hash != receipt.get("dep_hash_at_review"):
        print("Error: dependencies have changed since review. "
              "Run 'review-stale' again.", file=sys.stderr)
        sys.exit(1)

    # Check 4 (dir only): entries have not changed since review
    if source_type == "dir":
        codocs_docs_dir = project_root / ".codocs" / "docs"
        try:
            current_entries_hash = compute_entries_hash(codocs_docs_dir, source_path_rel)
        except Exception as exc:
            print(f"Error computing entries hash: {exc}", file=sys.stderr)
            sys.exit(1)

        if current_entries_hash != receipt.get("entries_hash_at_review"):
            print("Error: directory entries have changed since review. "
                  "Run 'review-stale' again.", file=sys.stderr)
            sys.exit(1)

    # All checks passed — update front matter
    codocs["source_hash"] = current_source_hash
    codocs["dep_hash"] = current_dep_hash
    if source_type == "dir":
        codocs["entries_hash"] = current_entries_hash

    verified_at = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()
    codocs["verified_at"] = verified_at

    # Write updated MD atomically (prevents partial-write corruption)
    new_text = render_md_frontmatter(meta, body)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=md_path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(new_text)
        os.replace(tmp_path, md_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    # Delete receipt
    receipt_path = get_receipt_path(state_dir, md_path, project_root)
    if receipt_path.exists():
        receipt_path.unlink()

    try:
        rel_display = str(md_path.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        rel_display = str(md_path)

    print(f"Hash metadata updated: {rel_display}")


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def gen_hash(project_root: Path, mode: str | None, targets: list) -> None:
    """Low-level hash computation for diagnostics.

    mode: 'file' | 'dir' | 'deps'
    targets: list of path arguments
    """
    if mode == "file":
        if not targets:
            print("Error: gen-hash file requires <path>", file=sys.stderr)
            sys.exit(1)
        file_path = Path(targets[0])
        if not file_path.is_absolute():
            file_path = project_root / targets[0]
        try:
            result = compute_file_hash(file_path)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(result)

    elif mode == "dir":
        if not targets:
            print("Error: gen-hash dir requires a <codocs-dir-path> argument", file=sys.stderr)
            sys.exit(1)
        # targets[0] is relative to project_root (e.g. '.codocs/docs/src')
        codocs_docs_dir = project_root / ".codocs" / "docs"
        dir_arg = targets[0].replace("\\", "/")
        # Strip the '.codocs/docs/' prefix to get source_dir_rel
        docs_prefix = ".codocs/docs/"
        if dir_arg.startswith(docs_prefix):
            source_dir_rel = dir_arg[len(docs_prefix):]
        else:
            # Interpret as absolute path under codocs/docs
            source_dir_rel = dir_arg
        try:
            result = compute_entries_hash(codocs_docs_dir, source_dir_rel)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(result)

    elif mode == "deps":
        # targets are dep paths relative to project root
        try:
            result = compute_dependency_hash(project_root, targets)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(result)

    elif mode is None:
        print("Error: gen-hash requires a mode argument: file | dir | deps", file=sys.stderr)
        sys.exit(1)

    else:
        print(f"Error: gen-hash unknown mode '{mode}'. Use: file | dir | deps", file=sys.stderr)
        sys.exit(1)


def bootstrap_meta(project_root: Path) -> None:
    """One-shot migration: inject schema-1 front matter into all tracked codocs MDs.

    Idempotent: MDs that already have valid schema-1 metadata are skipped.
    Body text is never modified.
    Prints summary: [bootstrap-meta] seeded N / skipped M / errors E
    """
    config = load_config(project_root)
    entries = scan(project_root, config)

    seeded = 0
    skipped = 0
    errors = 0

    now = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()

    for _, is_dir, source_path, md_path, _ in entries:
        if not md_path.exists():
            # No MD to bootstrap; skip silently
            continue

        # Skip _notes/
        codocs_docs_dir = project_root / ".codocs" / "docs"
        try:
            rel_md = md_path.relative_to(codocs_docs_dir)
            if rel_md.parts and rel_md.parts[0] == "_notes":
                continue
        except ValueError:
            pass

        # Read current content
        try:
            text = md_path.read_text(encoding="utf-8")
        except Exception as exc:
            print(f"[bootstrap-meta] WARN: could not read {md_path}: {exc}", file=sys.stderr)
            errors += 1
            continue

        # Parse existing front matter
        meta, body = parse_md_frontmatter(text)

        # Check idempotency: valid schema-1 metadata already present?
        source_type = "dir" if is_dir else "file"
        if meta is not None and isinstance(meta, dict) and "codocs" in meta:
            reasons = validate_frontmatter(meta, source_type)
            if not reasons:
                skipped += 1
                continue

        # Source file/dir must exist
        if not source_path.exists():
            print(f"[bootstrap-meta] WARN: source not found for {md_path.name}, skipping",
                  file=sys.stderr)
            errors += 1
            continue

        # Compute source_path relative to project_root (forward slashes)
        try:
            source_rel = str(source_path.relative_to(project_root)).replace("\\", "/")
        except ValueError:
            source_rel = str(source_path).replace("\\", "/")

        # Compute hashes
        try:
            dep_hash = compute_dependency_hash(project_root, [])
        except Exception as exc:
            print(f"[bootstrap-meta] WARN: dep_hash error for {md_path.name}: {exc}",
                  file=sys.stderr)
            errors += 1
            continue

        if is_dir:
            try:
                entries_hash = compute_entries_hash(codocs_docs_dir, source_rel)
            except Exception as exc:
                print(f"[bootstrap-meta] WARN: entries_hash error for {md_path.name}: {exc}",
                      file=sys.stderr)
                errors += 1
                continue

            new_codocs = {
                "schema": 1,
                "source_type": "dir",
                "source_path": source_rel,
                "entries_hash": entries_hash,
                "explicit_deps": [],
                "dep_hash": dep_hash,
                "hash_mode": "text-lf-sha256",
                "verified_at": now,
            }
        else:
            try:
                source_hash = compute_file_hash(source_path)
            except Exception as exc:
                print(f"[bootstrap-meta] WARN: source_hash error for {md_path.name}: {exc}",
                      file=sys.stderr)
                errors += 1
                continue

            new_codocs = {
                "schema": 1,
                "source_type": "file",
                "source_path": source_rel,
                "source_hash": source_hash,
                "explicit_deps": [],
                "dep_hash": dep_hash,
                "hash_mode": "text-lf-sha256",
                "verified_at": now,
            }

        # Build new metadata (preserve any existing non-codocs keys)
        if meta is None or not isinstance(meta, dict):
            new_meta = {"codocs": new_codocs}
        else:
            new_meta = dict(meta)
            new_meta["codocs"] = new_codocs

        # (body already equals text when parse_md_frontmatter returns meta=None)

        # Write atomically
        new_text = render_md_frontmatter(new_meta, body)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=md_path.parent, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(new_text)
            os.replace(tmp_path, md_path)
        except Exception as exc:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            print(f"[bootstrap-meta] WARN: write error for {md_path.name}: {exc}",
                  file=sys.stderr)
            errors += 1
            continue

        seeded += 1

    print(f"[bootstrap-meta] seeded {seeded} / skipped {skipped} / errors {errors}")




if __name__ == "__main__":
    args = sys.argv[1:]
    do_lint = "--lint" in args
    do_parent_sync = "--parent-sync" in args
    do_check_deps = "--check-deps" in args
    do_explain_hash = "--explain-hash" in args
    args = [a for a in args if a not in ("--lint", "--parent-sync", "--check-deps", "--explain-hash")]

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
    elif do_explain_hash:
        md_rel = args[1] if len(args) > 1 else None
        if not md_rel:
            print("Error: --explain-hash requires a <md-path> argument", file=sys.stderr)
            sys.exit(1)
        explain_hash(root, root / md_rel)
    elif len(args) >= 2 and args[1] == "review-stale":
        md_rel = args[2] if len(args) > 2 else None
        if not md_rel:
            print("Error: review-stale requires a <md-path> argument", file=sys.stderr)
            sys.exit(1)
        review_stale(root, root / md_rel)
    elif len(args) >= 2 and args[1] == "refresh-hash":
        after_edit = "--after-edit" in args
        remaining = [a for a in args[2:] if a != "--after-edit"]
        md_rel = remaining[0] if remaining else None
        if not md_rel:
            print("Error: refresh-hash requires a <md-path> argument", file=sys.stderr)
            sys.exit(1)
        refresh_hash(root, root / md_rel, after_edit=after_edit)
    elif len(args) >= 2 and args[1] == "gen-hash":
        mode = args[2] if len(args) > 2 else None
        targets = args[3:] if len(args) > 3 else []
        gen_hash(root, mode, targets)
    elif len(args) >= 2 and args[1] == "bootstrap-meta":
        bootstrap_meta(root)
    else:
        init(root)
