# -*- coding: utf-8 -*-
"""
剧本模型 - 剧本相关的数据库操作
使用安全的参数化查询
"""

from database import SafeDatabase
from security_utils import InputValidator
import logging

logger = logging.getLogger(__name__)


class ScriptModel:
    """剧本模型类 - 处理剧本相关的业务逻辑"""

    @staticmethod
    def get_all_scripts(status=None):
        """
        获取所有剧本列表

        Args:
            status: 剧本状态（可选，1-上架，0-下架）

        Returns:
            剧本列表

        安全措施：使用参数化查询
        """
        try:
            if status is not None:
                # 验证状态值
                status = InputValidator.validate_enum(status, [0, 1], "剧本状态")
                sql = """
                    SELECT s.Script_ID, s.Title, s.Type, s.Min_Players, s.Max_Players,
                           s.Duration, s.Base_Price, s.Status, s.Cover_Image,
                           p.Group_Category, p.Difficulty, p.Gender_Config
                    FROM T_Script s
                    LEFT JOIN T_Script_Profile p ON s.Script_ID = p.Script_ID
                    WHERE s.Status = %s
                    ORDER BY s.Script_ID
                """
                return SafeDatabase.execute_query(sql, (status,))
            else:
                sql = """
                    SELECT s.Script_ID, s.Title, s.Type, s.Min_Players, s.Max_Players,
                           s.Duration, s.Base_Price, s.Status, s.Cover_Image,
                           p.Group_Category, p.Difficulty, p.Gender_Config
                    FROM T_Script s
                    LEFT JOIN T_Script_Profile p ON s.Script_ID = p.Script_ID
                    ORDER BY s.Script_ID
                """
                return SafeDatabase.execute_query(sql)

        except Exception as e:
            logger.error(f"获取剧本列表失败: {str(e)}")
            raise

    @staticmethod
    def get_script_by_id(script_id):
        """
        根据ID获取剧本详情

        Args:
            script_id: 剧本ID

        Returns:
            剧本详情字典

        安全措施：验证ID格式，使用参数化查询
        """
        try:
            # 验证ID
            script_id = InputValidator.validate_id(script_id, "剧本ID")

            sql = """
                SELECT s.Script_ID, s.Title, s.Type, s.Min_Players, s.Max_Players,
                       s.Duration, s.Base_Price, s.Status, s.Cover_Image,
                       p.Group_Category, p.Sub_Category, p.Difficulty,
                       p.Duration_Min_Minutes, p.Duration_Max_Minutes,
                       p.Gender_Config, p.Allow_Gender_Bend, p.Synopsis
                FROM T_Script s
                LEFT JOIN T_Script_Profile p ON s.Script_ID = p.Script_ID
                WHERE s.Script_ID = %s
            """
            result = SafeDatabase.execute_query(sql, (script_id,), fetch_one=True)

            if not result:
                raise ValueError(f"剧本ID {script_id} 不存在")

            return result

        except Exception as e:
            logger.error(f"获取剧本详情失败: {str(e)}")
            raise

    @staticmethod
    def get_hot_scripts(limit=10):
        """
        获取热门剧本列表（按已支付订单数和总金额排序）

        Args:
            limit: 返回数量限制

        Returns:
            热门剧本列表，包含排名、订单数、总金额等信息
        """
        try:
            limit = InputValidator.validate_id(limit, "限制数量")

            sql = """
                SELECT
                    s.Script_ID, s.Title, s.Type, s.Min_Players, s.Max_Players,
                    s.Duration, s.Base_Price, s.Status, s.Cover_Image,
                    p.Group_Category, p.Difficulty, p.Gender_Config,
                    COUNT(o.Order_ID) as paid_orders,
                    IFNULL(SUM(o.Amount), 0) as total_amount
                FROM T_Script s
                LEFT JOIN T_Script_Profile p ON s.Script_ID = p.Script_ID
                LEFT JOIN T_Schedule sch ON s.Script_ID = sch.Script_ID
                LEFT JOIN T_Order o ON sch.Schedule_ID = o.Schedule_ID AND o.Pay_Status = 1
                WHERE s.Status = 1
                GROUP BY s.Script_ID
                ORDER BY paid_orders DESC, total_amount DESC
                LIMIT %s
            """
            results = SafeDatabase.execute_query(sql, (limit,))

            # 添加排名信息
            for idx, script in enumerate(results):
                script['hot_rank'] = idx + 1

            return results

        except Exception as e:
            logger.error(f"获取热门剧本失败: {str(e)}")
            raise
