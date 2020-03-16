Ubpa_GetTargetName(libs "${CMAKE_CURRENT_SOURCE_DIR}/../GenDll")

Ubpa_AddTarget(MODE "EXE" LIBS ${libs} TEST ON)
