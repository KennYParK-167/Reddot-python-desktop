-- TABLE 1 : UTILISATEURS.
CREATE TABLE IF NOT EXISTS `user` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` ENUM('user','admin') NOT NULL DEFAULT 'user',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_username` (`username`)
);

-- TABLE 2 : MESSAGES.
CREATE TABLE IF NOT EXISTS `messages` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NULL,
  `username` VARCHAR(50) NOT NULL,
  `message_text` TEXT NOT NULL,
  `timestamp` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_messages_timestamp` (`timestamp`),
  KEY `idx_messages_user_id` (`user_id`),
  CONSTRAINT `fk_messages_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE SET NULL
);

