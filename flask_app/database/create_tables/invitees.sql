CREATE TABLE IF NOT EXISTS `invitees` (
`invitee_id`      int auto_increment PRIMARY KEY        COMMENT 'the id of this invitee',
`event_id`        int                                   COMMENT 'the id of the event this invitee is invited to',
`email`           varchar(255) NOT NULL                 COMMENT 'the email of this invitee',
FOREIGN KEY (`event_id`) REFERENCES `events` (`event_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="Contains site invitee information";