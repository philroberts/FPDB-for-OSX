<?php

require dirname(__FILE__).'/config.php';

$PAGE_TITLE = 'Installing in Windows';

require SITE_PATH.'header.php';
require SITE_PATH.'sidebar.php';

?>

            <div id="main">

                <h1>Installing in Windows</h1>

<p>These instructions are for 32/64bit Windows NT/2k/XP/2k3/Vista/2k8. Well, in principle. I made them in XP Pro, if you discover any differences or problems please let me know. If you're still on Win3/95/98/ME then you should switch to GNU/Linux, *BSD or WinXP. Also see the installation pages for other plataforms.<br>
<br>
The length of these instructions is due to MS refusal to provide any kind of package management. <br>
<br>
Here are direct download links from 10Aug2008:<br>
<a href="http://dev.mysql.com/get/Downloads/MySQL-5.0/mysql-5.0.67-win32.zip/from/pick#mirrors">http://dev.mysql.com/get/Downloads/MySQL-5.0/mysql-5.0.67-win32.zip/from/pick#mirrors</a><br>
<a href="http://www.python.org/ftp/python/2.5.2/python-2.5.2.msi">http://www.python.org/ftp/python/2.5.2/python-2.5.2.msi</a><br>
<a href="http://downloads.sourceforge.net/mysql-python/MySQL-python-1.2.2.win32-py2.5.exe?modtime=1173863337&big_mirror=0">http://downloads.sourceforge.net/mysql-python/MySQL-python-1.2.2.win32-py2.5.exe?modtime=1173863337&amp;big_mirror=0</a><br>
<a href="http://ftp.gnome.org/pub/gnome/binaries/win32/gtk+/2.12/gtk+-bundle-2.12.11.zip">http://ftp.gnome.org/pub/gnome/binaries/win32/gtk+/2.12/gtk+-bundle-2.12.11.zip</a><br>
<a href="http://ftp.gnome.org/pub/GNOME/binaries/win32/pycairo/1.4/pycairo-1.4.12-1.win32-py2.5.exe">http://ftp.gnome.org/pub/GNOME/binaries/win32/pycairo/1.4/pycairo-1.4.12-1.win32-py2.5.exe</a><br>
<a href="http://ftp.gnome.org/pub/GNOME/binaries/win32/pygobject/2.14/pygobject-2.14.1-1.win32-py2.5.exe">http://ftp.gnome.org/pub/GNOME/binaries/win32/pygobject/2.14/pygobject-2.14.1-1.win32-py2.5.exe</a><br>
<a href="http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.12/pygtk-2.12.1-2.win32-py2.5.exe">http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.12/pygtk-2.12.1-2.win32-py2.5.exe</a><br>
<br>
<b>1a. Install MySQL and do its basic setup</b><br>
- Download Windows ZIP/Setup.exe<br>
- Unzip the archive, execute the setup file<br>
	At the end make sure you activate that you want to configure it now.<br>
	Use the advanced/detailed config. Leave everything as default unless stated below, or unless you have reason not to.<br>
	Make sure to DEACTIVATE TCP/IP networking, unless you want that and know how to secure it<br>
	Set a root password. Note that this is not the account/pw that fpdb will use.<br>
<br>
Once finished it shold confirm "service started successfully"<br>
<br>
<b>1b. MySQL database and user setup</b><br>
Now open a shell (aka command prompt aka DOS window):<br>
Click Start, then Run. In the opening window type "cmd" (without the inverted commas) and then click OK. A windows with a black background should open.<br>
<br>
Type (replacing yourPassword with the root password for MySQL you specified during installation):<br>
mysql --user=root --password=yourPassword<br>
<br>
It should say something like this:<br>
Welcome to the MySQL monitor.  Commands end with ; or \g.<br>
Your MySQL connection id is 4<br>
Server version: 5.0.60-log Gentoo Linux mysql-5.0.60-r1<br>
<br>
Type 'help;' or '\h' for help. Type '\c' to clear the buffer.<br>
<br>
mysql&gt;<br>
<br>
Now create the actual database. The default name is fpdb, I recommend you keep it. Type this:<br>
CREATE DATABASE fpdb;<br>
<br>
Next you need to create a user. I recommend you use the default fpdb. Type this (replacing newPassword with the password you want the fpdb user to have - this can, but for security shouldn't, be the same as the root mysql password):<br>
GRANT ALL PRIVILEGES ON fpdb.* TO 'fpdb'@'localhost' IDENTIFIED BY 'newPassword' WITH GRANT OPTION;<br>
<br>
Exit mysql by pressing Ctrl+D<br>
<br>
<b>2. Install python</b><br>
Get the latest Windows installer. As of this writing that is 2.5.2. Double click the .msi file to start installation and follow the prompts.<br>
<br>
<b>3. Install the Python-DBAPI package for MySQL:</b><br>
Get the package and double click to install.<br>
<br>
<b>4. </b> In MySQL create a new database fpdb and a user by the same name. Set a password. I did this in webmin. Then set permissions for that user to: Select | Insert | Update | Delete | Create | Drop<br>
<br>
<b>5. Time for GTK+ - here's the instructions from their bundle</b><br>
<br>
To use it, create some empty folder like c:\gtk . Using either<br>
Windows Explorer's built-in zip file management, or the command-line<br>
unzip.exe from<br>
ftp://tug.ctan.org/tex-archive/tools/zip/info-zip/WIN32/unz552xN.exe<br>
unzip this bundle.<br>
<br>
Then add the bin folder to your PATH. Make sure you have no other<br>
versions of GTK+ in PATH.<br>
To do that:<br>
Right click on "My Computer" ("Arbeitsplatz" in German Windows) on the Desktop or in (Windows) Explorer. Select Properties. Then click on the tab Advanced and then you should see Environment Variables. Simply append GTK's bin folder to the existing PATH (make sure to put a ; between the old PATH and GTK's folder to seperate the entries in this list).<br>
<br>
<b>6.</b> Install pycairo, pygobject and pygtk with double click.<br>
<br>
<b>7.</b> Copy the default.conf from the docs folder to the appropriate folder in your system, e.g. C:\Documents and Settings\Nick\Application Data\fpdb\profiles\default.conf<br>
<br>
Now edit the file, in particular you will always have to type in the correct password (insecure, I know) and if you differ from the default setup you may need to change host, database or user.<br>
<br>
<b>8.</b> Double click fpdb.py in the pyfpdb folder of where you downloaded/unpacked it to.<br>
When the program started open the menu Database and click "Create or Recreate Tables".<br>
<br>
That's it! Now you can use the bulk importer and the table viewer, more's coming. See readme-user.txt<br>
<br>
License<br>
=======<br>
Trademarks of third parties have been used under Fair Use or similar laws.<br>
<br>
Copyright 2008 Steffen Jobbagy-Felso<br>
Permission is granted to copy, distribute and/or modify this<br>
document under the terms of the GNU Free Documentation License,<br>
Version 1.2 as published by the Free Software Foundation; with<br>
no Invariant Sections, no Front-Cover Texts, and with no Back-Cover<br>
Texts. A copy of the license can be found in fdl-1.2.txt<br>
<br>
The program itself is licensed under AGPLv3, see agpl-3.0.txt</p>


            </div>

<?php

require SITE_PATH.'footer.php';

?>
