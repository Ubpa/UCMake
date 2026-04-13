# CPM.cmake

第三方包管理器，版本 0.27.2-development-version（来自 [TheLartians/CPM.cmake](https://github.com/TheLartians/CPM.cmake)）。基于 CMake 内置的 `FetchContent` 封装，提供更简洁的包声明语法和版本冲突警告。

## 核心 API

| 函数 | 说明 |
|------|------|
| `CPMAddPackage(...)` | 从 Git/本地/源码下载并添加依赖，支持 `GITHUB_REPOSITORY`、`GIT_TAG`、`SOURCE_DIR` 等参数 |
| `CPMFindPackage(...)` | 先尝试 `find_package`，找不到再 `CPMAddPackage` |
| `CPMDeclarePackage(Name ...)` | 预声明包参数（延迟实际下载），后续 `CPMGetPackage` 触发 |
| `CPMGetPackage(Name)` | 获取已声明的包 |
| `CPMUsePackageLock(file)` | 加载 lock 文件并启用 `cpm-update-package-lock` target |

## 缓存与模式控制

通过 option / 环境变量控制行为：

| 变量 | 说明 |
|------|------|
| `CPM_USE_LOCAL_PACKAGES` | 优先 `find_package` |
| `CPM_LOCAL_PACKAGES_ONLY` | 仅 `find_package`，找不到报错 |
| `CPM_DOWNLOAD_ALL` | 强制下载，跳过 `find_package` |
| `CPM_SOURCE_CACHE` | 源码缓存目录，同一 origin hash 复用 |
| `CPM_DONT_UPDATE_MODULE_PATH` | 不修改 `CMAKE_MODULE_PATH` |

## 关键细节

- **版本冲突**：同一包被多次 `include(CPM.cmake)` 时，如果子依赖用了更新版本会触发 `AUTHOR_WARNING`。当前代码注释了 `return()` 保护（即不拒绝重复加载），需注意潜在重复执行。
- **缓存 hash**：`CPM_SOURCE_CACHE` 模式下用 `SHA1(origin_parameters sorted)` 作子目录名，相同参数可复用离线缓存。
- **Shallow clone 自动判断**：`GIT_TAG` 不像 commit hash 时自动加 `GIT_SHALLOW TRUE` 加速下载。
- **Package lock**：`cpm-package-lock.cmake` 文件应提交到版本控制，记录实际使用的包声明。
