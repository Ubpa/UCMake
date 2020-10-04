cmake_minimum_required(VERSION 3.14 FATAL_ERROR)
project (Test VERSION 1.2.3.4)

set(A_A aa)
set(var A)
message(STATUS "${A_${var}}")

function(PrintVar var)
	message(STATUS "${var}: ${${var}}")
endfunction()

function(PrintValue value)
	message(STATUS "${value}")
endfunction()

PrintVar(PROJECT_SOURCE_DIR)
PrintVar(CMAKE_PROJECT_NAME)
PrintVar(PROJECT_VERSION)
PrintVar(PROJECT_VERSION_MAJOR)
PrintVar(PROJECT_VERSION_MINOR)
PrintVar(PROJECT_VERSION_PATCH)
PrintVar(PROJECT_VERSION_TWEAK)

set(Ubpa_bool TRUE CACHE BOOL "Ubpa bool")
set(Ubpa_string "a string" CACHE STRING "Ubpa string")
set(Ubpa_path ${PROJECT_SOURCE_DIR} CACHE PATH "Ubpa path")
set(Ubpa_filepath "${PROJECT_SOURCE_DIR}/CMakeLists.txt" CACHE FILEPATH "Ubpa filepath")

function(Parse)
  cmake_parse_arguments("ARG" # prefix
                        "TEST;INSTALL" # TRUE / FALSE
                        "MODE"
                        "NUMS" # list
                        ${ARGN})
  PrintVar(ARG_TEST)
  PrintVar(ARG_INSTALL)
  PrintVar(ARG_MODE)
  PrintVar(ARG_NUMS)
endfunction()

Parse(TEST
  MODE EXE
  NUMS 1 2 3 4)

set(i 0)
set(n 5)
while(i LESS n)
  PrintVar(i)
  math(EXPR i "${i} + 1")
endwhile()

set(nums 1 2 3 4 5)
foreach(num ${nums})
  PrintValue(${num})
endforeach()

set(list0 1 2 3 4 5) # list0: 1;2;3;4;5
set(list1 a b c d e) # list1: a;b;c;d;e
list(LENGTH list0 n)
set(i 0)
while(i LESS n)
  list(GET list0 ${i} v0)
  list(GET list1 ${i} v1)
  message(STATUS "${v0}, ${v1}")
  math(EXPR i "${i} + 1")
endwhile()

set(numletters 1 a 2 b 3 c)
list(LENGTH numletters n)
set(i 0)
while(i LESS n)
  list(SUBLIST numletters ${i} 2 numletter)
  list(GET numletter 0 num)
  list(GET numletter 1 letter)
  
  message(STATUS "num : ${num}, letter : ${letter}")
  
  math(EXPR i "${i} + 2")
endwhile()

string(REGEX
	MATCH
	"/(([^/]*)\\.(.*))$"
	out
	"xxx/ddd/aa.eee")

PrintVar(out)
PrintVar(CMAKE_MATCH_COUNT)
set(i 0)
while(i LESS_EQUAL CMAKE_MATCH_COUNT)
  PrintVar(CMAKE_MATCH_${i})
  math(EXPR i "${i} + 1")
endwhile()

string(REGEX
	MATCHALL
	"[_a-zA-Z][_a-zA-Z0-9]*"
	out
	"xxx/ddd/aa.eee")

PrintVar(out)
PrintVar(CMAKE_MATCH_COUNT)
set(i 0)
while(i LESS_EQUAL CMAKE_MATCH_COUNT)
  PrintVar(CMAKE_MATCH_${i})
  math(EXPR i "${i} + 1")
endwhile()

set(data 1 2 3 4 5 a 6 b 7)
list(FILTER data
  INCLUDE
  REGEX "[0-9]")
PrintVar(data)

set(data 1 2 3 4 5 a 6 b 7)
list(FILTER data
  EXCLUDE
  REGEX "[0-9]")
PrintVar(data)

set(specialStr "aaa;bbb")

# example 1
message(STATUS ${specialStr}) # aaabbb
message(STATUS "${specialStr}") # aaa;bbb

# example 2
function(PrintVar var)
    message(STATUS "${var}")
endfunction()

PrintVar(${specialStr})
PrintVar("${specialStr}")

file(READ "${CMAKE_SOURCE_DIR}/CMakeLists.txt" filestr)
# PrintValue("${filestr}")

file(REMOVE_RECURSE "testdir")

set(flag 0)
if(flag)
  message(STATUS "flag")
endif()

