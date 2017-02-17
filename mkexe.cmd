@echo off

call cxfreeze-simple cloud.py --target-name=wordcloud.exe

xcopy /y wordcloud.exe d:\App\Develop\Python\SCRIPTS\
