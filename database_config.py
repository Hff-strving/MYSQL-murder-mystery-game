# -*- coding: utf-8 -*-
"""
剧本杀店务管理系统 - 数据库配置文件
"""

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',      # 数据库主机地址
    'port': 3306,             # 数据库端口
    'user': 'root',           # 数据库用户名
    'password': '123456',  # 数据库密码
    'database': '剧本杀店务管理系统',  # 数据库名称
    'charset': 'utf8mb4'      # 字符集
}

# 数据库连接池配置
POOL_CONFIG = {
    'pool_size': 5,           # 连接池大小
    'max_overflow': 10,       # 最大溢出连接数
    'pool_timeout': 30,       # 连接超时时间（秒）
    'pool_recycle': 3600      # 连接回收时间（秒）
}
