' ===========================================
' EURO_GOALS Start Shortcut Script
' ===========================================

Set WshShell = CreateObject("WScript.Shell")

' 🔗 URL για την αρχική σελίδα
url = "https://euro-goals-v6f.onrender.com/"

' 🔘 Αν θες Chrome συγκεκριμένα:
chromePath = """C:\Program Files\Google\Chrome\Application\chrome.exe"""

If CreateObject("Scripting.FileSystemObject").FileExists(chromePath) Then
    WshShell.Run chromePath & " " & url
Else
    WshShell.Run url
End If
