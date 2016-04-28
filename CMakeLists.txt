cmake_minimum_required(VERSION 3.0)

include(ExternalProject)

set(PYDS_INSTALL_PREFIX "${CMAKE_CURRENT_BINARY_DIR}/prefix")
set(PYDS_DEFAULT_ARGS
        "-DCMAKE_PREFIX_PATH:PATH=${PYDS_INSTALL_PREFIX};${CMAKE_PREFIX_PATH}"
        "-DCMAKE_INSTALL_PREFIX:PATH=${PYDS_INSTALL_PREFIX}")

set(j2534_source "${CMAKE_CURRENT_SOURCE_DIR}/deps/j2534")
set(j2534_build "${CMAKE_CURRENT_BINARY_DIR}/deps/j2534")
ExternalProject_Add(j2534 SOURCE_DIR ${j2534_source} BINARY_DIR ${j2534_build} CMAKE_CACHE_ARGS ${PYDS_DEFAULT_ARGS})

set(uds_source "${CMAKE_CURRENT_SOURCE_DIR}/deps/uds")
set(uds_build "${CMAKE_CURRENT_BINARY_DIR}/deps/uds")
ExternalProject_Add(uds SOURCE_DIR ${uds_source} BINARY_DIR ${uds_build} CMAKE_CACHE_ARGS ${PYDS_DEFAULT_ARGS} DEPENDS j2534)