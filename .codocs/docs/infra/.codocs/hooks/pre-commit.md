---
codocs:
  schema: 1
  source_type: file
  source_path: infra/.codocs/hooks/pre-commit
  source_hash: sha256:8f8830285617ed3b79074416c08885d307134566dfe735679b66fceaf1329caf
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-15T02:35:39.898382+08:00'
---
# infra/.codocs/hooks/pre-commit

codocs pre-commit hook 静态脚本。由 `codocs init` 注册到 git hooks（直接或经 more-hooks dispatcher）。

## 四阶段流程

### Phase 1 — lint 硬拦截（可配置禁用）

调用 `codocs.py --lint`，对 `[STALE_FILE]`、`[MISSING]`、`[ORPHAN]`、`[CONFIG]` 类问题**直接 exit 1**。

`[STALE_DIR]` 是软警告：写入 `codocs_stale_dir_paths` + 设 `codocs_needs_stale_dir_check` 标记，打印提示，**不拦截**（留给 commit-msg 最终决策）。

### Phase 2 — doc-change 检查（可配置禁用）

从 `config.json` 读取 `roots`，找出暂存文件中属于受管控 root 的代码文件（排除 `.css`）。若有代码改动且**无任何** `.codocs/docs/` 文档改动，写入 pending 列表 + 设标记。**不拦截**，打印建议。

### Phase 3 — 父目录 MD 同步检查（可配置禁用）

找出已暂存的 `.codocs/docs/*.md` 文件，调用 `codocs.py --parent-sync` 检查直接父目录 MD 是否也已暂存。若有遗漏，设 `codocs_needs_parent_sync` 标记。**不拦截**。

### Phase 4 — dependency 检查（可配置禁用）

调用 `codocs.py --check-deps`，检查 `config.json` 中 `dependencies` 规则：若暂存文件触发了某条 `when` 规则但对应 `update` 文档未暂存，设 `codocs_needs_dep_check` 标记。**不拦截**。

## Self-location 模式

```bash
_hook_self="$(readlink -f "$0")"
INIT_PY="$(dirname "$(dirname "$_hook_self")")/codocs.py"
```

hook 自身解析 symlink 后，向上两级目录找 `codocs.py`（即 `infra/.codocs/codocs.py`）。这使 hook 作为静态文件可被任意位置 symlink，无需硬编码路径。

## 快速退出条件

- `.codocs/config.json` 不存在 → `exit 0`（跳过所有检查）
- Python 不可用或 stub → `exit 1` 并提示安装
- 暂存文件列表为空 → `exit 0`

## 与 commit-msg 的分工

pre-commit 只设标记，不做最终决策。commit-msg 读取标记，结合 commit message 中的跳过声明，执行拦截或放行。
