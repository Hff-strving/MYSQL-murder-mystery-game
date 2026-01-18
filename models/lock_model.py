# -*- coding: utf-8 -*-
"""
锁位模型 - 处理场次锁位逻辑
"""

from database import SafeDatabase
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class LockModel:
    """锁位模型类"""

    @staticmethod
    def create_lock(player_id, schedule_id, lock_minutes=15):
        """
        创建锁位记录

        Args:
            player_id: 玩家ID
            schedule_id: 场次ID
            lock_minutes: 锁定时长（分钟），默认15分钟

        Returns:
            lock_id: 锁位记录ID
        """
        try:
            # 检查该玩家是否已经锁定了这个场次
            check_sql = """
                SELECT LockID FROM t_lock_record
                WHERE Player_ID=%s AND Schedule_ID=%s AND Status=0
            """
            existing = SafeDatabase.execute_query(check_sql, (player_id, schedule_id), fetch_one=True)
            if existing:
                raise ValueError("您已经锁定了该场次")

            # 检查场次是否已满（包括已锁定的位置）
            capacity_sql = """
                SELECT
                    sc.Max_Players,
                    COUNT(DISTINCT o.Order_ID) as booked_count,
                    COUNT(DISTINCT l.LockID) as locked_count
                FROM T_Schedule s
                JOIN T_Script sc ON s.Script_ID = sc.Script_ID
                LEFT JOIN T_Order o ON s.Schedule_ID = o.Schedule_ID AND o.Pay_Status IN (0, 1)
                LEFT JOIN t_lock_record l ON s.Schedule_ID = l.Schedule_ID AND l.Status = 0 AND l.ExpireTime > NOW()
                WHERE s.Schedule_ID = %s
                GROUP BY s.Schedule_ID, sc.Max_Players
            """
            capacity = SafeDatabase.execute_query(capacity_sql, (schedule_id,), fetch_one=True)

            if not capacity:
                raise ValueError("场次不存在")

            total_occupied = (capacity.get('booked_count') or 0) + (capacity.get('locked_count') or 0)
            if total_occupied >= capacity['Max_Players']:
                raise ValueError("该场次已满")

            # 计算过期时间
            expire_time = datetime.now() + timedelta(minutes=lock_minutes)

            # 生成新的 LockID（表无自增）
            new_id_sql = "SELECT IFNULL(MAX(LockID), 7000) + 1 AS new_id FROM t_lock_record"
            new_id = SafeDatabase.execute_query(new_id_sql, fetch_one=True)['new_id']

            # 创建锁位记录（使用旧表字段名）
            insert_sql = """
                INSERT INTO t_lock_record
                (LockID, Schedule_ID, Player_ID, LockTime, ExpireTime, Status)
                VALUES (%s, %s, %s, NOW(), %s, 0)
            """
            SafeDatabase.execute_update(insert_sql, (new_id, schedule_id, player_id, expire_time))

            logger.info(f"创建锁位成功: LockID={new_id}, Player_ID={player_id}, Schedule_ID={schedule_id}")
            return new_id

        except Exception as e:
            logger.error(f"创建锁位失败: {str(e)}")
            raise

    @staticmethod
    def cancel_lock(lock_id, player_id):
        """
        取消锁位

        Args:
            lock_id: 锁位记录ID
            player_id: 玩家ID（用于验证权限）

        Returns:
            bool: 是否成功
        """
        try:
            # 验证锁位归属
            check_sql = "SELECT Player_ID, Status FROM t_lock_record WHERE LockID=%s"
            lock = SafeDatabase.execute_query(check_sql, (lock_id,), fetch_one=True)

            if not lock:
                raise ValueError("锁位记录不存在")

            if lock['Player_ID'] != player_id:
                raise ValueError("无权取消他人的锁位")

            if lock['Status'] != 0:
                raise ValueError("该锁位已失效")

            # 更新状态为已释放
            update_sql = "UPDATE t_lock_record SET Status=2 WHERE LockID=%s"
            SafeDatabase.execute_update(update_sql, (lock_id,))

            logger.info(f"取消锁位成功: Lock_ID={lock_id}")
            return True

        except Exception as e:
            logger.error(f"取消锁位失败: {str(e)}")
            raise

    @staticmethod
    def get_locks_by_player(player_id):
        """获取玩家的锁位记录"""
        try:
            sql = """
                SELECT
                    l.LockID, l.Schedule_ID, l.LockTime, l.ExpireTime, l.Status,
                    sc.Title as Script_Title, s.Start_Time, r.Room_Name,
                    d.DM_ID, d.Name AS DM_Name
                FROM t_lock_record l
                JOIN T_Schedule s ON l.Schedule_ID = s.Schedule_ID
                JOIN T_Script sc ON s.Script_ID = sc.Script_ID
                JOIN T_Room r ON s.Room_ID = r.Room_ID
                JOIN T_DM d ON s.DM_ID = d.DM_ID
                WHERE l.Player_ID = %s
                ORDER BY l.LockTime DESC
            """
            locks = SafeDatabase.execute_query(sql, (player_id,))
            return locks if locks else []
        except Exception as e:
            logger.error(f"查询玩家锁位失败: {str(e)}")
            raise

    @staticmethod
    def get_all_locks(dm_id=None):
        """
        获取锁位记录（员工/老板用）

        Args:
            dm_id: 可选，DM_ID 分域（staff 传入后仅返回自己 DM 的锁位）
        """
        try:
            sql = """
                SELECT
                    l.LockID, l.Schedule_ID, l.Player_ID, l.LockTime,
                    l.ExpireTime, l.Status,
                    p.Nickname as Player_Name, sc.Title as Script_Title,
                    s.Start_Time, r.Room_Name,
                    d.DM_ID, d.Name AS DM_Name
                FROM t_lock_record l
                JOIN T_Player p ON l.Player_ID = p.Player_ID
                JOIN T_Schedule s ON l.Schedule_ID = s.Schedule_ID
                JOIN T_Script sc ON s.Script_ID = sc.Script_ID
                JOIN T_Room r ON s.Room_ID = r.Room_ID
                JOIN T_DM d ON s.DM_ID = d.DM_ID
                WHERE 1=1
            """

            params = []
            if dm_id is not None:
                sql += " AND s.DM_ID = %s"
                params.append(dm_id)

            sql += " ORDER BY l.LockTime DESC"

            locks = SafeDatabase.execute_query(sql, tuple(params) if params else None)
            return locks if locks else []
        except Exception as e:
            logger.error(f"查询锁位失败: {str(e)}")
            raise
