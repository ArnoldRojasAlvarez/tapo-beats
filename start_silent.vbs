' TapoBeats Silent Launcher
' Runs start_tapobeats.bat without showing a console window
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run Chr(34) & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\start_tapobeats.bat" & Chr(34), 0, False
