' ============================================================
'  PDF Suite Local - INICIAR
'  Doble clic -> la app se abre. Sin ventanas visibles.
'  Usa WScript.Shell.Run para crear procesos verdaderamente
'  desvinculados (WindowStyle 7 = hidden, bWait = False).
' ============================================================
Set WshShell = CreateObject("WScript.Shell")
Set FSO      = CreateObject("Scripting.FileSystemObject")
AppDir       = FSO.GetParentFolderName(WScript.ScriptFullName)

' Verificar si ya esta corriendo
On Error Resume Next
Set http = CreateObject("MSXML2.XMLHTTP")
http.Open "GET", "http://127.0.0.1:8000/health", False
http.Send
If Err.Number = 0 And http.Status = 200 Then
    http.Open "GET", "http://localhost:3000", False
    http.Send
    If Err.Number = 0 And http.Status = 200 Then
        WshShell.Run "http://localhost:3000", 1, False
        WScript.Quit 0
    End If
End If
On Error GoTo 0

' Limpiar restos
For Each p In Array(8000, 3000)
    WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr :" & p & ".*LISTENING') do taskkill /PID %a /T /F", 7, True
Next
WScript.Sleep 1500

' Backend (invisibile, desvinculado)
WshShell.CurrentDirectory = AppDir & "\backend"
WshShell.Run "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000", 7, False

' Esperar a que el backend este listo
For i = 1 To 60
    WScript.Sleep 1000
    On Error Resume Next
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "GET", "http://127.0.0.1:8000/health", False
    http.Send
    If Err.Number = 0 And http.Status = 200 Then Exit For
    On Error GoTo 0
Next

' Frontend (invisible, desvinculado)
WshShell.CurrentDirectory = AppDir & "\frontend"
WshShell.Run "cmd /c npm run dev", 7, False

' Esperar a que el frontend este listo
For i = 1 To 120
    WScript.Sleep 1000
    On Error Resume Next
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "GET", "http://localhost:3000", False
    http.Send
    If Err.Number = 0 And http.Status = 200 Then Exit For
    On Error GoTo 0
Next

' Abrir navegador
WshShell.Run "http://localhost:3000", 1, False
