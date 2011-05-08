@echo off

rem  .bat script to run fpdb

rem    Copyright 2007-2011, Gerko de Roo

rem   This program is free software: you can redistribute it and/or modify
rem   it under the terms of the GNU Affero General Public License as published by
rem   the Free Software Foundation, version 3 of the License.
rem
rem   This program is distributed in the hope that it will be useful,
rem   but WITHOUT ANY WARRANTY; without even the implied warranty of
rem   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
rem   GNU General Public License for more details.
rem
rem   You should have received a copy of the GNU Affero General Public License
rem   along with this program. If not, see <http://www.gnu.org/licenses/>.
rem   In the "official" distribution you can find the license in agpl-3.0.txt.

cd pyfpdb

rem    Sanity-check that executable is installed in a valid ascii path.
rem    Work-around for horrible py2exe/python "missing dll" runtime crash

fpdb_folder_check.exe "%cd%"
if %ERRORLEVEL% == 1 goto:folder_check_error

rem    Next, Validate installation environment.
rem    fpdb_prerun will throw a tcl window and errorlevel 1 if a problem found
rem    problem will also be detailed in fpdb_prerun.txt
rem    -v flag (verbose) activates text output

fpdb_prerun.exe -v >..\fpdb_prerun.txt
if %ERRORLEVEL% == 1 goto:end

start /b fpdb.exe
goto:end

:folder_check_error

echo.
echo. ERROR - fpdb cannot start
echo. Folder %cd% is invalid for fpdb
echo.
echo. TO FIX
echo. - Move the fpdb folder to a path which is 100%% American-English characters
echo. - for example : 
echo. c:\fpdb or c:\mylocalprogrammes\fpdb would be valid for fpdb.
pause

:end

cd ..

