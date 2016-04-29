#!/bin/bash
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
ROOT_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
PYTHON_SITE_PACKAGES=`python  -c "from distutils.sysconfig import get_python_lib; import sys; print get_python_lib().replace(sys.prefix, '/').replace('dist-', 'site-')"`
LD_LIBRARY_PATH="${ROOT_DIR}/output/lib" PYTHONPATH="${ROOT_DIR}/output/${PYTHON_SITE_PACKAGES}" python ${ROOT_DIR}/pyds/main.py
