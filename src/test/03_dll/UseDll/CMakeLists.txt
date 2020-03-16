Ubpa_GetTargetName(GenDll "${CMAKE_CURRENT_SOURCE_DIR}/../GenDll")

Ubpa_AddTarget(MODE "EXE" LIBS "${GenDll}_shared" TEST ON)
