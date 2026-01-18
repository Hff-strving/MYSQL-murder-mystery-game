/*==============================================================*/
/* 数据库迁移脚本 - 001_add_auth.sql                            */
/* 功能：新增用户认证表，支持玩家和工作人员登录                  */
/* 创建时间: 2025-12-26                                          */
/*==============================================================*/

-- 创建用户表
CREATE TABLE IF NOT EXISTS T_User (
    User_ID BIGINT NOT NULL AUTO_INCREMENT,
    Username VARCHAR(50) NOT NULL UNIQUE,
    Phone CHAR(11) NOT NULL UNIQUE,
    Password_Hash VARCHAR(255) NOT NULL,
    Role ENUM('player', 'staff', 'boss') NOT NULL DEFAULT 'player',
    Ref_ID BIGINT,  -- 关联ID：player->T_Player.Player_ID，staff->T_DM.DM_ID，boss 为 NULL
    Create_Time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Last_Login TIMESTAMP NULL,
    PRIMARY KEY (User_ID),
    INDEX idx_username (Username),
    INDEX idx_phone (Phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户认证表';

-- 为现有玩家创建用户账号（默认密码：123456）
-- 密码哈希格式：盐$sha256哈希值（与后端auth_model.py一致）
-- 默认盐：default，密码：123456
INSERT IGNORE INTO T_User (Username, Phone, Password_Hash, Role, Ref_ID)
SELECT
    CONCAT('player_', Player_ID),
    COALESCE(Phone, CONCAT('1390000', LPAD(Player_ID, 4, '0'))),
    'default$697d423a3558f0ab2e71cea50014029628ee62cd154e1e81d5cd960932cce9b6',
    'player',
    Player_ID
FROM T_Player
WHERE Player_ID NOT IN (SELECT COALESCE(Ref_ID, 0) FROM T_User WHERE Role = 'player');

-- 为现有DM创建工作人员账号（默认密码：123456）
INSERT IGNORE INTO T_User (Username, Phone, Password_Hash, Role, Ref_ID)
SELECT
    CONCAT('staff_', DM_ID),
    Phone,
    'default$697d423a3558f0ab2e71cea50014029628ee62cd154e1e81d5cd960932cce9b6',
    'staff',
    DM_ID
FROM T_DM
WHERE DM_ID NOT IN (SELECT COALESCE(Ref_ID, 0) FROM T_User WHERE Role = 'staff');

-- 重要：如果这些“演示账号”以前已经存在（可能密码不是 123456 或 Ref_ID 为空），这里统一纠正
UPDATE T_User
SET Password_Hash = 'default$697d423a3558f0ab2e71cea50014029628ee62cd154e1e81d5cd960932cce9b6'
WHERE Role = 'player' AND Username LIKE 'player\\_%';

UPDATE T_User u
JOIN T_Player p ON u.Username = CONCAT('player_', p.Player_ID)
SET u.Ref_ID = p.Player_ID,
    u.Role = 'player'
WHERE u.Username LIKE 'player\\_%' AND (u.Ref_ID IS NULL OR u.Ref_ID = 0);

UPDATE T_User
SET Password_Hash = 'default$697d423a3558f0ab2e71cea50014029628ee62cd154e1e81d5cd960932cce9b6'
WHERE Role = 'staff' AND Username LIKE 'staff\\_%';

UPDATE T_User u
JOIN T_DM d ON u.Username = CONCAT('staff_', d.DM_ID)
SET u.Ref_ID = d.DM_ID,
    u.Role = 'staff'
WHERE u.Username LIKE 'staff\\_%' AND (u.Ref_ID IS NULL OR u.Ref_ID = 0);

-- 为 T_Script 表添加封面图片字段（兼容 MySQL 5.7：用 information_schema 判断是否已存在）
SET @has_cover := (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'T_Script'
      AND COLUMN_NAME = 'Cover_Image'
);
SET @sql := IF(@has_cover = 0,
    "ALTER TABLE T_Script ADD COLUMN Cover_Image VARCHAR(255) DEFAULT 'default.jpg' COMMENT '封面图片路径'",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
SELECT IF(@has_cover = 0, 'OK: T_Script.Cover_Image added', 'SKIP: T_Script.Cover_Image already exists') AS Status;

-- 更新现有剧本的封面图片（按 Script_ID 映射；避免覆盖已有自定义值）
UPDATE T_Script
SET Cover_Image = CONCAT('script_', Script_ID, '.jpg')
WHERE Cover_Image IS NULL OR Cover_Image = '' OR Cover_Image = 'default.jpg';

/*==============================================================*/
/* 验证数据                                                      */
/*==============================================================*/
-- 查看创建的用户数量
SELECT Role, COUNT(*) as Count FROM T_User GROUP BY Role;

-- 验证演示账号：玩家/员工的默认密码均为 123456
SELECT Username, Role, Ref_ID, Phone
FROM T_User
WHERE Username IN ('player_3001', 'player_3005', 'staff_demo', '郝飞帆')
   OR Username LIKE 'player\\_%'
   OR Username LIKE 'staff\\_%'
ORDER BY Role, Username
LIMIT 30;

-- 查看剧本封面图片
SELECT Script_ID, Title, Cover_Image FROM T_Script LIMIT 5;
