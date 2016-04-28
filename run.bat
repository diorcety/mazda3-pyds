@echo off
SET root_path=%~dp0
pushd "output/bin/"
setlocal
SET PYTHONPATH=%root_path%\output\lib\python\dist-packages
echo %PYTHONPATH%
python %root_path%/src/test.py
endlocal
popd
