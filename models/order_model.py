# -*- coding: utf-8 -*-
"""
订单模型 - 订单相关的数据库操作
包含订单创建、支付、取消等核心业务逻辑
"""

from database import SafeDatabase
from security_utils import InputValidator
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class OrderModel:
    """订单模型类 - 处理订单相关的业务逻辑"""

    # 订单状态常量
    STATUS_UNPAID = 0    # 待支付
    STATUS_PAID = 1      # 已支付
    STATUS_REFUNDED = 2  # 已退款

    @staticmethod
    def create_order(player_id, schedule_id, amount=None):
        """
        创建订单（安全版本 - 后端自动获取价格）

        Args:
            player_id: 玩家ID
            schedule_id: 场次ID
            amount: 订单金额（可选，后端会自动从数据库获取）

        Returns:
            新订单ID

        安全措施：
        1. 后端自动从数据库获取Real_Price，忽略前端传入的金额
        2. 使用参数化查询
        3. 使用事务确保数据一致性
        """
        try:
            # 1. 验证输入
            player_id = InputValidator.validate_id(player_id, "玩家ID")
            schedule_id = InputValidator.validate_id(schedule_id, "场次ID")

            # 2. 检查场次容量（包含锁位）
            capacity_sql = """
                SELECT
                    sc.Max_Players,
                    COUNT(DISTINCT o.Order_ID) AS booked_count,
                    COUNT(DISTINCT l.LockID) AS locked_count
                FROM T_Schedule sch
                JOIN T_Script sc ON sch.Script_ID = sc.Script_ID
                LEFT JOIN T_Order o ON sch.Schedule_ID = o.Schedule_ID AND o.Pay_Status IN (0, 1)
                LEFT JOIN t_lock_record l ON sch.Schedule_ID = l.Schedule_ID AND l.Status = 0 AND l.ExpireTime > NOW()
                WHERE sch.Schedule_ID = %s
                GROUP BY sch.Schedule_ID, sc.Max_Players
            """
            cap = SafeDatabase.execute_query(capacity_sql, (schedule_id,), fetch_one=True)
            if not cap:
                raise ValueError(f"场次 {schedule_id} 不存在")
            total_occupied = (cap.get('booked_count') or 0) + (cap.get('locked_count') or 0)
            if total_occupied >= cap['Max_Players']:
                raise ValueError("该场次已满")

            # 2. 检查该玩家是否已预约该场次（防止重复预约）
            duplicate_check_sql = """
                SELECT Order_ID FROM T_Order
                WHERE Player_ID = %s AND Schedule_ID = %s AND Pay_Status IN (0, 1)
            """
            existing_order = SafeDatabase.execute_query(duplicate_check_sql, (player_id, schedule_id), fetch_one=True)
            if existing_order:
                raise ValueError("您已经预约过该场次，请勿重复预约")

            # 3. 若已锁位，允许继续创建订单（会把锁位标记为“已转订单”）
            lock_check_sql = """
                SELECT LockID FROM t_lock_record
                WHERE Player_ID = %s AND Schedule_ID = %s AND Status = 0 AND ExpireTime > NOW()
                ORDER BY LockTime DESC
                LIMIT 1
            """
            existing_lock = SafeDatabase.execute_query(lock_check_sql, (player_id, schedule_id), fetch_one=True)

            # 4. 从数据库获取场次价格（安全！）
            price_sql = "SELECT Real_Price FROM T_Schedule WHERE Schedule_ID = %s"
            schedule = SafeDatabase.execute_query(price_sql, (schedule_id,), fetch_one=True)

            if not schedule:
                raise ValueError(f"场次 {schedule_id} 不存在")

            # 使用数据库中的价格，忽略前端传入的金额
            actual_amount = schedule['Real_Price']

            # 5. 生成订单ID（使用时间戳+随机数）
            import random
            order_id = int(datetime.now().strftime('%Y%m%d%H%M%S')) + random.randint(1000, 9999)

            # 6. 使用事务：插入订单 +（可选）锁位转订单
            operations = []

            insert_sql = """
                INSERT INTO T_Order (Order_ID, Player_ID, Schedule_ID, Amount,
                                     Pay_Status, Create_Time)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            operations.append((insert_sql, (order_id, player_id, schedule_id, actual_amount, OrderModel.STATUS_UNPAID)))

            if existing_lock:
                operations.append((
                    "UPDATE t_lock_record SET Status = 1 WHERE LockID = %s AND Status = 0",
                    (existing_lock['LockID'],)
                ))

            SafeDatabase.execute_transaction(operations)

            logger.info(f"订单创建成功: Order_ID={order_id}")
            return order_id

        except Exception as e:
            logger.error(f"创建订单失败: {str(e)}")
            raise

    @staticmethod
    def pay_order(order_id, channel=1):
        """
        支付订单（使用事务确保数据一致性）

        Args:
            order_id: 订单ID
            channel: 支付渠道（1-微信，2-支付宝，3-现金）

        Returns:
            交易流水ID

        安全措施：使用事务，确保订单状态和流水记录同步更新
        """
        try:
            # 验证输入
            order_id = InputValidator.validate_id(order_id, "订单ID")
            channel = InputValidator.validate_enum(channel, [1, 2, 3], "支付渠道")

            # 查询订单信息
            order_sql = "SELECT Amount, Pay_Status FROM T_Order WHERE Order_ID = %s"
            order = SafeDatabase.execute_query(order_sql, (order_id,), fetch_one=True)

            if not order:
                raise ValueError(f"订单 {order_id} 不存在")
            if order['Pay_Status'] == OrderModel.STATUS_PAID:
                raise ValueError("订单已支付，无需重复支付")

            # 生成交易流水ID
            import random
            trans_id = int(datetime.now().strftime('%Y%m%d%H%M%S')) + random.randint(1000, 9999)

            # 使用事务：更新订单状态 + 插入流水记录
            operations = [
                ("UPDATE T_Order SET Pay_Status=%s WHERE Order_ID=%s",
                 (OrderModel.STATUS_PAID, order_id)),
                ("INSERT INTO T_Transaction (Trans_ID, Order_ID, Amount, Trans_Type, Channel, Trans_Time, Result) VALUES (%s, %s, %s, %s, %s, NOW(), %s)",
                 (trans_id, order_id, order['Amount'], 1, channel, 1))
            ]

            SafeDatabase.execute_transaction(operations)
            logger.info(f"订单支付成功: Order_ID={order_id}, Trans_ID={trans_id}")
            return trans_id

        except Exception as e:
            logger.error(f"支付订单失败: {str(e)}")
            raise

    @staticmethod
    def cancel_order(order_id, player_id):
        """
        取消订单（仅限未支付订单）

        Args:
            order_id: 订单ID
            player_id: 玩家ID（用于验证权限）

        Returns:
            bool: 是否成功

        安全措施：
        1. 验证订单归属
        2. 仅允许取消未支付订单
        3. 使用事务同步释放关联锁位
        """
        try:
            # 验证输入
            order_id = InputValidator.validate_id(order_id, "订单ID")
            player_id = InputValidator.validate_id(player_id, "玩家ID")

            # 查询订单信息
            order_sql = """
                SELECT Player_ID, Pay_Status, Schedule_ID
                FROM T_Order
                WHERE Order_ID = %s
            """
            order = SafeDatabase.execute_query(order_sql, (order_id,), fetch_one=True)

            if not order:
                raise ValueError("订单不存在")

            if order['Player_ID'] != player_id:
                raise ValueError("无权取消他人的订单")

            # 检查订单状态：只能取消未支付或已支付的订单
            if order['Pay_Status'] not in [OrderModel.STATUS_UNPAID, OrderModel.STATUS_PAID]:
                raise ValueError("该订单无法取消")

            # 使用事务：更新订单状态 + 释放关联锁位
            operations = []

            # 根据支付状态决定新状态：未支付->已取消(3)，已支付->已退款(2)
            new_status = 3 if order['Pay_Status'] == OrderModel.STATUS_UNPAID else 2
            operations.append(
                ("UPDATE T_Order SET Pay_Status = %s WHERE Order_ID = %s", (new_status, order_id))
            )

            # 释放该玩家在该场次的锁位（如果有）
            operations.append(
                ("UPDATE t_lock_record SET Status = 2 WHERE Player_ID = %s AND Schedule_ID = %s AND Status = 0",
                 (player_id, order['Schedule_ID']))
            )

            SafeDatabase.execute_transaction(operations)
            logger.info(f"订单取消成功: Order_ID={order_id}")
            return True

        except Exception as e:
            logger.error(f"取消订单失败: {str(e)}")
            raise

    @staticmethod
    def get_orders_by_player(player_id):
        """
        查询玩家的所有订单

        Args:
            player_id: 玩家ID

        Returns:
            订单列表

        安全措施：参数化查询
        """
        try:
            player_id = InputValidator.validate_id(player_id, "玩家ID")

            sql = """
                SELECT o.Order_ID, o.Amount, o.Pay_Status, o.Create_Time,
                       s.Title AS Script_Title, sch.Start_Time,
                       r.Room_Name
                FROM T_Order o
                JOIN T_Schedule sch ON o.Schedule_ID = sch.Schedule_ID
                JOIN T_Script s ON sch.Script_ID = s.Script_ID
                JOIN T_Room r ON sch.Room_ID = r.Room_ID
                WHERE o.Player_ID = %s
                ORDER BY o.Create_Time DESC
            """
            return SafeDatabase.execute_query(sql, (player_id,))

        except Exception as e:
            logger.error(f"查询玩家订单失败: {str(e)}")
            raise

    @staticmethod
    def get_all_orders(dm_id=None):
        """
        查询订单（员工/老板用）

        - staff：传入 dm_id，仅返回该 DM 负责的场次订单
        - boss：不传 dm_id，返回全局订单；也可按 dm_id 过滤

        Args:
            dm_id: 可选，DM_ID 分域
        """
        try:
            sql = """
                SELECT o.Order_ID, o.Player_ID, o.Amount, o.Pay_Status, o.Create_Time,
                       sc.Title AS Script_Title, sch.Start_Time,
                       r.Room_Name,
                       d.DM_ID, d.Name AS DM_Name
                FROM T_Order o
                JOIN T_Schedule sch ON o.Schedule_ID = sch.Schedule_ID
                JOIN T_Script sc ON sch.Script_ID = sc.Script_ID
                JOIN T_Room r ON sch.Room_ID = r.Room_ID
                JOIN T_DM d ON sch.DM_ID = d.DM_ID
                WHERE 1=1
            """

            params = []
            if dm_id is not None:
                dm_id = InputValidator.validate_id(dm_id, "DM_ID")
                sql += " AND sch.DM_ID = %s"
                params.append(dm_id)

            sql += " ORDER BY o.Create_Time DESC"

            return SafeDatabase.execute_query(sql, tuple(params) if params else None)

        except Exception as e:
            logger.error(f"查询订单失败: {str(e)}")
            raise
