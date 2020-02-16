Ubpa_GetTargetName(config_targetName ${CMAKE_CURRENT_SOURCE_DIR})

configure_file(Ubpa_config_servant_dll.in "${PROJECT_SOURCE_DIR}/include/test_03_dll/Ubpa_config_servant_dll.h")

Ubpa_GlobGroupSrcs(RST sources PATHS
	${CMAKE_CURRENT_SOURCE_DIR}
	"${PROJECT_SOURCE_DIR}/include/test_03_dll"
)

Ubpa_AddTarget(MODE "DLL" SOURCES ${sources})
