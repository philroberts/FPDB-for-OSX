<?php

require dirname(__FILE__).'/config.php';

require SITE_PATH.'header.php';
require SITE_PATH.'sidebar.php';

?>

            <div id="main">

                <h1>Documentation</h1>

                <ul>
                    <li><a href="docs-overview.php">Overview</a></li>
                    <li><a href="docs-requirements.php">Requirements</a></li>
                </ul>

                <ul>
                    <li><a href="docs-install-windows.php">Install in Windows</a></li>
                    <li><a href="docs-install-gentoo.php">Install in Gentoo Linux</a></li>
                    <li><a href="default.conf">Default configuration file</a> (read the installation instructions)</li>
                    <li><a href="docs-git-instructions.php">Git instructions</a></li>
                </ul>

                <ul>
                    <li><a href="docs-usage.php">Usage instructions</a></li>
                    <li><a href="docs-abreviations.php">Abreviations</a></li>
                    <li><a href="docs-benchmarks.php">Benchmarks</a></li>
                </ul>

            </div>

<?php

require SITE_PATH.'footer.php';

?>
