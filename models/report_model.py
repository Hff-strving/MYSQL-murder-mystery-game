# -*- coding: utf-8 -*-
"""
报表模型 - 处理统计报表相关的业务逻辑
"""

from database import SafeDatabase
import logging

logger = logging.getLogger(__name__)


class ReportModel:
    """报表模型类"""

    @staticmethod
    def get_dashboard_stats(dm_id=None):
        """
        获取仪表盘统计数据

        Returns:
            包含今日、本周、本月营收和订单数的统计数据
        """
        try:
            sql = """
                SELECT
                    COALESCE(SUM(CASE WHEN DATE(t.Trans_Time) = CURDATE() THEN t.Amount ELSE 0 END), 0) AS today_revenue,
                    COUNT(CASE WHEN DATE(t.Trans_Time) = CURDATE() THEN 1 END) AS today_orders,

                    COALESCE(SUM(CASE WHEN YEARWEEK(t.Trans_Time, 1) = YEARWEEK(CURDATE(), 1) THEN t.Amount ELSE 0 END), 0) AS week_revenue,
                    COUNT(CASE WHEN YEARWEEK(t.Trans_Time, 1) = YEARWEEK(CURDATE(), 1) THEN 1 END) AS week_orders,

                    COALESCE(SUM(CASE WHEN DATE_FORMAT(t.Trans_Time, '%%Y-%%m') = DATE_FORMAT(CURDATE(), '%%Y-%%m') THEN t.Amount ELSE 0 END), 0) AS month_revenue,
                    COUNT(CASE WHEN DATE_FORMAT(t.Trans_Time, '%%Y-%%m') = DATE_FORMAT(CURDATE(), '%%Y-%%m') THEN 1 END) AS month_orders
                FROM T_Transaction t
                JOIN T_Order o ON t.Order_ID = o.Order_ID
                JOIN T_Schedule sch ON o.Schedule_ID = sch.Schedule_ID
                WHERE t.Trans_Type = 1 AND t.Result = 1
            """

            params = []
            if dm_id is not None:
                sql += " AND sch.DM_ID = %s"
                params.append(dm_id)

            stats = SafeDatabase.execute_query(sql, tuple(params) if params else None, fetch_one=True) or {}

            # 活跃锁位数（未过期）
            lock_sql = """
                SELECT COUNT(*) AS active_locks
                FROM t_lock_record l
                JOIN T_Schedule sch ON l.Schedule_ID = sch.Schedule_ID
                WHERE l.Status = 0 AND l.ExpireTime > NOW()
            """
            lock_params = []
            if dm_id is not None:
                lock_sql += " AND sch.DM_ID = %s"
                lock_params.append(dm_id)
            lock_row = SafeDatabase.execute_query(lock_sql, tuple(lock_params) if lock_params else None, fetch_one=True) or {}
            stats['active_locks'] = lock_row.get('active_locks', 0)

            # 未来7天上座率（预约+锁位 / 容量）
            occ_sql = """
                SELECT
                    COALESCE(SUM(t.occupied), 0) AS occupied,
                    COALESCE(SUM(t.capacity), 0) AS capacity
                FROM (
                    SELECT
                        sch.Schedule_ID,
                        sch.DM_ID,
                        sc.Max_Players AS capacity,
                        (SELECT COUNT(*) FROM T_Order o
                         WHERE o.Schedule_ID = sch.Schedule_ID AND o.Pay_Status IN (0, 1)) +
                        (SELECT COUNT(*) FROM t_lock_record l
                         WHERE l.Schedule_ID = sch.Schedule_ID AND l.Status = 0 AND l.ExpireTime > NOW()) AS occupied
                    FROM T_Schedule sch
                    JOIN T_Script sc ON sch.Script_ID = sc.Script_ID
                    WHERE sch.Start_Time >= NOW()
                      AND sch.Start_Time < DATE_ADD(NOW(), INTERVAL 7 DAY)
                      AND sch.Status IN (0, 1)
                ) t
                WHERE 1=1
            """
            occ_params = []
            if dm_id is not None:
                occ_sql += " AND t.DM_ID = %s"
                occ_params.append(dm_id)
            occ = SafeDatabase.execute_query(occ_sql, tuple(occ_params) if occ_params else None, fetch_one=True) or {}
            occupied = float(occ.get('occupied', 0) or 0)
            capacity = float(occ.get('capacity', 0) or 0)
            stats['occupancy_rate'] = round((occupied / capacity) * 100, 2) if capacity > 0 else 0.0

            # 最近订单（10条）
            recent_sql = """
                SELECT
                    o.Order_ID, o.Amount, o.Pay_Status, o.Create_Time,
                    sc.Title AS Script_Title,
                    sch.Start_Time,
                    r.Room_Name,
                    d.DM_ID, d.Name AS DM_Name
                FROM T_Order o
                JOIN T_Schedule sch ON o.Schedule_ID = sch.Schedule_ID
                JOIN T_Script sc ON sch.Script_ID = sc.Script_ID
                JOIN T_Room r ON sch.Room_ID = r.Room_ID
                JOIN T_DM d ON sch.DM_ID = d.DM_ID
                WHERE 1=1
            """
            recent_params = []
            if dm_id is not None:
                recent_sql += " AND sch.DM_ID = %s"
                recent_params.append(dm_id)
            recent_sql += " ORDER BY o.Create_Time DESC LIMIT 10"
            stats['recent_orders'] = SafeDatabase.execute_query(recent_sql, tuple(recent_params) if recent_params else None) or []

            # 即将开始的场次（10条）
            up_sql = """
                SELECT
                    sch.Schedule_ID,
                    sch.Start_Time,
                    sch.End_Time,
                    sch.Status,
                    sch.Real_Price,
                    r.Room_Name,
                    d.DM_ID, d.Name AS DM_Name,
                    sc.Script_ID,
                    sc.Title AS Script_Title,
                    sc.Max_Players,
                    (SELECT COUNT(*) FROM T_Order o
                     WHERE o.Schedule_ID = sch.Schedule_ID AND o.Pay_Status IN (0, 1)) AS Booked_Count,
                    (SELECT COUNT(*) FROM t_lock_record l
                     WHERE l.Schedule_ID = sch.Schedule_ID AND l.Status = 0 AND l.ExpireTime > NOW()) AS Locked_Count
                FROM T_Schedule sch
                JOIN T_Room r ON sch.Room_ID = r.Room_ID
                JOIN T_DM d ON sch.DM_ID = d.DM_ID
                JOIN T_Script sc ON sch.Script_ID = sc.Script_ID
                WHERE sch.Start_Time > NOW() AND sch.Status IN (0, 1)
            """
            up_params = []
            if dm_id is not None:
                up_sql += " AND sch.DM_ID = %s"
                up_params.append(dm_id)
            up_sql += " ORDER BY sch.Start_Time LIMIT 10"
            stats['upcoming_schedules'] = SafeDatabase.execute_query(up_sql, tuple(up_params) if up_params else None) or []

            logger.info("查询仪表盘统计成功")
            return stats

        except Exception as e:
            logger.error(f"查询仪表盘统计失败: {str(e)}")
            raise

    @staticmethod
    def get_top_scripts(start_date=None, end_date=None, limit=5, dm_id=None):
        """
        获取热门剧本Top N

        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量

        Returns:
            热门剧本列表
        """
        try:
            sql = """
                SELECT
                    s.Script_ID,
                    s.Title,
                    s.Cover_Image,
                    COUNT(CASE WHEN o.Pay_Status IN (0, 1) THEN 1 END) AS order_count,
                    COALESCE(SUM(CASE WHEN o.Pay_Status = 1 THEN o.Amount ELSE 0 END), 0) AS total_revenue
                FROM T_Script s
                LEFT JOIN T_Schedule sch ON s.Script_ID = sch.Script_ID
                LEFT JOIN T_Order o ON sch.Schedule_ID = o.Schedule_ID
                WHERE 1=1
            """

            params = []

            if start_date:
                sql += " AND DATE(o.Create_Time) >= %s"
                params.append(start_date)

            if end_date:
                sql += " AND DATE(o.Create_Time) <= %s"
                params.append(end_date)

            if dm_id is not None:
                sql += " AND sch.DM_ID = %s"
                params.append(dm_id)

            sql += """
                GROUP BY s.Script_ID, s.Title, s.Cover_Image
                ORDER BY order_count DESC, total_revenue DESC
                LIMIT %s
            """
            params.append(limit)

            scripts = SafeDatabase.execute_query(sql, tuple(params))
            logger.info(f"查询热门剧本成功，返回{len(scripts)}条")
            return scripts

        except Exception as e:
            logger.error(f"查询热门剧本失败: {str(e)}")
            raise

    @staticmethod
    def get_room_utilization(start_date=None, end_date=None, dm_id=None):
        """
        获取房间利用率统计

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            房间利用率列表
        """
        try:
            sql = """
                SELECT
                    r.Room_ID,
                    r.Room_Name,
                    COUNT(DISTINCT sch.Schedule_ID) AS total_schedules,
                    COUNT(DISTINCT CASE WHEN sch.Status = 1 THEN sch.Schedule_ID END) AS completed_schedules,
                    COUNT(DISTINCT CASE WHEN o.Pay_Status = 1 THEN o.Order_ID END) AS paid_orders,
                    ROUND(
                        CASE
                            WHEN COUNT(DISTINCT sch.Schedule_ID) > 0
                            THEN (COUNT(DISTINCT CASE WHEN sch.Status = 1 THEN sch.Schedule_ID END) * 100.0 / COUNT(DISTINCT sch.Schedule_ID))
                            ELSE 0
                        END, 2
                    ) AS utilization_rate
                FROM T_Room r
                LEFT JOIN T_Schedule sch ON r.Room_ID = sch.Room_ID
                LEFT JOIN T_Order o ON sch.Schedule_ID = o.Schedule_ID
                WHERE 1=1
            """

            params = []

            if start_date:
                sql += " AND DATE(sch.Start_Time) >= %s"
                params.append(start_date)

            if end_date:
                sql += " AND DATE(sch.Start_Time) <= %s"
                params.append(end_date)

            if dm_id is not None:
                sql += " AND sch.DM_ID = %s"
                params.append(dm_id)

            sql += """
                GROUP BY r.Room_ID, r.Room_Name
                ORDER BY utilization_rate DESC
            """

            rooms = SafeDatabase.execute_query(sql, tuple(params) if params else None)
            logger.info(f"查询房间利用率成功，返回{len(rooms)}条")
            return rooms

        except Exception as e:
            logger.error(f"查询房间利用率失败: {str(e)}")
            raise

    @staticmethod
    def get_lock_conversion_rate(start_date=None, end_date=None, dm_id=None):
        """
        获取锁位转化率统计

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            锁位转化率数据
        """
        try:
            sql = """
                SELECT
                    COUNT(DISTINCT l.LockID) AS total_locks,
                    COUNT(DISTINCT CASE WHEN l.Status = 1 THEN l.LockID END) AS converted_locks,
                    COUNT(DISTINCT o.Order_ID) AS total_orders,
                    COUNT(DISTINCT CASE WHEN o.Pay_Status = 1 THEN o.Order_ID END) AS paid_orders,
                    ROUND(
                        CASE
                            WHEN COUNT(DISTINCT l.LockID) > 0
                            THEN (COUNT(DISTINCT CASE WHEN l.Status = 1 THEN l.LockID END) * 100.0 / COUNT(DISTINCT l.LockID))
                            ELSE 0
                        END, 2
                    ) AS lock_to_order_rate,
                    ROUND(
                        CASE
                            WHEN COUNT(DISTINCT o.Order_ID) > 0
                            THEN (COUNT(DISTINCT CASE WHEN o.Pay_Status = 1 THEN o.Order_ID END) * 100.0 / COUNT(DISTINCT o.Order_ID))
                            ELSE 0
                        END, 2
                    ) AS order_to_pay_rate
                FROM t_lock_record l
                LEFT JOIN T_Order o ON l.Schedule_ID = o.Schedule_ID AND l.Player_ID = o.Player_ID
                LEFT JOIN T_Schedule sch ON l.Schedule_ID = sch.Schedule_ID
                WHERE 1=1
            """

            params = []

            if start_date:
                sql += " AND DATE(l.LockTime) >= %s"
                params.append(start_date)

            if end_date:
                sql += " AND DATE(l.LockTime) <= %s"
                params.append(end_date)

            if dm_id is not None:
                sql += " AND sch.DM_ID = %s"
                params.append(dm_id)

            result = SafeDatabase.execute_query(sql, tuple(params) if params else None, fetch_one=True) or {}
            logger.info("查询锁位转化率成功")
            return result

        except Exception as e:
            logger.error(f"查询锁位转化率失败: {str(e)}")
            raise

    @staticmethod
    def get_dm_performance(start_date=None, end_date=None):
        """
        老板报表：DM 业绩统计

        Returns:
            每位 DM 的场次数/订单数/已支付订单/营收/活跃锁位
        """
        try:
            sql = """
                SELECT
                    d.DM_ID,
                    d.Name AS DM_Name,
                    d.Phone,
                    d.Star_Level,
                    COUNT(DISTINCT sch.Schedule_ID) AS schedule_count,
                    COUNT(DISTINCT o.Order_ID) AS order_count,
                    COUNT(DISTINCT CASE WHEN o.Pay_Status = 1 THEN o.Order_ID END) AS paid_orders,
                    COALESCE(SUM(CASE WHEN t.Trans_Type = 1 AND t.Result = 1 THEN t.Amount ELSE 0 END), 0) AS revenue,
                    COUNT(DISTINCT CASE WHEN l.Status = 0 AND l.ExpireTime > NOW() THEN l.LockID END) AS active_locks
                FROM T_DM d
                LEFT JOIN T_Schedule sch ON d.DM_ID = sch.DM_ID
                LEFT JOIN T_Order o ON sch.Schedule_ID = o.Schedule_ID
                LEFT JOIN T_Transaction t ON o.Order_ID = t.Order_ID
                LEFT JOIN t_lock_record l ON sch.Schedule_ID = l.Schedule_ID
                WHERE 1=1
            """

            params = []
            if start_date:
                sql += " AND DATE(sch.Start_Time) >= %s"
                params.append(start_date)
            if end_date:
                sql += " AND DATE(sch.Start_Time) <= %s"
                params.append(end_date)

            sql += """
                GROUP BY d.DM_ID, d.Name, d.Phone, d.Star_Level
                ORDER BY revenue DESC, paid_orders DESC, order_count DESC
            """

            return SafeDatabase.execute_query(sql, tuple(params) if params else None) or []
        except Exception as e:
            logger.error(f"查询DM业绩失败: {str(e)}")
            raise
