@echo off
chcp 65001 >nul
set "QIHANG_RUNTIME=%~dp0口语运行"
set "PATH=%QIHANG_RUNTIME%\bin;%PATH%"
start "" /D "%~dp0" "%QIHANG_RUNTIME%\runtime\bin\javaw.exe" -Xmx512m "-Djava.library.path=%QIHANG_RUNTIME%\bin" -cp "%QIHANG_RUNTIME%\qihang-oral.jar;%QIHANG_RUNTIME%\json.jar" cn.qihang.oral.WindowsApp "%~dp0."
