# -*- coding: utf-8 -*-
"""
数据库连接层 - 安全的数据库操作封装
重点：防止SQL注入，使用参数化查询
"""

import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
import logging
from database_config import DB_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """数据库连接管理类 - 使用上下文管理器确保连接安全关闭"""

    def __init__(self):
        self.connection = None
        self.cursor = None

    def __enter__(self):
        """进入上下文时建立连接"""
        try:
            self.connection = pymysql.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                charset=DB_CONFIG['charset'],
                cursorclass=DictCursor,  # 返回字典格式结果
                autocommit=False  # 手动控制事务
            )
            self.cursor = self.connection.cursor()
            logger.info("数据库连接成功")
            return self
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            if exc_type:
                self.connection.rollback()  # 发生异常时回滚
                logger.warning("事务回滚")
            else:
                self.connection.commit()  # 正常情况下提交
                logger.info("事务提交")
            self.connection.close()
            logger.info("数据库连接关闭")


class SafeDatabase:
    """
    安全的数据库操作类
    核心安全措施：
    1. 使用参数化查询防止SQL注入
    2. 输入验证和清理
    3. 错误处理和日志记录
    4. 事务管理
    """

    @staticmethod
    def execute_query(sql, params=None, fetch_one=False, fetch_all=True):
        """
        安全执行查询语句（SELECT）

        Args:
            sql: SQL语句（使用%s作为占位符）
            params: 参数元组或列表
            fetch_one: 是否只返回一条记录
            fetch_all: 是否返回所有记录

        Returns:
            查询结果（字典或字典列表）

        安全说明：
        - 使用参数化查询，params会被安全转义
        - 永远不要使用字符串拼接构建SQL
        """
        try:
            with DatabaseConnection() as db:
                # 记录SQL日志（不记录敏感参数）
                logger.info(f"执行查询: {sql[:100]}...")

                # 执行参数化查询
                db.cursor.execute(sql, params or ())

                if fetch_one:
                    result = db.cursor.fetchone()
                elif fetch_all:
                    result = db.cursor.fetchall()
                else:
                    result = None

                logger.info(f"查询成功，返回 {len(result) if result else 0} 条记录")
                return result

        except Exception as e:
            logger.error(f"查询执行失败: {str(e)}")
            raise

    @staticmethod
    def execute_update(sql, params=None):
        """
        安全执行更新语句（INSERT/UPDATE/DELETE）

        Args:
            sql: SQL语句（使用%s作为占位符）
            params: 参数元组或列表

        Returns:
            影响的行数

        安全说明：
        - 使用参数化查询防止SQL注入
        - 自动事务管理（成功提交，失败回滚）
        """
        try:
            with DatabaseConnection() as db:
                logger.info(f"执行更新: {sql[:100]}...")

                # 执行参数化更新
                affected_rows = db.cursor.execute(sql, params or ())

                logger.info(f"更新成功，影响 {affected_rows} 行")
                return affected_rows

        except Exception as e:
            logger.error(f"更新执行失败: {str(e)}")
            raise

    @staticmethod
    def execute_transaction(operations):
        """
        安全执行事务（多个操作要么全部成功，要么全部失败）

        Args:
            operations: 操作列表，每个操作是(sql, params)元组

        Returns:
            所有操作影响的总行数

        示例：
            operations = [
                ("INSERT INTO T_Order (...) VALUES (%s, %s)", (val1, val2)),
                ("UPDATE T_Schedule SET Status=%s WHERE Schedule_ID=%s", (1, 123))
            ]
        """
        try:
            with DatabaseConnection() as db:
                logger.info(f"开始执行事务，共 {len(operations)} 个操作")
                total_affected = 0

                for sql, params in operations:
                    affected = db.cursor.execute(sql, params or ())
                    total_affected += affected

                logger.info(f"事务执行成功，共影响 {total_affected} 行")
                return total_affected

        except Exception as e:
            logger.error(f"事务执行失败，已回滚: {str(e)}")
            raise
