---
codocs:
  schema: 1
  source_type: file
  source_path: infra/.codocs/hooks/commit-msg
  source_hash: sha256:21db21b02511410d523a8a1d7b4a22e5245256788c6c8526a7eb5084c5423582
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-15T02:25:42.325309+08:00'
---
# infra/.codocs/hooks/commit-msg

codocs commit-msg hook 静态脚本。由 `codocs init` 注册到 `.git/hooks/commit-msg`（或通过 more-hooks 注册到 `hooks.d/`）。

## 职责

读取 pre-commit 阶段写入 `/tmp/` 的标记文件，对四类问题执行最终的拦截或放行决策：

| 标记文件 | 触发阶段 | 问题类型 |
|---|---|---|
| `codocs_needs_doc_check` | Phase 2 | 代码文件改动但无文档更新 |
| `codocs_needs_parent_sync` | Phase 3 | `.codocs/` MD 改动但父目录 MD 未同步 |
| `codocs_needs_dep_check` | Phase 4 | 依赖规则触发但关联文档未更新 |
| `codocs_needs_stale_dir_check` | STALE_DIR | 目录文档 entries_hash 已过期（软警告） |

## 核心行为

**跳过语法（`## codocs-skip` section）**

commit message 中可声明跳过，支持两种粒度：
- 路径级：`- .codocs/docs/<path>.md: <理由>` — 仅跳过指定文件的检查
- 全局：`- [all]: <理由>` — 跳过本次提交所有 codocs 检查

设计约束：仅 `[all]` 触发全局跳过；非 `.codocs/docs/` 开头且非 `[all]` 的条目**静默忽略**，防止拼写错误误触发全局跳过。

**四阶段检查逻辑**

每个阶段独立检查，将 pending 列表与 skip_paths 对比，找出"未被跳过声明覆盖"的条目：
- 有未覆盖项 → `block=true`，打印具体提示
- 全部覆盖 → 清除对应标记文件，继续

最终 `block=true` 时退出 1（拦截提交）；EXIT trap 负责清理 `DEPS_*` 和 `STALE_DIR_*` 临时文件。

## 与 pre-commit 的职责分工

pre-commit 只**设标记**（不拦截 Phase 2/3/4），commit-msg **读标记决策**。这样用户能在编辑 commit message 时同步完成跳过声明，无需两次操作。

## 运行时依赖

- 无 Python 依赖，纯 bash
- 使用 self-location 不适用（commit-msg 由 git 直接调用，路径已知）
- 临时文件均在 `${TMPDIR:-/tmp}/`
