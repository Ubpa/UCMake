message(STATUS "include UbpaDownload.cmake")

function(Ubpa_IsNeedDownload rst filename hash_type hash)
  if(EXISTS ${filename})
    file(${hash_type} ${filename} origFileHash)
    string(TOLOWER ${hash} lhash)
    string(TOLOWER ${origFileHash} lOrigFileHash)
    if(${lhash} STREQUAL ${lOrigFileHash})
      set(${rst} "FALSE" PARENT_SCOPE)
      return()
    endif()
  endif()
  
  set(${rst} "TRUE" PARENT_SCOPE)
endfunction()

function(Ubpa_DownloadFile url filename hash_type hash)
  Ubpa_IsNeedDownload(need ${filename} ${hash_type} ${hash})
  if(NOT need)
    message(STATUS "Found File: ${filename}")
    return()
  endif()
  string(REGEX MATCH ".*/" dir ${filename})
  file(MAKE_DIRECTORY ${dir})
  message(STATUS "Download File")
  message(STATUS "- url      : ${url}")
  message(STATUS "- file name: ${filename}")
  file(DOWNLOAD ${url} ${filename}
    TIMEOUT 120
    SHOW_PROGRESS
    EXPECTED_HASH ${hash_type}=${hash}
    TLS_VERIFY ON
    STATUS _download_status)
  list(GET _download_status 0 _download_code)
  list(GET _download_status 1 _download_msg)
  if(NOT _download_code EQUAL 0)
    message(FATAL_ERROR "Download failed (${_download_code}): ${_download_msg}\n  url: ${url}")
  endif()
endfunction()

function(Ubpa_DownloadZip url zipname hash_type hash)
  Ubpa_DownloadZip_Pro(${url} ${zipname} ${CMAKE_CURRENT_SOURCE_DIR} ${hash_type} ${hash})
endfunction()

function(Ubpa_DownloadZip_Pro url zipname dir hash_type hash)
  set(filename "${CMAKE_BINARY_DIR}/${PROJECT_NAME}/${zipname}")
  Ubpa_IsNeedDownload(need ${filename} ${hash_type} ${hash})
  if(NOT need)
    message(STATUS "Found File: ${filename}")
    return()
  endif()
  Ubpa_DownloadFile(${url} ${filename} ${hash_type} ${hash})
  file(MAKE_DIRECTORY ${dir})
  execute_process(
    COMMAND ${CMAKE_COMMAND} -E tar -xf ${filename}
    WORKING_DIRECTORY ${dir}
    RESULT_VARIABLE _extract_result)
  if(NOT _extract_result EQUAL 0)
    message(FATAL_ERROR "Extract failed (${_extract_result}): ${filename}")
  endif()
endfunction()

function(Ubpa_DownloadTestFile url filename hash_type hash)
  if(NOT ${Ubpa_BuildTest_${PROJECT_NAME}})
    return()
  endif()
  Ubpa_DownloadFile(${url} ${filename} ${hash_type} ${hash})
endfunction()

function(Ubpa_DownloadTestZip url zipname hash_type hash)
  if(NOT ${Ubpa_BuildTest_${PROJECT_NAME}})
    return()
  endif()
  Ubpa_DownloadZip(${url} ${zipname} ${hash_type} ${hash})
endfunction()

function(Ubpa_DownloadTestZip_Pro url zipname dir hash_type hash)
  if(NOT ${Ubpa_BuildTest_${PROJECT_NAME}})
    return()
  endif()
  Ubpa_DownloadZip_Pro(${url} ${zipname} ${dir} ${hash_type} ${hash})
endfunction()
