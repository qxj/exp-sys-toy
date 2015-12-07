<?php
// @(#) test.php  Time-stamp: <Julian Qian 2015-12-07 17:14:58>
// Copyright 2015 Julian Qian
// Author: Julian Qian <junist@gmail.com>
// Version: $Id: test.php,v 0.1 2015-12-04 15:56:51 jqian Exp $
//

require_once "exp_sys.php";

$value = ExpSys::get('search_top_cars');
var_dump($value);

$params = ExpSys::requested_params();
var_dump($params);

Logger::info('test');
