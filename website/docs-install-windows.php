<?php

$PAGE_TITLE = 'Installing in Windows';

require 'header.php';
require 'sidebar.php';

?>

<div id="main">

<h1>Installing in Windows</h1>

<div class="winInst">
<p>These instructions were made with Windows XP. They should also work with Windows NT / 2000 / 2003 / Vista and 2008. Please report any differences to gmic at users.sourceforge.net.
<p>If you're still using Win3/95/98/ME then you should switch to GNU/Linux, *BSD or WinXP.</p>
<p>An Installer will be made at some point.</p>

<div class="screenshot">
<img src="img/00.mySqlWebsite1.jpg" alt="windows install guide screenshot" />
<p><strong>1.</strong> Click <a href="http://dev.mysql.com/get/Downloads/MySQL-5.0/mysql-5.0.67-win32.zip/from/pick#mirrors">here</a> to open the <a href="http://dev.mysql.com/get/Downloads/MySQL-5.0/mysql-5.0.67-win32.zip/from/pick#mirrors">MySQL Download Page</a>. Click on the "No, thanks..." link to see the download links for the MySQL installer.</p>
</div>

<div class="screenshot">
<img src="img/01.mySqlWebsite2.jpg" alt="windows install guide screenshot" />
<p><strong>2.</strong> Click on one of the HTTP or FTP download links to download the zip file (mysql-5.0.67-win32.zip).</p>
</div>

<div class="screenshot">
<img src="img/02.mySqlSetup1.jpg" alt="windows install guide screenshot" />
<p><strong>3.</strong> Unzip the setup file to a folder of your choice and double-click on it. On the welcome screen click "Next".</p>
</div>

<div class="screenshot">
<img src="img/03.mySqlSetup3.jpg" alt="windows install guide screenshot" />
<p><strong>4.</strong> As the setup type "Typical" should be selected. Then click "Next". On the following screen click "Install" and installation will begin.</p>
</div>

<div class="screenshot">
<img src="img/04.mySqlSetup5.jpg" alt="windows install guide screenshot" />
<p><strong>5.</strong> Before the installation ends an ad for MySQL Enterprise edition will appear. Just click "Next" two times.</p>
</div>

<div class="screenshot">
<img src="img/05.mySqlSetup7.jpg" alt="windows install guide screenshot" />
<p><strong>6.</strong> Now make sure that "Configure the MySQL Server now" is checked and click "Finish".</p>
</div>

<div class="screenshot">
<img src="img/06.mySqlConfig1.jpg" alt="windows install guide screenshot" />
<p><strong>7.</strong> You are now looking at the MySQL Configuration Wizard. Click "Next".</p>
</div>

<div class="screenshot">
<img src="img/07.mySqlConfig2.jpg" alt="windows install guide screenshot" />
<p><strong>8.</strong> Make sure "Detailed Configuration" is selected. Then click "Next. Now "Developer machine" should be selected. Click "Next".</p>
</div>

<div class="screenshot">
<img src="img/08.mySqlConfig4.jpg" alt="windows install guide screenshot" />
<p><strong>9.</strong> On this screen "Multifunctional Database should be selected. Click "Next". On the next screen (InnoDB Tablespace) just click "Next".</p>
</div>

<div class="screenshot">
<img src="img/09.mySqlConfig7.jpg" alt="windows install guide screenshot" />
<p><strong>10.</strong> Now "Decision Support" should be selected. Click "Next". Now make sure "Enable TCP/IP Networking" <strong>IS</strong> selected. Then click "Next".</p>
</div>

<div class="screenshot">
<img src="img/10.mySqlConfig8.jpg" alt="windows install guide screenshot" />
<p><strong>11.</strong> Here "Standard Character Set" should be selected. Click "Next". Now make sure <strong>"Install As Windows Service"</strong> is selected.</p>
</div>

<div class="screenshot">
<img src="img/11.mySqlConfig10.jpg" alt="windows install guide screenshot" />
<p><strong>12.</strong> Now choose a root password. This will <strong>NOT</strong> be the password for your poker database. Click "Next".</p>
</div>

<div class="screenshot">
<img src="img/12.mySqlConfig11.jpg" alt="windows install guide screenshot" />
<p><strong>13.</strong> On this last screen of the Configuration Wizard just click "Execute." A few success messages will appear. Click "Finish".</p>
</div>

<div class="screenshot">
<img src="img/13.run.jpg" alt="windows install guide screenshot" />
<p><strong>14.</strong> Now click the Windows Start Button and then click "Run". Click into the white space of the new window, type <code>cmd</code> and hit ENTER.</p>
</div>

<div class="screenshot">
<img src="img/14.shellCdToMySql.jpg" alt="windows install guide screenshot" />
<p><strong>15.</strong> In the newly appeared console window type <code>cd "%PROGRAMFILES%\MySQL\MySQL Server 5.0\bin"</code> and hit ENTER.</p>
</div>

<div class="screenshot">
<img src="img/15.shellMySqlRootLogin.jpg" alt="windows install guide screenshot" />
<p><strong>16.</strong> Type <code>mysql --user=root --password=yourPassword</code> and hit ENTER (replace <code>yourPassword</code> with your chosen root password).</p>
</div>

<div class="screenshot">
<img src="img/16.shellMySqlPrompt.jpg" alt="windows install guide screenshot" />
<p><strong>17.</strong> A few lines followed by <code>mysql&gt;</code> will appear. This is the MySQL command prompt.</p>
</div>

<div class="screenshot">
<img src="img/17.shellMySqlCreateDB.jpg" alt="windows install guide screenshot" />
<p><strong>18.</strong> We will now create your poker database. Type <code>CREATE DATABASE fpdb;</code> and hit ENTER. "Query OK" says we were successful.</p>
</div>

<div class="screenshot">
<img src="img/18.shellMySqlCreateUser.jpg" alt="windows install guide screenshot" />
<p><strong>19.</strong> Type the following, <strong>replace</strong> <code>newPassword</code> with a password of your choice and hit ENTER:</p>
<p><code>GRANT ALL PRIVILEGES ON fpdb.* TO 'fpdb'@'localhost' IDENTIFIED BY 'newPassword' WITH GRANT OPTION;</code></p>
</div>

<div class="screenshot">
<img src="img/19.shellMySqlUserCreated.jpg" alt="windows install guide screenshot" />
<p><strong>20.</strong> Again it says "Query OK". Type <code>exit</code> and hit ENTER to exit the MySQL prompt. <strong>Leave this window open.</strong> We will need it later.</p>
</div>

<div class="screenshot">
<img src="img/20.pythonInst.jpg" alt="windows install guide screenshot" />
<p><strong>21.</strong> Click <a href="http://www.python.org/ftp/python/2.5.2/python-2.5.2.msi">here</a>, save the file python-2.5.2.msi where you want and double-click on it. In case of a warning window click "Execute".</p>
</div>

<div class="screenshot">
<img src="img/21.pythonInst4.jpg" alt="windows install guide screenshot" />
<p><strong>22.</strong>Click "Next" three times. Python will install. Then click finish.</p>
</div>

<div class="screenshot">
<img src="img/22.mySqlPythonInst1.jpg" alt="windows install guide screenshot" />
<p><strong>23.</strong> Click <a href="http://downloads.sourceforge.net/mysql-python/MySQL-python-1.2.2.win32-py2.5.exe?modtime=1173863337&big_mirror=0">here</a>, save MySQL-python-1.2.2.win32-py2.5.exe to a folder of your choice and double click it.  In case of a warning window click "Execute". Click "Next" three times. The Python API for MySQL will install. Click "Finish".</p>
</div>

<div class="screenshot">
<img src="img/23.shellMkDirGtk.jpg" alt="windows install guide screenshot" />
<p><strong>24.</strong> In the console window (which we left open) now type: <code>mkdir c:\gtk</code> and hit ENTER. Leave the window open again, we'll need it.</p>
<p>Now click <a href="http://ftp.gnome.org/pub/gnome/binaries/win32/gtk+/2.12/gtk+-bundle-2.12.11.zip">here</a> and save the gtk zip file  gtk+-bundle-2.12.11.zip to a folder of your choice. Unzip its contents to C:\gtk</p>
</div>

<div class="screenshot">
<img src="img/24.setGtkPath1.jpg" alt="windows install guide screenshot" />
<p><strong>25.</strong> Now <strong>right-click</strong> "My Computer" (on your Desktop) and click on "Properties". Now click on the tab "Advanced".</p>
</div>

<div class="screenshot">
<img src="img/25.setGtkPath2.jpg" alt="windows install guide screenshot" />
<p><strong>26.</strong> Click the button "Environ Variables". In the lower list of the new window click on "Path" (possibly you need to scroll).</p>
</div>

<div class="screenshot">
<img src="img/26.setGtkPath3.jpg" alt="windows install guide screenshot" />
<p><strong>27.</strong>Now click on the"Edit" button and a new window will pop up. To the value of the variable append <code>;C:\gtk\bin</code> Click Ok three times.</p>
</div>

<div class="screenshot">
<img src="img/27.pycairoInst.jpg" alt="windows install guide screenshot" />
<p><strong>28.</strong> Click <a href="http://ftp.gnome.org/pub/GNOME/binaries/win32/pycairo/1.4/pycairo-1.4.12-1.win32-py2.5.exe">here</a>, save the file pycairo-1.4.12-1.win32-py2.5.exe to a folder of your choice and double click on it.  In case of a warning window click "Execute". Now click "Next" three times. The pycairo graphics library API for Python will install. Click "Finish".</p>
</div>

<div class="screenshot">
<img src="img/28.pygobjectInst.jpg" alt="windows install guide screenshot" />
<p><strong>29.</strong> Click <a href="http://ftp.gnome.org/pub/GNOME/binaries/win32/pygobject/2.14/pygobject-2.14.1-1.win32-py2.5.exe">here</a>, save the file pygobject-2.14.1-1.win32-py2.5.exe to a folder of your choice and double click on it. In case of a warning click "Execute". Now click "Next" three times. The Python Gobject API will install. Click "Finish".</p>
</div>

<div class="screenshot">
<img src="img/29.pyGtkInst.jpg" alt="windows install guide screenshot" />
<p><strong>30.</strong> Click <a href="http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.12/pygtk-2.12.1-2.win32-py2.5.exe">here</a>, save the file pygtk-2.12.1-2.win32-py2.5.exe to a folder of your choice and double click on it. In case of a warning click "Execute". Now click "Next" three times. The Python API for Gtk+ will install. Click "Finish".</p>
</div>

<div class="screenshot">	<img src="img/30.shellMkDirProfiles.jpg" alt="windows install guide screenshot" />
<p><strong>31.</strong> In the console window now type: <code>mkdir "%homepath%\Application Data\fpdb"</code> and hit ENTER. Copy the file "default.conf" from the docs folder of your fpdb git to the directory C:\%homepath%\Application Data\fpdb\.</p>
</div>

<div class="screenshot">
<img src="img/31.editDbProfile.jpg" alt="windows install guide screenshot" />
<p><strong>32.</strong> Now open the file "default.conf" in WordPad (Start &gt; Programs &gt; Accessoirs &gt; WordPad) and replace the password in the <code>dbpassword</code> line  with your chosen password for the fpdb user. </p>
</div>

<div class="screenshot">
<img src="img/32.startFpdb.jpg" alt="windows install guide screenshot" />
<p><strong>33.</strong> Now start FPDB by double-clicking on the file fpdb.py in the folder fpdb. A console window should open up and shortly thereafter the fpdb application window should be visible. Click on the menu "Database" and select "Create or Recreate Tables".</p>
</div

<div class="screenshot">
<p><strong>Congratulations! Your fpdb installation is complete! Now you can use the bulk importer to import your hands into fpdb.</strong>
</div>
</div>

<p>A word on privelege separation: fpdb should not require root/Administrator rights to run. If it does it is a bug or serious misconfiguration, please let us know.</p>
<h4>License</h4>
<p>Trademarks of third parties have been used under Fair Use or similar laws.</p>
<p>Copyright 2008 Steffen Jobbagy-Felso</p>
<p>Permission is granted to copy, distribute and/or modify this document under the terms of the GNU Free Documentation License, Version 1.2 as published by the Free Software Foundation; with no Invariant Sections, no Front-Cover Texts, and with no Back-Cover Texts. A copy of the license can be found in fdl-1.2.txt. The program itself is licensed under AGPLv3, see agpl-3.0.txt</p>


            

<?php

require 'footer.php';

?>
