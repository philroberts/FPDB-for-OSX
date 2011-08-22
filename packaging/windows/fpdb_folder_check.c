/*

fpdb_folder_check.c

Copyright 2011 Gimick (bbtgaf@googlemail.com)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
In the "official" distribution you can find the license in agpl-3.0.txt.
*/

/* 
To compile this function, install mingw then DOS>fpdb_folder_check.c -o fpdb_folder_check.exe
*/

/*	
 Function needed because py2exe python apps crashes horribly if the application is 
  in a non-us-ascii folder.  (this is actually a windows python problem with "import")

  this function is not coded to cleanly handle codepage/locale/UTF.  
  The value of argv is not necessarily exactly what was passed....instead.....
 We will make two checks instead (yes, it is a hack):
 1  a char-by-char examination of the passed parameter to ensure 32 >= char <= 127
 2 A call to access() to check for folder exists  (This check catches most situations
    with accented chars but will obviously NOT fail if an accented and non-accented
    folder actually exists.

 In summary, this function is a hack and not 100% reliable, but hopefully will be 
  good enough to identify problems for most first-time users.
*/

#include <unistd.h>
#include <stdio.h>
#include <windows.h>

int main(int argc, char **argv)
{
int debugmode=0;

if (argc != 2) {
     printf ("A helper function to examine a directory passed in the first argument\n");
     printf ("Returns 0 if the directory exists, and contains only ascii characters 32 to 127\n");
     printf ("Returns 1 in all other cases\n");
     return 1;
    }

if (debugmode) {
    printf (argv[1],"\n");
    printf ("\nLength: %d ", strlen(argv[1]));
    printf ("\nMAX_PATH: %d ", MAX_PATH);
    printf ("\n");
    }

char *c = argv[1];
int i;

for(i=0; c[i]; i++) {
/* this loop finishes when c[i]<>true which is end of string (null \0) */
    if (debugmode) {printf(" %d ", c[i]);}
    if ((c[i] < 32)||(c[i] > 127)) {
        if (debugmode) {printf ("\nInvalid ASCII");} 
        return 1;
        }
    if (i > MAX_PATH-1) {
        if (debugmode) {printf ("\nMAX_PATH (%d chars) exceeded", MAX_PATH);}
        return 1;
        }
    }

if (debugmode) {printf ("\nascii OK\n");}

if (access(argv[1], F_OK) != 0) {
    if (debugmode) {printf ("\naccess() fail: Folder does not not exist");}
    return 1;
    }

if (debugmode) {printf ("\naccess() OK");}
return 0;

}
