if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")
# using Clang
  if(CMAKE_CXX_COMPILER_VERSION VERSION_LESS "10")
    message(WARNING "clang (< 10) not support concept")
    return()
  endif()
elseif ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
  if(CMAKE_CXX_COMPILER_VERSION VERSION_LESS "10")
    message(WARNING "gcc (< 10) not support concept")
    return()
  endif()
# using GCC
elseif ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "MSVC")
# using Visual Studio C++
  if(CMAKE_CXX_COMPILER_VERSION VERSION_LESS "19.23")
    message(WARNING "MSVC (< 1923 / 2019 16.3) not support concept")
    return()
  endif()
endif()

Ubpa_AddTarget(
  TEST
  MODE EXE
)
