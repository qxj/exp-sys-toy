CREATE TABLE `condition` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `cond_list` text COMMENT '条件列表，以逗号分隔。如，对于browser的cond_list：chrome,firefox,ie,...',
  `owner_id` int(11) DEFAULT NULL,
  `description` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `domain` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `parent_id` int(11) DEFAULT NULL COMMENT '父domain id',
  `name` varchar(255) DEFAULT NULL COMMENT '域名',
  `owner_id` int(11) DEFAULT NULL,
  `enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `buckets` int(11) DEFAULT NULL COMMENT '流量大小 [0,10000]',
  `create_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`),
  KEY `enabled` (`enabled`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

CREATE TABLE `experiment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `description` text,
  `control_id` int(11) DEFAULT NULL COMMENT '控制组id',
  `layer_id` int(11) DEFAULT NULL,
  `diversion` enum('uuid','user','random') DEFAULT NULL COMMENT '流量分配方式',
  `conditions` text COMMENT '流量过滤条件，json格式。如：{‘broswer’: [‘IE’, ‘firefox’], ‘build_version’: [‘1.8’, ‘1.9’]}',
  `parameters` text COMMENT '参数列表。如：param1=val1;param2=val2;...',
  `buckets` int(11) DEFAULT NULL COMMENT '抽样桶数量 [0,10000]',
  `start_time` datetime DEFAULT NULL COMMENT '实验启动时间',
  `end_time` datetime DEFAULT NULL COMMENT '实验结束时间',
  `status` enum('draft','pending','rejected','revert','pause','deploy','published','completed') DEFAULT NULL COMMENT '实验状态：草稿、待审核、被拒绝、撤销、暂停、待发布、已发布、完成',
  `create_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `layer_id` (`layer_id`),
  KEY `status` (`status`),
  KEY `start_time` (`start_time`),
  KEY `end_time` (`end_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `exp_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `exp_list` varchar(255) DEFAULT NULL COMMENT '实验组内的实验id列表，以逗号分隔',
  `name` varchar(255) DEFAULT NULL,
  `description` text,
  `owner_id` int(11) DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `layer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `domain_id` int(11) DEFAULT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `launch` tinyint(1) DEFAULT '0' COMMENT '是否launch layer',
  `enabled` tinyint(1) DEFAULT '1' COMMENT '是否启动',
  `create_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`),
  KEY `domain_id` (`domain_id`),
  KEY `user_id` (`owner_id`),
  KEY `enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `parameter` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `layer_id` int(11) DEFAULT NULL,
  `type` enum('bool','int','double','string') DEFAULT NULL COMMENT '参数类型',
  `value` varchar(255) DEFAULT NULL COMMENT '参数缺省值',
  `owner_id` int(11) DEFAULT NULL COMMENT '负责人id',
  `create_time` datetime DEFAULT NULL COMMENT '参数创建时间',
  `description` text COMMENT '具体参数说明',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`),
  KEY `layer_id` (`layer_id`),
  KEY `owner_id` (`owner_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `user` (
  `user_id` int(11) NOT NULL COMMENT '和icars_zh的user表保持同步',
  `username` varchar(45) DEFAULT NULL,
  `role` enum('user','manager','admin') DEFAULT NULL COMMENT '角色（普通用户、审核用户、管理员）',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='用户表';
