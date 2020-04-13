message(STATUS "include UbpaDownload.cmake")

function(Ubpa_DownloadFile url filename hash_type hash)
	if(EXISTS ${filename})
		file(${hash_type} ${filename} origFileHash)
		string(TOLOWER ${hash} lhash)
		string(TOLOWER ${origFileHash} lOrigFileHash)
		if(${lhash} STREQUAL ${lOrigFileHash})
			message(STATUS "Found File: ${filename} with same ${hash_type}")
			return()
		else()
			message(STATUS "Found File: ${filename} with different ${hash_type}")
		endif()
	endif()
	message(STATUS "Download File: ${filename}")
	file(DOWNLOAD ${url} ${filename}
		TIMEOUT 60  # seconds
		EXPECTED_HASH ${hash_type}=${hash}
		TLS_VERIFY ON)
endfunction()

function(Ubpa_DownloadTestFile url filename hash_type hash)
	if("${Ubpa_BuildTest}" STREQUAL "OFF" OR "${Ubpa_BuildTest}" STREQUAL "")
		return()
	endif()
	Ubpa_DownloadFile(${url} ${filename} ${hash_type} ${hash})
endfunction()
