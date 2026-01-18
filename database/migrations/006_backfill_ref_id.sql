/*==============================================================
  006_backfill_ref_id.sql
  作用：为 T_User(Role='player') 且 Ref_ID 为空/0 的旧账号补齐玩家档案并回填 Ref_ID

  背景：
  - 新版注册流程会在同一事务里创建 T_Player 并回填 T_User.Ref_ID
  - 但历史数据可能存在 Ref_ID 为空的玩家账号，导致“用户信息不完整/仅限玩家”等问题

  特性：
  - 兼容 MySQL 5.7
  - 可重复执行（对已补齐的数据无副作用）
==============================================================*/

SET NAMES utf8mb4;

START TRANSACTION;

-- 1) 计算 Player_ID 起始值（从当前最大值继续递增）
SET @max_pid := (SELECT IFNULL(MAX(Player_ID), 3000) FROM T_Player);

-- 2) 收集需要补齐的用户到临时表，并分配新的 Player_ID
DROP TEMPORARY TABLE IF EXISTS tmp_backfill_players;
CREATE TEMPORARY TABLE tmp_backfill_players AS
SELECT
  u.User_ID,
  (@max_pid := @max_pid + 1) AS Player_ID,
  u.Username AS Nickname,
  CASE
    WHEN u.Phone IS NULL OR u.Phone = '' THEN CONCAT('139', LPAD(u.User_ID, 8, '0'))
    WHEN EXISTS (SELECT 1 FROM T_Player p WHERE p.Phone = u.Phone) THEN CONCAT('139', LPAD(u.User_ID, 8, '0'))
    ELSE u.Phone
  END AS Phone
FROM T_User u
WHERE u.Role = 'player' AND (u.Ref_ID IS NULL OR u.Ref_ID = 0)
ORDER BY u.User_ID;

-- 3) 插入缺失的玩家档案
INSERT INTO T_Player (Player_ID, Open_ID, Nickname, Phone)
SELECT
  t.Player_ID,
  CONCAT('web_', REPLACE(UUID(), '-', '')),
  t.Nickname,
  t.Phone
FROM tmp_backfill_players t
LEFT JOIN T_Player p ON p.Player_ID = t.Player_ID
WHERE p.Player_ID IS NULL;

-- 4) 回填 Ref_ID
UPDATE T_User u
JOIN tmp_backfill_players t ON u.User_ID = t.User_ID
SET u.Ref_ID = t.Player_ID
WHERE u.Role = 'player' AND (u.Ref_ID IS NULL OR u.Ref_ID = 0);

COMMIT;

-- 5) 校验：仍然 Ref_ID 为空的玩家
SELECT User_ID, Username, Role, Ref_ID
FROM T_User
WHERE Role = 'player' AND (Ref_ID IS NULL OR Ref_ID = 0);

