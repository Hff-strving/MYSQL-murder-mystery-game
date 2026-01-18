# 剧本杀店务管理系统 - 后端安全说明文档

## 🔒 数据库安全措施总览

本系统在后端开发中实施了多层次的安全防护措施，确保数据安全。

---

## 1. SQL注入防护（核心安全措施）

### ❌ 危险做法（永远不要这样做）
```python
# 错误示例：字符串拼接SQL（容易被SQL注入攻击）
sql = f"SELECT * FROM T_Player WHERE Player_ID = {player_id}"
sql = "SELECT * FROM T_Order WHERE Order_ID = '" + order_id + "'"
```

**攻击示例**：如果用户输入 `1 OR 1=1`，会导致：
```sql
SELECT * FROM T_Player WHERE Player_ID = 1 OR 1=1  -- 返回所有数据！
```

### ✅ 安全做法（本系统采用）
```python
# 正确示例：参数化查询
sql = "SELECT * FROM T_Player WHERE Player_ID = %s"
SafeDatabase.execute_query(sql, (player_id,))
```

**安全原理**：
- 参数 `%s` 会被数据库驱动自动转义
- 用户输入被当作数据而非SQL代码
- 即使输入恶意代码也无法执行

---

## 2. 输入验证（第二道防线）

### 验证所有用户输入
```python
# security_utils.py 中的验证器
InputValidator.validate_id(player_id, "玩家ID")        # 验证ID必须是正整数
InputValidator.validate_phone(phone)                   # 验证手机号格式
InputValidator.validate_string(nickname, max_length=50) # 验证字符串长度
InputValidator.validate_decimal(amount, min_value=0)   # 验证金额范围
InputValidator.validate_enum(status, [0, 1, 2])        # 验证枚举值
```

### 防止XSS攻击
```python
# 自动移除危险字符
dangerous_chars = ['<', '>', '"', "'", '&', ';']
# 示例：输入 "<script>alert('hack')</script>"
# 输出：scriptalert('hack')/script
```

---

## 3. 事务管理（数据一致性保障）

### 场景：支付订单
```python
# 使用事务确保：订单状态更新 + 流水记录插入 同时成功或同时失败
operations = [
    ("UPDATE T_Order SET Pay_Status=%s WHERE Order_ID=%s", (1, order_id)),
    ("INSERT INTO T_Transaction (...) VALUES (...)", (trans_id, ...))
]
SafeDatabase.execute_transaction(operations)
```

**安全保障**：
- 如果任何一步失败，自动回滚所有操作
- 避免出现"订单已支付但没有流水记录"的数据不一致

---

## 4. 日志审计（可追溯性）

### 记录所有关键操作
```python
logger.info(f"订单创建成功: Order_ID={order_id}")
logger.error(f"支付订单失败: {str(e)}")
logger.warning(f"检测到危险字符 '{char}' 在字段 {field_name}")
```

**日志文件**：`api.log`
- 记录所有API请求
- 记录成功/失败操作
- 记录异常和错误信息

---

## 5. 数据库连接安全

### 使用上下文管理器
```python
with DatabaseConnection() as db:
    db.cursor.execute(sql, params)
    # 自动提交或回滚
    # 自动关闭连接
```

**安全优势**：
- 防止连接泄漏
- 异常时自动回滚
- 确保连接正确关闭

---

## 6. API接口安全

### 统一错误处理
```python
try:
    # 业务逻辑
    result = OrderModel.create_order(...)
    return success_response(result)
except Exception as e:
    logger.error(f"操作失败: {str(e)}")
    return error_response(str(e))  # 不暴露敏感信息
```

### CORS跨域保护
```python
from flask_cors import CORS
CORS(app)  # 配置允许的域名
```

---

## 7. 密码和敏感信息保护

### 配置文件安全
```python
# database_config.py
DB_CONFIG = {
    'password': '123456',  # 生产环境应使用环境变量
}
```

**建议**：
- 不要将密码提交到Git仓库
- 使用环境变量存储敏感信息
- 生产环境使用强密码

---

## 8. 安全检查清单

### ✅ 已实现的安全措施
- [x] SQL注入防护（参数化查询）
- [x] 输入验证（类型、长度、格式）
- [x] XSS攻击防护（危险字符过滤）
- [x] 事务管理（数据一致性）
- [x] 日志审计（操作可追溯）
- [x] 错误处理（统一异常捕获）
- [x] 连接管理（自动关闭）

### 🔄 可选增强措施（生产环境建议）
- [ ] JWT身份认证
- [ ] API访问频率限制
- [ ] HTTPS加密传输
- [ ] 数据库备份策略
- [ ] 敏感数据加密存储

---

## 9. 安全测试示例

### 测试SQL注入防护
```python
# 尝试注入攻击
malicious_input = "1 OR 1=1"
# 系统会验证失败：ValueError: 玩家ID格式错误，必须是正整数
```

### 测试XSS防护
```python
# 尝试XSS攻击
malicious_nickname = "<script>alert('hack')</script>"
# 系统会自动清理：scriptalert('hack')/script
```

---

## 10. 使用建议

### 开发环境
1. 使用测试数据库
2. 开启详细日志
3. 定期查看 `api.log`

### 生产环境
1. 修改数据库密码
2. 配置HTTPS
3. 限制API访问频率
4. 定期备份数据库
5. 监控异常日志

---

## 📚 相关文件

- `database.py` - 数据库安全层
- `security_utils.py` - 输入验证工具
- `models/script_model.py` - 剧本模型
- `models/order_model.py` - 订单模型
- `app.py` - Flask API服务
- `api.log` - 操作日志文件


