Ubpa_GlobGroupSrcs(RST sources PATHS
	${CMAKE_CURRENT_SOURCE_DIR}
	"${PROJECT_SOURCE_DIR}/include/test_01_GroupSrcs"
)

Ubpa_AddTarget(MODE "EXE" SOURCES ${sources} TEST ON)
