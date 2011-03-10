#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Steffen Schaumburg
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in agpl-3.0.txt.

import sys

def cards2String(arr):
	if (len(arr)%2!=0):
		print "TODO: raise error, cards2String failed, uneven length of arr"
		sys.exit(1)
	result = ""
	for i in range (len(arr)/2):
		if arr[i*2]==0:
			result+="??"
		else:
			if arr[i*2]==14:
				result+="A"
			elif arr[i*2]==13:
				result+="K"
			elif arr[i*2]==12:
				result+="Q"
			elif arr[i*2]==11:
				result+="J"
			elif arr[i*2]==10:
				result+="T"
			elif (arr[i*2]>=2 and arr[i*2]<=9):
				result+=str(arr[i*2])
			else:
				print "TODO: raise error, cards2String failed, arr[i*2]:", arr[i*2], "len(arr):", len(arr)
				print "arr:",arr
				sys.exit(1)
			result+=arr[i*2+1]
		result+=" "
	return result[:-1]

def id_to_player_name(cursor, id):
	cursor.execute("SELECT name FROM Players WHERE id=%s", (id, ))
	return cursor.fetchone()[0]

def position2String(pos):
	if pos=="B":
		return "BB"
	elif pos=="S":
		return "SB"
	elif pos=="0":
		return "Btn"
	else:
		return (pos+" off Btn")
	
def street_int2String(category, street):
	if (category=="holdem" or category=="omahahi" or category=="omahahilo"):
		if street==0:
			return "Preflop"
		elif street==1:
			return "Flop   "
		elif street==2:
			return "Turn   "
		elif street==3:
			return "River  "
		else:
			print "TODO: raise error, fpdb_util_lib.py street_int2String invalid street no"
			sys.exit(1)
	elif (category=="razz" or category=="studhi" or category=="studhilo"):
		return str(street)
	else:
		print "TODO: raise error, fpdb_util_lib.py street_int2String invalid category"
		sys.exit(1)
