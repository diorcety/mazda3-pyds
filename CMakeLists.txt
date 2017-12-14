cmake_minimum_required(VERSION 3.6)

include(ExternalProject)

set(PYTHON_VERSION "2.7.0" CACHE STRING "Python Version")
string(REPLACE "." ";" PYTHON_VERSION_LIST ${PYTHON_VERSION})
list(LENGTH PYTHON_VERSION_LIST PYTHON_VERSION_SZ)
if(PYTHON_VERSION_SZ GREATER 2)
    list(REMOVE_AT PYTHON_VERSION_LIST -1)
endif()
string(REPLACE ";" "." PYTHON_VERSION_C "${PYTHON_VERSION_LIST}")

# Set global vars
if(WIN32)
    if(MSYS)
        set(PKG_CONFIG_PATH ${CMAKE_INSTALL_PREFIX}/lib/pkgconfig;${PKG_CONFIG_PATH})
        set(LD_LIBRARY_PATH ${CMAKE_INSTALL_PREFIX}/lib;${LD_LIBRARY_PATH})
    else()
        string(REPLACE "/" "\\" PKG_CONFIG_PATH ${CMAKE_INSTALL_PREFIX}/lib/pkgconfig;${PKG_CONFIG_PATH})
        string(REPLACE "/" "\\" LD_LIBRARY_PATH ${CMAKE_INSTALL_PREFIX}/lib;${LD_LIBRARY_PATH})
    endif()
else()
    set(PKG_CONFIG_PATH ${CMAKE_INSTALL_PREFIX}/lib/pkgconfig:${PKG_CONFIG_PATH})
    set(LD_LIBRARY_PATH ${CMAKE_INSTALL_PREFIX}/lib:${LD_LIBRARY_PATH})
endif()
set(CMAKE_IGNORE_PATH)
foreach(p IN LISTS CMAKE_SYSTEM_PREFIX_PATH)
    if(NOT p STREQUAL CMAKE_INSTALL_PREFIX AND NOT p STREQUAL _CMAKE_INSTALL_DIR)
        list(APPEND CMAKE_IGNORE_PATH "${p}")
    endif()
endforeach(p)
string(REPLACE ";" "$<SEMICOLON>" CMAKE_IGNORE_PATH "${CMAKE_IGNORE_PATH}")

# Configure
if(CMAKE_SIZEOF_VOID_P EQUAL 8)
set(CMAKE_ISS_64  )
set(CMAKE_ISS_32 \;)
set(IS64 ON)
elseif(CMAKE_SIZEOF_VOID_P EQUAL 4)
set(CMAKE_ISS_64 \;)
set(CMAKE_ISS_32  )
set(IS64 OFF)
endif()

include(ProcessorCount)
ProcessorCount(N)

if(BUILTIN_PYTHON)
    set(PYTHON_SITE_PACKAGES /lib/python${PYTHON_VERSION_C}/site-packages)
    if(WIN32)
        string(REPLACE "/" "\\" PYTHON_EXECUTABLE ${CMAKE_INSTALL_PREFIX}/bin/python.exe)
    else()
        set(PYTHON_EXECUTABLE ${CMAKE_INSTALL_PREFIX}/bin/python)
    endif()
else()
    find_package(PythonInterp ${PYTHON_VERSION} REQUIRED)
    find_package(PythonLibs ${PYTHON_VERSION} REQUIRED)
    execute_process(COMMAND ${PYTHON_EXECUTABLE} -c "from distutils.sysconfig import get_python_lib; import sys; print('/'+get_python_lib(standard_lib=True, prefix='')+'/site-packages')" OUTPUT_VARIABLE PYTHON_SITE_PACKAGES OUTPUT_STRIP_TRAILING_WHITESPACE)
endif()
get_filename_component(PYTHON_EXECUTABLE_DIR ${PYTHON_EXECUTABLE} DIRECTORY)

if(WIN32)
    string(REPLACE "/" "\\" PYTHONPATH ${CMAKE_INSTALL_PREFIX}${PYTHON_SITE_PACKAGES})
    string(REPLACE "/" "\\" PYTHON_PREFIX ${CMAKE_INSTALL_PREFIX})
    string(REPLACE "/" "\\" INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX})
    set(PATH "${INSTALL_PREFIX}\\bin;${INSTALL_PREFIX}\\Scripts;${PATH};${PYTHON_EXECUTABLE_DIR};$ENV{PATH}")
    string(REPLACE ";" "^^" PATH "${PATH}")
else()
    set(PYTHONPATH ${CMAKE_INSTALL_PREFIX}${PYTHON_SITE_PACKAGES})
    set(PYTHON_PREFIX ${CMAKE_INSTALL_PREFIX})
    set(QMAKE_COMMAND ${CMAKE_INSTALL_PREFIX}/bin/qmake)
    set(INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX})
    set(PATH "${INSTALL_PREFIX}/bin:${PATH}:${PYTHON_EXECUTABLE_DIR}:$ENV{PATH}")
endif()

# Forward envs
set(ENV_COMMAND ${CMAKE_COMMAND} -E env "LD_LIBRARY_PATH=${LD_LIBRARY_PATH}" "PATH=${PATH}" "PYTHONPATH=${PYTHONPATH}" "PKG_CONFIG_PATH=${PKG_CONFIG_PATH}")
if(CMAKE_COMPILER_IS_GNUCC OR CMAKE_COMPILER_IS_GNUCXX OR (CMAKE_C_COMPILER_ID MATCHES "Clang") OR (CMAKE_CXX_COMPILER_ID MATCHES "Clang"))
    set(ENV_COMMAND ${ENV_COMMAND} "CC=${CMAKE_C_COMPILER}" "CXX=${CMAKE_CXX_COMPILER}")
endif()

function(cmake_build _project _path)
    set(options DEBUG OWN)
    set(oneValueArgs)
    set(multiValueArgs DEPENDS ENV ARGS)
    cmake_parse_arguments(cmake_build "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})
    set(cmake_build_PROJECT ${_project})
    set(cmake_build_PATH ${_path})
    set(cmake_build_BUILD_TYPE Release)
    if(cmake_build_DEBUG)
      if(WIN32)
        set(cmake_build_BUILD_TYPE RelWithDebInfo)
      else()
        set(cmake_build_BUILD_TYPE Debug)
      endif()
    endif()

    set(CFLAGS )
    set(CXXFLAGS )
    set(LDFLAGS )
    set(EXEFLAGS )

    set(ExternalProjectCMakeArgs
        "-DCMAKE_C_FLAGS=${CFLAGS} ${CMAKE_C_FLAGS}"
        "-DCMAKE_CXX_FLAGS=${CXXFLAGS} ${CMAKE_CXX_FLAGS}"
        "-DCMAKE_C_FLAGS_DEBUG=${CFLAGS} ${CMAKE_C_FLAGS_DEBUG}"
        "-DCMAKE_CXX_FLAGS_DEBUG=${CXXFLAGS} ${CMAKE_CXX_FLAGS_DEBUG}"
        "-DCMAKE_C_FLAGS_RELEASE=${CFLAGS} ${CMAKE_C_FLAGS_RELEASE}"
        "-DCMAKE_CXX_FLAGS_RELEASE=${CXXFLAGS} ${CMAKE_CXX_FLAGS_RELEASE}"
        "-DCMAKE_C_FLAGS_RELWITHDEBINFO=${CFLAGS} ${CMAKE_C_FLAGS_RELWITHDEBINFO}"
        "-DCMAKE_CXX_FLAGS_RELWITHDEBINFO=${CXXFLAGS} ${CMAKE_CXX_FLAGS_RELWITHDEBINFO}"
        "-DCMAKE_C_FLAGS_MINSIZEREL=${CFLAGS} ${CMAKE_C_FLAGS_MINSIZEREL}"
        "-DCMAKE_CXX_FLAGS_MINSIZEREL=${CXXFLAGS} ${CMAKE_CXX_FLAGS_MINSIZEREL}"
        "-DCMAKE_SHARED_LINKER_FLAGS=${LDFLAGS} ${CMAKE_SHARED_LINKER_FLAGS}"
        "-DCMAKE_STATIC_LINKER_FLAGS=${CMAKE_STATIC_LINKER_FLAGS}"
        "-DCMAKE_MODULE_LINKER_FLAGS=${LDFLAGS} ${CMAKE_MODULE_LINKER_FLAGS}"
        "-DCMAKE_EXE_LINKER_FLAGS=${EXEFLAGS} ${CMAKE_EXE_LINKER_FLAGS}"
        "-DCMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX}"
        "-DCMAKE_C_COMPILER=${CMAKE_C_COMPILER}"
        "-DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}"
        "-DCMAKE_SYSTEM_IGNORE_PATH=${CMAKE_IGNORE_PATH}"
        "-DBUILD_SHARED_LIBS:BOOL=ON"
        )

    ExternalProject_Add(${cmake_build_PROJECT}
        DOWNLOAD_COMMAND ""
        DOWNLOAD_DIR ${PROJECT_SOURCE_DIR}
        SOURCE_DIR ${PROJECT_SOURCE_DIR}/${cmake_build_PATH}
        BINARY_DIR ${PROJECT_BINARY_DIR}/${cmake_build_PROJECT}-build
        STAMP_DIR ${PROJECT_BINARY_DIR}/${cmake_build_PROJECT}-stamp
        TMP_DIR ${PROJECT_BINARY_DIR}/${cmake_build_PROJECT}-tmp
        INSTALL_DIR ${CMAKE_INSTALL_PREFIX}
        CMAKE_ARGS ${ExternalProjectCMakeArgs}
            "-DCMAKE_BUILD_TYPE=${cmake_build_BUILD_TYPE}"
            ${cmake_build_ARGS}
        LIST_SEPARATOR ^^
        CMAKE_COMMAND ${ENV_COMMAND} ${cmake_build_ENV} ${CMAKE_COMMAND}
        BUILD_COMMAND ${ENV_COMMAND} ${cmake_build_ENV} ${CMAKE_COMMAND} --build "."
        INSTALL_COMMAND ${ENV_COMMAND} ${cmake_build_ENV} ${CMAKE_COMMAND} --build "." --target install
        DEPENDS ${cmake_build_DEPENDS}
    )
endfunction(cmake_build)

function(python_build _project _path)
    set(options DEBUG DISTUTILS NOT_SDIST)
    set(oneValueArgs PREFIX)
    set(multiValueArgs DEPENDS ENV ARGS)
    cmake_parse_arguments(python_build "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})
    set(python_build_PROJECT ${_project})
    set(python_build_PATH ${_path})

    if(NOT python_build_PREFIX)
        set(python_build_PREFIX ${PYTHON_PREFIX})
    endif()

    if(BUILTIN_PYTHON)
        set(python_build_DEPENDS ${python_build_DEPENDS} python)
    endif()

    if(python_build_DISTUTILS)
        set(python_install_OPTS )
    else()
        set(python_install_OPTS --single-version-externally-managed --record ${PROJECT_BINARY_DIR}/${python_build_PROJECT}-tmp/record.txt)
    endif()

    set(python_pip_install_OPTS "--install-option=--prefix=${INSTALL_PREFIX}")

    if(python_build_NOT_SDIST)
        set(CONFIGURE_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/cmake/python_copy.cmake)
    else()
        set(CONFIGURE_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/cmake/python_sdist.cmake)
    endif()

    set(SETUP_PY setup.py)
    ExternalProject_Add(${python_build_PROJECT}
        DOWNLOAD_COMMAND ""
        BINARY_DIR ${PROJECT_BINARY_DIR}/${python_build_PROJECT}-build
        SOURCE_DIR ${PROJECT_SOURCE_DIR}/${python_build_PATH}
        STAMP_DIR ${PROJECT_BINARY_DIR}/${python_build_PROJECT}-stamp
        TMP_DIR ${PROJECT_BINARY_DIR}/${python_build_PROJECT}-tmp
        INSTALL_DIR ${CMAKE_INSTALL_PREFIX}
        LIST_SEPARATOR ^^
        CONFIGURE_COMMAND ${ENV_COMMAND} ${python_build_ENV} ${CMAKE_COMMAND} "-DPYTHON_EXECUTABLE=${PYTHON_EXECUTABLE}" "-DBUILD=${PROJECT_BINARY_DIR}/${python_build_PROJECT}-build" "-DSRC=${PROJECT_SOURCE_DIR}/${python_build_PATH}" "-DTMP=${PROJECT_BINARY_DIR}/${python_build_PROJECT}-tmp" -P ${CONFIGURE_SCRIPT}
        BUILD_COMMAND ${ENV_COMMAND} ${python_build_ENV} ${PYTHON_EXECUTABLE} ${SETUP_PY} build ${python_build_ARGS}
        INSTALL_COMMAND ${ENV_COMMAND} ${python_build_ENV} ${PYTHON_EXECUTABLE} ${SETUP_PY} install --prefix=${python_build_PREFIX} ${python_install_OPTS} ${python_build_ARGS} COMMAND ${ENV_COMMAND} ${python_build_ENV} ${PYTHON_EXECUTABLE} -m pip install --no-use-wheel --process-dependency-links ${python_pip_install_OPTS} .
        DEPENDS ${python_build_DEPENDS}
    )
endfunction(python_build)

function(pip_install _project _name)
    set(options DEBUG)
    set(oneValueArgs)
    set(multiValueArgs DEPENDS ENV ARGS)
    cmake_parse_arguments(pip_install "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})
    set(pip_install_PROJECT ${_project})
    set(pip_install_NAME ${_name})

    if(BUILTIN_PYTHON)
        set(pip_install_DEPENDS ${pip_install_DEPENDS} python)
    endif()

    set(pip_install_OPTS "--install-option=--prefix=${INSTALL_PREFIX}")

    set(BINARY_DIR ${PROJECT_BINARY_DIR}/${pip_install_PROJECT}-build)

    ExternalProject_Add(${pip_install_PROJECT}
        DOWNLOAD_COMMAND ""
        DOWNLOAD_DIR ${PROJECT_SOURCE_DIR}
        BINARY_DIR ${BINARY_DIR}
        STAMP_DIR ${PROJECT_BINARY_DIR}/${pip_install_PROJECT}-stamp
        TMP_DIR ${PROJECT_BINARY_DIR}/${pip_install_PROJECT}-tmp
        INSTALL_DIR ${CMAKE_INSTALL_PREFIX}
        LIST_SEPARATOR ^^
        CONFIGURE_COMMAND ""
        BUILD_COMMAND ""
        INSTALL_COMMAND ${ENV_COMMAND} ${pip_install_ENV} ${PYTHON_EXECUTABLE} -m pip install ${pip_install_OPTS} --no-use-wheel ${pip_install_ARGS} "--build=${BINARY_DIR}" ${pip_install_NAME}
        DEPENDS ${pip_install_DEPENDS}
    )
endfunction(pip_install)

pip_install(setuptools setuptools)

cmake_build(j2534 deps/j2534)
cmake_build(uds deps/uds DEPENDS j2534)

python_build(pyds . DEPENDS uds setuptools)