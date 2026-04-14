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
