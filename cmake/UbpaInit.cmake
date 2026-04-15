# 1. include all cmake files
# 2. debug postfix
# 3. C++ standard (default 20)
# 4. install prefix
# 5. set Ubpa_BuildTest_${PROJECT_NAME}
# 6. output directory
# 7. use folder

message(STATUS "include UbpaInit.cmake")

# capture list dir at include time (CMAKE_CURRENT_LIST_DIR changes inside macros)
set(UBPA_UCMAKE_LIST_DIR "${CMAKE_CURRENT_LIST_DIR}")

include("${CMAKE_CURRENT_LIST_DIR}/UbpaBasic.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/UbpaBuild.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/UbpaDownload.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/UbpaGit.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/UbpaPackage.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/UbpaQt.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/UbpaDoc.cmake")

#Ubpa_DownloadFile(
#  https://cdn.jsdelivr.net/gh/Ubpa/UData@master/UCMake/CPM/CPM_3b40429.cmake
#  "${CMAKE_CURRENT_LIST_DIR}/CPM.cmake"
#  SHA256 438E319D455FD96E18F6CAD9DF596FCD5C9CA3590B1B2EDFA01AF7809CD7BEC7
#)
set(CPM_USE_LOCAL_PACKAGES TRUE CACHE BOOL "" FORCE)
include("${CMAKE_CURRENT_LIST_DIR}/CPM.cmake")

# ---------------------------------------------------------

macro(Ubpa_InitProject)
  cmake_parse_arguments("_INIT" "" "CXX_STANDARD" "" ${ARGN})

  set(CMAKE_DEBUG_POSTFIX "d")
  set(CMAKE_RELEASE_POSTFIX "")
  set(CMAKE_MINSIZEREL_POSTFIX "msr")
  set(CMAKE_RELWITHDEBINFO_POSTFIX "rd")

  if(NOT "${_INIT_CXX_STANDARD}" STREQUAL "")
    set(CMAKE_CXX_STANDARD ${_INIT_CXX_STANDARD})
  else()
    set(CMAKE_CXX_STANDARD 20)
  endif()
  set(CMAKE_CXX_STANDARD_REQUIRED True)

  if(NOT CMAKE_BUILD_TYPE)
    message(NOTICE "No default CMAKE_BUILD_TYPE, so UCMake set it to \"Release\"")
    set(CMAKE_BUILD_TYPE Release CACHE STRING
      "Choose the type of build, options are: None Debug Release RelWithDebInfo MinSizeRel." FORCE)
  endif()

  add_compile_definitions(UCMAKE_CONFIG_$<UPPER_CASE:$<CONFIG>>)
  add_compile_definitions(
    $<$<CONFIG:Debug>:UCMAKE_CONFIG_POSTFIX="${CMAKE_DEBUG_POSTFIX}">
    $<$<CONFIG:Release>:UCMAKE_CONFIG_POSTFIX="">
    $<$<CONFIG:MinSizeRel>:UCMAKE_CONFIG_POSTFIX="${CMAKE_MINSIZEREL_POSTFIX}">
    $<$<CONFIG:RelWithDebInfo>:UCMAKE_CONFIG_POSTFIX="${CMAKE_RELWITHDEBINFO_POSTFIX}">
    $<$<NOT:$<OR:$<CONFIG:Debug>,$<CONFIG:Release>,$<CONFIG:MinSizeRel>,$<CONFIG:RelWithDebInfo>>>:UCMAKE_CONFIG_POSTFIX="">
  )
  if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")
  # using Clang
    message(STATUS "Compiler: Clang ${CMAKE_CXX_COMPILER_VERSION}")
    if(CMAKE_CXX_COMPILER_VERSION VERSION_LESS "10")
      message(FATAL_ERROR "clang (< 10) not support concept")
      return()
    endif()
  elseif ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
    message(STATUS "Compiler: GCC ${CMAKE_CXX_COMPILER_VERSION}")
    if(CMAKE_CXX_COMPILER_VERSION VERSION_LESS "10")
      message(FATAL_ERROR "gcc (< 10) not support concept")
      return()
    endif()
  # using GCC
  elseif ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "MSVC")
  # using Visual Studio C++
    message(STATUS "Compiler: MSVC ${CMAKE_CXX_COMPILER_VERSION}")
    if(CMAKE_CXX_COMPILER_VERSION VERSION_LESS "19.26")
      message(FATAL_ERROR "MSVC (< 1926 / 2019 16.6) not support concept")
      return()
    endif()
  else()
    message(WARNING "Unknown CMAKE_CXX_COMPILER_ID : ${CMAKE_CXX_COMPILER_ID}")
  endif()
  
  message(STATUS "CXX_STANDARD: ${CMAKE_CXX_STANDARD}")
  
  if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
    Ubpa_Path_Back(root ${CMAKE_INSTALL_PREFIX} 1)
    set(CMAKE_INSTALL_PREFIX "${root}/Ubpa" CACHE PATH "install prefix" FORCE)
  endif()
  
  set("Ubpa_BuildTest_${PROJECT_NAME}" TRUE CACHE BOOL "build tests for ${PROJECT_NAME}")

  # enable CTest
  enable_testing()

  # create a custom target for building all tests
  if(NOT TARGET ${PROJECT_NAME}_BuildTests)
    add_custom_target(${PROJECT_NAME}_BuildTests)
    set_target_properties(${PROJECT_NAME}_BuildTests PROPERTIES FOLDER "${PROJECT_NAME}")
  endif()

  # create a custom target for running all tests (builds first, then runs ctest)
  include(ProcessorCount)
  ProcessorCount(UBPA_PROCESSOR_COUNT)
  if(UBPA_PROCESSOR_COUNT EQUAL 0)
    set(UBPA_PROCESSOR_COUNT 4)
  endif()

  if(NOT TARGET ${PROJECT_NAME}_RunTests)
    add_custom_target(${PROJECT_NAME}_RunTests
      COMMAND ${CMAKE_CTEST_COMMAND} -j${UBPA_PROCESSOR_COUNT} --build-config $<CONFIG> --output-on-failure
      WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
      COMMENT "Running all tests for ${PROJECT_NAME} (parallel: ${UBPA_PROCESSOR_COUNT})..."
      DEPENDS ${PROJECT_NAME}_BuildTests
    )
    set_target_properties(${PROJECT_NAME}_RunTests PROPERTIES FOLDER "${PROJECT_NAME}")
  endif()

  # create a check target: rebuilds all test binaries then runs ctest
  # (unlike RunTests, this uses cmake --build to force MSBuild to recompile changed sources)
  if(NOT TARGET ${PROJECT_NAME}_Check)
    add_custom_target(${PROJECT_NAME}_Check
      COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --config $<CONFIG> --target ${PROJECT_NAME}_BuildTests
      COMMAND ${CMAKE_CTEST_COMMAND} -C $<CONFIG> -j${UBPA_PROCESSOR_COUNT} --output-on-failure
      WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
      COMMENT "Building tests and running ctest for ${PROJECT_NAME}..."
    )
    set_target_properties(${PROJECT_NAME}_Check PROPERTIES FOLDER "${PROJECT_NAME}")
  endif()

  # -- Hook tooling: generate project.env + auto-register via more-hooks ------
  # .more-hooks/ .codocs/ .ucmake/ sit alongside cmake/ in the UCMake install tree
  get_filename_component(_ucmake_root "${UBPA_UCMAKE_LIST_DIR}/.." ABSOLUTE)

  # Generate .ucmake/project.env (runtime values for the static ucmake hook script)
  set(UCMAKE_DEFAULT_CONFIG "Release")
  file(MAKE_DIRECTORY "${CMAKE_SOURCE_DIR}/.ucmake")
  file(WRITE "${CMAKE_SOURCE_DIR}/.ucmake/project.env"
    "UCMAKE_PROJECT_NAME=${PROJECT_NAME}\n"
    "UCMAKE_BUILD_DIR=${CMAKE_BINARY_DIR}\n"
    "UCMAKE_DEFAULT_CONFIG=${UCMAKE_DEFAULT_CONFIG}\n"
  )
  # Gitignore for .ucmake/ (project.env is a configure artifact, not tracked)
  file(WRITE "${CMAKE_SOURCE_DIR}/.ucmake/.gitignore" "project.env\n")
  message(STATUS "[UCMake] Generated .ucmake/project.env")

  # Auto-register hooks via more-hooks
  set(_more_hooks_py "${_ucmake_root}/.more-hooks/more-hooks.py")
  if(EXISTS "${_more_hooks_py}")
    find_package(Python3 COMPONENTS Interpreter QUIET)
    if(Python3_FOUND)
      # codocs pre-commit (priority 50)
      execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${_more_hooks_py}" register "${CMAKE_SOURCE_DIR}"
          --hook pre-commit
          --id codocs
          --script "${_ucmake_root}/.codocs/hooks/pre-commit"
          --priority 50
          --symlink
          --force
        RESULT_VARIABLE _mh_rc
        OUTPUT_QUIET ERROR_QUIET
      )
      # codocs commit-msg (priority 50)
      execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${_more_hooks_py}" register "${CMAKE_SOURCE_DIR}"
          --hook commit-msg
          --id codocs
          --script "${_ucmake_root}/.codocs/hooks/commit-msg"
          --priority 50
          --symlink
          --force
        RESULT_VARIABLE _mh_rc
        OUTPUT_QUIET ERROR_QUIET
      )
      # ucmake ascii-check pre-commit (priority 70)
      execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${_more_hooks_py}" register "${CMAKE_SOURCE_DIR}"
          --hook pre-commit
          --id ucmake-ascii
          --script "${_ucmake_root}/.ucmake/hooks/ascii-check"
          --priority 70
          --symlink
          --force
        RESULT_VARIABLE _mh_rc
        OUTPUT_QUIET ERROR_QUIET
      )
      # ucmake pre-commit (priority 80)
      execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${_more_hooks_py}" register "${CMAKE_SOURCE_DIR}"
          --hook pre-commit
          --id ucmake
          --script "${_ucmake_root}/.ucmake/hooks/pre-commit"
          --priority 80
          --symlink
          --force
        RESULT_VARIABLE _mh_rc
        OUTPUT_QUIET ERROR_QUIET
      )
      message(STATUS "[UCMake] Registered hooks via more-hooks (root: ${_ucmake_root})")
    else()
      message(WARNING "[UCMake] Hook registration skipped: Python3 not found")
    endif()
  else()
    message(WARNING "[UCMake] Hook registration skipped: more-hooks not found at ${_ucmake_root} (run cmake --install first)")
  endif()
  unset(_ucmake_root)
  unset(_more_hooks_py)
  unset(_mh_rc)

  # create a custom target for install
  if(NOT TARGET ${PROJECT_NAME}_Install)
    add_custom_target(${PROJECT_NAME}_Install
      COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --config $<CONFIG> --target install
      COMMENT "Installing ${PROJECT_NAME}..."
    )
    set_target_properties(${PROJECT_NAME}_Install PROPERTIES FOLDER "${PROJECT_NAME}")
  endif()

  # create a custom target for batch install (all 4 configurations)
  if(NOT TARGET ${PROJECT_NAME}_InstallAll)
    add_custom_target(${PROJECT_NAME}_InstallAll
      COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --config Debug --target install
      COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --config Release --target install
      COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --config MinSizeRel --target install
      COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --config RelWithDebInfo --target install
      COMMENT "Installing ${PROJECT_NAME} for all configurations (Debug, Release, MinSizeRel, RelWithDebInfo)..."
    )
    set_target_properties(${PROJECT_NAME}_InstallAll PROPERTIES FOLDER "${PROJECT_NAME}")
  endif()

  if(NOT Ubpa_RootProjectPath)
    set(Ubpa_RootProjectPath ${PROJECT_SOURCE_DIR})
  endif()
  
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${Ubpa_RootProjectPath}/bin")
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_MINSIZEREL ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELWITHDEBINFO ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${Ubpa_RootProjectPath}/lib")
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_DEBUG ${CMAKE_ARCHIVE_OUTPUT_DIRECTORY})
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_RELEASE ${CMAKE_ARCHIVE_OUTPUT_DIRECTORY})
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_MINSIZEREL ${CMAKE_ARCHIVE_OUTPUT_DIRECTORY})
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_RELWITHDEBINFO ${CMAKE_ARCHIVE_OUTPUT_DIRECTORY})
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${Ubpa_RootProjectPath}/bin")
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_DEBUG ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_MINSIZEREL ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELWITHDEBINFO ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
  
  set_property(GLOBAL PROPERTY USE_FOLDERS ON)

  option(Ubpa_${CMAKE_PROJECT_NAME}_BuildDoc "Build Doc (need Doxygen)" OFF)
  if(Ubpa_${CMAKE_PROJECT_NAME}_BuildDoc)
    find_package(Doxygen REQUIRED)
  else()
    message(STATUS "Not build doc")
  endif()
endmacro()
