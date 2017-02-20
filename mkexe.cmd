@echo off

set SRC=%~dp0
set DST=%PYTHONHOME%\SCRIPTS\

call cxfreeze-simple %SRC%cloud.py --target-name=%SRC%wordcloud.exe

IF DEFINED PYTHONHOME (
  xcopy /Y /D %SRC%wordcloud.exe %DST%
  xcopy /Y /D %SRC%stopwords.txt %DST%
  xcopy /Y /D %SRC%userdicts.txt %DST%
)
