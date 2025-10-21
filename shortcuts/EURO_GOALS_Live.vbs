' ===========================================
' EURO_GOALS Live Shortcut Script
' ===========================================

Set WshShell = CreateObject("WScript.Shell")

' 🔗 URL για τη live σελίδα
url = "https://euro-goals-v6f.onrender.com/live"

' 🔘 Chrome path (αν υπάρχει)
chromePath = """C:\Program Files\Google\Chrome\Application\chrome.exe"""

If CreateObject("Scripting.FileSystemObject").FileExists(chromePath) Then
    WshShell.Run chromePath & " " & url
Else
    WshShell.Run url
End If
