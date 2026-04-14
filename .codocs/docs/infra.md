---
codocs:
  schema: 1
  source_type: dir
  source_path: infra
  entries_hash: sha256:7bd7f20ec67de1bfe8b49a43420bdb7c46725f560e554a53e8d2dfe201a10b34
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-15T02:15:47.850211+08:00'
---
# infra/

UCMake 安装后提供的工具目录。下游库在 cmake configure 时（`Ubpa_InitProject()`）从这里自动注册 git hooks，无需用户手动操作。

## 索引

| 名称 | 类型 | 职责 |
|---|---|---|
| `.codocs/` | 目录 | codocs 文档完整性检查引擎 + git hooks |
| `.more-hooks/` | 目录 | git hook dispatcher 框架（解决多工具 hook 注册冲突）|
| `.ucmake/` | 目录 | UCMake 自身 pre-commit hook（构建+测试验证）|

## 架构概览

infra/ 实现了一套**分层 hook 注册架构**：

```
cmake configure (Ubpa_InitProject)
  ├─ more-hooks install-to-project   → 项目获得 .more-hooks/more-hooks.py
  ├─ more-hooks install              → .git/hooks/{pre-commit,commit-msg,...} = dispatcher
  ├─ more-hooks register --id codocs → .git/hooks.d/pre-commit/50-codocs
  │                                    .git/hooks.d/commit-msg/50-codocs
  └─ more-hooks register --id ucmake → .git/hooks.d/pre-commit/60-ucmake
```

每次 `git commit` 时，dispatcher 按优先级依次调用 codocs pre-commit → ucmake pre-commit → codocs commit-msg，任一失败即终止。

## 设计决策

**静态文件 + self-location**：所有 hook 脚本均为静态文件，通过相对路径或 symlink 解析定位同级工具脚本（如 `codocs.py`）。这使 infra 目录本身不需要安装过程，直接 symlink 即可使用。

**工具职责正交**：`.codocs/` 管文档质量、`.more-hooks/` 管 hook 调度、`.ucmake/` 管构建质量，三者无依赖交叉，可独立启用/禁用。
