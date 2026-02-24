# ----------------------------------------------------------------------------
#
# Ubpa_InitGit()
# - find git [required]
#
# ----------------------------------------------------------------------------
#
# Ubpa_UpdateSubModule()
# - update submodule
#
# ----------------------------------------------------------------------------

message(STATUS "include UbpaGit.cmake")

macro(Ubpa_InitGit)
  message(STATUS "----------")
  find_package(Git REQUIRED)
  message(STATUS "GIT_FOUND: ${GIT_FOUND}")
  message(STATUS "GIT_EXECUTABLE: ${GIT_EXECUTABLE}")
  message(STATUS "GIT_VERSION_STRING: ${GIT_VERSION_STRING}")
endmacro()

function(Ubpa_UpdateSubModule)
  if(NOT GIT_FOUND)
    message(FATAL_ERROR "you should call Ubpa_InitGit() before calling Ubpa_UpdateSubModule()")
  endif()
  execute_process(
    COMMAND ${GIT_EXECUTABLE} submodule update --init
    WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
    RESULT_VARIABLE _result
  )
  if(NOT _result EQUAL 0)
    message(FATAL_ERROR "git submodule update --init failed with: ${_result}")
  endif()
endfunction()
