---
codocs:
  schema: 1
  source_type: file
  source_path: infra/.codocs/codocs.py
  source_hash: sha256:6c6c79c4ab628d76734cbd09119a701528c08dbe034b8a49e71593c77d9a5bc6
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-15T02:25:42.125576+08:00'
---
# infra/.codocs/codocs.py

codocs 核心引擎。由 `codocs init` 复制到下游项目的 `.codocs/scripts/codocs.py`，之后所有 hook 和命令都调用本地副本（`.codocs/scripts/` 版本），而非 infra 原件。

## 命令一览

| 命令 | 说明 |
|---|---|
| `codocs.py .` | 扫描缺失 MD，底层优先排序输出（给 AI 按顺序创建）|
| `codocs.py . --lint` | 全量健康检查，报告 MISSING/ORPHAN/BLOAT/THIN/CONFIG/STALE_FILE/STALE_DIR |
| `codocs.py . --parent-sync <md…>` | 检查已暂存 MD 的父目录 MD 是否也已暂存 |
| `codocs.py . --check-deps <files…>` | 检查 config.json 依赖规则是否触发 |
| `codocs.py . review-stale <md>` | 展示过期原因 + 写审查 receipt |
| `codocs.py . refresh-hash <md>` | 核验 receipt 后更新 front matter 哈希 |
| `codocs.py . gen-hash file\|dir\|deps …` | 低级哈希计算（调试用） |
| `codocs.py . bootstrap-meta` | 一次性为所有已有 MD 注入/修复 schema-1 front matter |

## 核心数据结构

**Front matter（文件 MD）**
```yaml
codocs:
  schema: 1
  source_type: file
  source_path: src/Foo.cpp        # 相对 project_root
  source_hash: sha256:<hex>       # 源文件内容哈希（去 front matter）
  explicit_deps: []               # 显式依赖路径列表
  dep_hash: sha256:<hex>          # 依赖文件的聚合哈希
  hash_mode: text-lf-sha256
  verified_at: '2026-...'
```

**Front matter（目录 MD）**
- 用 `entries_hash` 替代 `source_hash`：对直接子 MD（文件/目录）的 body 内容做聚合哈希
- `source_hash: null`

## 哈希语义

- **source_hash**：文件 MD 对源文件 body（CRLF→LF 后）做 sha256；`.md` 文件先剥离 front matter 再哈希
- **entries_hash**：目录 MD 专用。枚举子 MD，按 `F\0<rel-path>\0<hash>` 或 `D\0<rel-path>\0<hash>` 格式排序后聚合哈希
- **dep_hash**：`explicit_deps` 列表为空时固定为空字符串的 sha256

## Stale 分类

| 分类 | 含义 | hook 处理 |
|---|---|---|
| STALE_FILE | source_hash/dep_hash 不匹配 | 硬拦截 |
| STALE_DIR | entries_hash/dep_hash 不匹配 | 软警告，commit-msg 决策 |
| MISSING | 源文件有 MD 缺失 | 硬拦截 |
| ORPHAN | MD 无对应源文件 | 硬拦截 |
| BLOAT/THIN | MD 与源文件大小比例失衡 | 软警告（lint only）|

## review-stale / refresh-hash 流程

1. `review-stale`：计算当前哈希，打印 MD body，写 receipt 到 `.git/.codocs-state/`（git 不追踪）
2. 人工审查 MD 内容，若需修改则编辑
3. `refresh-hash [--after-edit]`：校验 receipt（source/dep/entries/body 四项哈希均未变化，`--after-edit` 跳过 body 校验），更新 front matter，删除 receipt

## bootstrap-meta

幂等操作：扫描所有已有 MD，为缺少合法 schema-1 front matter 的文件注入元数据（计算实时哈希，原子写入）。新建文档后应立即运行以填充 PLACEHOLDER。

## Self-location（给 hooks 用的路径约定）

hooks 目录结构：`infra/.codocs/hooks/` → `infra/.codocs/codocs.py`，即 hook 文件向上两级即为引擎脚本。安装到项目后结构相同（`.codocs/scripts/codocs.py`，hooks 在 `.codocs/hooks/`）。
