#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2009-2011 Ray E. Barker
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

import re

desc = """
+-------------+---------------------+------+-----+---------+----------------+
| Field       | Type                | Null | Key | Default | Extra          |
+-------------+---------------------+------+-----+---------+----------------+
| id          | bigint(20) unsigned | NO   | PRI | NULL    | auto_increment | 
| tourneyId   | int(10) unsigned    | NO   | MUL | NULL    |                | 
| playerId    | int(10) unsigned    | NO   | MUL | NULL    |                | 
| payinAmount | int(11)             | NO   |     | NULL    |                | 
| rank        | int(11)             | NO   |     | NULL    |                | 
| winnings    | int(11)             | NO   |     | NULL    |                | 
| comment     | text                | YES  |     | NULL    |                | 
| commentTs   | datetime            | YES  |     | NULL    |                | 
+-------------+---------------------+------+-----+---------+----------------+
"""

table = """
{| border="1"
|+Gametypes Table
"""

# get rid of the verticle spacing and clean up
desc = re.sub("[\+\-]+", "", desc)
desc = re.sub("^\n+", "", desc)       # there's probably a better way
desc = re.sub("\n\n", "\n", desc)

# the first line is the header info
temp, desc = re.split("\n", desc, 1)
temp = re.sub("\|", "!", temp)
temp = re.sub(" !", " !!", temp)
table += temp + " Comments\n"

# the rest is he body of the table
for line in re.split("\n", desc):
    line = re.sub(" \|", " ||", line)
    table += "|+\n" + line + "\n"

table += "|}\n"
print table
