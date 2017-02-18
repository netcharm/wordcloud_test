@echo off

call cxfreeze-simple cloud.py --target-name=wordcloud.exe

IF DEFINED PYTHONHOME (
  xcopy /y wordcloud.exe %PYTHONHOME%\SCRIPTS\
)
