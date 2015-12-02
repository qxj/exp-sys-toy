<?php
// @(#) exp_defs.php  Time-stamp: <Julian Qian 2015-12-02 17:43:51>
// Copyright 2015 Julian Qian
// Author: Julian Qian <junist@gmail.com>
// Version: $Id: exp_defs.php,v 0.1 2015-12-02 16:12:19 jqian Exp $
//


class BucketRange {
  public
  function __construct($start=0, $end=0) {
    $this->start = $start;
    $this->end = $end;
  }

  public static
  function fromPb($pb) {
    $inst = new self();
    $inst->start = $pb->getStart();
    $inst->end = $pb->getEnd();
    return $inst;
  }

  public
  function num() {
    return $this->end - $this->start;
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

  private
  function _assign($bucketRange, $expId) {
    $start = $bucketRange->start;
    if ($start < $this->range->start) {
      // error
      $start = $this->range->start;
    }
    $end = $bucketRange->end;
    if ($end > $this->range->end) {
      // error
      $end = $this->range->end;
    }

    for ($i=$start-$this->range->start;
         $i<$end-$start; $i++) {
      $this->buckets[$i] = $expId;
    }
  }

  public
  function assign($bucketRanges, $expId) {
    foreach ($bucketRanges as $bucketRange) {
      $this->_assign($bucketRange, $expId);
    }
  }
}

class Domain {
  public
  function __construct($id=0, $bucketRanges=array()) {
    $this->id = $id;
    $this->ranges = $bucketRanges;
  }

  public static
  function fromPb($pb) {  // \exp_sys\Domain
    $inst = new self();
    $inst->id = $pb->getId();
    foreach ($pb->getRangesList() as $bucketRange) {
      $inst->ranges[] = $bucketRange;
    }
    return $inst;
  }
}

class Layer {
  public
  function __construct() {

  }
}