# 后端服务启动和测试指南

## 📦 环境准备

### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

**依赖说明**：
- `flask` - Web框架
- `flask-cors` - 跨域支持
- `pymysql` - MySQL数据库驱动
- `pyjwt` - JWT token生成和验证

### 2. 确认数据库配置
检查 `database_config.py` 中的配置是否正确：
- 数据库地址（默认：localhost）
- 用户名和密码
- 数据库名称
- 字符集：**必须使用 utf8mb4** 防止中文乱码

### 3. 执行数据库迁移脚本（按顺序）

**重要**：必须按顺序执行以下迁移脚本

```bash
# 连接MySQL（使用utf8mb4字符集）
mysql -u root -p --default-character-set=utf8mb4

# 选择数据库
USE your_database_name;

# 执行迁移脚本
source database/migrations/001_add_auth.sql;
source database/migrations/002_add_script_profile.sql;
source database/migrations/003_update_script_base.sql;
source database/migrations/004_enhance_lock_record.sql;

# （推荐）执行演示增强脚本：账号 + 触发器/视图/存储过程/函数/事件
source database/demo/init_complete_system.sql;
```

如需让管理端报表更“真实”（更多场次/历史订单/演示锁位），可选执行：
```sql
source database/demo/extend_schedule_data.sql;
source database/demo/insert_history_orders.sql;
source database/demo/optimize_lock_system.sql;
```

**迁移脚本说明**：
- `001_add_auth.sql` - 创建用户认证表（T_User）和封面图字段
- `002_add_script_profile.sql` - 创建剧本档案表（T_Script_Profile）
- `003_update_script_base.sql` - 同步剧本基础信息（标题/分类）
- `004_enhance_lock_record.sql` - 创建/确认锁位记录表（t_lock_record）

### 4. 验证数据库表结构

```sql
-- 检查核心表是否存在
SHOW TABLES LIKE 'T_%';
SHOW TABLES LIKE 't_lock_record';

-- 检查T_User表结构（必须有Ref_ID字段）
DESC T_User;

-- 检查t_lock_record表结构
DESC t_lock_record;
```

---

## 🚀 启动后端服务

### 方法一：直接运行
```bash
cd D:\我的资料\数据库设计及其应用\剧本杀管理系统
python app.py
```

### 方法二：使用命令行
```bash
python -m flask run --host=0.0.0.0 --port=5000
```

**启动成功标志**：
```
 * Running on http://0.0.0.0:5000
 * Restarting with stat
启动Flask API服务...
```

---

## 🧪 API测试

### 认证相关接口

#### 1. 用户注册
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testplayer",
    "phone": "13900001234",
    "password": "123456"
  }'
```

**预期响应**：
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {"user_id": 1}
}
```

**注意**：注册时会自动创建玩家档案（T_Player）并设置 Ref_ID

#### 2. 用户登录
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testplayer",
    "password": "123456"
  }'
```

**预期响应**：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "user_id": 1,
    "username": "testplayer",
    "role": "player",
    "ref_id": 3001,
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**重要**：保存返回的 token，后续请求需要使用

#### 3. 获取当前用户信息
```bash
curl http://localhost:5000/api/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 剧本相关接口

#### 4. 获取剧本列表
```bash
curl http://localhost:5000/api/scripts
```

#### 5. 获取热门剧本
```bash
curl http://localhost:5000/api/scripts/hot?limit=10
```

#### 6. 获取剧本详情
```bash
curl http://localhost:5000/api/scripts/1001
```

---

### 场次相关接口

#### 7. 获取剧本的场次列表
```bash
curl http://localhost:5000/api/scripts/1001/schedules
```

**预期响应**（包含锁位状态）：
```json
{
  "code": 200,
  "message": "查询成功",
  "data": [
    {
      "Schedule_ID": 4001,
      "Start_Time": "2025-12-29 14:00:00",
      "Real_Price": 168.00,
      "Max_Players": 7,
      "Booked_Count": 2,
      "Locked_Count": 1,
      "Room_Name": "推理房A",
      "DM_Name": "张三"
    }
  ]
}
```

---

### 订单相关接口（需要token）

#### 8. 创建订单
```bash
curl -X POST http://localhost:5000/api/orders \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"schedule_id": 4001}'
```

**注意**：
- 只传 `schedule_id`，不传 `player_id` 和 `amount`
- 后端会从token获取玩家ID，从数据库获取价格
- 只有玩家角色可以创建订单

#### 9. 支付订单
```bash
curl -X POST http://localhost:5000/api/orders/5001/pay \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1}'
```

#### 10. 查询我的订单
```bash
curl http://localhost:5000/api/my/orders \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 11. 查询所有订单（员工专用）
```bash
curl http://localhost:5000/api/admin/orders \
  -H "Authorization: Bearer STAFF_TOKEN"
```

---

### 锁位相关接口（需要token）

#### 12. 创建锁位
```bash
curl -X POST http://localhost:5000/api/locks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"schedule_id": 4001}'
```

**预期响应**：
```json
{
  "code": 200,
  "message": "锁位成功",
  "data": {"lock_id": 1}
}
```

#### 13. 取消锁位
```bash
curl -X POST http://localhost:5000/api/locks/1/cancel \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 14. 查询我的锁位
```bash
curl http://localhost:5000/api/my/locks \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 15. 查询所有锁位（员工专用）
```bash
curl http://localhost:5000/api/admin/locks \
  -H "Authorization: Bearer STAFF_TOKEN"
```

---

## 📊 查看日志

### 实时查看日志
```bash
tail -f api.log
```

### 日志内容示例
```
2025-12-28 15:30:45 - __main__ - INFO - 查询剧本列表成功，返回12条记录
2025-12-28 15:31:20 - __main__ - INFO - 创建订单成功: Order_ID=5001, Player_ID=3001
2025-12-28 15:32:10 - __main__ - INFO - 创建锁位成功: Lock_ID=1, Player_ID=3001, Schedule_ID=4001
```

---

## ⚠️ 常见问题

### 1. 数据库连接失败
**错误信息**：`数据库连接失败: (2003, "Can't connect to MySQL server")`

**解决方法**：
- 检查MySQL服务是否启动
- 检查 `database_config.py` 中的配置
- 确认数据库名称是否正确
- 确认用户名和密码是否正确

### 2. 模块导入错误
**错误信息**：`ModuleNotFoundError: No module named 'flask'` 或 `No module named 'jwt'`

**解决方法**：
```bash
pip install flask flask-cors pymysql pyjwt
```

### 3. 端口被占用
**错误信息**：`Address already in use`

**解决方法**：
- 修改 `app.py` 中的端口号（第403行）
- 或关闭占用5000端口的程序

### 4. 用户信息不完整错误
**错误信息**：`用户信息不完整` 或 `只有玩家可以创建订单`

**原因**：玩家账号缺少 Ref_ID（指向 T_Player 的外键）

**解决方法**：
```sql
-- 检查用户的 Ref_ID
SELECT User_ID, Username, Role, Ref_ID FROM T_User WHERE Username='testplayer';

-- 如果 Ref_ID 为 NULL，需要创建玩家档案
INSERT INTO T_Player (Player_ID, Open_ID, Nickname, Phone)
VALUES (3001, 'web_xxx', 'testplayer', '13900001234');

-- 更新用户的 Ref_ID
UPDATE T_User SET Ref_ID=3001 WHERE Username='testplayer';
```

### 5. 中文乱码问题
**原因**：数据库字符集不是 utf8mb4

**解决方法**：
```bash
# 连接时指定字符集
mysql -u root -p --default-character-set=utf8mb4

# 检查数据库字符集
SHOW VARIABLES LIKE 'character_set%';

# 修改数据库字符集
ALTER DATABASE your_database_name CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Token验证失败
**错误信息**：`缺少认证token` 或 `Token已过期`

**解决方法**：
- 确认请求头包含 `Authorization: Bearer <token>`
- Token 默认有效期24小时，过期需重新登录
- 检查 token 格式是否正确（Bearer + 空格 + token）

---

## 🔐 安全特性

### 1. 密码安全
- 使用 SHA256 + 随机盐哈希存储
- 密码不以明文存储或传输

### 2. Token认证
- 使用 JWT (JSON Web Token)
- Token 包含用户ID和角色信息
- 默认有效期24小时

### 3. 权限控制
- **玩家权限**：创建订单、支付订单、创建锁位、取消锁位
- **员工权限**：查看所有订单、查看所有锁位
- 所有写操作需要 token 验证

### 4. 防篡改
- 订单金额由后端从数据库获取，忽略前端传入
- 玩家ID从 token 解析，不接受前端传入
- 所有数据库操作使用参数化查询，防止SQL注入

---

## 📋 数据库表结构说明

### 核心表

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| T_User | 用户认证表 | User_ID, Username, Role, Ref_ID |
| T_Player | 玩家档案表 | Player_ID, Nickname, Phone |
| T_Script | 剧本基础信息 | Script_ID, Title, Type, Base_Price |
| T_Script_Profile | 剧本档案信息 | Script_ID, Group_Category, Difficulty |
| T_Schedule | 场次表 | Schedule_ID, Script_ID, Start_Time |
| T_Order | 订单表 | Order_ID, Player_ID, Schedule_ID, Pay_Status |
| t_lock_record | 锁位记录表 | LockID, Schedule_ID, Player_ID, LockTime, ExpireTime, Status |

### 字段命名注意
- T_User/T_Player/T_Script 等使用大写 T_ 前缀
- t_lock_record 使用小写 t_ 前缀
- 锁位表字段：LockID, LockTime, ExpireTime（与当前数据库一致）

---

## 🎯 下一步

后端服务启动成功后，你可以：

1. **使用 Postman 测试所有API接口**
   - 导入接口集合
   - 测试认证流程
   - 测试业务流程

2. **启动前端服务**
   - 前端统一使用 Vue：
     - `cd frontend-vue`
     - `npm run dev`
     - 访问：`http://127.0.0.1:5173`
   - 详细见：`docs/frontend.md`

3. **验证完整流程**
   - 玩家注册 → 登录 → 查看详情 → 预约 → 支付
   - 员工登录 → 查看管理后台 → 查看订单和锁位

4. **查看完整验证指南**
   - 参考：`docs/admin-plan.md`、`docs/lock-design.md`、`docs/test-data.md`

---

## 📚 相关文档

 - `docs/frontend.md` - Vue前端启动指南
 - `docs/test-data.md` - 测试/演示数据说明
 - `docs/security.md` - 安全特性说明

---

## 💡 提示

1. **开发模式**：`app.py` 中 `debug=True` 会自动重载代码
2. **生产环境**：记得修改 JWT_SECRET 密钥
3. **日志记录**：所有操作都会记录到 `api.log`
4. **错误处理**：API 统一返回格式 `{code, message, data}`
5. **事务支持**：订单创建和支付使用事务确保一致性
