@echo off
SET root_path=%~dp0
for /f %%i in ('python  -c "from distutils.sysconfig import get_python_lib; import sys; print get_python_lib().replace(sys.prefix, '').replace('dist-', 'site-')"') do set PYTHON_SITE_PACKAGES=%%i
setlocal
SET PYTHONPATH=%root_path%output\%PYTHON_SITE_PACKAGES%
SET PATH=%root_path%output\bin;%PATH%
python -m pyds %*
endlocal
