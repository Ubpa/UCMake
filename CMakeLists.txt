cmake_minimum_required(VERSION 3.16 FATAL_ERROR)

project (UCMake VERSION 1.0.0)
message(STATUS "[Project] ${PROJECT_NAME} ${PROJECT_VERSION}")

list(APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake")
include(UbpaInit)

Ubpa_InitProject(CXX_STANDARD 20)

Ubpa_AddSubDirsRec(src)

# Install infra alongside cmake/ in the package root.
# Files are listed explicitly to avoid symlink issues on Windows
# (Git checks out symlinks as plain text stubs).
set(_ucmake_pkg_name "${PROJECT_NAME}_${PROJECT_VERSION_MAJOR}_${PROJECT_VERSION_MINOR}_${PROJECT_VERSION_PATCH}")
set(_pkg_dst "\${CMAKE_INSTALL_PREFIX}/${_ucmake_pkg_name}")
set(_infra_files
    ".more-hooks/more-hooks.py"
    ".codocs/scripts/codocs.py"
    ".codocs/hooks/pre-commit"
    ".codocs/hooks/commit-msg"
    ".ucmake/hooks/pre-commit"
    ".ucmake/hooks/ascii-check"
)
set(_install_code "")
foreach(_src IN LISTS _infra_files)
    get_filename_component(_dst_dir "${_src}" DIRECTORY)
    string(APPEND _install_code "
    file(INSTALL \"${CMAKE_SOURCE_DIR}/${_src}\"
        DESTINATION \"${_pkg_dst}/${_dst_dir}\"
        USE_SOURCE_PERMISSIONS)")
endforeach()
install(CODE "${_install_code}")

Ubpa_Export(
  DIRECTORIES
    "cmake"
)
