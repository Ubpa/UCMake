---
codocs:
  schema: 1
  source_type: file
  source_path: infra/.more-hooks/more-hooks.py
  source_hash: sha256:3aa4d41953166b32063fa691792e395212426a678d4849d2a0ed470974f55bdd
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-15T02:15:47.850211+08:00'
---
# infra/.more-hooks/more-hooks.py

git hook dispatcher 框架。解决多工具（codocs、UCMake、自定义脚本）各自需要注册 git hook 时的互相覆盖问题。

## 核心架构

```
.git/hooks/<hook-name>         ← dispatcher（此脚本安装的 bash 脚本）
.git/hooks.d/<hook-name>/
    50-codocs                  ← symlink 或 copy 到实际 hook 脚本
    60-ucmake                  ← 另一个工具注册的 hook
```

dispatcher 按文件名字典序依次执行 `hooks.d/` 下的脚本，任一脚本非零退出即终止链。

## 主要操作

| 操作 | 说明 |
|---|---|
| `install-to-project <root>` | 将 more-hooks.py 复制到项目 `.more-hooks/`，使项目自包含 |
| `install <root>` | 在 `.git/hooks/` 安装 dispatcher（默认覆盖 4 个常用 hook）|
| `register <root> --hook <name> --id <id> --script <path>` | 注册脚本到 `hooks.d/`，自动安装 dispatcher |
| `unregister <root> --id <id>` | 移除指定 id 的所有注册 |
| `list <root>` | 列出所有已注册 hooks |

## 关键设计

**非破坏性注册**：`install_dispatcher` 检测已有 hook 是否为自己安装的 dispatcher（通过 `"more-hooks dispatcher"` 标记字符串），是则覆盖更新，否则跳过并打印警告。

**priority 命名**：注册文件名格式为 `{priority:02d}-{id}`（如 `50-codocs`），由 shell `ls | sort` 排序，无需 more-hooks 参与执行期调度。

**worktree 兼容**：`find_git_dir` 处理 `.git` 为文件（worktree）的情况，解析 `gitdir:` 指向。

## Python API

```python
from more_hooks import register_hook, unregister_hook, install_dispatcher
register_hook(project_root, "pre-commit", "codocs", "/path/to/hook", priority=50)
```

供其他工具（如 codocs init）在 configure 阶段调用，无需用户手动操作 CLI。

## 安装到项目的意义

`install-to-project` 将脚本复制到 `.more-hooks/`，使项目克隆后无需全局安装即可用 `python .more-hooks/more-hooks.py` 操作。这与 `infra/` 整体设计一致：所有工具脚本都内嵌到项目中。
