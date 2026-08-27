' 启动 ADB 脚本工具（隐藏控制台启动，无 cmd 窗口闪烁）
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
Set ws = CreateObject("Wscript.Shell")
ws.CurrentDirectory = base
ws.Run """" & base & "\..\..\.venv\Scripts\pythonw.exe"" """ & base & "\main.py""", 0, False
