<?php
// Experiment PHP Library
//
// Extract exp_sys configuration from pb file, and build experiment space to
// divert each request.

require_once "experiment.php";
require_once "DrSlump/Protobuf.php";

use \DrSlump\Protobuf;
use \exp_sys as exp;

class ExpSys {
  private static $instance = null;

  private
  function __construct() {

  }

  private
  function _build() {
    Protobuf::autoload();
    // init experiment space from pb
    $pb_file = F3::get('PDEXP.FILE');
    $data = file_get_contents($pb_file);
    $this->deploy = new exp\Deployment($data);
  }

  private
  function _divert() {
    $uuid = $_SERVER['HTTP_UUID'];

  }

  public
  function getInstance() {
    if (self::$instance == null) {
      self::$instance = new ExpSys;
    }
    return self::$instance;
  }

  public
  function getInt() {

  }
}