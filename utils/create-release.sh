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

#get rid of extraneous stuff
rm regression-test/*.found.txt
rm regression-test/*.pyc
rm pyfpdb/*.pyc

# make the fpdb_$1.zip file for windows
echo "*** making zip file"
zip -r ../fpdb_$1.zip docs
zip -r ../fpdb_$1.zip packaging
zip -r ../fpdb_$1.zip pyfpdb

# now make the fpdb_$1.tar.bz2 file for linux
echo "*** making tar.bz2 file"
tar --recursion -cjf ../fpdb_$1.tar.bz2 *


