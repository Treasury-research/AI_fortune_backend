-- ----------------------------
-- Table structure for AI_fortune_assets
-- ----------------------------
DROP TABLE IF EXISTS `AI_fortune_assets`;
CREATE TABLE `AI_fortune_assets`  (
  `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `name` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `createdAt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `user_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `is_public` int(4) NULL DEFAULT 0,
  `birthday` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `assets_name_index`(`name`) USING BTREE,
  INDEX `assets_create_time_index`(`createdAt`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Compact;

-- ----------------------------
-- Table structure for AI_fortune_assets_test
-- ----------------------------
DROP TABLE IF EXISTS `AI_fortune_assets_test`;
CREATE TABLE `AI_fortune_assets_test`  (
  `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `name` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `birthday` timestamp NULL DEFAULT NULL,
  `createdAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `report` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `first_reply` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `bazi_info_gpt` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `bazi_info` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `hot` int(11) NULL DEFAULT NULL,
  `recent_hot` int(11) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `id_UNIQUE`(`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Compact;


-- ----------------------------
-- Table structure for AI_fortune_bazi
-- ----------------------------
DROP TABLE IF EXISTS `AI_fortune_bazi`;
CREATE TABLE `AI_fortune_bazi`  (
  `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `birthday` datetime NULL DEFAULT NULL,
  `bazi_info` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `createdAt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `birthday_match` datetime NULL DEFAULT NULL,
  `conversation_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `matcher_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `matcher_type` int(4) NULL DEFAULT NULL,
  `bazi_info_gpt` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `thread_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `assistant_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `first_reply` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `run_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unique_concersation_id_matcher_id`(`conversation_id`, `matcher_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Compact;

-- ----------------------------
-- Table structure for AI_fortune_bazi_chat_test
-- ----------------------------
DROP TABLE IF EXISTS `AI_fortune_bazi_chat_test`;
CREATE TABLE `AI_fortune_bazi_chat_test`  (
  `bazi_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `conversation_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `bazi_info` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `bazi_info_gpt` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `first_reply` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `assistant_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `thread_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `matcher_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `matcher_type` int(11) NULL DEFAULT NULL,
  `is_deleted` int(11) NULL DEFAULT 0,
  `createdAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`bazi_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Compact;

-- ----------------------------
-- Table structure for AI_fortune_conversation
-- ----------------------------
DROP TABLE IF EXISTS `AI_fortune_conversation`;
CREATE TABLE `AI_fortune_conversation`  (
  `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `conversation_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `is_reset` int(4) NULL DEFAULT 0,
  `human` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `AI` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `createdAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `bazi_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Compact;

-- ----------------------------
-- Table structure for AI_fortune_conversation_test
-- ----------------------------
DROP TABLE IF EXISTS `AI_fortune_conversation_test`;
CREATE TABLE `AI_fortune_conversation_test`  (
  `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `conversation_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `bazi_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `human_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  `createdAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_reset` int(4) NULL DEFAULT 0,
  `AI_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Compact;

-- ----------------------------
-- Table structure for AI_fortune_matcherPerson_test
-- ----------------------------
DROP TABLE IF EXISTS `AI_fortune_matcherPerson_test`;
CREATE TABLE `AI_fortune_matcherPerson_test`  (
  `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `birthday` datetime NULL DEFAULT NULL,
  `gender` int(11) NULL DEFAULT NULL,
  `user_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `name` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `createdAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `id_UNIQUE`(`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Compact;

-- ----------------------------
-- Table structure for AI_fortune_tg_bot_conversation_user
-- ----------------------------
DROP TABLE IF EXISTS `AI_fortune_tg_bot_conversation_user`;
CREATE TABLE `AI_fortune_tg_bot_conversation_user`  (
  `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `conversation_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `bazi_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unique_conversation_id`(`conversation_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Compact;

-- ----------------------------
-- Table structure for AI_fortune_tg_bot_conversation_user_test
-- ----------------------------
DROP TABLE IF EXISTS `AI_fortune_tg_bot_conversation_user_test`;
CREATE TABLE `AI_fortune_tg_bot_conversation_user_test`  (
  `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `conversation_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `bazi_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unique_conversation_id`(`conversation_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Compact;

-- ----------------------------
-- Table structure for AI_fortune_tg_bot_other_human
-- ----------------------------
DROP TABLE IF EXISTS `AI_fortune_tg_bot_other_human`;
CREATE TABLE `AI_fortune_tg_bot_other_human`  (
  `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `birthday` datetime NULL DEFAULT NULL,
  `gender` int(11) NULL DEFAULT 0,
  `user_id` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `name` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `createdAt` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Compact;

-- ----------------------------
-- Table structure for AI_fortune_user_test
-- ----------------------------
DROP TABLE IF EXISTS `AI_fortune_user_test`;
CREATE TABLE `AI_fortune_user_test`  (
  `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `birthday` datetime NULL DEFAULT NULL,
  `name` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `gender` int(11) NULL DEFAULT NULL,
  `createdAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `account` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `id_UNIQUE`(`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Compact;
