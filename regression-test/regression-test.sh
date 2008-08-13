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

echo "Please note for this to really work you need to work on an empty database"

rm *.found.txt
../pyfpdb/fpdb_import.py -p$1 --file=ps-lhe-ring-3hands.txt -x
../pyfpdb/fpdb_import.py -p$1 --file=ps-lhe-ring-3hands.txt -x
#../pyfpdb/fpdb_import.py -p$1 --file=ftp-stud-hilo-ring-001.txt -x
#../pyfpdb/fpdb_import.py -p$1 --file=ftp-omaha-hi-pl-ring-001-005.txt -x

echo "it should've reported first that it stored 3, then that it had 3 duplicates"
#echo "    then 1 stored, then 5 stored"

./print_hand.py -p$1 --hand=14519394979 > ps.14519394979.found.txt && colordiff ps.14519394979.found.txt ps.14519394979.expected.txt
./print_hand.py -p$1 --hand=14519420999 > ps.14519420999.found.txt && colordiff ps.14519420999.found.txt ps.14519420999.expected.txt
./print_hand.py -p$1 --hand=14519433154 > ps.14519433154.found.txt && colordiff ps.14519433154.found.txt ps.14519433154.expected.txt

./PrintPlayerHudData.py -p$1 > ps-flags-3hands.found.txt && colordiff ps-flags-3hands.found.txt ps-flags-3hands.expected.txt

#./print_hand.py -p$1 --site="Full Tilt Poker" --hand=6367428246 > ftp.6367428246.found.txt && colordiff ftp.6367428246.found.txt ftp.6367428246.expected.txt

#./print_hand.py -p$1 --site="Full Tilt Poker" --hand=6929537410 > ftp.6929537410.found.txt && colordiff ftp.6929537410.found.txt ftp.6929537410.expected.txt
#./print_hand.py -p$1 --site="Full Tilt Poker" --hand=6929553738 > ftp.6929553738.found.txt && colordiff ftp.6929553738.found.txt ftp.6929553738.expected.txt
#./print_hand.py -p$1 --site="Full Tilt Poker" --hand=6929572212 > ftp.6929572212.found.txt && colordiff ftp.6929572212.found.txt ftp.6929572212.expected.txt
#./print_hand.py -p$1 --site="Full Tilt Poker" --hand=6929576743 > ftp.6929576743.found.txt && colordiff ftp.6929576743.found.txt ftp.6929576743.expected.txt
#./print_hand.py -p$1 --site="Full Tilt Poker" --hand=6929587483 > ftp.6929587483.found.txt && colordiff ftp.6929587483.found.txt ftp.6929587483.expected.txt

echo "if everything was printed as expected this worked"
