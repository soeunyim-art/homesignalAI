@echo off
chcp 65001 > nul

schtasks /create /tn "HomeSignalAI_MonthlyUpdate" /tr "\"C:\Users\KimSeongYoung\Desktop\HomeSignalAI\monthly_update.bat\"" /sc MONTHLY /d 5 /st 09:00 /ru "%USERNAME%" /f

if %errorlevel% == 0 (
    echo [SUCCESS] Task scheduled successfully. > result.txt
    echo   Name : HomeSignalAI_MonthlyUpdate >> result.txt
    echo   When : Every month on day 5 at 09:00 >> result.txt
    schtasks /query /tn "HomeSignalAI_MonthlyUpdate" /fo LIST >> result.txt
) else (
    echo [FAILED] Run as Administrator. > result.txt
)

type result.txt
timeout /t 10
