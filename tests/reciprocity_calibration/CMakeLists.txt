#
# Copyright 2014-2015 Ettus Research LLC
# Copyright 2018 Ettus Research, a National Instruments Company
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

cmake_minimum_required(VERSION 3.5.1)
project(INIT_USRP CXX)

### Configure Compiler ########################################################
set(CMAKE_CXX_STANDARD 17)


### Set up build environment ##################################################
# Choose a static or shared-library build (shared is default, and static will
# probably need some special care!)
# Set this to ON in order to link a static build of UHD:
option(UHD_USE_STATIC_LIBS OFF)

# To add UHD as a dependency to this project, add a line such as this:
find_package(UHD 3.5.0 REQUIRED)

## load in pkg-config support
find_package(PkgConfig)
## use pkg-config to get hints for 0mq locations
pkg_check_modules(PC_ZeroMQ QUIET zmq)
## use the hint from above to find where 'zmq.hpp' is located
find_path(ZeroMQ_INCLUDE_DIR
        NAMES zmq.hpp
        PATHS ${PC_ZeroMQ_INCLUDE_DIRS}
        )

## use the hint from above to find the location of libzmq
find_library(ZeroMQ_LIBRARY
        NAMES zmq
        PATHS ${PC_ZeroMQ_LIBRARY_DIRS}
        )

# This example also requires Boost.
# Set components here, then include UHDBoost to do the actual finding
set(UHD_BOOST_REQUIRED_COMPONENTS
    program_options
    system
    thread
)
set(BOOST_MIN_VERSION 1.65)
include(UHDBoost)

# need these include and link directories for the build
include_directories(
    ${Boost_INCLUDE_DIRS}
    ${UHD_INCLUDE_DIRS}
)
link_directories(${Boost_LIBRARY_DIRS})

### Make the executable #######################################################
add_executable(init_usrp main.cpp)

set(CMAKE_BUILD_TYPE "Release")

## add the include directory to our compile directives
target_include_directories(init_usrp PUBLIC ${ZeroMQ_INCLUDE_DIR})

# Shared library case: All we need to do is link against the library, and
# anything else we need (in this case, some Boost libraries):
target_link_libraries(init_usrp ${UHD_LIBRARIES} ${Boost_LIBRARIES} ${ZeroMQ_LIBRARY})
