# ----------------------------------------------------------------------------
#
# Ubpa_List_Print(STRS <string-list> [TITLE <title>] [PREFIX <prefix>])
# - print:
#          <title>
#          <prefix>item0
#          ...
#          <prefix>itemN
#
# ----------------------------------------------------------------------------
#
# Upba_List_ChangeSeperator(RST <result-name> SEPERATOR <seperator> LIST <list>)
# - seperator '/' : "a;b;c" -> "a/b/c"
#
# ----------------------------------------------------------------------------
#
# Ubpa_GetDirName(<result-name>)
# - get current directory name
#
# ----------------------------------------------------------------------------
#
# Ubpa_Path_Back(<rst> <path> <times>
#
# ----------------------------------------------------------------------------

message(STATUS "include UbpaBasic.cmake")

function(Ubpa_List_Print)
	cmake_parse_arguments("ARG" "" "TITLE;PREFIX" "STRS" ${ARGN})
	if(NOT ${ARG_TITLE} STREQUAL "")
		message(STATUS ${ARG_TITLE})
	endif()
	foreach(str ${ARG_STRS})
		message(STATUS "${ARG_PREFIX}${str}")
	endforeach()
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

function(Ubpa_GetDirName dirName)
	string(REGEX MATCH "([^/]*)$" TMP ${CMAKE_CURRENT_SOURCE_DIR})
	set(${dirName} ${TMP} PARENT_SCOPE)
endfunction()

function(Ubpa_Path_Back rst path times)
	math(EXPR stop "${times}-1")
	set(curPath ${path})
	foreach(index RANGE ${stop})
		string(REGEX MATCH "(.*)/" _ ${curPath})
		set(curPath ${CMAKE_MATCH_1})
	endforeach()
	set(${rst} ${curPath} PARENT_SCOPE)
endfunction()
