---
codocs:
  schema: 1
  source_type: file
  source_path: cmake/UbpaInit.cmake
  source_hash: sha256:016e74189775a46ea6079bab8796a393ce42acd613932fc12c9c611f29b8816a
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-29T16:35:56.043415+08:00'
---
# UbpaInit.cmake

项目初始化入口，`include` 本文件即可拉入所有 Ubpa CMake 模块，并调用 `Ubpa_InitProject()` 完成全局配置。

## 职责

1. 自动 include 所有其他 Ubpa*.cmake（Basic、Build、Download、Git、Package、Qt、Doc）及 CPM.cmake。
2. 强制 `CPM_USE_LOCAL_PACKAGES=TRUE`，优先使用本机已有包。
3. 提供 `Ubpa_InitProject()` macro 完成项目级全局设置。

## Ubpa_InitProject() 完成的配置

**签名**：`Ubpa_InitProject([CXX_STANDARD <std>])`，`CXX_STANDARD` 默认 20。

| 配置项 | 值 |
|--------|----|
| Debug/Release/MinSizeRel/RelWithDebInfo postfix | d / (空) / msr / rd |
| C++ 标准 | 默认 C++20，可通过 `CXX_STANDARD` 覆盖（required） |
| 默认 build type | Release（如未设置） |
| 全局编译宏 | `UCMAKE_CONFIG_<CONFIG>`（大写） + `UCMAKE_CONFIG_POSTFIX="<postfix>"` |
| 编译器最低版本 | Clang ≥ 10、GCC ≥ 10、MSVC ≥ 19.26（均以支持 concept 为门槛） |
| 安装前缀 | 默认改为 `<上级目录>/Ubpa`（仅在默认值时覆盖） |
| 输出目录 | bin（runtime/library）、lib（archive），所有配置统一，以 `Ubpa_RootProjectPath` 为根 |
| `Ubpa_RootProjectPath` | 首次调用时设为 `PROJECT_SOURCE_DIR`，嵌套项目不会覆盖 |

## 自动创建的便捷 target

以上 5 个 target 均放置在 IDE folder `<PROJECT>/UCMakePredefinedTargets` 下，与业务 target 区分。

| Target | 说明 |
|--------|------|
| `<PROJECT>_BuildTests` | 构建所有测试（不依赖 ALL） |
| `<PROJECT>_RunTests` | 先 BuildTests 再 `ctest -j<N>`，并行数自动检测（失败则回退 4） |
| `<PROJECT>_Check` | `cmake --build --target BuildTests` 强制重编后运行 ctest；与 RunTests 的区别是能正确触发 MSBuild 增量重编（适合 pre-commit hook 使用） |
| `<PROJECT>_Install` | 执行当前配置的 install |
| `<PROJECT>_InstallAll` | 依次 install Debug/Release/MinSizeRel/RelWithDebInfo 四个配置 |

## 注意

- 本文件是 macro，变量作用在调用方 scope，与 function 不同——`set()` 直接影响外部。
- `Ubpa_BuildTest_<PROJECT>` cache 变量控制 TEST 目标是否构建，默认 TRUE。
- USE_FOLDERS 全局开启，确保 IDE 中 target 按 folder 分组展示。
- `UBPA_UCMAKE_LIST_DIR` 在 include 时捕获 UCMake 安装目录，用于 macro 内定位工具目录（`.more-hooks/`、`.codocs/`、`.ucmake/`）。

## configure 时自动完成的 hook 配置

`Ubpa_InitProject()` 在 cmake configure 阶段执行两项工作：

**1. 生成 `.ucmake/project.env`**（运行时变量，供 hook 脚本读取）

```
UCMAKE_PROJECT_NAME=<PROJECT_NAME>
UCMAKE_BUILD_DIR=<CMAKE_BINARY_DIR>
UCMAKE_DEFAULT_CONFIG=Release
```

同时写入 `.ucmake/.gitignore`（内容 `project.env`），防止产物进 git。

**2. 通过 `more-hooks.py` 自动注册三个 hook**

| hook | id | priority | 脚本来源 |
|------|----|----------|---------|
| pre-commit | codocs | 50 | `.codocs/hooks/pre-commit` |
| commit-msg | codocs | 50 | `.codocs/hooks/commit-msg` |
| pre-commit | ucmake | 80 | `.ucmake/hooks/pre-commit` |

自愈性：重新 configure 时会更新 symlink 指向当前 UCMake 安装版本。

**前提条件**：需要先执行 `cmake --install` 将工具文件安装到位；若 `.more-hooks/more-hooks.py` 不存在，注册步骤会打印 WARNING 并跳过（不影响 configure 成功）。
