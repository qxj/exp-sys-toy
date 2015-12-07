<?php
// @(#) exp_defs.php  Time-stamp: <Julian Qian 2015-12-08 16:19:16>
// Copyright 2015 Julian Qian
// Author: Julian Qian <junist@gmail.com>
// Version: $Id: exp_defs.php,v 0.1 2015-12-02 16:12:19 jqian Exp $
//

if (!class_exists("Logger")) {
  require_once __DIR__ . "/exp_log.php";
}

define("BUCKETS_NUM_MAX", 10000);


class BucketRange {
  public
  function __construct($start=0, $end=0) {
    $this->start = intval($start);
    $this->end = intval($end);
  }

  public static
  function fromPb($pb) {
    return new self($pb->getStart(), $pb->getEnd());
  }

  public
  function num() {
    return $this->end - $this->start;
  }

  public
  function contain($idx) {
    return $idx >= $this->start && $idx < $this->end;
  }

  public
  function getStart() {
    return $this->start;
  }

  public
  function getEnd() {
    return $this->end;
  }

  public
  function toString() {
    return sprintf("<BucketRange %d~%d>", $this->start, $this->end);
  }
}

class Buckets {
  public
  function __construct($bucketRange) {
    $this->range = $bucketRange;
    $this->buckets = array();
    for ($i=0; $i<$bucketRange->num(); $i++) {
      $this->buckets[] = -1;
    }
  }

  public
  function toString() {
    return sprintf("<Buckets %s>", $this->range->toString());
  }

  private
  function _assign($bucketRange, $expId) {
    $start = $bucketRange->getStart();
    if ($start < $this->range->getStart()) {
      $start = $this->range->getStart();
      Logger::error("experiment %d start %d out of range %s",
              $expId, $start, $bucketRange->toString());
    }
    $end = $bucketRange->getEnd();
    if ($end > $this->range->getEnd()) {
      $end = $this->range->getEnd();
      Logger::error("experiment %d end %d out of range %s",
              $expId, $end, $bucketRange->toString());
    }

    for ($i=$start - $this->range->getStart();
         $i<$end - $this->range->getStart(); $i++) {
      $this->buckets[$i] = $expId;
    }
    Logger::debug("assign exp %d to range %s", $expId, $bucketRange->toString());
  }

  public
  function assign($bucketRanges, $expId) {
    foreach ($bucketRanges as $bucketRange) {
      $this->_assign($bucketRange, $expId);
    }
  }

  public
  function locate($idx) {
    if ($this->range->contain($idx)) {
      $offset = $idx - $this->range->getStart();
      return $this->buckets[$offset];
    }
    return -1;
  }
}

class Domain {
  public
  function __construct($id, $bucketRange) {
    $this->id = intval($id);
    $this->range = $bucketRange;
  }

  public static
  function fromPb($pb) {  // \exp_sys\Domain
    $range = $pb->getRange();
    return new self($pb->getId(), BucketRange::fromPb($range));
  }

  public
  function getId() {
    return $this->id;
  }

  public
  function getBucketRange() {
    return $this->range;
  }

  public
  function toString() {
    return sprintf("<Domain %d, %s>", $this->id, $this->range->toString());
  }
}

class Layer {
  public
  function __construct($id, $domain) {
    $this->id = intval($id);
    $this->domain_id = $domain->getId();
    $this->buckets = new Buckets($domain->getBucketRange());

    $this->biased = false;
    srand(time());
  }

  public
  function toString() {
    return sprintf("<Layer %d, domain %d, %s>", $this->id,
                   $this->domain_id, $this->buckets->toString());
  }

  public
  function assign($exp) {
    Logger::debug("layer %d assign exp %d", $this->id, $exp->getId());
    $this->buckets->assign($exp->getRanges(), $exp->getId());
  }

  public
  function divert($idx) {
    return $this->buckets->locate($idx);
  }

  public
  function bias($biased=null) {
    if ($biased === null) {
      return $this->biased;
    } else {
      $this->biased = $biased?true:false;
    }
  }

  public
  function getId() {
    return $this->id;
  }
}

class Experiment {
  public
  function __construct($id, $layer_id, $start_time, $end_time,
          $diversion, $parameters, $conditions, $bucketRanges) {
    $this->id = intval($id);
    $this->layer_id = intval($layer_id);
    $this->start_time = $start_time;
    $this->end_time = $end_time;
    $this->diversion = $diversion;
    $this->parameters = $parameters;
    $this->conditions = $conditions;
    $this->ranges = $bucketRanges;
  }

  public
  function toString() {
    return sprintf("<Exp %d, layer %d, time (%s~%s)>", $this->id,
                   $this->layer_id, $this->start_time, $this->end_time);
  }

  public static
  function fromPb($pb) {
    $parameters = array();
    foreach ($pb->getParameters() as $p) {
      $param = Parameter::fromPb($p);
      $parameters[$param->getName()] = $param->getValue();
    }
    $conditions = array();
    foreach ($pb->getConditions() as $c) {
      $cond = Condition::fromPb($c);
      $conditions[$cond->getName()] = $cond->getArgs();
    }
    // TODO ranges seems useless
    $ranges = array();
    foreach ($pb->getRanges() as $range) {
      $ranges[] = BucketRange::fromPb($range);
    }
    return new self($pb->getId(), $pb->getLayerId(),
            $pb->getStartTime(), $pb->getEndTime(), $pb->getDiversion(),
            $parameters, $conditions, $ranges);
  }

  public
  function validTime($timestamp) {
    $start = strtotime($this->start_time);
    $end   = strtotime($this->end_time);
    if ($timestamp >= $start && $timestamp <= $end) {
      return true;
    } else {
      return false;
    }
  }

  public
  function getRanges() {
    return $this->ranges;
  }

  public
  function getId() {
    return $this->id;
  }

  public
  function getLayerId() {
    return $this->layer_id;
  }

  public
  function getDiversion() {
    return $this->diversion;
  }

  public
  function getCond($name) {
    if (isset($this->conditions[$name])) {
      return $this->conditions[$name];
    }
    return null;
  }

  public
  function getCondMap() {
    return $this->conditions;
  }

  public
  function getParam($name) {
    if (isset($this->parameters[$name])) {
      return $this->parameters[$name];
    }
    return null;
  }

  public
  function getParamMap() {
    return $this->parameters;
  }
}

class Parameter {
  public
  function __construct($name, $value, $type=null) {
    $this->name = $name;
    switch ($type) {
      case \exp_sys\Parameter\Type::BOOL:
        if (strtolower($value) == 'true') {
          $this->value = true;
        } else {
          $this->value = false;
        }
        break;
      case \exp_sys\Parameter\Type::INT:
        $this->value = intval($value);
        break;
      case \exp_sys\Parameter\Type::DOUBLE:
        $this->value = doubleval($value);
        break;
      default:
        $this->value = strval($value);
        break;
    }
  }

  public static
  function fromPb($pb) {
    return new self($pb->getName(), $pb->getValue(), $pb->getType());
  }

  public
  function getName() {
    return $this->name;
  }

  public
  function getValue() {
    return $this->value;
  }
}

class Condition {
  public
  function __construct($name, $args) {
    $this->name = $name;
    $this->args = $args;
  }

  public static
  function fromPb($pb) {
    return new self($pb->getName(), $pb->getArgs());
  }

  public
  function getName() {
    return $this->name;
  }

  public
  function getArgs() {
    return $this->args;
  }
}