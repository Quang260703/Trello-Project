CREATE TABLE IF NOT EXISTS `user_board` (
`board_id`         int(11)  	   NOT NULL 	  COMMENT 'the id of this board',
`user_id`          int(11)  	   NOT NULL 	  COMMENT 'the id of this user',
PRIMARY KEY (`board_id`, `user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="Contains board-user relationship information";