---
codocs:
  schema: 1
  source_type: file
  source_path: cmake/UbpaPackage.cmake
  source_hash: sha256:5d63efd6da91b3751ba952efb2886f5873bba802f5a94e33beff04c98572019e
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-14T17:11:10.658413+08:00'
---
# UbpaPackage.cmake

包管理与导出模块，负责依赖声明（菱形依赖检测）和 CMake 安装包配置文件生成。

## API

| 函数/宏 | 说明 |
|---------|------|
| `Ubpa_DecodeVersion(<major> <minor> <patch> <version>)` | 从版本字符串中解析 major/minor/patch |
| `Ubpa_ToPackageName(<rst> <name> <version>)` | 生成包目录名：`<name>.<version>` 中 `.` 替换为 `_` |
| `Ubpa_PackageName(<rst>)` | 当前项目的包名（`PROJECT_NAME` + `PROJECT_VERSION`） |
| `Ubpa_AddDep(<name> <version>)` | 添加依赖，优先 `find_package`，找不到则从 GitHub `Ubpa/<name>` FetchContent |
| `Ubpa_Export([TARGET] [CPM] [DIRECTORIES <dirs>])` | 生成并安装 CMake 包配置文件（Config + ConfigVersion，可选 Targets） |

## Ubpa_AddDep 菱形依赖检测

- 全局维护 `Ubpa_<PROJECT>_dep_name_list` 和 `_dep_version_list`。
- 同一包再次添加时：版本相同则跳过（菱形但兼容），版本不同则 `FATAL_ERROR`。
- 依赖地址固定为 `https://github.com/Ubpa/<name>`，不支持自定义地址。

## Ubpa_Export 生成的安装结构

```
<package_name>/cmake/
    <PROJECT>Config.cmake
    <PROJECT>ConfigVersion.cmake
    <PROJECT>Targets.cmake      (仅 TARGET 选项)
```

版本兼容性策略：`SameMinorVersion`（允许更高 patch，不允许更高 minor）。

## UBPA_PACKAGE_INIT 注入

如果项目有依赖（或指定了 `CPM` 选项），生成的 Config.cmake 会注入：
1. include 目录自动添加到 `include_directories`
2. 确保 UCMake 可用（先 find_package 再 FetchContent 从 GitHub）
3. 重放所有 `Ubpa_AddDep` 调用（让下游用 `find_package(<PROJECT>)` 时自动传递依赖）

## 关键细节

- `DIRECTORIES` 参数支持带前缀路径（如 `include/Foo` → 安装到 `<pkg>/include/`），空前缀则直接装到包根目录。
- `Ubpa_AddDep` 是 macro，变量在调用方 scope，依赖列表修改会直接影响外部。
