Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run Chr(34) & "Run_EURO_GOALS_Fast_Icon.bat" & Chr(34), 1, False
Set WshShell = Nothing
