cmake_minimum_required(VERSION 3.16 FATAL_ERROR)

project (UCMake VERSION 0.7.3)
message(STATUS "[Project] ${PROJECT_NAME} ${PROJECT_VERSION}")

list(APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake")
include(UbpaInit)

Ubpa_InitProject(CXX_STANDARD 20)

Ubpa_AddSubDirsRec(src)

# Install infra/ (hook tooling: more-hooks, codocs, ucmake hooks)
# Must live alongside cmake/ so UbpaInit.cmake can resolve ../infra
set(_ucmake_pkg_name "${PROJECT_NAME}_${PROJECT_VERSION_MAJOR}_${PROJECT_VERSION_MINOR}_${PROJECT_VERSION_PATCH}")
install(DIRECTORY infra/ DESTINATION "${_ucmake_pkg_name}/infra")

Ubpa_Export(
  DIRECTORIES
    "cmake"
)
