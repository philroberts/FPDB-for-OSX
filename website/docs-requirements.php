<?php

$PAGE_TITLE = 'Requirements';

require 'header.php';
require 'sidebar.php';

?>

            <div id="main">

                <h1>Requirements</h1>
<p>
I recommend using a free/libre operating system, meaning a GNU/Linux distribution or a BSD variant (e.g. Gentoo GNU/Linux or OpenBSD) for ethical and practical reasons. Would you buy a car where you're prohibited from opening the bonnet under threat of jail? If the answer is no you should by the same logic not use closed source software for real money Poker :)<br>
<br>
Unfortunately you will always need one piece of unfree software: The poker client itself. Although not a direct dependency of fpdb you obviously will have a hard time putting this to productive use without running some poker client. As far as I know, only unfree clients are available. If you know better please let me know ASAP!<br>
<br>
If you can be bothered please do contact your poker site(s) and ask them to release free/libre clients, even if it is only for Windows. But lets be realistic, the chance of a positive answer is very low.<br>
<br>
Before I start the list a note on the databases, as of git96 I have yet to try using this with PostgreSQL, but if I'm not mistaken it should actually work by now (the stuff in fpdb-python at least).<br>
<br>
If you use a package management system (e.g. if you have GNU/Linux or *BSD) just check that you have mysql, mysql-python and pygtk or postgresql, pygresql and pygtk. Your package manager will take care of the rest for you.<br>
	<br>
Make new entries in this format:<br>
X. Program Name<br>
===============<br>
a. Optional?<br>
b. Required Version and Why<br>
c. Project Webpage<br>
d. License<br>
<br>
1. MySQL<br>
========<br>
a. Optional?<br>
	Choose MySQL or PostgreSQL<br>
b. Required Version and Why<br>
	At least 3.23 required due to mysql-python.<br>
	I use 5.0.54 and 5.0.60-r1 (GNU/Linux) and 5.0.51b (Windows).<br>
c. Project Webpage<br>
	http://www.mysql.com<br>
d. License<br>
	GPL2<br>
<br>
2. PostgreSQL<br>
=============<br>
a. Optional?<br>
	Choose MySQL or PostgreSQL<br>
b. Required Version and Why<br>
	I use 8.0.15 (GNU/Linux) and 8.3.3 (Windows) but I am not aware of any incompatibilities<br>
	with older or newer versions, pls report success/failure.<br>
c. Project Webpage<br>
	http://www.postgresql.org<br>
d. License<br>
	BSD License<br>
<br>
3. mysql-python<br>
===============<br>
a. Optional?<br>
	Required if you want to use MySQL backend<br>
b. Required Version and Why<br>
	I use 1.2.2 but I am not aware of any incompatibilities with older or newer versions, pls report success/failure.<br>
c. Project Webpage<br>
	http://sourceforge.net/projects/mysql-python/<br>
d. License<br>
	SF lists GNU General Public License (GPL), Python License (CNRI Python License), Zope Public License.<br>
	Project states GPL without version in Pkg-info.<br>
<br>
4. pygresql<br>
===========<br>
a. Optional?<br>
	Required if you want to use PostgreSQL backend<br>
b. Required Version and Why<br>
	I use 3.6.2 but I am not aware of any incompatibilities with older or newer versions, pls report success/failure.<br>
c. Project Webpage<br>
	http://www.pygresql.org/<br>
d. License<br>
	http://www.pygresql.org/readme.html#copyright-notice (BSD License?)<br>
	Summary: "Permission to use, copy, modify, and distribute this software and its <br>
	documentation for any purpose, without fee, and without a written agreement <br>
	is hereby granted[...]" plus Disclaimer.<br>
<br>
5. Python<br>
=========<br>
a. Optional?<br>
	Required.<br>
b. Required Version and Why<br>
	I use 2.4.4 and 2.5.2 but I am not aware of any incompatibilities with older or newer versions, pls report success/failure.<br>
c. Project Webpage<br>
	http://www.python.org<br>
d. License<br>
	Python License<br>
<br>
6. GTK+ and dependencies<br>
=======<br>
a. Optional?<br>
	Required.<br>
b. Required Version and Why<br>
	I use 2.12.9 but it should run with 2.10 or higher. That is needed as I used MessageDialog updates<br>
c. Project Webpage<br>
	Main: http://www.gtk.org/<br>
	API spec: http://library.gnome.org/devel/gtk/2.12/<br>
	Windows DLs (get the bundle unless you know what you're doing): http://www.gtk.org/download-windows.html<br>
d. License<br>
	LGPL2<br>
<br>
7. PyCairo<br>
==========<br>
a. Optional?<br>
	Required.<br>
b. Required Version and Why<br>
	?<br>
c. Project Webpage<br>
	main: http://www.pygtk.org<br>
d. License<br>
	LGPL2.1<br>
<br>
8. PyGObject<br>
============<br>
a. Optional?<br>
	Required.<br>
b. Required Version and Why<br>
	?<br>
c. Project Webpage<br>
	main: http://www.pygtk.org<br>
d. License<br>
	LGPL2.1<br>
<br>
9. PyGTK<br>
========<br>
a. Optional?<br>
	Required.<br>
b. Required Version and Why<br>
	?<br>
c. Project Webpage<br>
	main: http://www.pygtk.org<br>
d. License<br>
	LGPL2.1<br>
<br>
License (of this file)<br>
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
