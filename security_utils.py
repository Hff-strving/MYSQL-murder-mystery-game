# -*- coding: utf-8 -*-
"""
输入验证和安全工具类
防止恶意输入和数据注入攻击
"""

import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InputValidator:
    """输入验证类 - 确保所有用户输入都经过验证"""

    @staticmethod
    def validate_id(value, field_name="ID"):
        """
        验证ID类型字段（必须是正整数）

        Args:
            value: 待验证的值
            field_name: 字段名称（用于错误提示）

        Returns:
            验证后的整数值

        Raises:
            ValueError: 验证失败
        """
        try:
            int_value = int(value)
            if int_value <= 0:
                raise ValueError(f"{field_name}必须是正整数")
            return int_value
        except (TypeError, ValueError):
            raise ValueError(f"{field_name}格式错误，必须是正整数")

    @staticmethod
    def validate_phone(phone):
        """
        验证手机号格式（11位数字）

        Args:
            phone: 手机号字符串

        Returns:
            验证后的手机号

        Raises:
            ValueError: 格式错误
        """
        if not phone:
            return None

        # 移除空格和特殊字符
        phone = re.sub(r'[^\d]', '', str(phone))

        if not re.match(r'^1[3-9]\d{9}$', phone):
            raise ValueError("手机号格式错误，必须是11位数字")

        return phone

    @staticmethod
    def validate_string(value, field_name="字段", min_length=0, max_length=255, allow_empty=False):
        """
        验证字符串字段

        Args:
            value: 待验证的值
            field_name: 字段名称
            min_length: 最小长度
            max_length: 最大长度
            allow_empty: 是否允许空值

        Returns:
            清理后的字符串

        Raises:
            ValueError: 验证失败
        """
        if value is None or value == '':
            if allow_empty:
                return None
            raise ValueError(f"{field_name}不能为空")

        # 转换为字符串并去除首尾空格
        str_value = str(value).strip()

        # 检查长度
        if len(str_value) < min_length:
            raise ValueError(f"{field_name}长度不能少于{min_length}个字符")
        if len(str_value) > max_length:
            raise ValueError(f"{field_name}长度不能超过{max_length}个字符")

        # 防止XSS攻击：移除危险字符
        dangerous_chars = ['<', '>', '"', "'", '&', ';']
        for char in dangerous_chars:
            if char in str_value:
                logger.warning(f"检测到危险字符 '{char}' 在字段 {field_name}")
                str_value = str_value.replace(char, '')

        return str_value

    @staticmethod
    def validate_decimal(value, field_name="金额", min_value=0, max_value=999999.99):
        """
        验证金额类型字段

        Args:
            value: 待验证的值
            field_name: 字段名称
            min_value: 最小值
            max_value: 最大值

        Returns:
            验证后的Decimal值

        Raises:
            ValueError: 验证失败
        """
        try:
            from decimal import Decimal
            decimal_value = Decimal(str(value))

            if decimal_value < Decimal(str(min_value)):
                raise ValueError(f"{field_name}不能小于{min_value}")
            if decimal_value > Decimal(str(max_value)):
                raise ValueError(f"{field_name}不能大于{max_value}")

            return decimal_value
        except Exception:
            raise ValueError(f"{field_name}格式错误")

    @staticmethod
    def validate_enum(value, allowed_values, field_name="状态"):
        """
        验证枚举类型字段

        Args:
            value: 待验证的值
            allowed_values: 允许的值列表
            field_name: 字段名称

        Returns:
            验证后的值

        Raises:
            ValueError: 值不在允许范围内
        """
        if value not in allowed_values:
            raise ValueError(f"{field_name}值错误，允许的值为: {allowed_values}")
        return value
