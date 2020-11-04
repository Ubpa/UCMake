cmake_minimum_required(VERSION 3.14 FATAL_ERROR)

project (UCMake VERSION 0.6.3)
message(STATUS "[Project] ${PROJECT_NAME} ${PROJECT_VERSION}")

list(APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake")
include(UbpaInit)

Ubpa_InitProject()

Ubpa_AddSubDirsRec(src)

Ubpa_Export(
  DIRECTORIES
    "cmake"
)
