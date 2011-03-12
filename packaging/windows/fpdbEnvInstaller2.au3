; Copyright 2008-2011 Michael
; This program is free software: you can redistribute it and/or modify
; it under the terms of the GNU Affero General Public License as published by
; the Free Software Foundation, version 3 of the License.
; 
; This program is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
; GNU General Public License for more details.
; 
; You should have received a copy of the GNU Affero General Public License
; along with this program. If not, see <http://www.gnu.org/licenses/>.
; In the "official" distribution you can find the license in agpl-3.0.txt.


;"%programfiles%\MySQL\MySQL Server 5.0\bin\mysqld" --remove
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Includes
#include <GUIConstantsEx.au3>

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Variables
Dim $rootPwd = ""
Dim	$fpdbUserPwd = ""

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Welcome message and option to abort. Change of working dir to \fpdbEnv
Dim $welcomeBox = MsgBox(4100, "fpdb environment installation", "This installer will automatically create the environment which is needed to run fpdb." & @CRLF & @CRLF & _ 
"This means installing and configuring MySQL and Python including some special modules," & @CRLF & "creating a directory for your fpdb user profile and adding gtk to your path." & @CRLF & @CRLF & _
"You are advised to close all aplications before you proceed." & @CRLF & @CRLF & _
"DON'T use the keyboard or the mouse during installation unless you are asked to! Just WAIT until the message box 'End of Installation' pops up!" & @CRLF & @CRLF & _
"If you want to continue the installation click 'Yes'." & @CRLF & "If you want to abort the installation click 'No'.")
If $welcomeBox == 7 Then
	Exit																		;Exit Installation if 'No' button is clicked in message box
EndIf

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Ask user for mysql root password
GUICreate("FPDB Environment Installation", 600, 400) 
GUICtrlCreateLabel("For the installation of the FPDB Environment the MySQL root password and your poker database password are needed.",	 20,  25)
GUICtrlCreateLabel("In case MySQL and/or your fpdb poker database aren't installed on your computer, just pick a password.",			 20,  50)
GUICtrlCreateLabel("MySQL Root Password:", 														 										 20, 100)
$rootPw = GUICtrlCreateInput("your password here",																						150, 100, 100, 20)
GUICtrlCreateLabel("Retype password:", 																									290, 100)
$rootPwR = GUICtrlCreateInput("", 																										420, 100, 100, 20)
GUICtrlCreateLabel("Poker DB User Password:", 																								 20, 150)
$userPw = GUICtrlCreateInput("your password here",																						150, 150, 100, 20)
GUICtrlCreateLabel("Retype password:", 																									290, 150)
$userPwR = GUICtrlCreateInput("", 																										420, 150, 100, 20)
$okbutton = GUICtrlCreateButton("OK",																									270, 200, 60, 20)
$status = GUICtrlCreateLabel("This is the status line. It describes what the installer is doing at the moment.", 20, 250, 560)
GUISetState(@SW_SHOW)
While 1
	$msg = GUIGetMsg()
	Select
		Case $msg = $okbutton
			If Not(GUICtrlRead($rootPw) == GUICtrlRead($rootPwR)) OR GUICtrlRead($rootPw) == "" Then
				MsgBox(16, "", "The passwords don't macht! Try again!", 20, 250)
			ElseIf Not(GUICtrlRead($userPw) == GUICtrlRead($userPwR)) OR GUICtrlRead($userPw) == "" Then
				MsgBox(16, "", "The passwords don't macht! Try again!", 20, 250)
			Else
				$rootPwd = GUICtrlRead($rootPw)
				$fpdbUserPwd = GUICtrlRead($userPw)
				GUICtrlSetState($okbutton, $GUI_DISABLE)
				ExitLoop
			EndIf
	EndSelect
WEnd

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Files Needed
FileInstall("fpdb\7za.exe", "7za.exe")
FileInstall("fpdb\MySQL Server 5.0.7z", "MySQL Server 5.0.7z")
FileInstall("fpdb\gtk.7z", "gtk.7z")
FileInstall("fpdb\python-2.5.2.msi", "python-2.5.2.msi")
FileInstall("fpdb\pymysql.7z", "pymysql.7z")
FileInstall("fpdb\pycairo.7z", "pycairo.7z")
FileInstall("fpdb\pygobject.7z", "pygobject.7z")
FileInstall("fpdb\pygtk.7z", "pygtk.7z")
FileInstall("fpdb\psykopg2.7z", "psykopg2.7z")
FileInstall("fpdb\pywin32.7z", "pywin32.7z")

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; MySQL Install and configuration
If NOT FileExists(EnvGet("programfiles") & "\MySQL\MySQL Server 5.0\bin\mysql.exe") Then
	GUICtrlSetData($status, "Installing MySQL Database Management System and creating MySQL windows service.")
	RunWait('7za.exe x "MySQL Server 5.0.7z" -o"' & EnvGet("programfiles") & '\MySQL\" -aoa', "", @SW_HIDE)
	RunWait('"' & EnvGet("programfiles") & '\MySQL\MySQL Server 5.0\bin\mysqld" --install', "", @SW_HIDE)
	RunWait("net start mysql", "", @SW_HIDE)
	ProcessWait("mysqld.exe")
	GUICtrlSetData($status, "Securing important MySQL user accounts.")
	Sleep(5000)
	FileWrite(EnvGet("programfiles") & "\MySQL\MySQL Server 5.0\bin\mysql1.txt", "DELETE FROM mysql.user WHERE User = '';" & @CRLF)
	FileWrite(EnvGet("programfiles") & "\MySQL\MySQL Server 5.0\bin\mysql1.txt", "UPDATE mysql.user SET Password = PASSWORD('" & $rootPwd & "') WHERE User = 'root';" & @CRLF)
	FileWrite(EnvGet("programfiles") & "\MySQL\MySQL Server 5.0\bin\mysql1.txt", "FLUSH PRIVILEGES;" & @CRLF)
	RunWait(@ComSpec & ' /c mysql --user=root -e "source mysql1.txt"', EnvGet("programfiles") & '\MySQL\MySQL Server 5.0\bin\', @SW_HIDE)
EndIf
If NOT FileExists(EnvGet("programfiles") & "\MySQL\MySQL Server 5.0\data\fpdb") Then
	GUICtrlSetData($status, "Creating fpdb database.")
	FileWrite(EnvGet("programfiles") & "\MySQL\MySQL Server 5.0\bin\mysql2.txt", "create database fpdb;" & @CRLF)
	RunWait(@ComSpec & ' /c mysql --user=root --password=' & $rootPwd & ' -e "source mysql2.txt"', EnvGet("programfiles") & '\MySQL\MySQL Server 5.0\bin\', @SW_HIDE)
EndIf
GUICtrlSetData($status, "Creating MySQL user 'fpdb' and granting privileges.")
FileWrite(EnvGet("programfiles") & "\MySQL\MySQL Server 5.0\bin\mysql3.txt", "GRANT ALL PRIVILEGES ON fpdb.* TO 'fpdb'@'localhost' IDENTIFIED BY '" & $fpdbUserPwd & "' WITH GRANT OPTION;" & @CRLF)
RunWait(@ComSpec & ' /c mysql --user=root --password=' & $rootPwd & ' -e "source mysql3.txt"', EnvGet("programfiles") & '\MySQL\MySQL Server 5.0\bin\', @SW_HIDE)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; GTK
GUICtrlSetData($status, "Installing GTK.")
RunWait('7za.exe x "gtk.7z" -oc:\ -aoa', "", @SW_HIDE)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Python 2.5 Installation
GUICtrlSetData($status, "Installing Python 2.5.2")
RunWait("msiexec /quiet /i python-2.5.2.msi", "", @SW_HIDE)									;Install Python without user interaction

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; pymysql
GUICtrlSetData($status, "Installing pymysql")
RunWait('7za.exe x "pymysql.7z" -oC:\Python25\Lib\site-packages -aoa', "", @SW_HIDE)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; pycairo
GUICtrlSetData($status, "Installing pycairo")
RunWait('7za.exe x "pycairo.7z" -oC:\ -aoa', "", @SW_HIDE)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; pygobject
GUICtrlSetData($status, "Installing pygobject")
RunWait('7za.exe x "pygobject.7z" -oC:\ -aoa', "", @SW_HIDE)
RunWait(@ComSpec & ' /c C:\Python25\python.exe pygobject_postinstall.py -install', "C:\Python25\SCRIPTS", @SW_HIDE)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; pygtk
GUICtrlSetData($status, "Installing pygtk")
RunWait('7za.exe x "pygtk.7z" -oC:\ -aoa', "", @SW_HIDE)
RunWait(@ComSpec & ' /c C:\Python25\python.exe pygtk_postinstall.py -install', "C:\Python25\SCRIPTS", @SW_HIDE)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; psykopg2
GUICtrlSetData($status, "Installing psykopg2")
RunWait('7za.exe x "psykopg2.7z" -oC:\ -aoa', "", @SW_HIDE)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; pywin32
GUICtrlSetData($status, "Installing pywin32 for Python 2.5")
RunWait('7za.exe x "pywin32.7z" -oC:\ -aoa', "", @SW_HIDE)
RunWait(@ComSpec & ' /c C:\Python25\python.exe pywin32_postinstall.py -install', "C:\Python25\SCRIPTS", @SW_HIDE)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Creating directory for default.conf and coping the file into it
GUICtrlSetData($status, "Creating and installing default.conf file.")
$file = FileOpen("default.conf", 1)
FileWriteLine($file, "db-backend=2" & @CRLF)
FileWriteLine($file, "db-host=localhost" & @CRLF)
FileWriteLine($file, "db-databaseName=fpdb" & @CRLF)
FileWriteLine($file, "db-user=fpdb" & @CRLF)
FileWriteLine($file, "db-password=" & $fpdbUserPwd & @CRLF)
FileWriteLine($file, "tv-combinedStealFold=True" & @CRLF)
FileWriteLine($file, "tv-combined2B3B=True" & @CRLF)
FileWriteLine($file, "tv-combinedPostflop=True" & @CRLF)
FileWriteLine($file, "bulkImport-defaultPath=default" & @CRLF)
FileWriteLine($file, "hud-defaultPath=default" & @CRLF)
FileWriteLine($file, "imp-callFpdbHud=True" & @CRLF)
FileClose($file)
FileCopy("default.conf", EnvGet("appdata") & "\fpdb\", 9)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Registry
GUICtrlSetData($status, "Creating backup of path variable and adding GTK and Python to path variable.")
RegWrite("HKEY_CURRENT_USER\Environment", "PathBackup", "REG_SZ", RegRead("HKEY_CURRENT_USER\Environment", "path"))
RegWrite("HKEY_CURRENT_USER\Environment", "path", "REG_SZ", RegRead("HKEY_CURRENT_USER\Environment", "path") & ';C:\gtk\bin;C:\Python25')

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Delete installation files
GUICtrlSetData($status, "Deleting temporary installation files.")
FileDelete("7za.exe")
FileDelete("MySQL Server 5.0.7z")
FileDelete("gtk.7z")
FileDelete("python-2.5.2.msi")
FileDelete("pymysql.7z")
FileDelete("pycairo.7z")
FileDelete("pygobject.7z")
FileDelete("pygtk.7z")
FileDelete("psykopg2.7z")
FileDelete("pywin32.7z")
FileDelete("default.conf")

$goodbyeBox = MsgBox(4100, "End of Installation", "The Computer needs to be restarted for the installation to be complete." & @CRLF & _
	"After that you can start fpdb by double clicking the file fpdb.py which is located in the folder pyfpdb of the fpdb build you downloaded." & @CRLF & _
	"If you haven't downloaded fpdb yet you can do it here: http://ovh.dl.sourceforge.net/sourceforge/fpdb/fpdb-alpha2-p68.zip" & @CRLF & @CRLF & _
	"If you want to restart the computer now click 'Yes'." & @CRLF & _
	"If you want to restart the computer later click 'No'.")
If $goodbyeBox == 7 Then
	Exit																		;Exit Installation if 'No' button is clicked in message box
EndIf
Run("shutdown.exe -r -t 0")