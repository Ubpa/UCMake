# 1. include all cmake files
# 2. debug postfix
# 3. C++ 17
# 4. install prefix
# 5. set Ubpa_BuildTest_${PROJECT_NAME}
# 6. output directory
# 7. use folder

message(STATUS "include UbpaInit.cmake")

include("${CMAKE_CURRENT_LIST_DIR}/UbpaBasic.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/UbpaBuild.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/UbpaDownload.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/UbpaGit.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/UbpaPackage.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/UbpaQt.cmake")

#Ubpa_DownloadFile(
#  https://cdn.jsdelivr.net/gh/Ubpa/UData@master/UCMake/CPM/CPM_3b40429.cmake
#  "${CMAKE_CURRENT_LIST_DIR}/CPM.cmake"
#  SHA256 438E319D455FD96E18F6CAD9DF596FCD5C9CA3590B1B2EDFA01AF7809CD7BEC7
#)
set(CPM_USE_LOCAL_PACKAGES TRUE CACHE BOOL "" FORCE)
include("${CMAKE_CURRENT_LIST_DIR}/CPM.cmake")

# ---------------------------------------------------------

macro(Ubpa_InitProject)
  set(CMAKE_DEBUG_POSTFIX d)
  set(CMAKE_MINSIZEREL_POSTFIX msr)
  set(CMAKE_RELWITHDEBINFO_POSTFIX rd)

  set(CMAKE_CXX_STANDARD 20)
  set(CMAKE_CXX_STANDARD_REQUIRED True)
  
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
  
  if(NOT Ubpa_RootProjectPath)
    set(Ubpa_RootProjectPath ${PROJECT_SOURCE_DIR})
  endif()
  
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${Ubpa_RootProjectPath}/bin")
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG "${Ubpa_RootProjectPath}/bin")
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE "${Ubpa_RootProjectPath}/bin")
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_MINSIZEREL "${Ubpa_RootProjectPath}/bin")
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELWITHDEBINFO "${Ubpa_RootProjectPath}/bin")
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib")
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_DEBUG "${PROJECT_SOURCE_DIR}/lib")
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_RELEASE "${PROJECT_SOURCE_DIR}/lib")
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_MINSIZEREL "${PROJECT_SOURCE_DIR}/lib")
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_RELWITHDEBINFO "${PROJECT_SOURCE_DIR}/lib")
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/bin")
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_DEBUG "${PROJECT_SOURCE_DIR}/bin")
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE "${PROJECT_SOURCE_DIR}/bin")
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_MINSIZEREL "${PROJECT_SOURCE_DIR}/bin")
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELWITHDEBINFO "${PROJECT_SOURCE_DIR}/bin")
  
  set_property(GLOBAL PROPERTY USE_FOLDERS ON)
endmacro()
