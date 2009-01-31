#!/bin/sh

#Copyright 2008 Steffen Jobbagy-Felso
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in
#agpl-3.0.txt in the docs folder of the package.

rm regression-test/*.found.txt
rm regression-test/*.pyc
rm pyfpdb/*.pyc

mkdir fpdb-$1
cp -R docs fpdb-$1/
cp -R packaging fpdb-$1/
cp -R pyfpdb fpdb-$1/
#rm fpdb-$1/pyfpdb/HUD_config.*
cp pyfpdb/HUD_config.xml.example fpdb-$1/pyfpdb/HUD_config.xml
cp -R regression-test fpdb-$1/
cp -R utils fpdb-$1/

cd fpdb-$1
zip * releases/fpdb_$1 *
#tar -cf - * | bzip2 >> releases/fpdb_$1.tar.bz2
#cd ..
#rm -r fpdb-$1

#echo "Please ensure the files are named fpdb-1.0_alpha*_p*.*"
