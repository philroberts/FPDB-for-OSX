<?php

$PAGE_TITLE = 'Installing in Windows';

require 'header.php';
require 'sidebar.php';

?>

<div id="main">

<h2> How To Use the HUD</h2>

<h4>3 September, 2008</h4>

<h4>fpdb version alpha 3</h4>

<h3>Initial Configuration</h3>

<p>Install and configure the import/tracker program as detailed elsewhere.  You should have this line in your default.conf file.</p>

<code>imp-callFpdbHud=True</code>

<p>When you downloaded fpdb you got an example HUD configuration file named HUD_config.xml.</p>

<p>1. Open the subdirectory where you installed fpdb.</p>

<p>2. Make a backup copy of HUD_config.xml.</p>

<p>3. Check that the db_user and db_pass parameters are the ones you specified during database setup.  This line is near the bottom of your config file and specifies the database parameters to be used.</p>

<code>&lt;database db_name="fpdb" db_server="mysql" db_ip="localhost" db_user="fpdb" db_pass="fpdb" db_type="fpdb"&gt;&lt;/database&gt;</code>

<p>This should allow you to use the HUD with the stats and layout in the example configuration file.</p>

<h3>Running the HUD</h3>

<p>1.  Open fpdb and select Auto Import from the menu.  The fpdb main screen will change to show the autoimport dialog.</p>

<img src="img/docs.HudHowTo1.png" alt="Image of HUD" />

<p>Check that the path is pointing to your hand history subdirectory, if it is not, then click the browse button and select it. ?You can also adjust the interval between imports. Smaller intervals will get your updated HUD data more often, but might cause lag. If you experience lag, increase the interval.</p>

<p>2. Click "Start Autoimport" to start the import. fpdb will automatically start the HUD. When the HUD starts it will open a HUD main window.</p>

<img src="img/docs.HudHowTo2.png" alt="Image of HUD" />

<p>2. This window currently has no purpose other than providing a close button that will cause the HUD to exit.</p>

<p>3. Play a hand of poker (good luck). A few seconds after the completion of the hand the stat windows should overlay the poker client window.</p>

<img src="img/docs.HudHowTo3.png" alt="Image of HUD" />

<p>You will also see a small main window for each table that has a HUD. Clicking the close button on that window will kill the HUD stat windows for that table. The stat windows will not go away automatically when you close the table.</p>

<img src="img/docs.HudHowTo4.png" />

<p>4. Adjust the positions of the stat windows. By default, the stat windows are created without decorations (title bar, border, etc.). Double clicking on a stat will add the decorations to that stat window. You can then use the title bar to move the window and double click again to make the decorations disappear.</p>

<img src="img/docs.HudHowTo5.png" />

<img src="img/docs.HudHowTo6.png" />

<p>5. So play some poker: raise, bet, float, get all-in. You can find out what each stat is by hovering the mouse over the stat and looking at the tool tip. The tool tip also has the name of the player that the stat corresponds to, so it is useful in figuring out which stat window goes where if your windows are not in the right place. You can also get a pop up window with additional stats by single clicking on a stat.</p>

<img src="img/docs.HudHowTo7.png" />

<p>These windows do not automatically update when a new hand is imported, but they can be moved around the same way the stat window are moved. Single clicking anywhere on the popup will make it disappear.</p>

<h3>Configuring Stat Layouts</h3>

<p>OK, back to the HUD_config.xml file--saving a backup would be a good idea. Before you ask, yes, there will be a neat configuration function in the HUD, to make this quicker and easier. We thought you would prefer to have the HUD now rather than wait for us to write the configuration code.</p>

<p>1. Open your HUD_config.xml file in you text editor and scroll down to site entry for the layout you want to configure. For example, if you want to change a layout for Pokerstars, find the line that starts like this.</p>

<code>&lt;site site_name="PokerStars" ...</code>

<p>Below that line you will find several blocks of lines defining the stat layouts for tables with the various numbers of seats. For example the layout for 6-seated tables looks like this:</p>

<code>&lt;layout max="6" width="792" height="546" fav_seat="0&gt;<br>
&lt;location seat="1" x="681" y="119"&gt; &lt;/location&gt;<br>
&lt;location seat="2" x="681" y="301"&gt; &lt;/location&gt;<br>
&lt;location seat="3" x="487" y="369"&gt; &lt;/location&gt;<br>
&lt;location seat="4" x="226" y="369"&gt; &lt;/location&gt;<br>
&lt;location seat="5" x="0" y="301"&gt; &lt;/location&gt;<br>
&lt;location seat="6" x="0" y="119"&gt; &lt;/location&gt;<br>
&lt;/layout&gt;</code>

<p>The first line of this layout specifies that it is for a 6-max (max="6") table that has been sized to 792 x 546 (width="792" height="546").  The fav_seat parameter is not used at this time.</p>

<p>The next 6 lines specify where the stat windows are placed on the poker client window.  The x and y positions are measured from the inside upper left of the poker client window.  That is x = 0, y = 0  would be the first usable pixel to the right of the window border and below the title bar.</p>

<p>So if you are using the layout in the example above and decide that the stat window for seat 3 is being place 9 pixels too high, you would change the line for seat="3" to be:</p>

<code>&lt;location seat="3" x="487" y="378"&gt; &lt;/location&gt;</code>

<p>If you use smaller or larger client windows you should correct the width and height parameters so that they are up-to-date when automatic resizing is implemented.</p>

<h3>Configuring the Stats Shown in the stat windows</h3>

<p>The definition of the stat window stats is in the "supported games" paragraph of the HUD_config.xml file.  For example:</p>

<code>&lt;game game_name="studhilo" db="fpdb" rows="2" cols="3"&gt;<br>
&lt;stat row="0" col="0" stat_name="vpip"    tip="tip1" click="tog_decorate" popup="default"&gt; &lt;/stat&gt;<br>
&lt;stat row="0" col="1" stat_name="pfr"     tip="tip1" click="tog_decorate" popup="default"&gt; &lt;/stat&gt;<br>
&lt;stat row="0" col="2" stat_name="ffreq_1" tip="tip1" click="tog_decorate" popup="default"&gt; &lt;/stat&gt;<br>
&lt;stat row="1" col="0" stat_name="n"       tip="tip1" click="tog_decorate" popup="default"&gt; &lt;/stat&gt;<br>
&lt;stat row="1" col="1" stat_name="wtsd"    tip="tip1" click="tog_decorate" popup="default"&gt; &lt;/stat&gt;<br>
&lt;stat row="1" col="2" stat_name="wmsd"    tip="tip1" click="tog_decorate" popup="default"&gt; &lt;/stat&gt;<br>
&lt;/game&gt;</code>

<p>The first line specifies the game that this stat paragraph is used for (game = "studhilo") and the number of rows and columns in the stat window.  In this case we have specified 2 rows and 3 columns so we can have 2x3 = 6 stats.  Rows and columns are numbered from 0, so the 3 columns are numbered 0, 1, and 2.</p>

<p>The subsequent lines in the stat paragraph specify which stats are displayed in the various parts of the window.  In this example, vpip is displayed in col 0, row 0.</p>

<p>So to create stat windows with 4 columns of 2 rows you would change the cols parameter in the first line to cols = "4" and add 2 additional rows to specify the stats for row 2, col 3 and row 1, col 3.</p>

<p>The click and tip parameters in this paragraph are not currently used.  The popup parameter is explained in the next section.</p>

<h3>Configuring Popup Windows</h3>

<p>Each stat location can display a different popup window when clicked.  In the example just above, each of the stats has the "default" popup specified.  You can see the definition of the default popup by scrolling farther down in your config file.  It should look like this.</p>

<code>&lt;popup_windows&gt;<br>
&lt;pu pu_name="default"&gt;<br>
&lt;pu_stat pu_stat_name = "n"&gt; &lt;/pu_stat&gt;<br>
&lt;pu_stat pu_stat_name = "vpip"&gt; &lt;/pu_stat&gt;<br>
&lt;pu_stat pu_stat_name = "pfr"&gt; &lt;/pu_stat&gt;<br>
...<br>
&lt;pu_stat pu_stat_name = "ffreq_4"&gt; &lt;/pu_stat&gt;<br>
&lt;/pu&gt;<br>
&lt;/popup_windows&gt;</code>

<p>You can create a new popup by making a new pu elelment, with a new name and a new list of stats.  You then specify that popup name in the popup parameter in one or more of your stats.</p>

<h3>Currently Supported Stats</h3>

<dl>
<dt>a_freq_1</dt>	<dd>Flop/4th aggression frequency.</dd>
<dt>a_freq_2</dt>	<dd>Turn/5th aggression frequency.</dd>
<dt>a_freq_3</dt>	<dd>River/6th aggression frequency.</dd>
<dt>a_freq_4</dt>	<dd>7th street aggression frequency.</dd>
<dt>cb_1</dt>		<dd>Flop continuation bet.</dd>
<dt>cb_2</dt>		<dd>Turn continuation bet.</dd>
<dt>cb_3</dt>		<dd>River continuation bet.</dd>
<dt>cb_4</dt>		<dd>7th street continuation bet.</dd>
<dt>f_BB_steal</dt>	<dd>Folded BB to steal.</dd>
<dt>f_SB_steal</dt>	<dd>Folded SB to steal.</dd>
<dt>ffreq_1</dt>	<dd>Flop/4th fold frequency.</dd>
<dt>ffreq_2</dt>	<dd>Turn/5th fold frequency.</dd>
<dt>ffreq_3</dt>	<dd>River/6th fold frequency.</dd>
<dt>ffreq_4</dt>	<dd>7th fold frequency.</dd>
<dt>n</dt>		<dd>Number of hands played.</dd>
<dt>pfr</dt>		<dd>Preflop (3rd street) raise.</dd>
<dt>saw_f</dt>		<dd>Saw flop/4th.</dd>
<dt>steal</dt>		<dd>Steal %.</dd>
<dt>three_B_0</dt>	<dd>Three bet preflop/3rd.</dd>
<dt>vpip</dt>		<dd>Voluntarily put $ in the pot.</dd>
<dt>wmsd</dt>		<dd>Won $ at showdown.</dd>
<dt>wtsd</dt>		<dd>Went to SD when saw flop/4th.</dd>
<dt>WMsF</dt>		<dd>Won $ when saw flop/4th.</dd>
</dl>
           

<?php

require 'footer.php';

?>