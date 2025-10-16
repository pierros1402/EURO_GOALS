@echo off
chcp 65001 >nul
title ⚽ EURO_GOALS v6f Fast Updater

:MENU
cls
echo.
echo ================================
echo         ⚽ EURO_GOALS MENU
echo ================================
echo.
echo  1. Εκκίνηση EURO_GOALS
echo  2. Καθαρισμός αρχείων LOG
echo  3. Έξοδος
echo.
set /p choice=Επιλογή (1-3):

if "%choice%"=="1" goto RUN
if "%choice%"=="2" goto CLEAN
if "%choice%"=="3" exit
goto MENU

:RUN
cls
echo Εκκίνηση EURO_GOALS...
"C:\Users\pierr\AppData\Local\Programs\Python\Python314\python.exe" EURO_GOALS_v6f_debug.py
pause
goto MENU

:CLEAN
cls
echo Καθαρισμός αρχείων log...
del /q "EURO_GOALS_log.txt" 2>nul
del /q "log_dualsource.txt" 2>nul
echo.
echo ✅ Καθαρίστηκαν τα logs επιτυχώς!
pause
goto MENU
