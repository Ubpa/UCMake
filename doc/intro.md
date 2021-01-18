# 基础知识

### 开头

```cmake
cmake_minimum_required(VERSION 3.14 FATAL_ERROR)
project (<project-name> VERSION 1.2.3.4)
# CMAKE_PROJECT_NAME
# PROJECT_VERSION
# - PROJECT_VERSION_MAJOR
# - PROJECT_VERSION_MINOR
# - PROJECT_VERSION_PATCH
# - PROJECT_VERSION_TWEAK
# PROJECT_SOURCE_DIR
```

### 路径变量

- `<project_name>_BINARY_DIR` 含 `project()` 的 `CMakeLists.txt` 所在目录的子文件 `build/` 
- `<project_name>_SOURCE_DIR`：含 `project()` 的 `CMakeLists.txt` 所在目录
- `CMAKE_BINARY_DIR`：`build/` 
- `CMAKE_SOURCE_DIR`：最上级 `CMakeLists.txt` 所在目录
- `CMAKE_CURRENT_BINARY_DIR`：`build/` 内，`CMAKE_CURRENT_SOURCE_DIR` 关于 `CMAKE_SOURCE_DIR` 的相对路径加上 `<project_name>_SOURCE_DIR` 
- `CMAKE_CURRENT_SOURCE_DIR`：正在处理的 `CMakeLists.txt` 所在目录
- `CMAKE_CURRENT_LIST_DIR`：正在处理的 `CMakeLists.txt` 所在目录
  - 当使用 `include()` 时，该变量与 `CMAKE_CURRENT_SOURCE_DIR` 不同
  - （貌似）使用 `find_package()` 时，该变量与 `CMAKE_CURRENT_SOURCE_DIR` 不同

### 变量

- [set](https://cmake.org/cmake/help/v3.16/command/set.html) 

```cmake
# normal
set(<variable-name> <value>... [PARENT_SCOPE])
# cache
set(<variable-name> <value>... CACHE <type> <docstring> [FORCE])
# type: BOOL, FILEPATH, PATH, STRING
# FORCE: 每次 configure 都会刷新
```

- 变量需要区分变量名和变量值，如 `var` 和 `${var}` 

- 变量可以嵌套取值

  ```cmake
  set(A_A aa)
  set(var A)
  message(STATUS "${A_${var}}") # aa
  ```

### 类型

- 字符串 [string](https://cmake.org/cmake/help/v3.16/command/string.html) 

  - 基础

    - 格式 `"..."`，如 `"dd${var}dd"`，`"a string"` 

    - 转义字符加双斜杠，如 `"...\\n..."` 

    - 特殊字符加单斜杠，如 `"...\"..."` 

    - `${var}` 不同于 `"${var}"` 

      ```cmake
      set(specialStr "aaa;bbb")
      
      # example 1
      message(STATUS ${specialStr}) # aaabbb
      message(STATUS "${specialStr}") # aaa;bbb
      
      # example 2
      function(PrintVar var)
        message(STATUS "${var}")
      endfunction()
      
      PrintVar(${specialStr}) # aaa
      PrintVar("${specialStr}") # aaa;bbb
      ```

  - find：`string(FIND <string> <substring> <output_variable> [REVERSE])`，未找到则结果为 `-1` 

  - manipulation

    ```cmake
    string(APPEND <string-var> [<input>...])
    string(PREPEND <string-var> [<input>...])
    string(CONCAT <out-var> [<input>...])
    string(JOIN <glue> <out-var> [<input>...])
    string(TOLOWER <string> <out-var>)
    string(TOUPPER <string> <out-var>)
    string(LENGTH <string> <out-var>)
    string(SUBSTRING <string> <begin> <length> <out-var>)
    string(STRIP <string> <out-var>)
    string(GENEX_STRIP <string> <out-var>)
    string(REPEAT <string> <count> <out-var>)
    ```

  - comparison：`string(COMPARE <op> <string1> <string2> <out-var>)` 

  - hashing：`string(<HASH> <out-var> <input>)` 

- 列表 [list](https://cmake.org/cmake/help/v3.16/command/list.html) 

  - 创建：`set(<list_name> <item>...)` 或 `set(<list_name> "${item_0};${item_1};...;${item_n}")` 

### 调试

[message](https://cmake.org/cmake/help/v3.16/command/message.html) 

```cmake
message(STATUS/WARNING/FATAL_ERROR "str")
```

### 函数

- 按名传参和按值传参

```cmake
function(PrintVar var)
  message(STATUS "${var}: ${${var}}")
endfunction()

function(PrintValue value)
  message(STATUS "${value}")
endfunction()

set(num 3)
PrintVar(num)
PrintValue(${num})
```

- [cmake_parse_arguments](https://cmake.org/cmake/help/v3.16/command/cmake_parse_arguments.html) 

```cmake
cmake_parse_arguments("ARG" # prefix
                      <options> # TRUE / FALSE
                      <one_value_keywords>
                      <multi_value_keywords> # list
                      ${ARGN})
# 结果为 ARG_*
# - ARG_<option>
# - ARG_<one_value_keyword>
# - ARG_<multi_value_keyword>
```

- list 作为参数
  - 调用时写成 `${list}` 会被展开成多个参数
  - 调用时写成 `"${list}"`，函数内部参数即为正常 list
  - 调用时写成 `<list>`，函数内部需使用 `${arg_list}` 得到正常 list

### 控制流

- 循环 n 次

```cmake
set(i 0)
while(i LESS <n>)
  # ...
  math(EXPR i "${i} + 1")
endwhile()
```

- 遍历单个 list

```cmake
foreach(v ${list})
  # ... ${v}
endforeach()
```

- 遍历两个等长 list

```cmake
list(LENGTH <list0> n)
set(i 0)
while(i LESS n)
  list(GET <list0> ${i} v0)
  list(GET <list1> ${i} v1)
  # ...
  math(EXPR i "${i} + 1")
endwhile()
```

- 遍历结构 list

```cmake
list(LENGTH <struct_list> n)
set(i 0)
while(i LESS n)
  list(SUBLIST <struct_list> ${i} <struct_size> <obj>)
  list(GET <obj> 0 <field_0>)
  list(GET <obj> 1 <field_1>)
  # ...
  list(GET <obj> k <field_k>) # k == <struct_size> - 1
  
  # ...
  math(EXPR i "${i} + ${struct_size}")
endwhile()
```

### 正则表达式

- string

```cmake
string(REGEX
	MATCH
	<regular_expression>
	<output_variable>
	<input> [<input>...])
# 匹配一次
# CMAKE_MATCH_<n>
# - 由 '()' 句法捕获
# - n : 0, 1, ..., 9
# - CMAKE_MATCH_0 == <output_variable>
# - n == CMAKE_MATCH_COUNT

string(REGEX
	MATCHALL
	<regular_expression>
	<output_variable>
	<input> [<input>...])
# 匹配多次，结果为 list
# CMAKE_MATCH_* 无用

string(REGEX
	REPLACE
	<regular_expression>
	<replacement_expression>
	<output_variable>
	<input> [<input>...])
# \1, \2, ..., \9 表示 '()' 捕获的结果
# 在 <replacement_expression> 中需要写成 \\1, \\2, ..., \\9
```

- list

```cmake
list(FILTER <list>
  INCLUDE/EXCLUDE
  REGEX <regular_expression>)
# INCLUDE: 将所有匹配替换成 <list>
# EXCLUDE: 将所有匹配从 <list> 排除
```

### target

- add: [add_executable](https://cmake.org/cmake/help/v3.16/command/add_executable.html), [add_library](https://cmake.org/cmake/help/v3.16/command/add_library.html) 

```cmake
# 1. add target
  # 1.1 exe
  add_executable(<name> [<source>...])

  # 1.2 lib/dll
    # 1.2.1 normal
    add_library(<name> STATIC|SHARED [<source>...])
    # 1.2.2 interface : e.g. pure head files
    add_library(<name> INTERFACE)

# 2. alias
add_library(<alias> ALIAS <target>)
# <alias> 可以用命名空间 <namespace>::<id>，如 Ubpa::XXX
```

- source: 

```cmake
target_sources(<target>
  PUBLIC    <item>...
  PRIVATE   <item>...
  INTERFACE <item>...
)

# gather sources
file(GLOB_RECURSE sources
  # header files
  <path>/*.h
  <path>/*.hpp
  <path>/*.hxx
  <path>/*.inl
  
  # source files
  <path>/*.c
  
  <path>/*.cc
  <path>/*.cpp
  <path>/*.cxx
  
  # shader files
  <path>/*.vert # glsl vertex shader
  <path>/*.tesc # glsl tessellation control shader
  <path>/*.tese # glsl tessellation evaluation shader
  <path>/*.geom # glsl geometry shader
  <path>/*.frag # glsl fragment shader
  <path>/*.comp # glsl compute shader
  
  <path>/*.hlsl
  
  # Qt files
  <path>/*.qrc
  <path>/*.ui
)

# group
foreach(source ${sources})
  get_filename_component(dir ${source} DIRECTORY)
  if(${CMAKE_CURRENT_SOURCE_DIR} STREQUAL ${dir})
    source_group("src" FILES ${source})
  else()
    file(RELATIVE_PATH rdir ${PROJECT_SOURCE_DIR} ${dir})
    if(MSVC)
      string(REPLACE "/" "\\" rdir_MSVC ${rdir})
      set(rdir "${rdir_MSVC}")
    endif()
    source_group(${rdir} FILES ${source})
  endif()
endforeach()
```

- definition

```cmake
target_compile_definitions(<target>
  PUBLIC    <item>...
  PRIVATE   <item>...
  INTERFACE <item>...
)
# <item> => #define <item>
```

- include directorie

```cmake
target_include_directories(mylib PUBLIC
  $<BUILD_INTERFACE:<absolute_path>>
  $<INSTALL_INTERFACE:<relative_path>>  # <install_prefix>/<relative_path>
)
# e.g.
# - <absolute_path>: ${PROJECT_SOURCE_DIR}/include
# - <relative_path>: <package_name>/include
```

- link library

```cmake
target_link_libraries(<target>
  PUBLIC    <item>...
  PRIVATE   <item>...
  INTERFACE <item>...
)
```

### file

- Reading

  - READ: `file(READ <filename> <out>)` 
  - STRINGS: `file(STRINGS <filename> <variable> [<options>...])` 
  - HASH: `file(<HASH> <filename> <variable>)` 
    - `<HASH>`：`MD5/SHA1/SHA224/SHA256/SHA384/SHA512/SHA3_224/SHA3_256/SHA3_384/SHA3_512` 

- Writing

  - WRITE/APPEND: `file(WRITE/APPEND <filename> <content>...)` 
  - TOUCH: `file(TOUCH [<files>...])` 
    - 若文件不存在，创建空文件
    - 若文件存在，则更新访问和/或修改时间
    - TOUCH_NOCREATE
  - GENERATE: `file(GENERATE OUTPUT <output_file> <INPUT input-file|CONTENT content>)` 
    - 在 **generation 阶段** 生成文件
    - 可添加 `CONTIDION <expression>`，其中 `<expression> == 0/1` 

- file system

  - GLOB

    ```cmake
    file(GLOB/GLOB_RECURSE <out_list>
         [LIST_DIRECTORIES true|false] # 是否包含目录
         [RELATIVE <path>] # 相对路径
         [CONFIGURE_DEPENDS] # 将结果的所有文件作为 rebuild 的检测对象
         [<globbing-expressions>...] # 简化版的正则表达式
         )
    ```

    - `<globbing-expressions>` 
      - ref：[Linux Programmer's Manual GLOB](http://man7.org/linux/man-pages/man7/glob.7.html) 
      - `?`：匹配单个字符
      - `*`：匹配**文件名/文件夹名**内的任意个字符
      - `**`：跨目录匹配任意个字符
      - `[...]`：同于正则表达式的 `[...]` 
      - `[!...]`：补

  - RENAME：`file(RENAME <oldname> <newname>)`，移动文件或文件夹

  - REMOVE：`file(REMOVE/REMOVE_RECURSE [<files>...])` 

    - `REMOVE`：删除文件，不能删除文件夹
    - `REMOVE_RECURSE`：删除文件或文件夹

  - MAKE_DIRECTORY：`file(MAKE_DIRECTORY [<directories>...])`，递归创建文件夹

  - COPY/INSTALL：`file(COPY/INSTALL <files>... DESTINATION <dir>`，拷贝/安装文件

- path conversion

  - `file(RELATIVE_PATH <variable> <directory> <file>)` 
  - `file(TO_CMAKE_PATH "<path>" <variable>)`，`'/'` 
  - `file(TO_NATIVE_PATH "<path>" <variable>)`，Windows `'\\'`，其他 `'/'` 

- transfer

  - `file(DOWNLOAD <url> <file> [<options>...])` 
    - `INACTIVITY_TIMEOUT <seconds>`：无响应等待时长
    - `TIMEOUT <seconds>`：总等待时长
    - `SHOW_PROGReSS`：进度
    - `STATUS <variable>`：状态为两个值的 list，前者为 0 时表示无错
    - `EXPECTED_HASH <HASH>=<value>`：哈希值

### package

- `<namespace>`，e.g. `Ubpa` 

- `<package_name>` 

  - e.g. `${PROJECT_NAME}_${PROJECT_VERSION_MAJOR}_${PROJECT_VERSION_MINOR}_${PROJECT_VERSION_PATCH}` 

- target name：`${PROJECT_NAME}_${relative_path}`，其中 `/` 要转成 `_` 

  - `string(REPLACE "/" "_" targetName "${PROJECT_NAME}_${relative_path}")` 

- bin, dll, lib path

  ```cmake
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/bin")
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG "${PROJECT_SOURCE_DIR}/bin")
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE "${PROJECT_SOURCE_DIR}/bin")
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib")
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_DEBUG "${PROJECT_SOURCE_DIR}/lib")
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_RELEASE "${PROJECT_SOURCE_DIR}/lib")
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib")
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_DEBUG "${PROJECT_SOURCE_DIR}/lib")
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE "${PROJECT_SOURCE_DIR}/lib")
  ```

- debug postfix

  - dll, lib: `set(CMAKE_DEBUG_POSTFIX d)` 
  - exe: `set_target_properties(<target> PROPERTIES DEBUG_POSTFIX ${CMAKE_DEBUG_POSTFIX})` 

- install

  ```cmake
  install(TARGETS <target>...
    EXPORT "${PROJECT_NAME}Targets" # 链接 export
    RUNTIME DESTINATION bin # .exe, .dll
    LIBRARY DESTINATION "${package_name}/lib" # non-DLL shared library
    ARCHIVE DESTINATION "${package_name}/lib" # .lib
  )
  
  install(FILES "${PROJECT_SOURCE_DIR}/include" DESTINATION "${package_name}/include")
  ```

- install export

  ```cmake
  install(EXPORT "${PROJECT_NAME}Targets"
    NAMESPACE <namespace>
  )
  ```

- config

  ```cmake
  include(CMakePackageConfigHelpers)
  
  configure_package_config_file(${PROJECT_SOURCE_DIR}/config/Config.cmake.in
    "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake"
    INSTALL_DESTINATION "${package_name}/cmake" # 仅生成文件使用，后续还需要自行 install
    NO_SET_AND_CHECK_MACRO
    NO_CHECK_REQUIRED_COMPONENTS_MACRO
    PATH_VARS "${package_name}/include"
  )
  
  write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake"
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY ExactVersion
  )
  
  install(FILES ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake
                ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake
          DESTINATION “${PROJECT_NAME}/cmake”
  )
  ```

# 配合 VS

- cmake -G "Visual Studio 16 2019" -A x64 -S ./ -B ./build

