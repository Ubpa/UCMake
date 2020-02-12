#项目名，默认为目录名
Ubpa_GetDirName(DIRNAME)
set(targetName "${DIRNAME}")

#多个源文件用 ';' 分隔
#如：
# list(APPEND sources "main.cpp;src_2.cpp;help.h")
# list(APPEND sources "help2.h")
Ubpa_GlobGroupSrcs(files0 ${CMAKE_CURRENT_SOURCE_DIR})
Ubpa_GlobGroupSrcs(files1 "${PROJECT_SOURCE_DIR}/include/Test_01_GroupSrcs")
set(sources "")
list(APPEND sources "${files0}")
list(APPEND sources "${files1}")

#多个库文件用 ';' 分隔，如果为空，则为 ""
#如：
# list(APPEND libs "")
# list(APPEND libs "a;b")
set(libs "")

Ubpa_AddTarget(MODE "EXE" NAME "${targetName}" SOURCES ${sources} LIBS ${libs})
