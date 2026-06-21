' Launch WhisperWriter silently (no console window) using pythonw.exe.
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")

baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = baseDir

pythonw = """" & baseDir & "\venv\Scripts\pythonw.exe"""
runpy = """" & baseDir & "\run.py"""

' 0 = hidden window, False = don't wait for it to finish
sh.Run pythonw & " " & runpy, 0, False
