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
	message(STATUS "find package: ${name}-${version}")
	find_package(${name} ${version} EXACT QUIET)
	if(${${name}_FOUND})
		message(STATUS "${name}-${version} found")
	else()
		set(_address "https://github.com/Ubpa/${name}")
		message(STATUS "${name}-${version} not found, so fetch it ...\n"
		"fetch: ${_address} with tag v${version}")
		FetchContent_Declare(
		  ${name}
		  GIT_REPOSITORY "https://github.com/Ubpa/${name}"
		  GIT_TAG "v${version}"
		)
		message(STATUS "${name}-${version} fetch done, building ...")
		FetchContent_MakeAvailable(${name})
		message(STATUS "${name}-${version} build done")
	endif()
endmacro()

macro(Ubpa_Export)
	cmake_parse_arguments("ARG" "" "INC;TARGET" "" ${ARGN})
	
	set(package_name "${PROJECT_NAME}-${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}")
	message(STATUS "export ${package_name}")
	
	if(NOT "${ARG_TARGET}" STREQUAL "OFF")
		# generate the export targets for the build tree
		# needs to be after the install(TARGETS ) command
		export(EXPORT "${PROJECT_NAME}Targets"
			NAMESPACE "Ubpa::"
		#	#FILE "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Targets.cmake"
		)
		
		# install the configuration targets
		install(EXPORT "${PROJECT_NAME}Targets"
			FILE "${PROJECT_NAME}Targets.cmake"
			NAMESPACE "Ubpa::"
			DESTINATION "${package_name}/cmake"
		)
	endif()
	
	include(CMakePackageConfigHelpers)
	
	# generate the config file that is includes the exports
	configure_package_config_file(${PROJECT_SOURCE_DIR}/config/Config.cmake.in
		"${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake"
		INSTALL_DESTINATION "${package_name}/cmake"
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
		DESTINATION "${package_name}/cmake"
	)
	
	if(NOT "${ARG_INC}" STREQUAL "OFF")
		install(DIRECTORY "include" DESTINATION ${package_name})
	endif()
endmacro()
