# [ Interface ]
#
# Ubpa_GetDirName(<result-name>)
# - get current directory name
#
# Ubpa_AddSubDirs()
# - add all subdirectories
#
# Ubpa_AddCurPathSrcs(<result-name>)
# - add currunt path sources : *.h, *.hpp, *.inl, *.cpp, *.cxx
#
# Upba_List_ChangeSeperator(RST <result-name> SEPERATOR <seperator> LIST <list>)
# - seperator '/' : "a;b;c" -> "a/b/c"
#
# Ubpa_AddTarget_GDR(MODE <mode> NAME <name> SOURCES <sources-list>
#     LIBS_GENERAL <libsG-list> LIBS_DEBUG <libsD-list> LIBS_RELEASE <libsR-list>)
# - mode       : EXE / LIB / DLL
# - libsG-list : auto add DEBUG_POSTFIX for debug mode
# - auto set folder, target prefix and some properties
#
# Ubpa_AddTarget(MODE <mode> NAME <name> SOURCES <sources-list> LIBS <libs-list>)
# - call Ubpa_AddTarget(MODE <mode> NAME <name> SOURCES <sources-list>
#            LIBS_GENERAL <libsG-list> LIBS_DEBUG "" LIBS_RELEASE "")
#
# QtBegin()
# - call it before adding Qt target
#
# QtEnd()
# - call it after adding Qt target

function(Ubpa_GetDirName dirName)
	string(REGEX MATCH "([^/]*)$" TMP ${CMAKE_CURRENT_SOURCE_DIR})
	set(${dirName} ${TMP} PARENT_SCOPE)
endfunction()

function(Ubpa_AddSubDirs)
	file(GLOB children RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/*)
	set(dirList "")
	foreach(child ${children})
		if(IS_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/${child})
			list(APPEND dirList ${child})
		endif()
	endforeach()
	Ubpa_GetDirName(dirName)
	list(APPEND Ubpa_Folders ${dirName})
	foreach(dir ${dirList})
		add_subdirectory(${dir})
	endforeach()
endfunction()

function(Ubpa_AddCurPathSrcs rst)
	file(GLOB sources
		"${CMAKE_CURRENT_SOURCE_DIR}/*.h"
		"${CMAKE_CURRENT_SOURCE_DIR}/*.hpp"
		"${CMAKE_CURRENT_SOURCE_DIR}/*.inl"
		"${CMAKE_CURRENT_SOURCE_DIR}/*.cpp"
		"${CMAKE_CURRENT_SOURCE_DIR}/*.cxx"
		"${CMAKE_CURRENT_SOURCE_DIR}/*.cc"
	)
	set(${rst} ${sources} PARENT_SCOPE)
endfunction()

function(Upba_List_ChangeSeperator)
    # https://www.cnblogs.com/cynchanpin/p/7354864.html
	# https://blog.csdn.net/fuyajun01/article/details/9036443
	cmake_parse_arguments("ARG" "" "RST;SEPERATOR" "LIST" ${ARGN})
	list(LENGTH ARG_LIST listLen)
	if($<BOOL:${listLen}>)
		set(${ARG_RST} "" PARENT_SCOPE)
	else()
		set(rst "")
		list(POP_BACK ARG_LIST back)
		foreach(item ${ARG_LIST})
			set(rst "${rst}${item}${ARG_SEPERATOR}")
		endforeach()
		set(${ARG_RST} "${rst}${back}" PARENT_SCOPE)
	endif()
endfunction()

function(Ubpa_AddTarget_GDR)
    # https://www.cnblogs.com/cynchanpin/p/7354864.html
	# https://blog.csdn.net/fuyajun01/article/details/9036443
	cmake_parse_arguments("ARG" "" "MODE;NAME" "SOURCES;LIBS_GENERAL;LIBS_DEBUG;LIBS_RELEASE" ${ARGN})
	Upba_List_ChangeSeperator(RST folderPrefix SEPERATOR "_" LIST ${Ubpa_Folders})
	Upba_List_ChangeSeperator(RST folderPath SEPERATOR "/" LIST ${Ubpa_Folders})
	set(targetName "${PROJECT_NAME}_${folderPrefix}_${ARG_NAME}")
	
	message(STATUS "----------")
	
	message(STATUS "- name: ${targetName}")
	message(STATUS "- folder : ${folderPath}")
	message(STATUS "- mode: ${ARG_MODE}")
	message(STATUS "- sources:")
	foreach(source ${ARG_SOURCES})
	    message(STATUS "    ${source}")
	endforeach()
	message(STATUS "- libs:")
	message(STATUS "  - general:")
	foreach(lib ${ARG_LIBS_GENERAL})
	    message(STATUS "      ${lib}")
	endforeach()
	message(STATUS "  - debug:")
	foreach(lib ${ARG_LIBS_DEBUG})
	    message(STATUS "      ${lib}")
	endforeach()
	message(STATUS "  - release:")
	foreach(lib ${ARG_LIBS_RELEASE})
	    message(STATUS "      ${lib}")
	endforeach()
	
	if(sourcesNum EQUAL 0)
		message(WARNING "Target [${targetName}] has no source")
		return()
	endif()
	
	# add target
	if(${ARG_MODE} STREQUAL "EXE")
		add_executable(${targetName} ${ARG_SOURCES})
		if(MSVC)
			set_target_properties(${targetName} PROPERTIES VS_DEBUGGER_WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}/bin")
		endif()
		set_target_properties(${targetName} PROPERTIES DEBUG_POSTFIX ${CMAKE_DEBUG_POSTFIX})
	elseif(${ARG_MODE} STREQUAL "LIB")
		add_library(${targetName} ${ARG_SOURCES})
		# 无需手动设置
		#set_target_properties(${targetName} PROPERTIES DEBUG_POSTFIX ${CMAKE_DEBUG_POSTFIX})
	elseif(${ARG_MODE} STREQUAL "DLL")
		add_library(${targetName} SHARED ${ARG_SOURCES})
	else()
		message(FATAL_ERROR "mode [${ARG_MODE}] is not supported")
		return()
	endif()
	
	# folder
	set_target_properties(${targetName} PROPERTIES FOLDER ${folderPath})
	
	foreach(lib ${ARG_LIBS_GENERAL})
		target_link_libraries(${targetName} general ${lib})
	endforeach()
	foreach(lib ${ARG_LIBS_DEBUG})
		target_link_libraries(${targetName} debug ${lib})
	endforeach()
	foreach(lib ${ARG_LIBS_RELEASE})
		target_link_libraries(${targetName} optimized ${lib})
	endforeach()
	install(TARGETS ${targetName}
		RUNTIME DESTINATION "bin"
		ARCHIVE DESTINATION "lib"
		LIBRARY DESTINATION "lib")
		
	message(STATUS "----------")
endfunction()

function(Ubpa_AddTarget)
    # https://www.cnblogs.com/cynchanpin/p/7354864.html
	# https://blog.csdn.net/fuyajun01/article/details/9036443
	cmake_parse_arguments("ARG" "" "MODE;NAME" "SOURCES;LIBS" ${ARGN})
	Ubpa_AddTarget_GDR(MODE ${ARG_MODE} NAME ${ARG_NAME} SOURCES ${ARG_SOURCES} LIBS_GENERAL ${ARG_LIBS} LIBS_DEBUG "" LIBS_RELEASE "")
endfunction()

function(Ubpa_QtBegin)
	set(CMAKE_AUTOMOC ON PARENT_SCOPE)
	set(CMAKE_AUTOUIC ON PARENT_SCOPE)
	set(CMAKE_AUTORCC ON PARENT_SCOPE)
endfunction()

function(Ubpa_QtEnd)
	set(CMAKE_AUTOMOC OFF PARENT_SCOPE)
	set(CMAKE_AUTOUIC OFF PARENT_SCOPE)
	set(CMAKE_AUTORCC OFF PARENT_SCOPE)
endfunction()
