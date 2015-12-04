<?php
// @(#) exp_defs.php  Time-stamp: <Julian Qian 2015-12-04 11:29:25>
// Copyright 2015 Julian Qian
// Author: Julian Qian <junist@gmail.com>
// Version: $Id: exp_defs.php,v 0.1 2015-11-18 11:14:00 jqian Exp $
//

// Experiment PHP Library
//
// Extract exp_sys configuration from pb file, and build experiment space to
// divert each request.

require_once "DrSlump/Protobuf.php";

require_once "experiment.php";
require_once "exp_defs.php";

use \DrSlump\Protobuf;
use \exp_sys as exp;

class ExpSys {
  private static $_instance = null;
  // firstly, divert by uuid, ... finally, divert by random
  private $_diversions = array('uuid', 'random');
  private $_layers = array();
  private $_exps = array();
  // parameters with default value
  private $_baseParams = array();
  // parameters in diverted experiments
  private $_params = array();
  // parameters are requested
  private $_reqParams = array();

  private
  function __construct() {
    $this->_build();
    $this->_divert();
  }

  private
  function _build() {
    $deploy = $this->_get_deploy();
    // get domains
    $domains = array();
    foreach ($deploy->getDomainsList() as $domain) {
      $domains[$domain->getId()] = Domain::fromPb($domain);
    }
    // get layers
    foreach ($deploy->getLayersList() as $layer) {
      $domain = $domains[$layer->getDomainId()];
      $this->_layers[] = new Layer($layer->getId(), $domain);
    }
    // assign experiments
    foreach ($deploy->getExperimentsList() as $exp) {
      $this->_exps[$exp->getId()] = Experiment::fromPb($exp);
      $layer = $this->_layers[$exp->getLayerId()];
      $layer->assign($exp);
    }
    foreach ($deploy->getParametersList() as $param) {
      $this->_baseParams[$param->getName()] = $param->getValue();
    }
  }

  private
  function _get_deploy() {
    $deploy = null;
    if (function_exists('apc_fetch')) {
      $deploy_apc_key = 'deploy';
      $deploy = apc_fetch($deploy_apc_key);
      if ($deploy === false) {
        $deploy = $this->_get_deploy_pb();
        apc_store($deploy_apc_key, $deploy, 60);  // 60s expiration
      }
    } else {
      $deploy = $this->_get_deploy_pb();
    }
    return $deploy;
  }

  private
  function _get_deploy_pb() {
    Protobuf::autoload();
    // init experiment space from pb
    $pb_file = '../../bin/exp_sys.pb';
    if (class_exists('F3')) {
      $pb_file = F3::get('PDEXP.FILE');
    }
    $data = file_get_contents($pb_file);
    return new exp\Deployment($data);
  }

  private static
  function _hash_id($id) {
    return intval(substr(hash('md5', $id), 0, 8), 16);
  }

  private
  function _get_divert_id($diversion) {
    switch ($diversion) {
      case 'uuid':
        return $this->_hash_id($_SERVER['HTTP_UUID']);
      default:
        return rand(0, BUCKETS_NUM_MAX -1);
    }
  }

  private
  function _valid_conditions($exp) {
    $ret = true;
    foreach ($exp->getConds() as $cond => $args) {
      switch ($cond) {
        case 'browser':
          // TODO
          break;
        case 'site':
          // TODO
          break;
      }
    }
    return $ret;
  }

  private
  function _valid_time($exp) {
    return $exp->validTime(time());
  }


  private
  function _divert() {
    foreach ($this->_diversions as $diversion) {
      foreach ($this->_layers as &$layer) {
        if (!$layer->bias()) {
          $idx = $this->_get_divert_id($diversion) % BUCKETS_NUM_MAX;
          $expId = $layer->divert($idx);
          if ($expId > 0) {
            $exp = $this->_exps[$expId];
            // check time
            if ($this->_valid_time($exp)) {
              // check conditions
              if ($this->_valid_conditions($exp)) {
                $this->_params = array_merge($this->_params, $exp->getParamMap());
              } else {
                $layer->bias(true);
              }
            }
          }
        }
      }
    }
  }

  public static
  function instance() {
    if (self::$_instance == null) {
      self::$_instance = new ExpSys;
    }
    return self::$_instance;
  }

  public
  function get($name) {
    if (in_array($name, $this->_params)) {
      $value = $this->_params[$name];
      // log parameters
      $this->_reqParams[$name] = $value;
      return $value;
    }
    if (in_array($name, $this->_baseParams)) {
      return $this->_baseParams[$name];
    }
    return null;
  }

  public
  function get_requested_params() {  // for logger and stats
    return $this->_reqParams;
  }
}