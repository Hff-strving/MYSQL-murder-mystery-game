/*==============================================================*/
/* init_complete_system.sql                                     */
/* 目的：为演示环境补齐“员工登录 + 锁位过期清理 + 防重复预约索引”          */
/* 兼容：MySQL 5.7（不使用 DROP/CREATE INDEX IF EXISTS 语法）            */
/* 使用：mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source init_complete_system.sql" */
/*==============================================================*/

SET NAMES utf8mb4;

/*==================== 0) 扩展角色：增加 boss ====================*/
/* 说明：
   - 早期脚本里 Role 是 ENUM('player','staff')，这里扩展为 ENUM('player','staff','boss')
   - MySQL 5.7 不支持 IF NOT EXISTS，因此用 information_schema + PREPARE 做幂等 */
SET @role_type := (
  SELECT COLUMN_TYPE
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'T_User'
    AND COLUMN_NAME = 'Role'
);

SET @needs_boss := IF(@role_type IS NULL, 0, IF(LOCATE('boss', @role_type) > 0, 0, 1));
SET @sql := IF(@needs_boss = 1,
  'ALTER TABLE T_User MODIFY COLUMN Role ENUM(''player'',''staff'',''boss'') NOT NULL DEFAULT ''player''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
SELECT IF(@needs_boss = 1, 'OK: T_User.Role extended to include boss', 'SKIP: T_User.Role already supports boss (or table missing)') AS Status;

/*==================== 1) 创建可登录的演示员工账号 ====================*/
/* 说明：
   - 后端员工登录支持 `T_User(Role=staff, Password_Hash)` 与 `T_Staff_Account(Password)` 两种来源
   - 这里创建一个不依赖其它表的 `staff_demo`（写入 T_User），避免用户名/手机号冲突
   - 账号：staff_demo / 123456（或手机号 18800000000 / 123456）
*/
SET @salt := LOWER(REPLACE(UUID(), '-', ''));
SET @pwd := '123456';
SET @hash := LOWER(SHA2(CONCAT(@pwd, @salt), 256));

INSERT INTO T_User (Username, Phone, Password_Hash, Role, Ref_ID, Create_Time)
VALUES ('staff_demo', '18800000000', CONCAT(@salt, '$', @hash), 'staff', NULL, NOW())
ON DUPLICATE KEY UPDATE
  Password_Hash = VALUES(Password_Hash),
  Role = 'staff';

/* staff_demo 默认绑定一个 DM（否则“只能看自己订单”会无数据/无权限） */
SET @dm_id := (SELECT MIN(DM_ID) FROM T_DM);
UPDATE T_User
SET Ref_ID = @dm_id
WHERE Username = 'staff_demo' AND Role = 'staff' AND (@dm_id IS NOT NULL) AND (Ref_ID IS NULL OR Ref_ID = 0);

SELECT 'OK: staff_demo created/updated (password=123456)' AS Status;

/*==================== 1.0.1) 补齐 DM 对应的员工账号（可选） ====================*/
/* 说明：
   - 便于演示“每个员工只能看自己的订单/锁位/场次”
   - 账号：staff_<DM_ID> / 123456（也可用 DM 的手机号登录）
   - 使用固定哈希：salt=default，password=123456（与 auth_model.py 规则一致） */
INSERT IGNORE INTO T_User (Username, Phone, Password_Hash, Role, Ref_ID, Create_Time)
SELECT
  CONCAT('staff_', DM_ID),
  Phone,
  'default$697d423a3558f0ab2e71cea50014029628ee62cd154e1e81d5cd960932cce9b6',
  'staff',
  DM_ID,
  NOW()
FROM T_DM;

SELECT 'OK: staff_<DM_ID> accounts ensured (password=123456)' AS Status;

/*==================== 1.1) 创建老板账号（全局可见） ====================*/
/* 账号：郝飞帆 / 123456（或手机号 18800000001 / 123456） */
SET @salt := LOWER(REPLACE(UUID(), '-', ''));
SET @pwd := '123456';
SET @hash := LOWER(SHA2(CONCAT(@pwd, @salt), 256));

INSERT INTO T_User (Username, Phone, Password_Hash, Role, Ref_ID, Create_Time)
VALUES ('郝飞帆', '18800000001', CONCAT(@salt, '$', @hash), 'boss', NULL, NOW())
ON DUPLICATE KEY UPDATE
  Password_Hash = VALUES(Password_Hash),
  Role = 'boss';

SELECT 'OK: boss user 郝飞帆 created/updated (password=123456)' AS Status;

/*==================== 2) 锁位超时自动过期（可选） ====================*/
/* 注意：
   - 需要 MySQL event_scheduler 开启；若你没有权限开启 GLOBAL 变量，可以跳过
   - 本系统逻辑中：Locked_Count 只统计 Status=0 且 ExpireTime>NOW()，所以事件不是必需
*/
DROP EVENT IF EXISTS evt_expire_locks;

DELIMITER $$
CREATE EVENT evt_expire_locks
ON SCHEDULE EVERY 1 MINUTE
STARTS CURRENT_TIMESTAMP
DO
BEGIN
  UPDATE t_lock_record
  SET Status = 3
  WHERE Status = 0 AND ExpireTime < NOW();
END$$
DELIMITER ;

SELECT 'OK: evt_expire_locks created (requires event_scheduler=ON)' AS Status;

/*==================== 3) 防重复预约索引（演示用） ====================*/
/* 注意：
   - MySQL 5.7 不支持 ALTER TABLE ... DROP INDEX IF EXISTS
   - 你的库里 UK_Player_Schedule 可能被外键依赖（用于约束/索引 Player_ID、Schedule_ID），强行 DROP 会报：
       ERROR 1553: Cannot drop index ... needed in a foreign key constraint
   - 因此这里改为：如果不存在则创建；如果已存在则跳过，不做 DROP。*/
SET @idx_exists := (
  SELECT COUNT(*)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'T_Order'
    AND INDEX_NAME = 'UK_Player_Schedule'
);

SET @sql := IF(@idx_exists = 0,
  'ALTER TABLE T_Order ADD UNIQUE INDEX UK_Player_Schedule (Player_ID, Schedule_ID, Pay_Status)',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT IF(@idx_exists = 0, 'OK: UK_Player_Schedule created', 'SKIP: UK_Player_Schedule already exists (kept for FK)') AS Status;

/*==================== 3.1) 触发器：防重复预约/锁位（演示用） ====================*/
/* 说明：
   - 后端已经做了重复校验；这里用触发器把规则下沉到数据库层，便于写“触发器/约束”报告
   - 触发器可重复执行：先 DROP 再 CREATE */

DROP TRIGGER IF EXISTS trg_prevent_duplicate_order;
DELIMITER $$
CREATE TRIGGER trg_prevent_duplicate_order
BEFORE INSERT ON T_Order
FOR EACH ROW
BEGIN
  IF EXISTS (
    SELECT 1 FROM T_Order
    WHERE Player_ID = NEW.Player_ID
      AND Schedule_ID = NEW.Schedule_ID
      AND Pay_Status IN (0, 1)
    LIMIT 1
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '您已经预约过该场次，请勿重复预约';
  END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trg_prevent_duplicate_lock;
DELIMITER $$
CREATE TRIGGER trg_prevent_duplicate_lock
BEFORE INSERT ON t_lock_record
FOR EACH ROW
BEGIN
  IF EXISTS (
    SELECT 1 FROM t_lock_record
    WHERE Player_ID = NEW.Player_ID
      AND Schedule_ID = NEW.Schedule_ID
      AND Status = 0
    LIMIT 1
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '您已经锁定过该场次';
  END IF;

  IF NEW.ExpireTime IS NULL THEN
    SET NEW.ExpireTime = DATE_ADD(NOW(), INTERVAL 15 MINUTE);
  END IF;
END$$
DELIMITER ;

SELECT 'OK: triggers created (duplicate order/lock prevention)' AS Status;

/*==================== 3.2) 视图 + 存储过程 + 函数（演示用） ====================*/
/* 说明：
   - 用于报告中“视图/存储过程/函数”的展示
   - 不强依赖后端代码，但可在 MySQL 中直接调用验证 */

DROP VIEW IF EXISTS v_order_detail;
CREATE VIEW v_order_detail AS
SELECT
  o.Order_ID, o.Player_ID, o.Schedule_ID, o.Amount, o.Pay_Status, o.Create_Time,
  sch.Start_Time, sch.End_Time, sch.Status AS Schedule_Status,
  r.Room_ID, r.Room_Name,
  d.DM_ID, d.Name AS DM_Name,
  sc.Script_ID, sc.Title AS Script_Title
FROM T_Order o
JOIN T_Schedule sch ON o.Schedule_ID = sch.Schedule_ID
JOIN T_Room r ON sch.Room_ID = r.Room_ID
JOIN T_DM d ON sch.DM_ID = d.DM_ID
JOIN T_Script sc ON sch.Script_ID = sc.Script_ID;

DROP VIEW IF EXISTS v_lock_detail;
CREATE VIEW v_lock_detail AS
SELECT
  l.LockID, l.Schedule_ID, l.Player_ID, l.LockTime, l.ExpireTime, l.Status,
  sch.Start_Time, sch.End_Time, sch.Status AS Schedule_Status,
  r.Room_ID, r.Room_Name,
  d.DM_ID, d.Name AS DM_Name,
  sc.Script_ID, sc.Title AS Script_Title
FROM t_lock_record l
JOIN T_Schedule sch ON l.Schedule_ID = sch.Schedule_ID
JOIN T_Room r ON sch.Room_ID = r.Room_ID
JOIN T_DM d ON sch.DM_ID = d.DM_ID
JOIN T_Script sc ON sch.Script_ID = sc.Script_ID;

DROP PROCEDURE IF EXISTS sp_dm_orders;
DELIMITER $$
CREATE PROCEDURE sp_dm_orders(IN p_dm_id BIGINT)
BEGIN
  SELECT *
  FROM v_order_detail
  WHERE (p_dm_id IS NULL OR DM_ID = p_dm_id)
  ORDER BY Create_Time DESC;
END$$
DELIMITER ;

DROP PROCEDURE IF EXISTS sp_dm_locks;
DELIMITER $$
CREATE PROCEDURE sp_dm_locks(IN p_dm_id BIGINT)
BEGIN
  SELECT *
  FROM v_lock_detail
  WHERE (p_dm_id IS NULL OR DM_ID = p_dm_id)
  ORDER BY LockTime DESC;
END$$
DELIMITER ;

DROP FUNCTION IF EXISTS fn_schedule_occupied;
DELIMITER $$
CREATE FUNCTION fn_schedule_occupied(p_schedule_id BIGINT)
RETURNS INT
DETERMINISTIC
BEGIN
  DECLARE booked INT DEFAULT 0;
  DECLARE locked INT DEFAULT 0;
  SELECT COUNT(*) INTO booked
  FROM T_Order o
  WHERE o.Schedule_ID = p_schedule_id AND o.Pay_Status IN (0, 1);

  SELECT COUNT(*) INTO locked
  FROM t_lock_record l
  WHERE l.Schedule_ID = p_schedule_id AND l.Status = 0 AND l.ExpireTime > NOW();

  RETURN booked + locked;
END$$
DELIMITER ;

SELECT 'OK: views/procs/functions created (v_order_detail, v_lock_detail, sp_dm_orders, sp_dm_locks, fn_schedule_occupied)' AS Status;

/*==================== 4) 结束校验 ====================*/
SELECT Username, Phone, Role, Ref_ID
FROM T_User
WHERE Username IN ('staff_demo', '郝飞帆')
   OR Phone IN ('18800000000', '18800000001');
