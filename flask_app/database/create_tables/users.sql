CREATE TABLE IF NOT EXISTS `users` (
`user_id`         int  	       auto_increment PRIMARY KEY   COMMENT 'the id of this user',
`name`            varchar(100) NOT NULL                     COMMENT 'the name of this user',
`email`           varchar(255) NOT NULL UNIQUE              COMMENT 'the email of this user',
`password`        varchar(255) NOT NULL                     COMMENT 'the encrypted password of this user'
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="Contains site user information";