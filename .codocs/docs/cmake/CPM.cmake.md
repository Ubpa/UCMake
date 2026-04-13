# CPM.cmake

第三方包管理器，版本 **0.42.1**（来自 [cpm-cmake/CPM.cmake](https://github.com/cpm-cmake/CPM.cmake)）。基于 CMake 内置的 `FetchContent` 封装，提供更简洁的包声明语法和版本冲突警告。

## 核心 API

| 函数 | 说明 |
|------|------|
| `CPMAddPackage(...)` | 从 Git/本地/源码下载并添加依赖，支持 `GITHUB_REPOSITORY`、`GIT_TAG`、`SOURCE_DIR` 等参数 |
| `CPMFindPackage(...)` | 先尝试 `find_package`，找不到再 `CPMAddPackage` |
| `CPMDeclarePackage(Name ...)` | 预声明包参数（延迟实际下载），后续 `CPMGetPackage` 触发 |
| `CPMGetPackage(Name)` | 获取已声明的包 |
| `CPMRegisterPackage(Name Version)` | 注册已添加的包名和版本（内部使用，也可手动调用） |
| `CPMUsePackageLock(file)` | 加载 lock 文件并启用 `cpm-update-package-lock` target |

## CPMAddPackage 参数

单值参数（`oneValueArgs`）：

| 参数 | 说明 |
|------|------|
| `NAME` | 包名；未指定时从 Git URL 自动推断 |
| `VERSION` | 版本号；未指定时从 `GIT_TAG` 提取 |
| `GIT_TAG` | Git tag / branch / commit hash |
| `GITHUB_REPOSITORY` | `owner/repo` 形式，自动补全为 `https://github.com/...` |
| `GITLAB_REPOSITORY` | 同上，GitLab |
| `BITBUCKET_REPOSITORY` | 同上，Bitbucket |
| `GIT_REPOSITORY` | 完整 Git URL |
| `SOURCE_DIR` | 本地源码目录（不下载） |
| `GIT_SHALLOW` | 显式控制 shallow clone；不设则自动判断 |
| `DOWNLOAD_ONLY` | 只下载，不调用 `add_subdirectory` |
| `FIND_PACKAGE_ARGUMENTS` | 传给 `find_package` 的额外参数 |
| `NO_CACHE` | 强制每次重新下载，不使用 `CPM_SOURCE_CACHE` |
| `SYSTEM` | 将依赖标记为 SYSTEM（屏蔽编译警告）；快捷语法时默认开启 |
| `EXCLUDE_FROM_ALL` | 排除出 ALL target；快捷语法时默认开启 |
| `SOURCE_SUBDIR` | 指定子目录作为 CMake 根（适用于 monorepo） |
| `CUSTOM_CACHE_KEY` | 自定义缓存 key，覆盖默认 hash |
| `FORCE` | 强制重新添加，即使已存在同名包 |

多值参数：`URL`（多镜像）、`OPTIONS`（`-D` 选项）、`DOWNLOAD_COMMAND`、`PATCHES`（patch 文件列表）。

**快捷语法**（单字符串）：
```cmake
CPMAddPackage("gh:nlohmann/json@3.11.3")   # GitHub shorthand
CPMAddPackage("URI gh:nlohmann/json@3.11.3 OPTIONS \"JSON_BuildTests OFF\"")
```
快捷语法自动设置 `EXCLUDE_FROM_ALL YES` 和 `SYSTEM YES`。

## 缓存与模式控制

通过 option / 环境变量控制行为（均支持对应的 `$ENV{}` 环境变量同名启用）：

| 变量 | 说明 |
|------|------|
| `CPM_USE_LOCAL_PACKAGES` | 优先 `find_package` |
| `CPM_LOCAL_PACKAGES_ONLY` | 仅 `find_package`，找不到报错 |
| `CPM_DOWNLOAD_ALL` | 强制下载，跳过 `find_package` |
| `CPM_SOURCE_CACHE` | 源码缓存目录，同一 origin hash 复用 |
| `CPM_USE_NAMED_CACHE_DIRECTORIES` | 缓存目录最内层加包名子目录，便于识别 |
| `CPM_DONT_UPDATE_MODULE_PATH` | 不修改 `CMAKE_MODULE_PATH` |
| `CPM_DONT_CREATE_PACKAGE_LOCK` | 不生成 package lock 文件 |
| `CPM_INCLUDE_ALL_IN_PACKAGE_LOCK` | 将所有包（含无版本）写入 lock 文件 |

## 关键细节

- **仓库迁移**：从 `TheLartians/CPM.cmake` 迁移到 `cpm-cmake/CPM.cmake`，文档和 issue 均已转移。
- **版本冲突**：同一包被多次 `include(CPM.cmake)` 时，子依赖若用了更新版本触发 `AUTHOR_WARNING`；未设 `return()` 保护，注意潜在重复执行。
- **CMake 策略**：`cpm_set_policies()` 在初始化和每次 `CPMAddPackage` 时调用，统一设置：
  - `CMP0077`：允许覆盖 cache 变量（`set()` 不受 `-D` 缓存影响）
  - `CMP0126`：同上，针对 `set(CACHE)`
  - `CMP0135`：FetchContent 使用下载时间戳而非 archive 内时间戳，保证 URL 变更时可正确重建
  - `CMP0150`：相对 git 路径相对于父项目远程地址解析
- **缓存 hash**：`CPM_SOURCE_CACHE` 模式下以 `SHA1(sorted origin params)` 为子目录名；启用 `CPM_USE_NAMED_CACHE_DIRECTORIES` 在最内层追加包名，便于人工识别。
- **Shallow clone**：`GIT_TAG` 非 commit hash 时自动加 `GIT_SHALLOW TRUE`；通过 `GIT_SHALLOW FALSE` 可显式禁用。
- **Patch 支持**：`PATCHES` 参数接收 patch 文件列表，内部通过 `PATCH_COMMAND` 传给 `ExternalProject_Add`；Windows 上找不到 `patch` 时会在 git 安装目录附近查找。
- **find_package 重定向**：CMake ≥ 3.24 时写 `CMAKE_FIND_PACKAGE_REDIRECTS_DIR`（Config 模式重定向），旧版本写 `Find${Name}.cmake` 到 `CPM_MODULE_PATH`。
- **Package lock**：`cpm-package-lock.cmake` 应提交到版本控制；`CPMUsePackageLock()` 加载并注册 `cpm-update-package-lock` target 用于更新。
- **`CPMGetPackageVersion(Name Output)`**：查询已注册包的版本号，存入 `Output` 变量。
