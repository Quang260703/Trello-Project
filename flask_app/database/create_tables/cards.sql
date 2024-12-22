CREATE TABLE IF NOT EXISTS `cards` (
`card_id`     int(11)       NOT NULL    AUTO_INCREMENT      COMMENT 'The card id',
`board_id`    int(11)       NOT NULL 				        COMMENT 'FK:The board id',
`list_id`     int(11)       NOT NULL					    COMMENT 'The list id: 0: To do; 1: Doing; 2:Completed',
`position`    int(11)       NOT NULL					    COMMENT 'The position of this card in the list',
`name`        varchar(500)  NOT NULL                        COMMENT 'The name of this card',
`description` varchar(500)  NULL                        COMMENT 'The description of this card',
PRIMARY KEY (`card_id`),
FOREIGN KEY (board_id) REFERENCES boards(board_id)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="Cards in this board";