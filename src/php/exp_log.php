<?php
// @(#) exp_log.php  Time-stamp: <Julian Qian 2015-12-07 15:24:20>
// Copyright 2015 Julian Qian
// Author: Julian Qian <junist@gmail.com>
// Version: $Id: exp_log.php,v 0.1 2015-12-07 11:59:39 jqian Exp $
//


class Logger {
  private static $_logger = null;

  public static
  function _write_log($prefix, $format, $args) {
    $log = '['. strtoupper($prefix) .']';
    $trace = debug_backtrace(FALSE);
    $bt = $trace[4];
    $log .= '[' . $bt['file'] . ':';
    $log .= $bt['function'] . ':';
    $log .= $bt['line'] . '] ';
    $log .= @vsprintf($format, $args) . "\n";
    echo $log;
  }

  public static
  function __callStatic($name, $argv) {
    $format = array_shift($argv);
    @call_user_func_array(array("Logger", "_write_log"),
            array($name, $format, $argv));
  }
}