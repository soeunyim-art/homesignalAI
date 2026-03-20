@echo off
chcp 65001 > nul

cd /d "C:\Users\KimSeongYoung\Desktop\HomeSignalAI"

if not exist logs mkdir logs

set LOG_FILE=logs\update_%date:~0,4%%date:~5,2%.log

echo ======================================== >> %LOG_FILE%
echo [START] %date% %time% >> %LOG_FILE%
echo ======================================== >> %LOG_FILE%

python collect_data.py update >> %LOG_FILE% 2>&1

echo [DONE] %date% %time% >> %LOG_FILE%
echo. >> %LOG_FILE%
