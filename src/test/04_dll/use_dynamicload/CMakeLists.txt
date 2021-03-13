Ubpa_AddTarget(
  TEST
  RET_TARGET_NAME tname
  MODE EXE
)

add_dependencies(${tname} UCMake_test_04_dll_gen)
