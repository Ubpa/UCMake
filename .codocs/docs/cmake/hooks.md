---
codocs:
  schema: 1
  source_type: dir
  source_path: cmake/hooks
  entries_hash: sha256:add6af32fad6a86d600eadd0b5c6306a229f89aaba98174e1b9dc272556dea84
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-14T17:11:10.658413+08:00'
---
# cmake/hooks/

CMake 模板 hooks 目录，存放由 UCMake 在 configure 阶段生成的 git hook 模板文件。

## 文件索引

| 名称 | 类型 | 职责 |
|------|------|------|
| pre-commit.in | 文件 | pre-commit hook 模板，configure 时生成可安装的 bash 脚本 |

## 设计

UCMake 通过 `configure_file` 将 `.in` 模板实例化为项目专属 hook，再由开发者通过 more-hooks 注册。这样每个使用 UCMake 的项目都能获得"构建+测试通过才允许提交"的保障，且 hook 脚本路径、项目名、构建配置均自动填充，无需手动维护。
