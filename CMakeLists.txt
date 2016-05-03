CMAKE_MINIMUM_REQUIRED(VERSION 3.0)

INCLUDE(ExternalProject)

SET(PYDS_INSTALL_PREFIX ${CMAKE_SOURCE_DIR}/output)

FIND_PACKAGE(PythonInterp REQUIRED)
if (PYTHONINTERP_FOUND)
    EXECUTE_PROCESS(COMMAND ${PYTHON_EXECUTABLE} -c "from distutils.sysconfig import get_python_lib; import sys; print get_python_lib().replace(sys.prefix, '').replace('dist-', 'site-')" OUTPUT_VARIABLE PYTHON_SITE_PACKAGES OUTPUT_STRIP_TRAILING_WHITESPACE)
    IF (WIN32)
        STRING(REGEX REPLACE "\\\\" "/" PYTHON_SITE_PACKAGES "${PYTHON_SITE_PACKAGES}")
    ENDIF()
ENDIF()

SET(PYDS_DEFAULT_ARGS
        "-DCMAKE_PREFIX_PATH:PATH=${PYDS_INSTALL_PREFIX};${CMAKE_PREFIX_PATH}"
        "-DCMAKE_INSTALL_PREFIX:PATH=${PYDS_INSTALL_PREFIX}"
        "-DPYTHON_SITE_PACKAGES:PATH=${PYDS_INSTALL_PREFIX}/${PYTHON_SITE_PACKAGES}")

SET(j2534_source "${CMAKE_CURRENT_SOURCE_DIR}/deps/j2534")
SET(j2534_build "${CMAKE_CURRENT_BINARY_DIR}/deps/j2534")
EXTERNALPROJECT_ADD(j2534 SOURCE_DIR ${j2534_source} BINARY_DIR ${j2534_build} CMAKE_CACHE_ARGS ${PYDS_DEFAULT_ARGS})

SET(uds_source "${CMAKE_CURRENT_SOURCE_DIR}/deps/uds")
SET(uds_build "${CMAKE_CURRENT_BINARY_DIR}/deps/uds")
EXTERNALPROJECT_ADD(uds SOURCE_DIR ${uds_source} BINARY_DIR ${uds_build} CMAKE_CACHE_ARGS ${PYDS_DEFAULT_ARGS} DEPENDS j2534)

IF(PYTHONINTERP_FOUND)
    SET(MODULE_PY             "${CMAKE_CURRENT_SOURCE_DIR}/deps/ids")
    SET(MODULE_PY_OUTPUT      "${MODULE_PY}/build/lib/ids.py")

    #SCRIPT 1
    SET(SCRIPT "
from __future__ import print_function
import sys
import os
import site
os.environ['PYTHONPATH'] = '${PYDS_INSTALL_PREFIX}${PYTHON_SITE_PACKAGES}'
sys.path.append('${PYDS_INSTALL_PREFIX}${PYTHON_SITE_PACKAGES}')
site.addsitedir('${PYDS_INSTALL_PREFIX}${PYTHON_SITE_PACKAGES}')
sys.argv = ['setup.py','install','--prefix=${PYDS_INSTALL_PREFIX}']
execfile('setup.py')
from setuptools.command import easy_install
easy_install.main(['-U','--zip-ok','--prefix=${PYDS_INSTALL_PREFIX}','setuptools'])
    ")
    IF (WIN32)
        STRING(REGEX REPLACE "\\/" "\\\\\\\\" SCRIPT "${SCRIPT}")
    ENDIF()
    FILE(WRITE ${CMAKE_BINARY_DIR}/setup.py "${SCRIPT}")

    #SCRIPT 2
    SET(SCRIPT "
from __future__ import print_function
import os
import sys
import site
os.environ['PYTHONPATH'] = '${PYDS_INSTALL_PREFIX}${PYTHON_SITE_PACKAGES}'
sys.path.append('${PYDS_INSTALL_PREFIX}${PYTHON_SITE_PACKAGES}')
site.addsitedir('${PYDS_INSTALL_PREFIX}${PYTHON_SITE_PACKAGES}')
from setuptools.command import easy_install
easy_install.main(['-U','--zip-ok','--prefix=${PYDS_INSTALL_PREFIX}','mock'])
    ")
    IF (WIN32)
        STRING(REGEX REPLACE "\\/" "\\\\\\\\" SCRIPT "${SCRIPT}")
    ENDIF()
    FILE(WRITE ${CMAKE_BINARY_DIR}/setup2.py "${SCRIPT}")

    ADD_CUSTOM_COMMAND(OUTPUT ${MODULE_PY_OUTPUT}
            WORKING_DIRECTORY ${MODULE_PY}
            COMMAND ${PYTHON_EXECUTABLE} setup.py build
            COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_BINARY_DIR}/setup.py
            COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_BINARY_DIR}/setup2.py
            DEPENDS ${MODULE_PY}/ids.py)
    ADD_CUSTOM_TARGET(target ALL DEPENDS ${MODULE_PY_OUTPUT})
ENDIF()