---
codocs:
  schema: 1
  source_type: dir
  source_path: cmake
  entries_hash: sha256:f744f9ead714e7a2b4701382118c31bd00f89a0b77c56452e13d0be641f41d3b
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-15T01:06:56.215460+08:00'
  source_hash: null
---
# cmake/

UCMake 的 CMake 模块目录，提供统一的项目初始化、构建、包管理、下载和 Qt 集成能力。通常只需 `include(cmake/UbpaInit.cmake)` 即可拉入全部模块，再调用 `Ubpa_InitProject()` 完成项目全局配置。

## 索引

| 名称 | 类型 | 职责 |
|------|------|------|
| UbpaInit.cmake | 文件 | 入口模块，include 所有其他模块并提供 `Ubpa_InitProject()` 完成全局配置 |
| UbpaBuild.cmake | 文件 | 核心构建模块，`Ubpa_AddTarget()` 统一创建各类 CMake target |
| UbpaPackage.cmake | 文件 | 包管理与导出，依赖声明（菱形依赖检测）和 Config/Targets 安装包生成 |
| UbpaBasic.cmake | 文件 | 基础工具函数（列表打印、目录名获取、路径回溯） |
| UbpaDownload.cmake | 文件 | 文件/zip 下载工具，带 hash 校验缓存 |
| UbpaGit.cmake | 文件 | Git 初始化和子模块更新 |
| UbpaQt.cmake | 文件 | Qt5 集成（初始化、AUTOMOC/AUTOUIC/AUTORCC 开关、Windows DLL 安装） |
| UbpaDoc.cmake | 文件 | Doxygen 文档构建辅助 |
| CPM.cmake | 文件 | 第三方包管理器（CPM.cmake v0.42.1），基于 FetchContent 的包声明与缓存 |
