CREATE TABLE IF NOT EXISTS `availability` (
    `availability_id`   int auto_increment PRIMARY KEY                      COMMENT 'the id for this availability',
    `event_id`          int NOT NULL                                        COMMENT 'the id for this event',
    `user_id`           int NOT NULL                                        COMMENT 'the id for this user',
    `date`              date NOT NULL                                       COMMENT 'the date of the slot',
    `time`              time NOT NULL                                       COMMENT 'the time of the slot',
    `status`            enum('available', 'maybe', 'unavailable') NOT NULL  COMMENT 'the different types of availability',
    FOREIGN KEY (`event_id`) REFERENCES `events` (`event_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
    UNIQUE KEY `unique_slot` (`event_id`, `user_id`, `date`, `time`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='Contains site availability info';