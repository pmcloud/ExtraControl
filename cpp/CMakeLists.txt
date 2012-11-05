#  ===========================================================================
#
#   Copyright 2012 xxxxxxxx - TODO
#   License: TODO
#  ___________________________________________________________________________
#
#  Global policy:
#
#  Note that some of the third-party libraries have their own CMakeLists.txt;
#  we intentionally do not use them.
#
#  Note, also, that several libraries below have more source files than we
#  actually use.
#  ___________________________________________________________________________


cmake_minimum_required (VERSION 2.6)
project (serclient)
find_package (Threads)
set (CMAKE_VERBOSE_MAKEFILE on)

add_definitions (-DTIXML_USE_STL)
if (MSVC)
	set (CMAKE_CXX_FLAGS "/W3 /WL /wd4996 /vmg /GR /Gy /EHs /Zc:forScope,wchar_t /D_WIN32_WINNT=0x0501")
	set (CMAKE_CXX_FLAGS_DEBUG "/D_DEBUG /Zi /MTd /Od /GS /RTC1")
	set (CMAKE_CXX_FLAGS_RELEASE "/MT /Ox")
endif ()

if (CMAKE_COMPILER_IS_GNUCXX)
	set (CMAKE_CXX_FLAGS "-Wall -ansi -pedantic-errors -Wextra -Wno-long-long -Wabi")
endif ()

set (THREADS_SRC
	third-party/tinythreadpp/source/tinythread.cpp
	third-party/tinythreadpp/source/tinythread.h
)

set (OPTION_PARSING_SRC
	third-party/optparse/optparse.cpp
	third-party/optparse/optparse.h
)

set (LOGGING_SRC
	devtools/logger.cpp
	devtools/logger_file.cpp
)

set (CRC32_SRC
	third-party/crc32/crc.c
)
set_source_files_properties(${CRC32_SRC} PROPERTIES LANGUAGE CXX)

set (XML_SRC
	third-party/tinyxml/tinyxml.cpp
	third-party/tinyxml/tinyxmlparser.cpp
	third-party/tinyxml/tinyxmlerror.cpp
)

set (BASE64_SRC
	third-party/base64/base64.cpp	
)

include_directories(third-party/serial/include/)
add_subdirectory(third-party/serial/)

include_directories(.)
string(TOLOWER ${CMAKE_SYSTEM_NAME} BASE_PLATFORM)
set (SERCLIENT_SRC
	serialwatcher.cpp
	packet.cpp
	packetio.cpp
	module.cpp
	moduleio.cpp
	commandobserver.cpp
	commandrequest.cpp
	utils/${BASE_PLATFORM}/launchprocess.cpp
        tools.cpp
)

if (WIN32)
    set (SERCLIENT_SRC WindowsService.cpp ${SERCLIENT_SRC})
else()
    set (SERCLIENT_SRC main.cpp ${SERCLIENT_SRC})
endif()

add_executable(serclient ${THREADS_SRC} ${OPTION_PARSING_SRC} ${LOGGING_SRC} ${CRC32_SRC} ${XML_SRC} ${BASE64_SRC} ${SERIAL_PORT_SRC} ${SERCLIENT_SRC})
target_link_libraries(serclient ${CMAKE_THREAD_LIBS_INIT} serial)

if ("${UNIX}")
	target_link_libraries(serclient rt ${CMAKE_THREAD_LIBS_INIT})
elseif (WIN32)
	target_link_libraries(serclient ws2_32 advapi32 winmm)
endif()

# Add module subdirectories
#
#add_subdirectory(custom/)
#add_subdirectory(internals/)
add_subdirectory(plugins/)
