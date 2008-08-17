<?php

require dirname(__FILE__).'/config.php';

$PAGE_TITLE = 'Screenshots';

require SITE_PATH.'header.php';
require SITE_PATH.'sidebar.php';

?>

            <div id="main">

                <h1>Screenshots</h1>

                <p>Importing hands:<br><br><a href="<?php echo SITE_URL;?>screenshots/01.png" target="_blank"><img src="<?php echo SITE_URL;?>screenshots/01-thumb.png"></a></p>
                <br>
                <p>Table viewer:<br><br><a href="<?php echo SITE_URL;?>screenshots/02.png" target="_blank"><img src="<?php echo SITE_URL;?>screenshots/02-thumb.png"></a></p>


            </div>

<?php

require SITE_PATH.'footer.php';

?>
