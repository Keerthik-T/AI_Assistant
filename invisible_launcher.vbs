' ==============================================================================
' FurinaOS Invisible Autostart Launcher
' ==============================================================================
' Description: Runs the start_furina.bat file completely hidden (Window Style 0),
'              preventing any command prompt windows from showing up.
'
' INSTRUCTIONS FOR WINDOWS AUTOSTART:
' 1. Press Win + R on your keyboard.
' 2. Type "shell:startup" (without quotes) and press Enter.
'    This will open the Windows Startup folder in File Explorer.
' 3. Right-click this file (invisible_launcher.vbs) and select "Create shortcut".
' 4. Move or copy the created shortcut file into that Startup folder.
' ==============================================================================

Dim WShell
Set WShell = CreateObject("WScript.Shell")
WShell.Run """c:\Users\ADMIN\AI Assistant\start_furina.bat""", 0, False
Set WShell = Nothing
