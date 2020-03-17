# ----------------------------------------------------------------------------
#
# Ubpa_AddDep(<dep-list>)
#
# ----------------------------------------------------------------------------
#
# Ubpa_Export([INC <inc>])
# - export some files
# - inc: default ON, install include/
#
# ----------------------------------------------------------------------------

message(STATUS "include UbpaPackage.cmake")

macro(Ubpa_AddDep name version)
	find_package(${name} ${version} EXACT QUIET)
	if(${UCMake_FOUND})
		message(STATUS "${dep}-${version} found")
	else()
		message(STATUS "${dep}-${version} not found, so fetch it ...")
		FetchContent_Declare(
		  ${name}
		  GIT_REPOSITORY "https://github.com/Ubpa/${dep}"
		  GIT_TAG "v${version}"
		)
		FetchContent_MakeAvailable(${name})
		message(STATUS "${dep}-${version} fetch done")
	endif()
endmacro()

macro(Ubpa_Export)
	cmake_parse_arguments("ARG" "" "INC" "" ${ARGN})
	
	set(package_name "${PROJECT_NAME}-${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}")
	message(STATUS "export ${package_name}")
	# install the configuration targets
	install(EXPORT "${PROJECT_NAME}Targets"
		FILE "${PROJECT_NAME}Targets.cmake"
		DESTINATION "lib/${package_name}/cmake"
	)
	
	include(CMakePackageConfigHelpers)
	
	# generate the config file that is includes the exports
	configure_package_config_file(${PROJECT_SOURCE_DIR}/config/Config.cmake.in
		"${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake"
		INSTALL_DESTINATION "lib/${package_name}/cmake"
		NO_SET_AND_CHECK_MACRO
		NO_CHECK_REQUIRED_COMPONENTS_MACRO
	)
	
	# generate the version file for the config file
	write_basic_package_version_file(
		"${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake"
		VERSION "${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}"
		COMPATIBILITY AnyNewerVersion
	)
	
	# install the configuration file
	install(FILES
		"${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake"
		"${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake"
		DESTINATION "lib/${package_name}/cmake"
	)

	# generate the export targets for the build tree
	# needs to be after the install(TARGETS ) command
	export(EXPORT "${PROJECT_NAME}Targets"
		NAMESPACE "${PROJECT_NAME}::"
		FILE "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Targets.cmake"
	)

	install(FILES
		"${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Targets.cmake"
		DESTINATION "lib/${package_name}/cmake"
	)
	
	if(NOT "${ARG_INC}" STREQUAL "OFF")
		install(DIRECTORY "include" DESTINATION ${CMAKE_INSTALL_PREFIX})
	endif()
endmacro()