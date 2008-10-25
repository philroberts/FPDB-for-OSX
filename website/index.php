<?php

$PAGE_TITLE = 'Homepage';

require 'header.php';
require 'sidebar.php';

?>

<div id="main">

<h1>Welcome!</h1>

<p><strong>fpdb</strong> is a database program to track your online poker games, the behaviour of the other players and your winnings/losses. Supports Holdem, Omaha, Stud and Razz for cash games as well as SnG and MTT tournaments with more possibly coming in the future. The software is currently in alpha status, which means some of the features are not working yet. As it's open source you're free to add any feature you like or modify the existing ones to fit your needs.</p>

                <p>To see what fpdb can do, go to the <a href="<?php echo SITE_URL; ?>features.php">features</a> page. If you're ready to test it, take a look at the <a href="<?php echo SITE_URL; ?>docs.php">documentation</a>.</p>

            </div>

<?php

require 'footer.php';

?>
