---
codocs:
  schema: 1
  source_type: dir
  source_path: infra/.ucmake/hooks
  entries_hash: sha256:05ed2615ce5f4190adb186a8f61ec51066581444b88cc95ee99826d4eedd5642
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-15T02:15:47.850211+08:00'
---
# infra/.ucmake/hooks/

UCMake 自身的 git hook 静态脚本目录。

## 索引

| 名称 | 类型 | 职责 |
|---|---|---|
| `pre-commit` | 文件 | cmake 构建 + 测试验证，失败则拦截提交 |

## 设计说明

UCMake hook 采用"静态脚本 + 动态 env 加载"模式：脚本本身无任何项目相关变量，所有配置从 `.ucmake/project.env` 读取（由 cmake configure 生成）。这使 infra 中的脚本作为只读模板被多个项目共享，configure 阶段将其注册到各自项目的 git hooks 中。
