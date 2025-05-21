CREATE TABLE IF NOT EXISTS `events` (
`event_id`      int auto_increment PRIMARY KEY COMMENT 'the id of this event',
`creator_id`    int                            COMMENT 'the id of the user that created this event',
`name`          varchar(100) NOT NULL          COMMENT 'the name of this event',
`start_date`    date NOT NULL                  COMMENT 'the start date of this event',
`end_date`      date NOT NULL                  COMMENT 'the end date of this event',
`start_time`    time NOT NULL                  COMMENT 'the start time of this event',
`end_time`      time NOT NULL                  COMMENT 'the end time of this event',
FOREIGN KEY (`creator_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="Contains site event information";