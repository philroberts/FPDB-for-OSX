#!/usr/bin/python

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