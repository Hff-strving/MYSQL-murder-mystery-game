# -*- coding: utf-8 -*-
"""
Flask API服务 - 提供RESTful接口
注重安全性：输入验证、错误处理、日志记录
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.script_model import ScriptModel
from models.order_model import OrderModel
from models.auth_model import AuthModel
from models.schedule_model import ScheduleModel
from models.lock_model import LockModel
from models.report_model import ReportModel
from database import SafeDatabase
import logging
from functools import wraps

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 统一响应格式
def success_response(data=None, message="操作成功"):
    """成功响应"""
    return jsonify({
        'code': 200,
        'message': message,
        'data': data
    })

def error_response(message="操作失败", code=400):
    """错误响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': None
    }), code

# Token验证装饰器
def token_required(f):
    """验证token的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return error_response("缺少认证token", 401)

        try:
            if token.startswith('Bearer '):
                token = token[7:]
            payload = AuthModel.verify_token(token)
            request.current_user = payload
        except Exception as e:
            return error_response(str(e), 401)

        return f(*args, **kwargs)
    return decorated


def _require_staff_or_boss():
    role = request.current_user.get('role')
    if role not in ('staff', 'boss'):
        return None, error_response("无权限访问", 403)
    return role, None


def _resolve_staff_dm_id(user_id):
    """
    将“员工账号”映射到 DM_ID，用于数据分域：员工只能看到自己带队（DM）的订单/锁位/场次。

    支持两类员工来源：
    1) T_User(Role='staff', Ref_ID=DM_ID)
    2) T_Staff_Account（通过 Phone 反查 T_DM.DM_ID）
    """
    # 1) 优先从 T_User 读取 Ref_ID（DM_ID）
    user_sql = "SELECT Ref_ID FROM T_User WHERE User_ID=%s AND Role='staff'"
    user = SafeDatabase.execute_query(user_sql, (user_id,), fetch_one=True)
    if user and user.get('Ref_ID'):
        return int(user['Ref_ID']), None

    # 2) 兼容：从 T_Staff_Account 读取 Phone，再匹配到 T_DM
    try:
        staff_sql = "SELECT Phone FROM T_Staff_Account WHERE Staff_ID=%s"
        staff = SafeDatabase.execute_query(staff_sql, (user_id,), fetch_one=True)
        if staff and staff.get('Phone'):
            dm_sql = "SELECT DM_ID FROM T_DM WHERE Phone=%s"
            dm = SafeDatabase.execute_query(dm_sql, (staff['Phone'],), fetch_one=True)
            if dm and dm.get('DM_ID'):
                return int(dm['DM_ID']), None
    except Exception:
        # 可能没有该表，或字段不一致；忽略，走最终错误
        pass

    return None, error_response("员工账号未绑定 DM（请使用 staff_* 账号或手机号登录）", 403)


def _get_admin_scope_dm_id(role, user_id):
    """
    返回本次请求应该使用的 DM_ID 分域：
    - staff：强制为该员工绑定的 DM_ID
    - boss：允许 query param dm_id 过滤；不传则为 None（全局）
    """
    if role == 'staff':
        return _resolve_staff_dm_id(user_id)

    dm_id = request.args.get('dm_id', type=int)
    return dm_id, None


# ==================== 认证相关接口 ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    用户注册
    POST /api/auth/register
    Body: {"username": "test", "phone": "13900001234", "password": "123456"}
    """
    try:
        data = request.get_json()
        if data.get('role') and data.get('role') != 'player':
            return error_response("仅允许注册玩家账号", 403)
        user_id = AuthModel.register(
            data['username'],
            data['phone'],
            data['password'],
            'player'
        )
        logger.info(f"用户注册成功: User_ID={user_id}")
        return success_response({'user_id': user_id}, "注册成功")
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    用户登录
    POST /api/auth/login
    Body: {"username": "test", "password": "123456"}
    """
    try:
        data = request.get_json()
        result = AuthModel.login(data['username'], data['password'])
        logger.info(f"用户登录成功: {result['username']}")
        return success_response(result, "登录成功")
    except Exception as e:
        logger.error(f"用户登录失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/me', methods=['GET'])
@token_required
def get_current_user():
    """
    获取当前用户信息
    GET /api/me
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']
        role = request.current_user.get('role')
        user = AuthModel.get_current_user_info(user_id, role)
        return success_response(user, "查询成功")
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return error_response(str(e))


# ==================== 剧本相关接口 ====================

@app.route('/api/scripts', methods=['GET'])
def get_scripts():
    """
    获取剧本列表
    GET /api/scripts?status=1
    """
    try:
        status = request.args.get('status', type=int)
        scripts = ScriptModel.get_all_scripts(status)
        logger.info(f"查询剧本列表成功，返回{len(scripts)}条记录")
        return success_response(scripts, "查询成功")
    except Exception as e:
        logger.error(f"查询剧本列表失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/scripts/hot', methods=['GET'])
def get_hot_scripts():
    """
    获取热门剧本列表
    GET /api/scripts/hot?limit=10
    """
    try:
        limit = request.args.get('limit', default=10, type=int)
        scripts = ScriptModel.get_hot_scripts(limit)
        logger.info(f"查询热门剧本成功，返回{len(scripts)}条记录")
        return success_response(scripts, "查询成功")
    except Exception as e:
        logger.error(f"查询热门剧本失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/scripts/<int:script_id>', methods=['GET'])
def get_script_detail(script_id):
    """
    获取剧本详情
    GET /api/scripts/1001
    """
    try:
        script = ScriptModel.get_script_by_id(script_id)
        logger.info(f"查询剧本详情成功: Script_ID={script_id}")
        return success_response(script, "查询成功")
    except Exception as e:
        logger.error(f"查询剧本详情失败: {str(e)}")
        return error_response(str(e))


# ==================== 场次相关接口 ====================

@app.route('/api/scripts/<int:script_id>/schedules', methods=['GET'])
def get_script_schedules(script_id):
    """
    获取剧本的场次列表（支持查询玩家预约状态）
    GET /api/scripts/1001/schedules
    GET /api/scripts/1001/schedules?player_id=2001
    """
    try:
        # 获取可选的玩家ID参数
        player_id = request.args.get('player_id', type=int)
        schedules = ScheduleModel.get_schedules_by_script(script_id, player_id)
        logger.info(f"查询剧本场次成功: Script_ID={script_id}, Player_ID={player_id}")
        return success_response(schedules, "查询成功")
    except Exception as e:
        logger.error(f"查询剧本场次失败: {str(e)}")
        return error_response(str(e))


# ==================== 订单相关接口 ====================

@app.route('/api/orders', methods=['POST'])
@token_required
def create_order():
    """
    创建订单（安全版本：使用token鉴权，禁止伪造player_id）
    POST /api/orders
    Body: {"schedule_id": 4001}
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        # 验证用户角色和获取Ref_ID
        user_sql = "SELECT Ref_ID, Role FROM T_User WHERE User_ID=%s"
        user = SafeDatabase.execute_query(user_sql, (user_id,), fetch_one=True)

        if not user or user['Role'] != 'player':
            return error_response("只有玩家可以创建订单", 403)

        if not user['Ref_ID']:
            return error_response("用户信息不完整", 400)

        # 从请求体获取场次ID（忽略前端传入的player_id和amount）
        data = request.get_json()
        schedule_id = data.get('schedule_id')

        if not schedule_id:
            return error_response("缺少场次ID", 400)

        # 使用后端获取的player_id创建订单
        order_id = OrderModel.create_order(
            user['Ref_ID'],  # 使用后端验证的player_id
            schedule_id,
            None  # amount由后端自动获取
        )
        logger.info(f"创建订单成功: Order_ID={order_id}, Player_ID={user['Ref_ID']}")
        return success_response({'order_id': order_id}, "订单创建成功")
    except Exception as e:
        logger.error(f"创建订单失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/orders/<int:order_id>/pay', methods=['POST'])
@token_required
def pay_order(order_id):
    """
    支付订单（安全版本：只能支付自己的订单）
    POST /api/orders/5001/pay
    Body: {"channel": 1}
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        # 验证用户角色和获取Ref_ID
        user_sql = "SELECT Ref_ID, Role FROM T_User WHERE User_ID=%s"
        user = SafeDatabase.execute_query(user_sql, (user_id,), fetch_one=True)

        if not user or user['Role'] != 'player':
            return error_response("只有玩家可以支付订单", 403)

        if not user['Ref_ID']:
            return error_response("用户信息不完整", 400)

        # 验证订单归属：只能支付自己的订单
        order_check_sql = "SELECT Player_ID FROM T_Order WHERE Order_ID=%s"
        order = SafeDatabase.execute_query(order_check_sql, (order_id,), fetch_one=True)

        if not order:
            return error_response("订单不存在", 404)

        if order['Player_ID'] != user['Ref_ID']:
            return error_response("无权支付他人订单", 403)

        # 执行支付
        data = request.get_json()
        channel = data.get('channel', 1)
        trans_id = OrderModel.pay_order(order_id, channel)
        logger.info(f"支付订单成功: Order_ID={order_id}, Trans_ID={trans_id}, Player_ID={user['Ref_ID']}")
        return success_response({'trans_id': trans_id}, "支付成功")
    except Exception as e:
        logger.error(f"支付订单失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
@token_required
def cancel_order(order_id):
    """
    取消订单（仅限未支付订单）
    POST /api/orders/5001/cancel
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        # 验证用户角色和获取Ref_ID
        user_sql = "SELECT Ref_ID, Role FROM T_User WHERE User_ID=%s"
        user = SafeDatabase.execute_query(user_sql, (user_id,), fetch_one=True)

        if not user or user['Role'] != 'player':
            return error_response("只有玩家可以取消订单", 403)

        if not user['Ref_ID']:
            return error_response("用户信息不完整", 400)

        # 执行取消订单
        OrderModel.cancel_order(order_id, user['Ref_ID'])
        logger.info(f"取消订单成功: Order_ID={order_id}, Player_ID={user['Ref_ID']}")
        return success_response(None, "订单已取消")
    except Exception as e:
        logger.error(f"取消订单失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/my/orders', methods=['GET'])
@token_required
def get_my_orders():
    """
    查询当前用户的订单（安全版本）
    GET /api/my/orders
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        # 从T_User获取Ref_ID
        user_sql = "SELECT Ref_ID, Role FROM T_User WHERE User_ID=%s"
        user = SafeDatabase.execute_query(user_sql, (user_id,), fetch_one=True)

        if not user or user['Role'] != 'player':
            return error_response("只有玩家可以查看订单", 403)

        if not user['Ref_ID']:
            return error_response("用户信息不完整", 400)

        orders = OrderModel.get_orders_by_player(user['Ref_ID'])
        logger.info(f"查询我的订单成功: Player_ID={user['Ref_ID']}")
        return success_response(orders, "查询成功")
    except Exception as e:
        logger.error(f"查询我的订单失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/players/<int:player_id>/orders', methods=['GET'])
def get_player_orders(player_id):
    """
    查询玩家订单（保留兼容）
    GET /api/players/3001/orders
    """
    try:
        orders = OrderModel.get_orders_by_player(player_id)
        logger.info(f"查询玩家订单成功: Player_ID={player_id}")
        return success_response(orders, "查询成功")
    except Exception as e:
        logger.error(f"查询玩家订单失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/admin/orders', methods=['GET'])
@token_required
def get_all_orders():
    """
    查询所有订单（员工专用）
    GET /api/admin/orders
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        role, err = _require_staff_or_boss()
        if err:
            return err

        dm_id, err = _get_admin_scope_dm_id(role, user_id)
        if err:
            return err

        # 获取所有订单
        orders = OrderModel.get_all_orders(dm_id=dm_id)
        logger.info(f"员工查询所有订单成功: User_ID={user_id}")
        return success_response(orders, "查询成功")
    except Exception as e:
        logger.error(f"查询所有订单失败: {str(e)}")
        return error_response(str(e))


# ==================== 锁位相关接口 ====================

@app.route('/api/locks', methods=['POST'])
@token_required
def create_lock():
    """
    创建锁位记录
    POST /api/locks
    Body: {"schedule_id": 4001}
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        # 验证用户角色和获取Ref_ID
        user_sql = "SELECT Ref_ID, Role FROM T_User WHERE User_ID=%s"
        user = SafeDatabase.execute_query(user_sql, (user_id,), fetch_one=True)

        if not user or user['Role'] != 'player':
            return error_response("只有玩家可以锁位", 403)

        if not user['Ref_ID']:
            return error_response("用户信息不完整", 400)

        # 获取场次ID
        data = request.get_json()
        schedule_id = data.get('schedule_id')

        if not schedule_id:
            return error_response("缺少场次ID", 400)

        # 创建锁位
        lock_id = LockModel.create_lock(user['Ref_ID'], schedule_id)
        logger.info(f"创建锁位成功: Lock_ID={lock_id}, Player_ID={user['Ref_ID']}")
        return success_response({'lock_id': lock_id}, "锁位成功")
    except Exception as e:
        logger.error(f"创建锁位失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/locks/<int:lock_id>/cancel', methods=['POST'])
@token_required
def cancel_lock(lock_id):
    """
    取消锁位
    POST /api/locks/<id>/cancel
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        # 获取玩家ID
        user_sql = "SELECT Ref_ID, Role FROM T_User WHERE User_ID=%s"
        user = SafeDatabase.execute_query(user_sql, (user_id,), fetch_one=True)

        if not user or user['Role'] != 'player':
            return error_response("只有玩家可以取消锁位", 403)

        # 取消锁位
        LockModel.cancel_lock(lock_id, user['Ref_ID'])
        logger.info(f"取消锁位成功: Lock_ID={lock_id}")
        return success_response(None, "取消成功")
    except Exception as e:
        logger.error(f"取消锁位失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/my/locks', methods=['GET'])
@token_required
def get_my_locks():
    """
    查询当前玩家的锁位记录
    GET /api/my/locks
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        # 获取玩家ID
        user_sql = "SELECT Ref_ID, Role FROM T_User WHERE User_ID=%s"
        user = SafeDatabase.execute_query(user_sql, (user_id,), fetch_one=True)

        if not user or user['Role'] != 'player':
            return error_response("只有玩家可以查看锁位", 403)

        # 查询锁位记录
        locks = LockModel.get_locks_by_player(user['Ref_ID'])
        logger.info(f"查询玩家锁位成功: Player_ID={user['Ref_ID']}")
        return success_response(locks, "查询成功")
    except Exception as e:
        logger.error(f"查询玩家锁位失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/admin/locks', methods=['GET'])
@token_required
def get_all_locks():
    """
    查询所有锁位记录（员工专用）
    GET /api/admin/locks
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        role, err = _require_staff_or_boss()
        if err:
            return err

        dm_id, err = _get_admin_scope_dm_id(role, user_id)
        if err:
            return err

        # 查询所有锁位
        locks = LockModel.get_all_locks(dm_id=dm_id)
        logger.info(f"员工查询所有锁位成功: User_ID={user_id}")
        return success_response(locks, "查询成功")
    except Exception as e:
        logger.error(f"查询所有锁位失败: {str(e)}")
        return error_response(str(e))


# ==================== 场次管理接口（员工专用） ====================

@app.route('/api/admin/schedules', methods=['GET'])
@token_required
def get_admin_schedules():
    """
    获取所有场次列表（员工专用，支持筛选）
    GET /api/admin/schedules?date=2024-01-01&room_id=1&script_id=1001&status=0
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        role, err = _require_staff_or_boss()
        if err:
            return err

        dm_id, err = _get_admin_scope_dm_id(role, user_id)
        if err:
            return err

        # 获取筛选参数
        date = request.args.get('date')
        room_id = request.args.get('room_id', type=int)
        script_id = request.args.get('script_id', type=int)
        status = request.args.get('status', type=int)

        schedules = ScheduleModel.get_all_schedules(date, room_id, script_id, status, dm_id=dm_id)
        logger.info(f"员工查询场次成功: User_ID={user_id}, 返回{len(schedules)}条")
        return success_response(schedules, "查询成功")
    except Exception as e:
        logger.error(f"查询场次失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/admin/schedules', methods=['POST'])
@token_required
def create_admin_schedule():
    """
    创建新场次（员工专用）
    POST /api/admin/schedules
    Body: {"script_id": 1001, "room_id": 1, "dm_id": 3001, "start_time": "2024-01-01 14:00:00", "end_time": "2024-01-01 18:00:00", "real_price": 168.00}
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        role, err = _require_staff_or_boss()
        if err:
            return err

        dm_id, err = _get_admin_scope_dm_id(role, user_id)
        if err:
            return err

        data = request.get_json()

        # staff 只能创建自己的场次：忽略前端传入 dm_id
        if role == 'staff':
            data = dict(data or {})
            data['dm_id'] = dm_id

        schedule_id = ScheduleModel.create_schedule(
            data['script_id'],
            data['room_id'],
            data['dm_id'],
            data['start_time'],
            data['end_time'],
            data['real_price']
        )
        logger.info(f"员工创建场次成功: Schedule_ID={schedule_id}, User_ID={user_id}")
        return success_response({'schedule_id': schedule_id}, "场次创建成功")
    except Exception as e:
        logger.error(f"创建场次失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/admin/schedules/<int:schedule_id>', methods=['PUT'])
@token_required
def update_admin_schedule(schedule_id):
    """
    更新场次信息（员工专用）
    PUT /api/admin/schedules/4001
    Body: {"start_time": "2024-01-01 15:00:00", "real_price": 188.00}
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        role, err = _require_staff_or_boss()
        if err:
            return err

        dm_id, err = _get_admin_scope_dm_id(role, user_id)
        if err:
            return err

        data = request.get_json()

        # staff 只能更新自己的场次，且不能把 DM 改成别人
        if role == 'staff':
            check_sql = "SELECT DM_ID FROM T_Schedule WHERE Schedule_ID=%s"
            sch = SafeDatabase.execute_query(check_sql, (schedule_id,), fetch_one=True)
            if not sch:
                return error_response("场次不存在", 404)
            if int(sch['DM_ID']) != int(dm_id):
                return error_response("无权限更新其他员工的场次", 403)
            data = dict(data or {})
            data['dm_id'] = dm_id

        ScheduleModel.update_schedule(
            schedule_id,
            script_id=data.get('script_id'),
            room_id=data.get('room_id'),
            dm_id=data.get('dm_id'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            real_price=data.get('real_price'),
            status=data.get('status')
        )
        logger.info(f"员工更新场次成功: Schedule_ID={schedule_id}, User_ID={user_id}")
        return success_response(None, "场次更新成功")
    except Exception as e:
        logger.error(f"更新场次失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/admin/schedules/<int:schedule_id>/cancel', methods=['POST'])
@token_required
def cancel_admin_schedule(schedule_id):
    """
    取消场次（员工专用）
    POST /api/admin/schedules/4001/cancel
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        role, err = _require_staff_or_boss()
        if err:
            return err

        dm_id, err = _get_admin_scope_dm_id(role, user_id)
        if err:
            return err

        if role == 'staff':
            check_sql = "SELECT DM_ID FROM T_Schedule WHERE Schedule_ID=%s"
            sch = SafeDatabase.execute_query(check_sql, (schedule_id,), fetch_one=True)
            if not sch:
                return error_response("场次不存在", 404)
            if int(sch['DM_ID']) != int(dm_id):
                return error_response("无权限取消其他员工的场次", 403)

        ScheduleModel.cancel_schedule(schedule_id)
        logger.info(f"员工取消场次成功: Schedule_ID={schedule_id}, User_ID={user_id}")
        return success_response(None, "场次已取消")
    except Exception as e:
        logger.error(f"取消场次失败: {str(e)}")
        return error_response(str(e))


# ==================== 报表统计接口（员工专用） ====================

@app.route('/api/admin/dms', methods=['GET'])
@token_required
def get_admin_dms():
    """
    获取 DM 列表（老板专用，用于筛选）
    GET /api/admin/dms
    """
    try:
        if request.current_user.get('role') != 'boss':
            return error_response("只有老板可以查看 DM 列表", 403)

        dms = SafeDatabase.execute_query(
            "SELECT DM_ID, Name, Phone, Star_Level FROM T_DM ORDER BY DM_ID"
        )
        return success_response(dms, "查询成功")
    except Exception as e:
        logger.error(f"查询DM列表失败: {str(e)}")
        return error_response(str(e))

@app.route('/api/admin/rooms', methods=['GET'])
@token_required
def get_admin_rooms():
    """
    获取房间列表（staff/boss）
    GET /api/admin/rooms
    """
    try:
        role, err = _require_staff_or_boss()
        if err:
            return err

        rooms = SafeDatabase.execute_query(
            "SELECT Room_ID, Room_Name FROM T_Room ORDER BY Room_ID"
        )
        return success_response(rooms, "查询成功")
    except Exception as e:
        logger.error(f"查询房间列表失败: {str(e)}")
        return error_response(str(e))

@app.route('/api/admin/db-objects', methods=['GET'])
@token_required
def get_admin_db_objects():
    """
    数据库对象自检（用于展示：触发器/视图/存储过程/函数/事件/关键索引）
    GET /api/admin/db-objects
    """
    try:
        role, err = _require_staff_or_boss()
        if err:
            return err

        schema_row = SafeDatabase.execute_query("SELECT DATABASE() AS db", fetch_one=True) or {}
        schema = schema_row.get('db')
        if not schema:
            return error_response("无法获取当前数据库名", 500)

        def _exists_list(table, schema_col, name_col, names):
            placeholders = ",".join(["%s"] * len(names))
            sql = f"""
                SELECT {name_col} AS name
                FROM information_schema.{table}
                WHERE {schema_col} = %s AND {name_col} IN ({placeholders})
            """
            rows = SafeDatabase.execute_query(sql, (schema, *names)) or []
            found = {r['name'] for r in rows}
            return {n: (n in found) for n in names}

        trigger_names = ['trg_prevent_duplicate_order', 'trg_prevent_duplicate_lock']
        view_names = ['v_order_detail', 'v_lock_detail']
        proc_names = ['sp_dm_orders', 'sp_dm_locks']
        func_names = ['fn_schedule_occupied']
        event_names = ['evt_expire_locks']

        triggers = _exists_list('TRIGGERS', 'TRIGGER_SCHEMA', 'TRIGGER_NAME', trigger_names)
        views = _exists_list('VIEWS', 'TABLE_SCHEMA', 'TABLE_NAME', view_names)

        routines_sql = """
            SELECT ROUTINE_NAME AS name, ROUTINE_TYPE AS type
            FROM information_schema.ROUTINES
            WHERE ROUTINE_SCHEMA = %s AND ROUTINE_NAME IN (%s, %s, %s)
        """
        routine_rows = SafeDatabase.execute_query(routines_sql, (schema, *proc_names, *func_names)) or []
        routines_found = {(r['name'], r['type']) for r in routine_rows}
        procs = {n: ((n, 'PROCEDURE') in routines_found) for n in proc_names}
        funcs = {n: ((n, 'FUNCTION') in routines_found) for n in func_names}

        events = _exists_list('EVENTS', 'EVENT_SCHEMA', 'EVENT_NAME', event_names)

        idx_sql = """
            SELECT TABLE_NAME, INDEX_NAME
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = %s AND (
                (TABLE_NAME = 'T_Order' AND INDEX_NAME = 'UK_Player_Schedule') OR
                (TABLE_NAME = 't_lock_record' AND INDEX_NAME = 'idx_lock_expire') OR
                (TABLE_NAME = 't_lock_record' AND INDEX_NAME = 'idx_lock_schedule')
            )
        """
        idx_rows = SafeDatabase.execute_query(idx_sql, (schema,)) or []
        idx_found = {(r['TABLE_NAME'], r['INDEX_NAME']) for r in idx_rows}
        indexes = {
            'T_Order.UK_Player_Schedule': (('T_Order', 'UK_Player_Schedule') in idx_found),
            't_lock_record.idx_lock_expire': (('t_lock_record', 'idx_lock_expire') in idx_found),
            't_lock_record.idx_lock_schedule': (('t_lock_record', 'idx_lock_schedule') in idx_found),
        }

        role_type_row = SafeDatabase.execute_query(
            """
            SELECT COLUMN_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'T_User' AND COLUMN_NAME = 'Role'
            """,
            (schema,),
            fetch_one=True
        ) or {}
        role_type = role_type_row.get('COLUMN_TYPE') or ''

        return success_response({
            'schema': schema,
            'current_role': role,
            'objects': {
                'triggers': triggers,
                'views': views,
                'procedures': procs,
                'functions': funcs,
                'events': events,
                'indexes': indexes,
                'role_enum': role_type,
            }
        }, "查询成功")
    except Exception as e:
        logger.error(f"数据库对象自检失败: {str(e)}")
        return error_response(str(e))

@app.route('/api/admin/dashboard', methods=['GET'])
@token_required
def get_dashboard():
    """
    获取仪表盘统计数据（员工专用）
    GET /api/admin/dashboard
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        role, err = _require_staff_or_boss()
        if err:
            return err

        dm_id, err = _get_admin_scope_dm_id(role, user_id)
        if err:
            return err

        stats = ReportModel.get_dashboard_stats(dm_id=dm_id)
        logger.info(f"员工查询仪表盘统计成功: User_ID={user_id}")
        return success_response(stats, "查询成功")
    except Exception as e:
        logger.error(f"查询仪表盘统计失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/admin/reports/top-scripts', methods=['GET'])
@token_required
def get_top_scripts_report():
    """
    获取热门剧本Top N（员工专用）
    GET /api/admin/reports/top-scripts?start=2024-01-01&end=2024-12-31&limit=5
    Headers: Authorization: Bearer <token>
    """
    try:
        user_id = request.current_user['user_id']

        role, err = _require_staff_or_boss()
        if err:
            return err

        dm_id, err = _get_admin_scope_dm_id(role, user_id)
        if err:
            return err

        start_date = request.args.get('start')
        end_date = request.args.get('end')
        limit = request.args.get('limit', default=5, type=int)

        scripts = ReportModel.get_top_scripts(start_date, end_date, limit, dm_id=dm_id)
        logger.info(f"员工查询热门剧本成功: User_ID={user_id}")
        return success_response(scripts, "查询成功")
    except Exception as e:
        logger.error(f"查询热门剧本失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/admin/reports/room-utilization', methods=['GET'])
@token_required
def get_room_utilization_report():
    """
    房间利用率报表（员工/老板）
    GET /api/admin/reports/room-utilization?start=2025-12-01&end=2025-12-31
    """
    try:
        user_id = request.current_user['user_id']
        role, err = _require_staff_or_boss()
        if err:
            return err

        dm_id, err = _get_admin_scope_dm_id(role, user_id)
        if err:
            return err

        start_date = request.args.get('start')
        end_date = request.args.get('end')
        rooms = ReportModel.get_room_utilization(start_date, end_date, dm_id=dm_id)
        return success_response(rooms, "查询成功")
    except Exception as e:
        logger.error(f"查询房间利用率失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/admin/reports/lock-conversion', methods=['GET'])
@token_required
def get_lock_conversion_report():
    """
    锁位转化率报表（员工/老板）
    GET /api/admin/reports/lock-conversion?start=2025-12-01&end=2025-12-31
    """
    try:
        user_id = request.current_user['user_id']
        role, err = _require_staff_or_boss()
        if err:
            return err

        dm_id, err = _get_admin_scope_dm_id(role, user_id)
        if err:
            return err

        start_date = request.args.get('start')
        end_date = request.args.get('end')
        result = ReportModel.get_lock_conversion_rate(start_date, end_date, dm_id=dm_id)
        return success_response(result, "查询成功")
    except Exception as e:
        logger.error(f"查询锁位转化率失败: {str(e)}")
        return error_response(str(e))


@app.route('/api/admin/reports/dm-performance', methods=['GET'])
@token_required
def get_dm_performance_report():
    """
    DM 业绩报表（老板专用）
    GET /api/admin/reports/dm-performance?start=2025-12-01&end=2025-12-31
    """
    try:
        if request.current_user.get('role') != 'boss':
            return error_response("只有老板可以查看DM业绩", 403)

        start_date = request.args.get('start')
        end_date = request.args.get('end')
        rows = ReportModel.get_dm_performance(start_date, end_date)
        return success_response(rows, "查询成功")
    except Exception as e:
        logger.error(f"查询DM业绩失败: {str(e)}")
        return error_response(str(e))


# ==================== 启动服务 ====================

if __name__ == '__main__':
    logger.info("启动Flask API服务...")
    app.run(host='0.0.0.0', port=5000, debug=True)
