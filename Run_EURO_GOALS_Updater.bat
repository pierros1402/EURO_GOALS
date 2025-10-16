@echo off
chcp 65001 >nul
title EURO_GOALS v6f Fast Updater ⚽

setlocal
set "current=v6f"
set "version_file=version_online.txt"

echo Έλεγχος για ενημερώσεις...
if not exist "%version_file%" (
    echo ❌ Δεν βρέθηκε το αρχείο %version_file%.
    echo Παραλείπεται ο έλεγχος ενημέρωσης.
) else (
    for /f "usebackq delims=" %%a in ("%version_file%") do set "online=%%a"
    if "%current%"=="%online%" (
        echo ✅ Εχετε την τελευταία έκδοση: %current%
    ) else (
        echo 🆕 Νέα έκδοση διαθέσιμη: %online%
        echo (Τρέχουσα: %current%)
    )
)

echo.
echo ⚽ Εκκίνηση EURO_GOALS...
start "" /min python EURO_GOALS_v6f_fast.py

echo.
pause
exit
