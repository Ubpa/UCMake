# UbpaDownload.cmake

文件下载与 zip 解压工具模块，支持 hash 校验缓存（已存在且 hash 匹配则跳过下载）。

## API

| 函数 | 说明 |
|------|------|
| `Ubpa_IsNeedDownload(<rst> <filename> <hash_type> <hash>)` | 检查文件是否存在且 hash 匹配，结果写入 `rst`（`TRUE`/`FALSE`） |
| `Ubpa_DownloadFile(<url> <filename> <hash_type> <hash>)` | 下载单文件，带 hash 校验和超时（120s），失败 FATAL_ERROR |
| `Ubpa_DownloadZip(<url> <zipname> <hash_type> <hash>)` | 下载并解压 zip 到 `CMAKE_CURRENT_SOURCE_DIR` |
| `Ubpa_DownloadZip_Pro(<url> <zipname> <dir> <hash_type> <hash>)` | 同上，可指定解压目录；zip 缓存于 `CMAKE_BINARY_DIR/<PROJECT_NAME>/` |
| `Ubpa_DownloadTestFile(...)` | 同 `DownloadFile`，但受 `Ubpa_BuildTest_<PROJECT>` 开关控制 |
| `Ubpa_DownloadTestZip(...)` | 同 `DownloadZip`，受测试开关控制 |
| `Ubpa_DownloadTestZip_Pro(...)` | 同 `DownloadZip_Pro`，受测试开关控制 |

## 关键细节

- **hash 比较大小写不敏感**：双方均转小写后比较，避免因大小写不一致误判需要重新下载。
- **zip 缓存路径**：统一放在 `${CMAKE_BINARY_DIR}/${PROJECT_NAME}/${zipname}`，按项目隔离，避免多项目冲突。
- **解压用 `cmake -E tar`**，跨平台，但不支持密码保护 zip。
