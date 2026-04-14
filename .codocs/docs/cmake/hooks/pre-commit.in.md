---
codocs:
  schema: 1
  source_type: file
  source_path: cmake/hooks/pre-commit.in
  source_hash: sha256:706edd9d65ea8d84fcf8154ca49dd71a4365ee5b68d905729dc97abc98e22998
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-14T17:11:10.658413+08:00'
---
# cmake/hooks/pre-commit.in

CMake 模板文件，configure 时由 `@...@` 占位符替换为项目具体值，生成可直接安装的 pre-commit hook 脚本。

## 用途

在 CMake configure 阶段自动生成针对当前项目的 pre-commit hook，通过 more-hooks 注册到 `.git/hooks/pre-commit`：

```bash
python .more-hooks/more-hooks.py register . \
  --hook pre-commit --id <PROJECT_NAME_LOWER>-ci \
  --script .ucmake/hooks/pre-commit --priority 80 --symlink
```

## 行为

1. 检查 `CMAKE_BINARY_DIR` 是否存在，不存在则跳过（允许无 build 目录时正常提交）
2. 执行 `cmake --build <BUILD_DIR> --config <UCMAKE_DEFAULT_CONFIG> --target <PROJECT_NAME>_Check`
3. 构建或测试失败 → 打印错误并 `exit 1` 阻断提交

## 占位符

| 占位符 | 替换值 |
|--------|--------|
| `@PROJECT_NAME@` | CMake 项目名（用于日志前缀） |
| `@PROJECT_NAME_LOWER@` | 小写项目名（用于 hook id） |
| `@CMAKE_BINARY_DIR@` | 构建目录路径 |
| `@UCMAKE_DEFAULT_CONFIG@` | 默认构建配置（如 Release/Debug） |

## 注意

- 文件本身是模板，不可直接执行，configure 后的输出文件才可安装
- `_Check` target 是 UCMake 约定的测试聚合 target（见 UbpaBuild.cmake）
