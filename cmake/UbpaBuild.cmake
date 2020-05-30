message(STATUS "include UbpaBuild.cmake")

function(Ubpa_AddSubDirsRec path)
  message(STATUS "----------")
  file(GLOB_RECURSE children LIST_DIRECTORIES true ${CMAKE_CURRENT_SOURCE_DIR}/${path}/*)
  set(dirs "")
  list(APPEND children "${CMAKE_CURRENT_SOURCE_DIR}/${path}")
  foreach(item ${children})
    if(IS_DIRECTORY ${item} AND EXISTS "${item}/CMakeLists.txt")
      list(APPEND dirs ${item})
    endif()
  endforeach()
  Ubpa_List_Print(TITLE "directories:" PREFIX "- " STRS ${dirs})
  foreach(dir ${dirs})
    add_subdirectory(${dir})
  endforeach()
endfunction()

function(Ubpa_GetTargetName rst targetPath)
  file(RELATIVE_PATH targetRelPath "${PROJECT_SOURCE_DIR}/src" "${targetPath}")
  string(REPLACE "/" "_" targetName "${PROJECT_NAME}_${targetRelPath}")
  set(${rst} ${targetName} PARENT_SCOPE)
endfunction()

function(Ubpa_AddTarget)
  set(arglist "")
  list(APPEND arglist SOURCE INC LIB DEFINE C_OPTION L_OPTION)
  list(APPEND arglist INC_INTERFACE LIB_INTERFACE DEFINE_INTERFACE C_OPTION_INTERFACE L_OPTION_INTERFACE)
  list(APPEND arglist INC_PRIVATE LIB_PRIVATE DEFINE_PRIVATE C_OPTION_PRIVATE L_OPTION_PRIVATE)
  cmake_parse_arguments("ARG" "TEST" "MODE;RET_TARGET_NAME" "${arglist}" ${ARGN})
  
  # [option]
  # TEST
  # [value]
  # MODE: EXE / STATIC / SHARED / HEAD
  # RET_TARGET_NAME
  # [list] : public, interface, private
  # SOURCE: dir(recursive), file, auto add currunt dir | target_sources
  # INC: dir                                           | target_include_directories
  # LIB: <lib-target>, *.lib                           | target_link_libraries
  # DEFINE: #define ...                                | target_compile_definitions
  # C_OPTION: compile options                          | target_compile_options
  # L_OPTION: link options                             | target_link_options
  
  # test
  if(ARG_TEST AND NOT "${Ubpa_Build${PROJECT_NAME}Test}")
    return()
  endif()
  
  # sources
  set(sources "")
  list(APPEND ARG_SOURCE ${CMAKE_CURRENT_SOURCE_DIR})
  foreach(item ${ARG_SOURCE})
    if(IS_DIRECTORY ${item})
      file(GLOB_RECURSE itemSrcs
        # cmake
        ${item}/*.cmake
        
        # header files
        ${item}/*.h
        ${item}/*.hpp
        ${item}/*.hxx
        ${item}/*.inl
        
        # source files
        ${item}/*.c
        
        ${item}/*.cc
        ${item}/*.cpp
        ${item}/*.cxx
        
        # shader files
        ${item}/*.vert # glsl vertex shader
        ${item}/*.tesc # glsl tessellation control shader
        ${item}/*.tese # glsl tessellation evaluation shader
        ${item}/*.geom # glsl geometry shader
        ${item}/*.frag # glsl fragment shader
        ${item}/*.comp # glsl compute shader
        
        ${item}/*.hlsl
        
        # Qt files
        ${item}/*.qrc
        ${item}/*.ui
      )
      list(APPEND sources ${itemSrcs})
    else()
      if(NOT IS_ABSOLUTE ${item})
        set(item "${CMAKE_CURRENT_LIST_DIR}/${item}")
      endif()
      list(APPEND sources ${item})
    endif()
  endforeach()
  
  # group
  foreach(source ${sources})
    get_filename_component(dir ${source} DIRECTORY)
    if(${CMAKE_CURRENT_SOURCE_DIR} STREQUAL ${dir})
      source_group("src" FILES ${source})
    else()
      file(RELATIVE_PATH rdir ${PROJECT_SOURCE_DIR} ${dir})
      if(MSVC)
        string(REPLACE "/" "\\" rdir_MSVC ${rdir})
        set(rdir "${rdir_MSVC}")
      endif()
      source_group(${rdir} FILES ${source})
    endif()
  endforeach()
  
  # target folder
  file(RELATIVE_PATH targetRelPath "${PROJECT_SOURCE_DIR}/src" "${CMAKE_CURRENT_SOURCE_DIR}/..")
  set(targetFolder "${PROJECT_NAME}/${targetRelPath}")
  
  Ubpa_GetTargetName(targetName ${CMAKE_CURRENT_SOURCE_DIR})
  if(NOT  "${ARG_RET_TARGET_NAME}" STREQUAL "")
    set(${ARG_RET_TARGET_NAME} ${targetName} PARENT_SCOPE)
  endif()
  
  # print
  message(STATUS "----------")
  message(STATUS "- name: ${targetName}")
  message(STATUS "- folder : ${targetFolder}")
  message(STATUS "- mode: ${ARG_MODE}")
  Ubpa_List_Print(STRS ${ARG_DEFINE}
    TITLE  "- define:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_DEFINE_PRIVATE}
    TITLE  "- define private:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${sources}
    TITLE  "- sources:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_LIB}
    TITLE  "- lib:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_LIB_INTERFACE}
    TITLE  "- lib interface:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_LIB_PRIVATE}
    TITLE  "- lib private:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_INC}
    TITLE  "- inc:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_INC_INTERFACE}
    TITLE  "- inc interface:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_INC_PRIVATE}
    TITLE  "- inc private:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_DEFINE}
    TITLE  "- define:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_DEFINE_INTERFACE}
    TITLE  "- define interface:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_DEFINE_PRIVATE}
    TITLE  "- define private:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_C_OPTION}
    TITLE  "- compile opt:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_C_OPTION_INTERFACE}
    TITLE  "- compile opt interface:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_C_OPTION_PRIVATE}
    TITLE  "- compile opt private:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_L_OPTION}
    TITLE  "- link opt:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_L_OPTION_INTERFACE}
    TITLE  "- link opt interface:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_L_OPTION_PRIVATE}
    TITLE  "- link opt private:"
    PREFIX "  * ")
  
  Ubpa_PackageName(package_name)
  
  # add target
  if("${ARG_MODE}" STREQUAL "EXE")
    add_executable(${targetName})
    add_executable("Ubpa::${targetName}" ALIAS ${targetName})
    if(MSVC)
      set_target_properties(${targetName} PROPERTIES VS_DEBUGGER_WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}/bin")
    endif()
    set_target_properties(${targetName} PROPERTIES DEBUG_POSTFIX ${CMAKE_DEBUG_POSTFIX})
  elseif("${ARG_MODE}" STREQUAL "STATIC")
    add_library(${targetName} STATIC)
	add_library("Ubpa::${targetName}" ALIAS ${targetName})
  elseif("${ARG_MODE}" STREQUAL "SHARED")
    add_library(${targetName} SHARED)
	add_library("Ubpa::${targetName}" ALIAS ${targetName})
  elseif("${ARG_MODE}" STREQUAL "HEAD")
    add_library(${targetName} INTERFACE)
	add_library("Ubpa::${targetName}" ALIAS ${targetName})
  else()
    message(FATAL_ERROR "mode [${ARG_MODE}] is not supported")
    return()
  endif()
  
  # folder
  if(NOT ${ARG_MODE} STREQUAL "HEAD")
    set_target_properties(${targetName} PROPERTIES FOLDER ${targetFolder})
  endif()
  
  # target source
  if(NOT ${ARG_MODE} STREQUAL "HEAD")
    target_sources(${targetName} PRIVATE ${sources})
  else()
    target_sources(${targetName} INTERFACE ${sources})
  endif()
  
  # target define
  if(NOT ${ARG_MODE} STREQUAL "HEAD")
    target_compile_definitions(${targetName}
      PUBLIC ${ARG_DEFINE}
	  INTERFACE ${ARG_DEFINE_INTERFACE}
      PRIVATE ${ARG_DEFINE_PRIVATE}
    )
  else()
    target_compile_definitions(${targetName} INTERFACE ${ARG_DEFINE} ${ARG_DEFINE_PRIVATE} ${ARG_DEFINE_INTERFACE})
  endif()
  
  # target lib
  if(NOT ${ARG_MODE} STREQUAL "HEAD")
    target_link_libraries(${targetName}
      PUBLIC ${ARG_LIB}
	  INTERFACE ${ARG_LIB_INTERFACE}
      PRIVATE ${ARG_LIB_PRIVATE}
    )
  else()
    target_link_libraries(${targetName} INTERFACE ${ARG_LIB} ${ARG_LIB_PRIVATE} ${ARG_LIB_INTERFACE})
  endif()
  
  # target inc
  foreach(inc ${ARG_INC})
    if(NOT ${ARG_MODE} STREQUAL "HEAD")
      target_include_directories(${targetName} PUBLIC
        $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/${inc}>
        $<INSTALL_INTERFACE:${package_name}/${inc}>
      )
    else()
      target_include_directories(${targetName} INTERFACE
        $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/${inc}>
        $<INSTALL_INTERFACE:${package_name}/${inc}>
      )
    endif()
  endforeach()
  foreach(inc ${ARG_INC_PRIVATE})
    if(NOT ${ARG_MODE} STREQUAL "HEAD")
      target_include_directories(${targetName} PRIVATE
        $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/${inc}>
        $<INSTALL_INTERFACE:${package_name}/${inc}>
      )
    else()
      target_include_directories(${targetName} INTERFACE
        $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/${inc}>
        $<INSTALL_INTERFACE:${package_name}/${inc}>
      )
    endif()
  endforeach()
  foreach(inc ${ARG_INC_INTERFACE})
    target_include_directories(${targetName} INTERFACE
      $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/${inc}>
      $<INSTALL_INTERFACE:${package_name}/${inc}>
    )
  endforeach()
  
  # target compile option
  if(NOT ${ARG_MODE} STREQUAL "HEAD")
    target_compile_options(${targetName}
      PUBLIC ${ARG_C_OPTION}
      INTERFACE ${ARG_C_OPTION_INTERFACE}
      PRIVATE ${ARG_C_OPTION_PRIVATE}
    )
  else()
    target_compile_options(${targetName} INTERFACE ${ARG_C_OPTION} ${ARG_C_OPTION_PRIVATE} ${ARG_C_OPTION_INTERFACE})
  endif()
  
  # target link option
  if(NOT ${ARG_MODE} STREQUAL "HEAD")
    target_link_options(${targetName}
      PUBLIC ${ARG_L_OPTION}
      INTERFACE ${ARG_L_OPTION_INTERFACE}
      PRIVATE ${ARG_L_OPTION_PRIVATE}
    )
  else()
    target_compile_options(${targetName} INTERFACE ${ARG_L_OPTION} ${ARG_L_OPTION_PRIVATE} ${ARG_L_OPTION_INTERFACE})
  endif()
  
  if(NOT ARG_TEST)
    install(TARGETS ${targetName}
      EXPORT "${PROJECT_NAME}Targets"
      RUNTIME DESTINATION "bin"
      ARCHIVE DESTINATION "${package_name}/lib"
      LIBRARY DESTINATION "${package_name}/lib"
    )
  endif()
endfunction()
