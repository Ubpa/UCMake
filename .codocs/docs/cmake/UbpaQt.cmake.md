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

Qt5 集成工具，封装 Qt 初始化、自动工具开关和 Windows DLL 安装。

## API

| 函数/宏 | 说明 |
|---------|------|
| `Ubpa_QtInit(COMPONENTS <list>)` | 全局 Qt5 初始化：`find_package(Qt5)`、开 `CMAKE_INCLUDE_CURRENT_DIR`，Windows 下自动安装各组件 DLL（Debug/Release） |
| `Ubpa_QtBegin()` | 开启 AUTOMOC/AUTOUIC/AUTORCC（作用于调用方 scope） |
| `Ubpa_QtEnd()` | 关闭 AUTOMOC/AUTOUIC/AUTORCC |

## 关键细节

- `Ubpa_QtInit` 是 **macro**，`CMAKE_INCLUDE_CURRENT_DIR` 的修改在调用方 scope 生效（作用全局）。
- Windows DLL 安装路径通过 `Qt5_DIR` 向上退 3 层得到 Qt 根目录（`<root>/lib/cmake/Qt5` → 上退 3 → `<root>`），再拼 `bin/Qt5<Cmpt>.dll`。若 DLL 不存在则 WARNING，不会中断 configure。
- `Ubpa_QtBegin/End` 通过 function + PARENT_SCOPE 修改外层变量，用于在 `Ubpa_AddTarget(QT)` 中临时开关自动工具，避免污染非 Qt target。
