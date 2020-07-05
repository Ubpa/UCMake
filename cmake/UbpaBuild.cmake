message(STATUS "include UbpaBuild.cmake")

function(Ubpa_AddSubDirsRec path)
  file(GLOB_RECURSE children LIST_DIRECTORIES true ${CMAKE_CURRENT_SOURCE_DIR}/${path}/*)
  set(dirs "")
  list(APPEND children "${CMAKE_CURRENT_SOURCE_DIR}/${path}")
  foreach(item ${children})
    if(IS_DIRECTORY ${item} AND EXISTS "${item}/CMakeLists.txt")
      list(APPEND dirs ${item})
    endif()
  endforeach()
  foreach(dir ${dirs})
    add_subdirectory(${dir})
  endforeach()
endfunction()

function(Ubpa_GetTargetName rst targetPath)
  file(RELATIVE_PATH targetRelPath "${PROJECT_SOURCE_DIR}/src" "${targetPath}")
  string(REPLACE "/" "_" targetName "${PROJECT_NAME}_${targetRelPath}")
  set(${rst} ${targetName} PARENT_SCOPE)
endfunction()

function(_Ubpa_ExpandSources rst _sources)
  set(tmp_rst "")
  foreach(item ${${_sources}})
    if(IS_DIRECTORY ${item})
      file(GLOB_RECURSE itemSrcs
        # cmake
        ${item}/*.cmake
        
        # INTERFACEer files
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
        
        #${item}/*.hlsl
        #${item}/*.hlsli
        #${item}/*.fx
        #${item}/*.fxh
        
        # Qt files
        ${item}/*.qrc
        ${item}/*.ui
      )
      list(APPEND tmp_rst ${itemSrcs})
    else()
      if(NOT IS_ABSOLUTE "${item}")
		get_filename_component(item "${item}" ABSOLUTE)
      endif()
      list(APPEND tmp_rst ${item})
    endif()
  endforeach()
  set(${rst} ${tmp_rst} PARENT_SCOPE)
endfunction()

function(Ubpa_AddTarget)
  message(STATUS "----------")

  set(arglist "")
  # public
  list(APPEND arglist SOURCE_PUBLIC INC LIB DEFINE C_OPTION L_OPTION)
  # interface
  list(APPEND arglist SOURCE_INTERFACE INC_INTERFACE LIB_INTERFACE DEFINE_INTERFACE C_OPTION_INTERFACE L_OPTION_INTERFACE)
  # private
  list(APPEND arglist SOURCE INC_PRIVATE LIB_PRIVATE DEFINE_PRIVATE C_OPTION_PRIVATE L_OPTION_PRIVATE)
  cmake_parse_arguments("ARG" "TEST;QT;NOT_GROUP" "MODE;ADD_CURRENT_TO;RET_TARGET_NAME" "${arglist}" ${ARGN})
  
  # default
  if("${ARG_ADD_CURRENT_TO}" STREQUAL "")
    set(ARG_ADD_CURRENT_TO "PRIVATE")
  endif()
  
  # [option]
  # TEST
  # QT
  # NOT_GROUP
  # [value]
  # MODE: EXE / STATIC / SHARED / INTERFACE
  # ADD_CURRENT_TO: PUBLIC / INTERFACE / PRIVATE (default) / NONE
  # RET_TARGET_NAME
  # [list] : public, interface, private
  # SOURCE: dir(recursive), file, auto add currunt dir | target_sources
  # INC: dir                                           | target_include_directories
  # LIB: <lib-target>, *.lib                           | target_link_libraries
  # DEFINE: #define ...                                | target_compile_definitions
  # C_OPTION: compile options                          | target_compile_options
  # L_OPTION: link options                             | target_link_options
  
  # test
  if(ARG_TEST AND NOT "${Ubpa_BuildTest_${PROJECT_NAME}}")
    return()
  endif()
  
  if(ARG_QT)
    Ubpa_QtBegin()
  endif()
  
  # sources
  if("${ARG_ADD_CURRENT_TO}" STREQUAL "PUBLIC")
    list(APPEND ARG_SOURCE_PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
  elseif("${ARG_ADD_CURRENT_TO}" STREQUAL "INTERFACE")
    list(APPEND ARG_SOURCE_INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})
  elseif("${ARG_ADD_CURRENT_TO}" STREQUAL "PRIVATE")
    list(APPEND ARG_SOURCE ${CMAKE_CURRENT_SOURCE_DIR})
  elseif(NOT "${ARG_ADD_CURRENT_TO}" STREQUAL "NONE")
    message(FATAL_ERROR "ADD_CURRENT_TO [${ARG_ADD_CURRENT_TO}] is not supported")
  endif()
  _Ubpa_ExpandSources(sources_public ARG_SOURCE_PUBLIC)
  _Ubpa_ExpandSources(sources_interface ARG_SOURCE_INTERFACE)
  _Ubpa_ExpandSources(sources_private ARG_SOURCE)
  
  # group
  if(NOT NOT_GROUP)
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
  endif()
  
  # target folder
  file(RELATIVE_PATH targetRelPath "${PROJECT_SOURCE_DIR}/src" "${CMAKE_CURRENT_SOURCE_DIR}/..")
  set(targetFolder "${PROJECT_NAME}/${targetRelPath}")
  
  Ubpa_GetTargetName(targetName ${CMAKE_CURRENT_SOURCE_DIR})
  if(NOT "${ARG_RET_TARGET_NAME}" STREQUAL "")
    set(${ARG_RET_TARGET_NAME} ${targetName} PARENT_SCOPE)
  endif()
  
  # print
  message(STATUS "- name: ${targetName}")
  message(STATUS "- folder : ${targetFolder}")
  message(STATUS "- mode: ${ARG_MODE}")
  Ubpa_List_Print(STRS ${sources_private}
    TITLE  "- sources (private):"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${sources_interface}
    TITLE  "- sources interface:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${sources_public}
    TITLE  "- sources public:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_DEFINE}
    TITLE  "- define (public):"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_DEFINE_PRIVATE}
    TITLE  "- define interface:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_DEFINE_INTERFACE}
    TITLE  "- define private:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_LIB}
    TITLE  "- lib (public):"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_LIB_INTERFACE}
    TITLE  "- lib interface:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_LIB_PRIVATE}
    TITLE  "- lib private:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_INC}
    TITLE  "- inc (public):"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_INC_INTERFACE}
    TITLE  "- inc interface:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_INC_PRIVATE}
    TITLE  "- inc private:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_DEFINE}
    TITLE  "- define (public):"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_DEFINE_INTERFACE}
    TITLE  "- define interface:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_DEFINE_PRIVATE}
    TITLE  "- define private:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_C_OPTION}
    TITLE  "- compile option (public):"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_C_OPTION_INTERFACE}
    TITLE  "- compile option interface:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_C_OPTION_PRIVATE}
    TITLE  "- compile option private:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_L_OPTION}
    TITLE  "- link option (public):"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_L_OPTION_INTERFACE}
    TITLE  "- link option interface:"
    PREFIX "  * ")
  Ubpa_List_Print(STRS ${ARG_L_OPTION_PRIVATE}
    TITLE  "- link option private:"
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
  elseif("${ARG_MODE}" STREQUAL "INTERFACE")
    add_library(${targetName} INTERFACE)
    add_library("Ubpa::${targetName}" ALIAS ${targetName})
  else()
    message(FATAL_ERROR "mode [${ARG_MODE}] is not supported")
    return()
  endif()
  
  # folder
  if(NOT ${ARG_MODE} STREQUAL "INTERFACE")
    set_target_properties(${targetName} PROPERTIES FOLDER ${targetFolder})
  endif()
  
  # target sources
  if(NOT ${ARG_MODE} STREQUAL "INTERFACE")
    target_sources(${targetName}
	  PUBLIC ${sources_public}
	  INTERFACE ${sources_interface}
	  PRIVATE ${sources_private}
	)
  else()
    target_sources(${targetName} INTERFACE ${sources_public} ${sources_interface} ${sources_private})
  endif()
  
  # target define
  if(NOT ${ARG_MODE} STREQUAL "INTERFACE")
    target_compile_definitions(${targetName}
      PUBLIC ${ARG_DEFINE}
      INTERFACE ${ARG_DEFINE_INTERFACE}
      PRIVATE ${ARG_DEFINE_PRIVATE}
    )
  else()
    target_compile_definitions(${targetName} INTERFACE ${ARG_DEFINE} ${ARG_DEFINE_PRIVATE} ${ARG_DEFINE_INTERFACE})
  endif()
  
  # target lib
  if(NOT ${ARG_MODE} STREQUAL "INTERFACE")
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
    if(NOT ${ARG_MODE} STREQUAL "INTERFACE")
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
    if(NOT ${ARG_MODE} STREQUAL "INTERFACE")
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
  if(NOT ${ARG_MODE} STREQUAL "INTERFACE")
    target_compile_options(${targetName}
      PUBLIC ${ARG_C_OPTION}
      INTERFACE ${ARG_C_OPTION_INTERFACE}
      PRIVATE ${ARG_C_OPTION_PRIVATE}
    )
  else()
    target_compile_options(${targetName} INTERFACE ${ARG_C_OPTION} ${ARG_C_OPTION_PRIVATE} ${ARG_C_OPTION_INTERFACE})
  endif()
  
  # target link option
  if(NOT ${ARG_MODE} STREQUAL "INTERFACE")
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
  
  if(ARG_QT)
    Ubpa_QtEnd()
  endif()
  
  message(STATUS "----------")
endfunction()
