' PDF Suite - DETENER
' Mata los servicios por puerto, sin preguntar nada.
Set WshShell = CreateObject("WScript.Shell")

For Each p In Array(8000, 3000)
    WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr :" & p & ".*LISTENING') do taskkill /PID %a /T /F", 7, True
Next

WScript.Sleep 1000
MsgBox "PDF Suite detenido.", 64, "PDF Suite"
