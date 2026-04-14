---
codocs:
  schema: 1
  source_type: file
  source_path: cmake/UbpaBasic.cmake
  source_hash: sha256:aae9120c4f47a25d4eb6a6ea5281c1d12c6c9a0062bb78b9735cc7785dd652ff
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-14T17:11:10.658413+08:00'
---
# UbpaBasic.cmake

基础工具函数集，供其他 Ubpa*.cmake 模块复用。

## API

| 函数 | 说明 |
|------|------|
| `Ubpa_List_Print(STRS <list> [TITLE <t>] [PREFIX <p>])` | 打印列表，支持可选标题和行前缀，列表为空时直接返回 |
| `Ubpa_GetDirName(<result>)` | 将当前目录名（`CMAKE_CURRENT_SOURCE_DIR` 最后一段）写入变量 |
| `Ubpa_Path_Back(<result> <path> <times>)` | 从路径末尾向上退 `times` 层，等效于 `dirname` 执行 N 次 |

## 实现细节

- `Ubpa_Path_Back` 用正则 `(.*)\/` 循环截取，每次去掉最后一段。`times=0` 时 `math(EXPR stop "-1")`，`foreach(RANGE -1)` 不执行任何循环，返回原路径不变。`times=1` 截去最后一段，以此类推。
