CREATE TABLE IF NOT EXISTS `book` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '自增id',
  `name` varchar(64) NOT NULL DEFAULT '' COMMENT '图书名',
  `author` varchar(32) NOT NULL DEFAULT '' COMMENT '图书作者',
  `price` float(5,2) default 0.0 COMMENT '图书价格',
  `publisher` varchar(32) NOT NULL DEFAULT '' COMMENT '出版社',
  `type` varchar(8) NOT NULL DEFAULT 1 COMMENT '类型：1科技 2历史 3教育 4社科 5文艺',
  `isbn` varchar(13) NOT NULL DEFAULT 1 COMMENT '国际标准书号',
  `ptime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '初版时间',
  `ctime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `utime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `deleted` tinyint(1) unsigned NOT NULL DEFAULT 0 COMMENT '是否删除：0 未删除 1 已删除',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='图书信息';