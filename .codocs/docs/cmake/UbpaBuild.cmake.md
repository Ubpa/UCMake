---
codocs:
  schema: 1
  source_type: file
  source_path: cmake/UbpaBuild.cmake
  source_hash: sha256:e2fe4ff91bb98744d900580078a298ae7923a17f010053f6cf127d35aff4bf37
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-14T17:11:10.658413+08:00'
---
# UbpaBuild.cmake

目标构建核心模块，提供统一的 `Ubpa_AddTarget` 函数，屏蔽 CMake 原生 API 的繁琐性。

## API

| 函数 | 说明 |
|------|------|
| `Ubpa_AddSubDirsRec(path)` | 递归扫描 `path` 下所有含 `CMakeLists.txt` 的子目录并 `add_subdirectory` |
| `Ubpa_GetTargetName(<result> <targetPath>)` | 根据路径生成 target 名：相对 `src/` 路径 + `_` + `PROJECT_NAME` 前缀 |
| `Ubpa_AddTarget(...)` | 统一添加各类 target，详见下方 |

## Ubpa_AddTarget 参数

**Mode（必选）**：`EXE` / `STATIC` / `SHARED` / `INTERFACE` / `STATIC_AND_SHARED`

**布尔开关**：
- `TEST` — 测试目标（受 `Ubpa_BuildTest_<PROJECT>` 控制，排除出 ALL，自动注册 CTest）
- `QT` — 启用 Qt（调用 `Ubpa_QtBegin/End`）
- `NOT_GROUP` — 不生成 MSVC source_group

**单值**：
- `ADD_CURRENT_TO` — 当前目录加入哪个可见性（`PUBLIC`/`INTERFACE`/`PRIVATE`(默认)/`NONE`）
- `OUTPUT_NAME` — 覆盖输出文件名
- `RET_TARGET_NAME` — 将生成的 target 名写回调用方变量
- `CXX_STANDARD` — 覆盖 C++ 标准（默认继承 `CMAKE_CXX_STANDARD`）
- `PCH_REUSE_FROM` — 复用另一个 target 的预编译头

**列表（三种可见性 PUBLIC/INTERFACE/PRIVATE）**：
- `SOURCE` / `SOURCE_PUBLIC` / `SOURCE_INTERFACE` — 源文件或目录（目录递归展开）
- `INC` / `INC_INTERFACE` / `INC_PRIVATE` — include 目录
- `LIB` / `LIB_INTERFACE` / `LIB_PRIVATE` — 链接库
- `DEFINE` / `DEFINE_INTERFACE` / `DEFINE_PRIVATE` — 编译宏定义
- `C_OPTION` / `C_OPTION_INTERFACE` / `C_OPTION_PRIVATE` — 编译选项
- `L_OPTION` / `L_OPTION_INTERFACE` / `L_OPTION_PRIVATE` — 链接选项
- `PCH` / `PCH_PUBLIC` / `PCH_INTERFACE` — 预编译头

## 关键行为

- **INTERFACE mode**：自动将所有 PUBLIC/PRIVATE 参数合并为 INTERFACE，使 INTERFACE library 使用正确。
- **源文件展开**（`_Ubpa_ExpandSources`）：目录参数会递归展开为文件列表，支持 .h/.hpp/.cpp/.cxx/.inl/.glsl 着色器后缀等（HLSL 被注释禁用）。
- **MSVC /MP**：非 INTERFACE target 自动添加并行编译选项。
- **install**：非 TEST target 自动安装，`INC` 和 `SOURCE_PUBLIC` 用 `$<BUILD_INTERFACE:>/$<INSTALL_INTERFACE:>` generator expression 处理路径，安装后路径前缀为 `<package_name>/`。
- **SHARED 宏**：SHARED 模式自动添加 `UCMAKE_EXPORT_<target>` 私有定义，`STATIC_AND_SHARED` 的 static 端加 `UCMAKE_STATIC_<target>` 公共定义。
- **PDB 安装**：MSVC 下自动安装各配置的 .pdb 文件（dll pdb → bin，lib pdb → lib 目录）。
- **CXX_STANDARD**：通过 `target_compile_features(cxx_std_XX)` 设置，会传播给依赖方，而非仅设置 `CMAKE_CXX_STANDARD`。
