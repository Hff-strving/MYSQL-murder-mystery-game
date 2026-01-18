-- ============================================================
-- ?????? SQL ???MySQL 5.7 ???
-- ??????? mysql -D ????????????? USE?
-- ============================================================

-- 1) ???????MySQL 5.7 ??? CREATE INDEX IF NOT EXISTS?
SET @idx_exists := (
  SELECT COUNT(*)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 't_lock_record'
    AND INDEX_NAME = 'idx_lock_expire'
);
SET @sql := IF(@idx_exists = 0,
  'CREATE INDEX idx_lock_expire ON t_lock_record (Status, ExpireTime)',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
  SELECT COUNT(*)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 't_lock_record'
    AND INDEX_NAME = 'idx_lock_schedule'
);
SET @sql := IF(@idx_exists = 0,
  'CREATE INDEX idx_lock_schedule ON t_lock_record (Schedule_ID, Status)',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'OK: lock indexes ensured' AS Status;

-- 2) ???????????????
INSERT IGNORE INTO t_lock_record (LockID, Schedule_ID, Player_ID, LockTime, ExpireTime, Status) VALUES
(6001, 4011, 3011, '2025-12-29 10:30:00', '2025-12-29 10:45:00', 0),
(6002, 4011, 3012, '2025-12-29 10:32:00', '2025-12-29 10:47:00', 0),
(6003, 4012, 3013, '2025-12-29 11:00:00', '2025-12-29 11:15:00', 0);

SELECT 'OK: demo locks inserted' AS Status;
