# UbpaBasic.cmake

基础工具函数集，供其他 Ubpa*.cmake 模块复用。

## API

| 函数 | 说明 |
|------|------|
| `Ubpa_List_Print(STRS <list> [TITLE <t>] [PREFIX <p>])` | 打印列表，支持可选标题和行前缀，列表为空时直接返回 |
| `Ubpa_GetDirName(<result>)` | 将当前目录名（`CMAKE_CURRENT_SOURCE_DIR` 最后一段）写入变量 |
| `Ubpa_Path_Back(<result> <path> <times>)` | 从路径末尾向上退 `times` 层，等效于 `dirname` 执行 N 次 |

## 实现细节

- `Ubpa_Path_Back` 用正则 `(.*)\/` 循环截取，每次去掉最后一段。注意：`times=0` 时 RANGE 0 仍执行一次循环，会意外截断一层——调用方需确保 `times >= 1`。
