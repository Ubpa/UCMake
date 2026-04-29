---
codocs:
  schema: 1
  source_type: file
  source_path: cmake/UbpaQt.cmake
  source_hash: sha256:665659f6b532142ae8c39c2c17b5077d376ac8f6d30f203e6bc111082e8d7d0a
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-14T17:11:10.658413+08:00'
---
# UbpaQt.cmake

Qt5 集成：初始化、AUTOMOC/AUTOUIC/AUTORCC 开关、Windows DLL 安装。

## API

| 函数/宏 | 说明 |
|---------|------|
| `Ubpa_QtInit(COMPONENTS <list>)` | `find_package(Qt5)`、开 `CMAKE_INCLUDE_CURRENT_DIR`，Windows 下安装组件 DLL |
| `Ubpa_QtBegin()` / `Ubpa_QtEnd()` | 开/关 AUTOMOC/AUTOUIC/AUTORCC，供 `Ubpa_AddTarget(QT)` 临时切换 |

## 注意

- `Ubpa_QtInit` 是 macro，`CMAKE_INCLUDE_CURRENT_DIR` 在调用方 scope 生效（全局）。
- DLL 路径从 `Qt5_DIR` 上退 3 层推断，不存在 WARNING 不中断 configure。
