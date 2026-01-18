# -*- coding: utf-8 -*-
"""
用户认证模型 - 处理登录、注册、JWT token
"""

from database import SafeDatabase
from security_utils import InputValidator
import logging
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash

logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET = 'your-secret-key-change-in-production'  # 生产环境必须改
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


class AuthModel:
    """用户认证模型类"""

    @staticmethod
    def hash_password(password):
        """密码哈希（使用SHA256+盐）"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${pwd_hash}"

    @staticmethod
    def verify_password(password, stored_hash):
        """验证密码"""
        try:
            # 兼容旧数据：部分账号可能用 Werkzeug/Flask 的 generate_password_hash 生成
            # 例如：pbkdf2:sha256:260000$salt$hash
            if isinstance(stored_hash, str) and stored_hash.startswith(('pbkdf2:', 'scrypt:')):
                return check_password_hash(stored_hash, password)

            # 项目默认格式：salt$sha256(password+salt)
            salt, pwd_hash = stored_hash.split('$')
            check_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return check_hash == pwd_hash
        except:
            return False

    @staticmethod
    def generate_token(user_id, role):
        """生成JWT token"""
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_token(token):
        """验证JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token已过期")
        except jwt.InvalidTokenError:
            raise ValueError("无效的Token")

    @staticmethod
    def register(username, phone, password, role='player'):
        """
        用户注册（修复版：player角色会同时创建T_Player）

        Args:
            username: 用户名
            phone: 手机号
            password: 密码
            role: 角色（player/staff）

        Returns:
            user_id: 新用户ID
        """
        try:
            # 验证输入
            username = InputValidator.validate_string(username, "用户名", min_length=3, max_length=50)
            phone = InputValidator.validate_phone(phone)

            if len(password) < 6:
                raise ValueError("密码长度不能少于6位")

            # 检查用户名和手机号是否已存在
            check_sql = "SELECT User_ID FROM T_User WHERE Username=%s OR Phone=%s"
            existing = SafeDatabase.execute_query(check_sql, (username, phone), fetch_one=True)
            if existing:
                raise ValueError("用户名或手机号已存在")

            # 哈希密码
            password_hash = AuthModel.hash_password(password)

            ref_id = None
            operations = []

            # 如果是玩家角色，需要先创建T_Player记录
            if role == 'player':
                import uuid
                # 生成新的Player_ID
                player_id_sql = "SELECT IFNULL(MAX(Player_ID), 3000) + 1 AS new_id FROM T_Player"
                result = SafeDatabase.execute_query(player_id_sql, fetch_one=True)
                new_player_id = result['new_id']

                # 将插入T_Player记录加入事务
                player_sql = """
                    INSERT INTO T_Player (Player_ID, Open_ID, Nickname, Phone)
                    VALUES (%s, %s, %s, %s)
                """
                open_id = f"web_{uuid.uuid4().hex[:16]}"
                operations.append((player_sql, (new_player_id, open_id, username, phone)))

                ref_id = new_player_id
                logger.info(f"准备创建玩家记录: Player_ID={new_player_id}")

            # 插入用户记录（使用事务，包含T_Player和T_User）
            operations.append((
                "INSERT INTO T_User (Username, Phone, Password_Hash, Role, Ref_ID, Create_Time) VALUES (%s, %s, %s, %s, %s, NOW())",
                (username, phone, password_hash, role, ref_id)
            ))
            SafeDatabase.execute_transaction(operations)

            # 获取新用户ID
            user_sql = "SELECT User_ID FROM T_User WHERE Username=%s"
            user = SafeDatabase.execute_query(user_sql, (username,), fetch_one=True)

            logger.info(f"用户注册成功: {username}, Ref_ID={ref_id}")
            return user['User_ID']

        except Exception as e:
            logger.error(f"用户注册失败: {str(e)}")
            raise

    @staticmethod
    def login(username, password):
        """
        用户登录（支持员工和玩家）

        Args:
            username: 用户名或手机号
            password: 密码

        Returns:
            dict: {user_id, username, role, token}
        """
        try:
            # 先尝试员工登录（从 T_Staff_Account 查询）
            staff_sql = """
                SELECT Staff_ID, Username, Password, Real_Name, Role, Status
                FROM T_Staff_Account
                WHERE (Username=%s OR Phone=%s) AND Status=1
            """
            staff = SafeDatabase.execute_query(staff_sql, (username, username), fetch_one=True)

            if staff:
                # 员工登录：直接比对密码（未加密）
                if password != staff['Password']:
                    raise ValueError("用户名或密码错误")

                # 更新最后登录时间
                update_sql = "UPDATE T_Staff_Account SET Last_Login=NOW() WHERE Staff_ID=%s"
                SafeDatabase.execute_update(update_sql, (staff['Staff_ID'],))

                # 生成token（使用 Staff_ID 作为 user_id）
                token = AuthModel.generate_token(staff['Staff_ID'], 'staff')

                logger.info(f"员工登录成功: {staff['Username']}")
                return {
                    'user_id': staff['Staff_ID'],
                    'username': staff['Username'],
                    'role': 'staff',
                    'ref_id': staff['Staff_ID'],  # 员工的 ref_id 就是自己的 Staff_ID
                    'token': token
                }

            # 如果不是员工，尝试玩家登录（从 T_User 查询）
            user_sql = """
                SELECT User_ID, Username, Password_Hash, Role, Ref_ID
                FROM T_User
                WHERE Username=%s OR Phone=%s
            """
            user = SafeDatabase.execute_query(user_sql, (username, username), fetch_one=True)

            if not user:
                raise ValueError("用户名或密码错误")

            # 验证密码（加密密码）
            if not AuthModel.verify_password(password, user['Password_Hash']):
                raise ValueError("用户名或密码错误")

            # 更新最后登录时间
            update_sql = "UPDATE T_User SET Last_Login=NOW() WHERE User_ID=%s"
            SafeDatabase.execute_update(update_sql, (user['User_ID'],))

            # 生成token
            token = AuthModel.generate_token(user['User_ID'], user['Role'])

            logger.info(f"用户登录成功: {user['Username']}")
            return {
                'user_id': user['User_ID'],
                'username': user['Username'],
                'role': user['Role'],
                'ref_id': user['Ref_ID'],
                'token': token
            }

        except Exception as e:
            logger.error(f"用户登录失败: {str(e)}")
            raise

    @staticmethod
    def get_current_user(user_id):
        """
        获取当前用户信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 用户信息
        """
        try:
            sql = """
                SELECT User_ID, Username, Phone, Role, Ref_ID, Create_Time, Last_Login
                FROM T_User
                WHERE User_ID=%s
            """
            user = SafeDatabase.execute_query(sql, (user_id,), fetch_one=True)

            if not user:
                raise ValueError("用户不存在")

            return user

        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            raise

    @staticmethod
    def get_current_user_info(user_id, role=None):
        """
        获取当前用户信息（统一返回前端可用字段）

        - player：从 T_User 读取
        - staff：优先从 T_Staff_Account 读取；若不存在则回退到 T_User(Role=staff)

        Returns:
            dict: {user_id, username, role, ref_id, phone?}
        """
        # staff：优先读取员工账号表（存在则以员工账号表为准）
        if role == 'staff':
            try:
                staff_sql = """
                    SELECT Staff_ID, Username, Phone, Real_Name, Role, Status, Last_Login
                    FROM T_Staff_Account
                    WHERE Staff_ID=%s
                """
                staff = SafeDatabase.execute_query(staff_sql, (user_id,), fetch_one=True)
                if staff and int(staff.get('Status', 1)) == 1:
                    return {
                        'user_id': staff['Staff_ID'],
                        'username': staff['Username'],
                        'role': 'staff',
                        'ref_id': staff['Staff_ID'],
                        'phone': staff.get('Phone'),
                        'real_name': staff.get('Real_Name')
                    }
            except Exception as e:
                # 兼容没有 T_Staff_Account 表或字段不一致的环境
                logger.warning(f"读取 T_Staff_Account 失败，回退到 T_User: {str(e)}")

        # player / fallback：从 T_User 读取
        user_sql = """
            SELECT User_ID, Username, Phone, Role, Ref_ID, Create_Time, Last_Login
            FROM T_User
            WHERE User_ID=%s
        """
        user = SafeDatabase.execute_query(user_sql, (user_id,), fetch_one=True)
        if not user:
            raise ValueError("用户不存在")

        # staff fallback：只允许 Role=staff 的记录作为员工
        if role == 'staff' and user.get('Role') != 'staff':
            raise ValueError("无权限访问")

        return {
            'user_id': user['User_ID'],
            'username': user['Username'],
            'role': user['Role'],
            'ref_id': user.get('Ref_ID'),
            'phone': user.get('Phone')
        }
