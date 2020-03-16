Ubpa_GlobGroupSrcs(RST sources PATHS
	${CMAKE_CURRENT_SOURCE_DIR}
	"${PROJECT_SOURCE_DIR}/include/test_02_lib"
)

Ubpa_AddTarget(MODE "LIB" SOURCES ${sources} TEST ON)
