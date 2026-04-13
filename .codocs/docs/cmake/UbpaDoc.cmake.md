# UbpaDoc.cmake

Doxygen 文档构建辅助模块。

## API

`Ubpa_BuildDoc(doxyfilein)` — 若 `Doxygen::doxygen` target 存在，基于输入的 Doxyfile 模板生成配置后创建 `<CMAKE_PROJECT_NAME>_doc` 自定义 target；否则静默跳过。

## 行为说明

- 用 `configure_file(@ONLY)` 将 Doxyfile 模板中的 CMake 变量展开，输出到 `CMAKE_CURRENT_BINARY_DIR/Doxyfile`。
- 创建的 target 被放入与项目同名的 IDE folder。
- 只有在 CMake configure 时已找到 Doxygen（通常通过 `find_package(Doxygen)`）才有效，否则整个函数为空操作。
