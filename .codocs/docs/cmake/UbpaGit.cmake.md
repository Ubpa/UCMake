# UbpaGit.cmake

Git 环境初始化和子模块更新工具。

## API

| 函数/宏 | 说明 |
|---------|------|
| `Ubpa_InitGit()` | `find_package(Git REQUIRED)`，打印 Git 路径和版本（macro，变量在调用方作用域） |
| `Ubpa_UpdateSubModule()` | 执行 `git submodule update --init`，失败则 FATAL_ERROR |

## 约定

- `Ubpa_UpdateSubModule` 依赖 `GIT_FOUND`，必须先调用 `Ubpa_InitGit()`，否则直接报错。
- 子模块更新基于 `PROJECT_SOURCE_DIR`，适合在顶层 CMakeLists 中调用。
