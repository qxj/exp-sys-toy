<?php
// @(#) test.php  Time-stamp: <Julian Qian 2015-12-08 16:44:48>
// Copyright 2015 Julian Qian
// Author: Julian Qian <junist@gmail.com>
// Version: $Id: test.php,v 0.1 2015-12-04 15:56:51 jqian Exp $
//

require_once __DIR__ . "/exp_sys.php";

Logger::disable();

$total = 1000;
$matched = 0;
ExpSys::instance();
for ($i=0; $i<$total; $i++) {
  ExpSys::instance()->reset_for_test();
  $value = ExpSys::instance()->get('search_send_distance');
  $params = ExpSys::instance()->diverted_params();
  if (count($params) > 0) {
    $matched++;
  }
}

Logger::enable();
Logger::info('matched %d/%d', $matched, $total);
