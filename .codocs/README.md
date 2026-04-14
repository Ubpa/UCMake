# codocs

代码语义文档系统。每个源文件/目录都有对应的 `.codocs/docs/*.md`，记录**语义**（接口约定、设计决策、算法要点、陷阱），而非语法。信息密度远高于直接读源码，是 AI 理解代码的首选入口。

## 目录结构

```
.codocs/
├── README.md           ← 本文件（由 codocs init 安装）
├── config.json         ← roots、excludes、hook 开关
├── scripts/
│   └── codocs.py       ← lint / missing-check / parent-sync
├── hooks/              ← hook 源文件（通过 more-hooks 注册到 .git）
│   ├── pre-commit
│   └── commit-msg
└── docs/               ← 源码树的语义镜像
    ├── src.md          ← src/ 目录的索引和概述
    └── src/
        └── Foo.cpp.md  ← src/Foo.cpp 的语义文档
```

路径映射：`src/Foo.cpp` → `.codocs/docs/src/Foo.cpp.md`

## 重新安装 hooks

克隆后执行：

```bash
python .codocs/scripts/codocs.py .
```

## Lint

```bash
python .codocs/scripts/codocs.py . --lint
```

报告 `[MISSING]`（文档缺失）、`[ORPHAN]`（源文件已删）、`[BLOAT]`（文档过长）、`[THIN]`（文档过短）、`[STALE_FILE]`（文件文档哈希过时）、`[STALE_DIR]`（目录文档子条目哈希过时）。

## 文档维护规范（AI 必读）

### 默认行为：更新文档

提交涉及 `config.json` 中 `roots` 范围内的文件时，**默认应该更新对应文档**。

**codocs-skip 是最后手段，不是可以随意选择的捷径。** 遇到 hook 提示时，第一反应应该是"这段文档需要更新什么"，而不是"怎么跳过"。

### 什么时候才能用 codocs-skip

仅当文档描述**仍然完全准确、无需任何修改**时才可以跳过。跳过前必须 Read 对应 md 逐字确认。

可以跳过的情况（文档完全不受影响）：
- ✅ 修改了函数内部实现，但接口语义、参数、返回值、注意事项一字未变
- ✅ 修复了 bug，且文档中没有提到被修复的行为
- ✅ 改了注释格式或变量名，文档中没有涉及这些细节
- ✅ 父目录 MD 的索引表：无新增/删除/改名文件，职责摘要未变

**必须更新文档的情况（不可跳过）**：
- ❌ 新增了公共函数/类型 — 文档里本来就没有，必须补写
- ❌ 删除或修改了文档中描述的功能/接口
- ❌ 修改了接口语义、参数含义、返回值约定
- ❌ 添加了重要注意事项或已知陷阱

### 跳过声明格式

在 commit message **末尾**添加，理由必须具体说明为何文档不受影响：

```
## codocs-skip
- .codocs/docs/src/Runtime/Foo.cpp.md: 仅修改内部实现，接口描述未变
- .codocs/docs/include/UCommon.md: 索引表无新增/删除/改名，不受影响
```

**禁止使用笼统理由**：`"无需更新"`、`"内容未变"`、`"文档无需同步"` 等描述说明没有真正审查过文档，属于无效跳过声明。

全局跳过（慎用，仅在文件较多且已逐一确认后）：

```
## codocs-skip
- [all]: <具体理由>
```

## Commit hooks 行为

| Phase | 时机 | 检查内容 | 拦截方式 |
|-------|------|----------|----------|
| 1 | pre-commit | ORPHAN / MISSING / CONFIG lint | 硬拦截，必须修复 |
| 1 | pre-commit | STALE_FILE lint（源文件或依赖哈希变更） | 硬拦截，必须 review-stale + refresh-hash |
| 1 | pre-commit | STALE_DIR lint（子 MD 哈希变更） | 软警告，设置标志位 |
| 2 | pre-commit + commit-msg | 受管控代码有改动但无文档更新 | 软警告，需 skip 声明 |
| 3 | pre-commit + commit-msg | 子文档改动但父目录 MD 未同步 | 软警告，需 skip 声明 |
| 4 | pre-commit + commit-msg | 依赖规则触发的关联文档未更新 | 软警告，需 skip 声明 |
| commit-msg Check 4 | commit-msg | STALE_DIR 未被 codocs-skip 覆盖 | 硬拦截 |

## Freshness Metadata（新鲜度元数据）

所有受追踪的 `.codocs/docs/**/*.md` 文件包含 schema-1 YAML front matter，记录文档与源码的绑定状态。

### 文件文档示例

```yaml
---
codocs:
  schema: 1
  source_type: file
  source_path: src/Foo.cpp        # 相对项目根目录的源文件路径
  source_hash: sha256:abc123...   # 源文件内容的哈希（决定 STALE_FILE）
  explicit_deps: []               # 额外声明的依赖路径列表
  dep_hash: sha256:def456...      # 所有依赖内容的哈希
  hash_mode: text-lf-sha256
  verified_at: 2026-04-14T12:35:00+08:00
---
```

### 目录文档示例

```yaml
---
codocs:
  schema: 1
  source_type: dir
  source_path: src/               # 对应目录路径
  entries_hash: sha256:ghi789...  # 所有直接子 MD body 的哈希（决定 STALE_DIR）
  explicit_deps: []
  dep_hash: sha256:jkl012...
  hash_mode: text-lf-sha256
  verified_at: 2026-04-14T12:35:00+08:00
---
```

### 各字段含义

| 字段 | 含义 |
|------|------|
| `source_hash` | 源文件内容快照；源文件改动后与存档不符 → `STALE_FILE` |
| `entries_hash` | 所有直接子 MD body 的快照；子 MD 更新后与存档不符 → `STALE_DIR` |
| `dep_hash` | `explicit_deps` 中声明的额外依赖内容快照 |
| `verified_at` | 上次 review 通过并刷新哈希的时间戳 |

### 辅助命令

```bash
# 查看文档哈希明细
python .codocs/scripts/codocs.py . explain-hash <md-path>

# 手动计算哈希（用于调试）
python .codocs/scripts/codocs.py . gen-hash file <source-path>
python .codocs/scripts/codocs.py . gen-hash dir <dir-path>
python .codocs/scripts/codocs.py . gen-hash deps <dep1> [dep2 ...]
```

## Stale Review 工作流

### 检测

运行 lint 或在 pre-commit 时自动检测：

```bash
python .codocs/scripts/codocs.py . --lint
```

`[STALE_FILE]` 表示源文件或依赖已变更，文档**必须**重新审阅。  
`[STALE_DIR]` 表示子 MD 有更新，父目录索引文档可能需同步。

### 完整流程

```
检测到 STALE_FILE 或 STALE_DIR
        │
        ▼
1. review-stale  ← 打印变更原因 + MD body，存储 review receipt
        │
        ▼
2. 按需更新 MD body（用 Edit 工具修改语义内容）
        │
        ▼
3. refresh-hash  ← 需要有效 receipt；刷新 YAML 哈希；删除 receipt
```

### 命令

```bash
# 步骤 1：审阅并存储 receipt
python .codocs/scripts/codocs.py . review-stale <md-path>

# 步骤 3：刷新哈希（receipt 有效后才能执行）
python .codocs/scripts/codocs.py . refresh-hash <md-path>
```

### Review Receipt

- 存储位置：`.git/.codocs-state/`（不被 git 追踪）
- 作用：防止跳过 review 直接刷新哈希
- `refresh-hash` 要求 receipt 存在且有效，执行后自动删除

## One-Shot Bootstrap（一键迁移）

新项目首次启用 freshness 检查，或为已有文档补注元数据时，运行：

```bash
python .codocs/scripts/codocs.py . bootstrap-meta
```

该命令为 `.codocs/docs/` 下所有受追踪的 MD 注入 schema-1 front matter（计算初始哈希、写入 `verified_at`）。

- **幂等**：可多次运行，不会覆盖已有的有效元数据
- **适用时机**：
  - 新项目 `codocs init` 完成后
  - 从旧版 codocs（无 front matter）升级时
  - 团队成员克隆仓库后首次使用
