---
codocs:
  schema: 1
  source_type: file
  source_path: cmake/UbpaDownload.cmake
  source_hash: sha256:284dacbbd77eebd6425d63910bca38ab0f6346798472f346374f8a192b11f532
  explicit_deps: []
  dep_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  hash_mode: text-lf-sha256
  verified_at: '2026-04-14T17:11:10.658413+08:00'
---
# UbpaDownload.cmake

文件下载与 zip 解压工具模块，支持 hash 校验缓存（已存在且 hash 匹配则跳过下载）。

## API

| 函数 | 说明 |
|------|------|
| `Ubpa_IsNeedDownload(<rst> <filename> <hash_type> <hash>)` | 检查文件是否存在且 hash 匹配，结果写入 `rst` |
| `Ubpa_DownloadFile(<url> <filename> <hash_type> <hash>)` | 下载单文件，带 hash 校验和超时（120s），失败 FATAL_ERROR |
| `Ubpa_DownloadZip(<url> <zipname> <hash_type> <hash>)` | 下载并解压 zip 到 `CMAKE_CURRENT_SOURCE_DIR` |
| `Ubpa_DownloadZip_Pro(<url> <zipname> <dir> <hash_type> <hash>)` | 同上，可指定解压目录 |
| `Ubpa_DownloadTestFile/Zip/Zip_Pro(...)` | 同上三个函数，受 `Ubpa_BuildTest_<PROJECT>` 开关控制 |

## 注意

- hash 比较大小写不敏感（双方均转小写）。
- zip 缓存路径：`${CMAKE_BINARY_DIR}/${PROJECT_NAME}/${zipname}`，按项目隔离。
- 解压用 `cmake -E tar`，不支持密码保护 zip。
