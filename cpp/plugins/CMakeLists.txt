#  ===========================================================================
#
#   Copyright 2012 xxxxxxxx - TODO
#   License: TODO
#  ___________________________________________________________________________

cmake_minimum_required (VERSION 2.6)
project (plugins)
set (CMAKE_VERBOSE_MAKEFILE on)

if (MSVC)
	set (CMAKE_CXX_FLAGS "/W3 /WL /wd4996 /vmg /GR /Gy /EHs /Zc:forScope,wchar_t /D_WIN32_WINNT=0x0501")
	set (CMAKE_CXX_FLAGS_DEBUG "/D_DEBUG /Zi /MTd /Od /GS /RTC1")
	set (CMAKE_CXX_FLAGS_RELEASE "/MT /Ox")
endif ()

if (CMAKE_COMPILER_IS_GNUCXX)
	set (CMAKE_CXX_FLAGS "-Wall -ansi -pedantic-errors -Wextra -Wno-long-long -Wabi")
endif ()

include_directories(.)
include_directories(..)
string(TOLOWER ${CMAKE_SYSTEM_NAME} PLAT)
set (OSINFO_SRC
	osinfo.cpp
	${PLAT}/osinfo_impl.cpp
	../utils/canreadfile.cpp
)

if ("${UNIX}")
	# osinfo requires launchProcess on Unices
	set (OSINFO_SRC ${OSINFO_SRC}
		../utils/linux/launchprocess.cpp
                ../devtools/logger.cpp
	)
endif ()

set (SYSTEMSTATUS_SRC
	systemstatus.cpp
	timestring.cpp
)

set (REMOVE_SRC
	remove.cpp
)

set (EXEC_SRC
	exec.cpp
	../utils/${PLAT}/launchprocess.cpp
        ../devtools/logger.cpp
)

add_executable(osinfo ${OSINFO_SRC})
add_executable(systemstatus ${SYSTEMSTATUS_SRC})
add_executable(remove ${REMOVE_SRC})
add_executable(exec ${EXEC_SRC})
