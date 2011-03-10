#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RushNotesMerge.py

            EXPERIMENTAL - USE WITH CARE

Merge .queue file with hero's note to generate fresh .merge file

normal usage 
$> ./pyfpdb/RushNotesMerge.py "/home/foo/.wine/drive_c/Program Files/Full Tilt Poker/heroname.xml"

The generated file can then replace heroname.xml (if all is well).


"""
#    Copyright 2010-2011,  "Gimick" of the FPDB project  fpdb.sourceforge.net
#
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

########################################################################

#TODO gettextify

#    Standard Library modules
import os
import sys
from xml.dom import minidom 

#
# overload minidom methods to fix bug where \n is parsed as " ".
# described here: http://bugs.python.org/issue7139
#

def _write_data(writer, data, isAttrib=False):
    "Writes datachars to writer."
    if isAttrib:
        data = data.replace("\r", "&#xD;").replace("\n", "&#xA;")
        data = data.replace("\t", "&#x9;")
    writer.write(data)
minidom._write_data = _write_data

def writexml(self, writer, indent="", addindent="", newl=""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        _write_data(writer, attrs[a_name].value, isAttrib=True)
        writer.write("\"")
    if self.childNodes:
        writer.write(">%s"%(newl))
        for node in self.childNodes:
            node.writexml(writer,indent+addindent,addindent,newl)
        writer.write("%s</%s>%s" % (indent,self.tagName,newl))
    else:
        writer.write("/>%s"%(newl))
# For an introduction to overriding instance methods, see
#   http://irrepupavel.com/documents/python/instancemethod/
instancemethod = type(minidom.Element.writexml)
minidom.Element.writexml = instancemethod(
    writexml, None, minidom.Element)



statqueue=0
statupdated=0
statadded=0

def cleannote(textin):
    if textin.find("~fpdb~") == -1: return textin
    if textin.find("~ends~") == -1: return textin
    if textin.find("~fpdb~") > textin.find("~ends~"): return textin
    return textin[0:textin.find("~fpdb~")] + textin[textin.find("~ends~")+6:]
# get out now if parameter not passed
try: 
    sys.argv[1] <> ""
except: 
    print "A parameter is required, quitting now"
    print "normal usage is something like:"
    print '$> ./pyfpdb/RushNotesMerge.py "/home/foo/.wine/drive_c/Program Files/Full Tilt Poker/myhero.xml"'
    quit()

if not os.path.isfile(sys.argv[1]):
    print "Hero notes file not found, quitting"
    print "normal usage is something like:"
    print '$> ./pyfpdb/RushNotesMerge.py "/home/foo/.wine/drive_c/Program Files/Full Tilt Poker/myhero.xml"'
    quit()

if not os.path.isfile((sys.argv[1]+".queue")):
    print "Nothing found to merge, quitting"
    quit()

print "***************************************************************"
print "IMPORTANT: *** Before running this merge: ***"
print "Closedown the FullTiltClient and wait for it to completely stop"
print "If FullTiltClient was running, run the merge again once it"
print "has stopped completely"
print "***************************************************************"
print
print "read from: ", sys.argv[1]
print "updated with: ", sys.argv[1]+".queue"

#read queue and turn into a dict
queuedict = {}
xmlqueue = minidom.parse(sys.argv[1]+".queue")
notelist = xmlqueue.getElementsByTagName('NOTE')
        
for noteentry in notelist:                            
    noteplayer = noteentry.getAttribute("PlayerId")  
    notetext = noteentry.getAttribute("Text")
    queuedict[noteplayer] = notetext  
    statqueue = statqueue + 1

#read existing player note file

xmlnotefile = minidom.parse(sys.argv[1])
notelist = xmlnotefile.getElementsByTagName('NOTE')

#
#for existing players, empty out existing fpdbtext and refill
#        
for noteentry in notelist: 
    noteplayer = noteentry.getAttribute("PlayerId")
    if noteplayer in queuedict:        
        existingnote = noteentry.getAttribute("Text")
        newnote=cleannote(existingnote)
        newnote = newnote + queuedict[noteplayer]
        noteentry.setAttribute("Text",newnote)
        statupdated = statupdated + 1
        del queuedict[noteplayer]                  

#
#create entries for new players (those remaining in the dictionary)
#
if len(queuedict) > 0:
    playerdata=xmlnotefile.lastChild #move to the PLAYERDATA node (assume last one in the list)
    notesnode=playerdata.childNodes[1] #Find NOTES node 

for newplayer in queuedict:
    newentry = xmlnotefile.createElement("NOTE")
    newentry.setAttribute("PlayerId", newplayer)
    newentry.setAttribute("Text", queuedict[newplayer])              
    notesnode.insertBefore(newentry,None)
    newentry = xmlnotefile.createTextNode("\n")
    notesnode.insertBefore(newentry,None)
    statadded=statadded+1
                
#print xmlnotefile.toprettyxml()

mergednotes = open(sys.argv[1]+".merged", 'w')
xmlnotefile.writexml(mergednotes)
mergednotes.close()

xmlnotefile.unlink

print "written to: ", sys.argv[1]+".merged"
print ""
print "number in queue: ", statqueue
print "existing players updated: ", statupdated
print "new players added: ", statadded
print "\n"
print "Use a viewer to check the contents of the merge file."
print "If you are happy, carry out the following steps:"
print "1 Rename or delete the existing notes file (normally <heroname>.xml)"
print "2 Rename the .merged file to become the new notes file"
print "3 Delete the .queue file (it will be created at the next rush autoimport)"

