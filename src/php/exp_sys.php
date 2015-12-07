<?php
// @(#) exp_defs.php  Time-stamp: <Julian Qian 2015-12-07 17:15:31>
// Copyright 2015 Julian Qian
// Author: Julian Qian <junist@gmail.com>
// Version: $Id: exp_defs.php,v 0.1 2015-11-18 11:14:00 jqian Exp $
//

// Experiment PHP Library
//
// Extract exp_sys configuration from pb file, and build experiment space to
// divert each request.

// require_once "/usr/share/php/DrSlump/Protobuf.php";

error_reporting(E_ALL ^ E_NOTICE);

require_once "experiment.proto.php";
require_once "exp_defs.php";

// use \DrSlump\Protobuf;
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
    srand(time());
    $this->_rand_id = rand(0, BUCKETS_NUM_MAX -1);
    //
    $this->_build();
    $this->_divert();
  }

  private
  function _build() {
    $deploy = $this->_get_deploy();
    // get domains
    $domains = array();
    foreach ($deploy->getDomains() as $d) {
      $domain = Domain::fromPb($d);
      $domains[$domain->getId()] = $domain;
      Logger::info("load domain %s", $domain->toString());
    }
    // get layers
    foreach ($deploy->getLayers() as $l) {
      $domain = $domains[$l->getDomainId()];
      $layer = new Layer($l->getId(), $domain);
      $this->_layers[] = $layer;
      Logger::info("load layer %s", $layer->toString());
    }
    // assign experiments
    foreach ($deploy->getExperiments() as $e) {
      $exp = Experiment::fromPb($e);
      $this->_exps[$exp->getId()] = $exp;
      $layer = $this->_layers[$exp->getLayerId()];
      $layer->assign($exp);
      Logger::info("load exp %s", $exp->toString());
    }
    foreach ($deploy->getParameters() as $p) {
      $param = Parameter::fromPb($p);
      $this->_baseParams[$param->getName()] = $param->getValue();
      Logger::info("load param %s", $param->getName());
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
    // init experiment space from pb
    $pb_file = '../../bin/exp_sys.pb';
    if (class_exists('F3')) {
      $pb_file = F3::get('PDEXP.FILE');
    }
    $data = file_get_contents($pb_file);
    return exp\Deployment::parseFromString($data);
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
        return $this->_rand_id;
    }
  }

  private
  function _valid_conditions($exp) {
    $ret = true;
    foreach ($exp->getCondMap() as $cond => $args) {
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
      Logger::info("start diversion by %s", $diversion);
      foreach ($this->_layers as &$layer) {
        Logger::info("process layer %d", $layer->getId());
        if (!$layer->bias()) {
          $divId = $this->_get_divert_id($diversion) % BUCKETS_NUM_MAX;
          Logger::info("divert id: %d", $divId);
          $expId = $layer->divert($divId);
          if ($expId > 0) {
            Logger::info("divert to experiment %d", $expId);
            $exp = $this->_exps[$expId];
            // check time
            if ($this->_valid_time($exp)) {
              // check conditions
              if ($this->_valid_conditions($exp)) {
                $this->_params = array_merge($this->_params, $exp->getParamMap());
              } else {
                Logger::info("biased layer %d", $layer->getId());
                $layer->bias(true);
              }
            } else {
              Logger::info("experiment %d is out of time", $expId);
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

  public static
  function __callStatic($method, $argv) {
    switch($method) {
      case "get":
        $name = array_shift($argv);
        return self::instance()->_get($name);
      case "requested_params":
        return self::instance()->_requested_params();
      default:
        Logger::error("wrong method.");
        return;
    }
  }

  private
  function _get($name) {
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

  private
  function _requested_params() {  // for logger and stats
    return $this->_reqParams;
  }
}