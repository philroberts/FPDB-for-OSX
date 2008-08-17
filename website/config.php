<?php

define('CONFIG', 1);
define('SITE_PATH', str_replace("\\", "/", dirname(__FILE__)).'/');

if ($_SERVER['SERVER_ADDR'] == '127.0.0.1') {
    define('DEV_HOST', 1);
    define('SITE_URL', 'http://127.0.0.1/fpdb/');
    define('PRINT_ERRORS', 1);
} else {
    define('DEV_HOST', 0);
    define('SITE_URL', 'http://fpdb.sourceforge.net/');
    define('PRINT_ERRORS', 0);
}

?>
