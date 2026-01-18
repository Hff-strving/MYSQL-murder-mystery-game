# -*- coding: utf-8 -*-
"""
场次模型 - 处理场次相关的业务逻辑
"""

from database import SafeDatabase
from security_utils import InputValidator
import logging

logger = logging.getLogger(__name__)


class ScheduleModel:
    """场次模型类"""

    @staticmethod
    def get_schedules_by_script(script_id, player_id=None):
        """
        获取指定剧本的未来场次列表（支持查询玩家预约状态）

        Args:
            script_id: 剧本ID
            player_id: 玩家ID（可选，用于查询该玩家是否已预约）

        Returns:
            场次列表（包含 User_Booked 字段表示当前玩家是否已预约）
        """
        try:
            script_id = InputValidator.validate_id(script_id, "剧本ID")

            # 基础查询
            sql = """
                SELECT
                    sch.Schedule_ID,
                    sch.Start_Time,
                    sch.End_Time,
                    sch.Status,
                    sch.Real_Price,
                    r.Room_Name,
                    d.Name AS DM_Name,
                    s.Title AS Script_Title,
                    s.Max_Players,
                    (SELECT COUNT(*) FROM T_Order o
                     WHERE o.Schedule_ID = sch.Schedule_ID
                     AND o.Pay_Status IN (0, 1)) AS Booked_Count,
                    (SELECT COUNT(*) FROM t_lock_record l
                     WHERE l.Schedule_ID = sch.Schedule_ID
                     AND l.Status = 0
                     AND l.ExpireTime > NOW()) AS Locked_Count
            """

            # 如果提供了玩家ID，添加该玩家的预约状态查询
            if player_id:
                sql += """,
                    (SELECT COUNT(*) FROM T_Order o
                     WHERE o.Schedule_ID = sch.Schedule_ID
                     AND o.Player_ID = %s
                     AND o.Pay_Status IN (0, 1)) AS User_Booked
                """
                sql += """,
                    (SELECT COUNT(*) FROM t_lock_record l
                     WHERE l.Schedule_ID = sch.Schedule_ID
                     AND l.Player_ID = %s
                     AND l.Status = 0
                     AND l.ExpireTime > NOW()) AS User_Locked
                """

            sql += """
                FROM T_Schedule sch
                JOIN T_Room r ON sch.Room_ID = r.Room_ID
                JOIN T_DM d ON sch.DM_ID = d.DM_ID
                JOIN T_Script s ON sch.Script_ID = s.Script_ID
                WHERE sch.Script_ID = %s
                AND sch.Start_Time > NOW()
                AND sch.Status IN (0, 1)
                ORDER BY sch.Start_Time
            """

            # 根据是否有玩家ID决定参数（User_Booked + User_Locked 都需要 player_id）
            params = (player_id, player_id, script_id) if player_id else (script_id,)
            schedules = SafeDatabase.execute_query(sql, params)
            logger.info(f"查询剧本场次成功: Script_ID={script_id}, 返回{len(schedules)}条")
            return schedules

        except Exception as e:
            logger.error(f"查询剧本场次失败: {str(e)}")
            raise

    @staticmethod
    def get_all_schedules(date=None, room_id=None, script_id=None, status=None, dm_id=None):
        """
        获取所有场次列表（员工管理用）

        Args:
            date: 日期筛选（YYYY-MM-DD）
            room_id: 房间ID筛选
            script_id: 剧本ID筛选
            status: 状态筛选

        Returns:
            场次列表
        """
        try:
            sql = """
                SELECT
                    sch.Schedule_ID,
                    sch.Start_Time,
                    sch.End_Time,
                    sch.Status,
                    sch.Real_Price,
                    r.Room_ID,
                    r.Room_Name,
                    d.DM_ID,
                    d.Name AS DM_Name,
                    s.Script_ID,
                    s.Title AS Script_Title,
                    s.Max_Players,
                    (SELECT COUNT(*) FROM T_Order o
                     WHERE o.Schedule_ID = sch.Schedule_ID
                     AND o.Pay_Status IN (0, 1)) AS Booked_Count,
                    (SELECT COUNT(*) FROM t_lock_record l
                     WHERE l.Schedule_ID = sch.Schedule_ID
                     AND l.Status = 0
                     AND l.ExpireTime > NOW()) AS Locked_Count
                FROM T_Schedule sch
                JOIN T_Room r ON sch.Room_ID = r.Room_ID
                JOIN T_DM d ON sch.DM_ID = d.DM_ID
                JOIN T_Script s ON sch.Script_ID = s.Script_ID
                WHERE 1=1
            """

            params = []

            if date:
                sql += " AND DATE(sch.Start_Time) = %s"
                params.append(date)

            if room_id:
                sql += " AND sch.Room_ID = %s"
                params.append(room_id)

            if script_id:
                sql += " AND sch.Script_ID = %s"
                params.append(script_id)

            if status is not None:
                sql += " AND sch.Status = %s"
                params.append(status)

            if dm_id is not None:
                sql += " AND sch.DM_ID = %s"
                params.append(dm_id)

            sql += " ORDER BY sch.Start_Time DESC"

            schedules = SafeDatabase.execute_query(sql, tuple(params))
            logger.info(f"查询所有场次成功，返回{len(schedules)}条")
            return schedules

        except Exception as e:
            logger.error(f"查询所有场次失败: {str(e)}")
            raise

    @staticmethod
    def create_schedule(script_id, room_id, dm_id, start_time, end_time, real_price):
        """
        创建新场次

        Args:
            script_id: 剧本ID
            room_id: 房间ID
            dm_id: DM ID
            start_time: 开始时间
            end_time: 结束时间
            real_price: 实际价格

        Returns:
            新场次ID
        """
        try:
            script_id = InputValidator.validate_id(script_id, "剧本ID")
            room_id = InputValidator.validate_id(room_id, "房间ID")
            dm_id = InputValidator.validate_id(dm_id, "DM ID")

            sql = """
                INSERT INTO T_Schedule (Script_ID, Room_ID, DM_ID, Start_Time, End_Time, Real_Price, Status)
                VALUES (%s, %s, %s, %s, %s, %s, 0)
            """

            schedule_id = SafeDatabase.execute_update(
                sql,
                (script_id, room_id, dm_id, start_time, end_time, real_price)
            )

            logger.info(f"创建场次成功: Schedule_ID={schedule_id}")
            return schedule_id

        except Exception as e:
            logger.error(f"创建场次失败: {str(e)}")
            raise

    @staticmethod
    def update_schedule(schedule_id, script_id=None, room_id=None, dm_id=None,
                       start_time=None, end_time=None, real_price=None, status=None):
        """
        更新场次信息

        Args:
            schedule_id: 场次ID
            其他参数: 需要更新的字段（可选）

        Returns:
            影响的行数
        """
        try:
            schedule_id = InputValidator.validate_id(schedule_id, "场次ID")

            updates = []
            params = []

            if script_id is not None:
                updates.append("Script_ID = %s")
                params.append(script_id)

            if room_id is not None:
                updates.append("Room_ID = %s")
                params.append(room_id)

            if dm_id is not None:
                updates.append("DM_ID = %s")
                params.append(dm_id)

            if start_time is not None:
                updates.append("Start_Time = %s")
                params.append(start_time)

            if end_time is not None:
                updates.append("End_Time = %s")
                params.append(end_time)

            if real_price is not None:
                updates.append("Real_Price = %s")
                params.append(real_price)

            if status is not None:
                updates.append("Status = %s")
                params.append(status)

            if not updates:
                raise ValueError("没有需要更新的字段")

            params.append(schedule_id)
            sql = f"UPDATE T_Schedule SET {', '.join(updates)} WHERE Schedule_ID = %s"

            affected = SafeDatabase.execute_update(sql, tuple(params))
            logger.info(f"更新场次成功: Schedule_ID={schedule_id}")
            return affected

        except Exception as e:
            logger.error(f"更新场次失败: {str(e)}")
            raise

    @staticmethod
    def cancel_schedule(schedule_id):
        """
        取消场次（设置状态为2-已取消）

        Args:
            schedule_id: 场次ID

        Returns:
            影响的行数
        """
        try:
            schedule_id = InputValidator.validate_id(schedule_id, "场次ID")

            # 检查是否有已支付的订单
            check_sql = """
                SELECT COUNT(*) as paid_count
                FROM T_Order
                WHERE Schedule_ID = %s AND Pay_Status = 1
            """
            result = SafeDatabase.execute_query(check_sql, (schedule_id,), fetch_one=True)

            if result['paid_count'] > 0:
                raise ValueError("该场次有已支付订单，无法取消")

            sql = "UPDATE T_Schedule SET Status = 2 WHERE Schedule_ID = %s"
            affected = SafeDatabase.execute_update(sql, (schedule_id,))

            logger.info(f"取消场次成功: Schedule_ID={schedule_id}")
            return affected

        except Exception as e:
            logger.error(f"取消场次失败: {str(e)}")
            raise
