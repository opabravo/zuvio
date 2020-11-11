@echo off

pyinstaller --clean --onefile Zuvio.py

del /s /q /f Zuvio.spec
rmdir /s /q __pycache__
rmdir /s /q build

:cmd
pause null