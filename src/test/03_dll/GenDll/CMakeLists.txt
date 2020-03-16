Ubpa_GetTargetName(config_targetName ${CMAKE_CURRENT_SOURCE_DIR})
set(config_targetName "${config_targetName}_shared")
configure_file(${PROJECT_SOURCE_DIR}/config/Ubpa_config_dll.in "${PROJECT_SOURCE_DIR}/include/test_03_dll/Ubpa_config_dll_servant.h")

Ubpa_GlobGroupSrcs(RST sources PATHS
	${CMAKE_CURRENT_SOURCE_DIR}
	"${PROJECT_SOURCE_DIR}/include/test_03_dll"
)

Ubpa_AddTarget(MODE "DS" SOURCES ${sources} TEST ON)
