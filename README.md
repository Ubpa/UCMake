# UCMake

Ubpa 的 CMake 工具库，为 C++ 项目提供统一的初始化、构建、包管理和依赖下载能力。只需一行 `include` 即可获得完整的项目脚手架。

## 功能模块

| 模块 | 职责 |
|------|------|
| `UbpaInit.cmake` | 入口：include 所有模块，提供 `Ubpa_InitProject()` |
| `UbpaBuild.cmake` | 核心：`Ubpa_AddTarget()` 统一创建 EXE/STATIC/SHARED/INTERFACE target |
| `UbpaPackage.cmake` | 包管理：依赖声明（菱形依赖检测）、Config/Targets 安装包生成 |
| `UbpaDownload.cmake` | 文件/zip 下载，带 hash 校验缓存 |
| `UbpaGit.cmake` | Git 初始化、子模块更新 |
| `UbpaQt.cmake` | Qt5 集成（AUTOMOC/AUTOUIC/AUTORCC、Windows DLL 安装） |
| `UbpaDoc.cmake` | Doxygen 文档构建 |
| `CPM.cmake` | 第三方包管理器（v0.27.2，基于 FetchContent） |

## 快速上手

### 1. 引入 UCMake

**方式一：子模块 / 本地路径**

```cmake
list(APPEND CMAKE_MODULE_PATH "${PATH_TO_UCMAKE}/cmake")
include(UbpaInit)
```

**方式二：CPM（推荐）**

```cmake
CPMAddPackage(NAME UCMake GITHUB_REPOSITORY Ubpa/UCMake GIT_TAG v0.7.3)
list(APPEND CMAKE_MODULE_PATH "${UCMake_SOURCE_DIR}/cmake")
include(UbpaInit)
```

**方式三：find_package**

安装 UCMake 后（或通过 `CMAKE_PREFIX_PATH` 指向安装目录）：

```cmake
find_package(UCMake 0.7.3 REQUIRED)
# 所有 Ubpa_* 宏已可用，直接初始化项目
Ubpa_InitProject()
```

### 2. 初始化项目

在顶层 `CMakeLists.txt` 中调用 `Ubpa_InitProject()`，完成全局配置：

```cmake
cmake_minimum_required(VERSION 3.16 FATAL_ERROR)
project(MyProject VERSION 1.0.0)

list(APPEND CMAKE_MODULE_PATH "${PATH_TO_UCMAKE}/cmake")
include(UbpaInit)

Ubpa_InitProject()
```

`Ubpa_InitProject()` 自动完成：
- C++20、Debug postfix（`d`）、Release 为默认构建类型
- 全局宏 `UCMAKE_CONFIG_<CONFIG>` 和 `UCMAKE_CONFIG_POSTFIX`
- 输出目录统一到 `bin/`（runtime）和 `lib/`（archive）
- 启用 IDE folder、CTest
- 创建 `<PROJECT>_BuildTests` / `_RunTests` / `_Install` / `_InstallAll` 便捷 target
- 自动注册 git hooks（codocs 文档检查、pre-commit 构建验证），**无需任何手动操作**

### 3. 添加 target

在子目录的 `CMakeLists.txt` 中使用 `Ubpa_AddTarget()`：

```cmake
# 静态库
Ubpa_AddTarget(
  MODE STATIC
  INC  include
  LIB  SomeDep::SomeDep
)

# 可执行文件（测试）
Ubpa_AddTarget(
  MODE EXE
  TEST
  LIB_PRIVATE ${PROJECT_NAME}_MyLib
)

# Header-only 库
Ubpa_AddTarget(
  MODE      INTERFACE
  INC       include
  LIB       AnotherDep::AnotherDep
)
```

`Ubpa_AddTarget()` 自动处理：target 命名（`<PROJECT>_<relative_path>`）、源文件递归展开、MSVC `/MP` 并行编译、PDB 安装、`$<BUILD_INTERFACE>/$<INSTALL_INTERFACE>` 路径处理。

### 4. 导出包

```cmake
Ubpa_Export(
  TARGET       # 生成 Targets.cmake
  DIRECTORIES  include cmake
)
```

## 添加依赖

```cmake
# 优先本地 find_package，找不到则从 GitHub Ubpa/<name> 拉取
Ubpa_AddDep(UDRefl 0.9.3)
Ubpa_AddDep(USTL  0.1.1)
```

同一依赖被多个子项目声明时，版本相同自动跳过，版本不同立即报错（菱形依赖保护）。

## 编译器要求

| 编译器 | 最低版本 | 说明 |
|--------|----------|------|
| MSVC   | 19.26（VS2019 16.6） | 支持 C++20 concept |
| GCC    | 10 | 支持 C++20 concept |
| Clang  | 10 | 支持 C++20 concept |

CMake 最低版本：**3.16**

## 文档

- [CMake 基础参考](doc/intro.md)
- [cmake/ 模块语义文档](.codocs/docs/cmake.md)（codocs）
