<?php
// @(#) exp_defs.php  Time-stamp: <Julian Qian 2016-01-13 11:17:17>
// Copyright 2015, 2016 Julian Qian
// Author: Julian Qian <junist@gmail.com>
// Version: $Id: exp_defs.php,v 0.1 2015-11-18 11:14:00 jqian Exp $
//

// Experiment PHP Library
//
// Extract exp_sys configuration from pb file, and build experiment space to
// divert each request.

// error_reporting(E_ALL ^ E_NOTICE);

require_once __DIR__ . "/exp_defs.php";


class ExpSys {
  private static $_instance = null;
  // firstly, divert by uuid, ... finally, divert by random
  private $_diversions = array(
      'uuid'   => null,
      'user'   => null,
      'random' => null);
  private $_layers = array();
  private $_exps = array();
  // parameters with default value
  private $_baseParams = array();
  // parameters in diverted experiments
  private $_params = array();
  // parameters are requested
  private $_divParams = array();

  private
  function __construct() {
    srand(time());
    $this->_diversions['random'] = rand(0, BUCKETS_NUM_MAX -1);
    if (isset($_SERVER['HTTP_UUID'])) {
      $this->_diversions['uuid'] = $_SERVER['HTTP_UUID'];
    }
    // build exp_sys
    try {
      $this->_build();
    } catch (Exception $e) {
      Logger::error("Failed to load experiment system, %s", $e->getMessage());
    }
    $this->_divert();
  }

  private
  function _build() {
    $deploy = $this->_get_deploy();
    // get domains
    $domains = array();
    foreach ($deploy->{'domains'} as $d) {
      $domain = Domain::fromJson($d);
      $domains[$domain->getId()] = $domain;
      Logger::debug("load domain %s", $domain->toString());
    }
    // get layers
    foreach ($deploy->{'layers'} as $l) {
      $domain = $domains[$l->{'domain_id'}];
      $layer = new Layer($l->{'id'}, $domain);
      $this->_layers[$l->{'id'}] = $layer;
      Logger::debug("load layer %s", $layer->toString());
    }
    // assign experiments
    foreach ($deploy->{'experiments'} as $e) {
      $exp = Experiment::fromJson($e);
      $this->_exps[$exp->getId()] = $exp;
      $layer = $this->_layers[$exp->getLayerId()];
      $layer->assign($exp);
      Logger::debug("load exp %s", $exp->toString());
    }
    foreach ($deploy->{'parameters'} as $p) {
      $param = Parameter::fromJson($p);
      $this->_baseParams[$param->getName()] = $param->getValue();
      Logger::debug("load param %s => %s", $param->getName(), $param->getValue());
    }
  }

  private
  function _get_deploy() {
    $deploy = null;
    if (function_exists('apc_fetch')) {
      $deploy_apc_key = 'deploy';
      $deploy = apc_fetch($deploy_apc_key);
      if ($deploy === false) {
        $deploy = $this->_get_deploy_json();
        apc_store($deploy_apc_key, $deploy, 60);  // 60s expiration
      }
    } else {
      $deploy = $this->_get_deploy_json();
    }
    return $deploy;
  }

  private
  function _get_deploy_json() {
    // init experiment space from json
    $json_file = "";
    if (class_exists('F3')) {
      $json_file = F3::get('PDEXP.FILE');
    }
    if (!$json_file) {
      $json_file = '/home/work/exp_sys.json';
    }
    if (!file_exists($json_file)) {
      $json_file = __DIR__ . '/exp_sys.json';
    }
    $data = @file_get_contents($json_file);
    if ($data === false) {
      throw new Exception("json file $json_file is missing");
    }
    return @json_decode($data);
  }

  private static
  function _hash_id($id) {
    return intval(substr(hash('md5', $id), 0, 8), 16);
  }

  private static
  function _divert_id($id, $layer_id) {
    $new_id = sprintf("%s_%s", $id, $layer_id);
    return self::_hash_id($new_id) % BUCKETS_NUM_MAX;
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
    foreach ($this->_diversions as $diversion => $divId) {
      if ($divId !== null) {
        Logger::trace("start diversion %s, id %s", $diversion, $divId);
        foreach ($this->_layers as &$layer) {
          Logger::debug("process layer %d", $layer->getId());
          if (!$layer->bias()) {
            $modId = self::_divert_id($divId, $layer->getId());
            Logger::debug("divert id: %d, mod id: %d", $divId, $modId);
            $expId = $layer->divert($modId);
            if ($expId > 0) {
              Logger::debug("divert to experiment %d", $expId);
              $exp = $this->_exps[$expId];
              // check diversion
              if ($exp->getDiversion() == $diversion) {
                // check time
                if ($this->_valid_time($exp)) {
                  // check conditions
                  if ($this->_valid_conditions($exp)) {
                    $this->_params = array_merge($this->_params, $exp->getParamMap());
                    Logger::trace("active experiment %d in layer %d",
                            $exp->getId(), $layer->getId());
                  } else {
                    $layer->bias(true);
                    Logger::debug("biased layer %d", $layer->getId());
                  }
                } else {
                  Logger::debug("experiment %d is out of time", $expId);
                }
              } else {
                Logger::debug("experiment %d is mismatched diversion", $expId);
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

  public static
  function diverted_params() {  // for logger and stats
    if (self::$_instance == null) {
      return array();
    } else {
      return self::$_instance->_divParams;
    }
  }

  public
  function get($name) {
    if (array_key_exists($name, $this->_params)) {
      $value = $this->_params[$name];
      // log parameters
      $this->_divParams[$name] = $value;
      Logger::trace("get paramter %s => %s", $name, $value);
      return $value;
    }
    if (array_key_exists($name, $this->_baseParams)) {
      return $this->_baseParams[$name];
    }
    return null;
  }

  public
  function reset_for_test() {  // only for test
    $this->_diversions['random'] = rand(0, BUCKETS_NUM_MAX -1);
    $this->_divParams = array();
    $this->_params = array();
    $this->_divert();
  }

}