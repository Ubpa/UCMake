set (libs "")
if(MSVC)
  #
elseif("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")
  list(APPEND libs "dl")
elseif("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
  list(APPEND libs "dl")
endif()

Ubpa_AddTarget(
  TEST
  RET_TARGET_NAME tname
  MODE EXE
  LIB_PRIVATE
    ${libs}
)

add_dependencies(${tname} UCMake_test_05_dll_class_virtual_gen)
