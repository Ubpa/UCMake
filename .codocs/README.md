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

报告 `[MISSING]`（文档缺失）、`[ORPHAN]`（源文件已删）、`[BLOAT]`（文档过长）、`[THIN]`（文档过短）。

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
| 1 | pre-commit | ORPHAN / MISSING lint | 硬拦截，必须修复 |
| 2 | pre-commit + commit-msg | 受管控代码有改动但无文档更新 | 软警告，需 skip 声明 |
| 3 | pre-commit + commit-msg | 子文档改动但父目录 MD 未同步 | 软警告，需 skip 声明 |
| 4 | pre-commit + commit-msg | 依赖规则触发的关联文档未更新 | 软警告，需 skip 声明 |
