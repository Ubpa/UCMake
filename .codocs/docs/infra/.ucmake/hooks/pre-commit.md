---
codocs:
  schema: 1
  source_type: file
  source_path: infra/.ucmake/hooks/pre-commit
  source_hash: sha256:f53409a32b8706f5c2f5203ff65bd58740c16e530dc8ec949bbde555195a3def
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-15T02:15:47.850211+08:00'
---
# infra/.ucmake/hooks/pre-commit

UCMake 自身的 pre-commit hook 静态脚本。由 cmake configure 时（`Ubpa_InitProject()`）注册到下游项目的 git hooks。

## 职责

在每次提交前执行**构建 + 测试**，阻止编译失败或测试不通过的代码进入版本库。

## 运行机制

所有项目相关变量从 `.ucmake/project.env` 动态加载，hook 本身无任何硬编码路径：

```
ROOT/.ucmake/project.env  →  UCMAKE_BUILD_DIR
                              UCMAKE_DEFAULT_CONFIG
                              UCMAKE_PROJECT_NAME
```

实际执行：
```bash
cmake --build $UCMAKE_BUILD_DIR --config $UCMAKE_DEFAULT_CONFIG \
      --target ${UCMAKE_PROJECT_NAME}_Check
```

`_Check` target 是 UCMake 约定的聚合目标，覆盖构建 + 单元测试。

## 快速退出条件

- `.ucmake/project.env` 不存在 → 打印提示，`exit 0`（不拦截，提示重跑 cmake configure）
- `$UCMAKE_BUILD_DIR` 目录不存在 → 打印提示，`exit 0`

## 设计决策

- **静态文件 + 动态 env 加载**：hook 脚本本身永远不需要修改，变量全部由 cmake configure 写入 `project.env`。这使 infra 目录可作为只读模板，不同项目共享同一份 hook 代码。
- **失败即拦截**：cmake 返回非零时打印 "Build or tests failed. Commit aborted."，exit 1。
