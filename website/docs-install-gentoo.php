<?php

$PAGE_TITLE = 'Installing in Gentoo';

require 'header.php';
require 'sidebar.php';

?>

            <div id="main">

                <h1>Installing in Gentoo Linux</h1>

<p>Last checked: 3 Aug 2008, git99<br><br>

These instructions are for Gentoo GNU/Linux, but if you adapt the steps installing and starting stuff it should work on any other OS as well.<br><br>

1. Install everything. Check if anything is already installed and if it is remove it from the command.<br><br>

For mysql:<br>
emerge mysql mysql-python pygtk -av<br>
/etc/init.d/mysql start<br>
rc-update add mysql default<br><br>

For postgresql:<br>
emerge postgresql pygresql pygtk <br>
/etc/init.d/postgresql start<br>
rc-update add postgresql default<br>

<br><br>
2. Manual configuration steps<br>
<br>
emerge --config mysql<br>
The --config step will ask you for the mysql root user - set this securely, we will create a seperate account for fpdb<br>
<br><br>
3. Create a mysql user and a database<br>
Now open a shell (aka command prompt aka DOS window):<br>
Click Start, then Run. In the opening window type "cmd" (without the inverted commas) and then click OK. A windows with a black background should open.<br><br>

Type (replacing yourPassword with the root password for MySQL you specified during installation):<br>
mysql --user=root --password=yourPassword<br><br>

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

Next you need to create a user. I recommend you use the default fpdb. Type this (replacing newPassword with the password you want the fpdb user to have - this can, but for security shouldn't, be the same as the root mysql password):<br>
GRANT ALL PRIVILEGES ON fpdb.* TO 'fpdb'@'localhost' IDENTIFIED BY 'newPassword' WITH GRANT OPTION;<br><br>

Copy the .conf file from this directory to ~/.fpdb/profiles/default.conf and edit it according to what you configured just now, in particular you will definitely have to put in the password you configured. I know this is insecure, will fix it before stable release.<br>
<br>
4. Guided installation steps<br>
Run the GUI as described in readme-user and click the menu database -&gt; recreate tables<br>
<br>
That's it! Now see readme-user.txt for usage instructions.<br>
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

require 'footer.php';

?>
