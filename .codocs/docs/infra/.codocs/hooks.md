---
codocs:
  schema: 1
  source_type: dir
  source_path: infra/.codocs/hooks
  entries_hash: sha256:c0cce72ea1a2d5eba4ffd93a6bf80d8ac2b4d1d617e75ca99a041e58f9ff452b
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-15T02:15:47.850211+08:00'
---
# infra/.codocs/hooks/

codocs git hook 静态脚本目录。

## 索引

| 名称 | 类型 | 职责 |
|---|---|---|
| `pre-commit` | 文件 | 四阶段 lint/检查，设临时标记，不直接拦截（Phase 2/3/4） |
| `commit-msg` | 文件 | 读取 pre-commit 标记，结合 commit message 跳过声明，执行最终拦截 |

## 设计说明

这两个脚本实现了**两阶段决策**架构：pre-commit 收集信息并设标记，commit-msg 在用户填写 commit message 之后做最终判断。这允许用户在同一次 `git commit` 流程中既完成 commit message 编写，又内联声明跳过原因，而无需多次操作。

hooks 均为纯 bash 静态脚本，通过 self-location 模式定位 `codocs.py`（向上两级目录），可被 symlink 到任意位置使用。
