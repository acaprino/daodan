@echo off
rem First-time setup on Windows.
if not exist data mkdir data
call "%~dp0build.bat" %*
