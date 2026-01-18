# 剧本杀店务管理系统 - 最终部署指南（Flask + MySQL + Vue）

## ✅ 已修复的问题

1. **MySQL 5.7 兼容性** ✓
   - 移除了 `IF EXISTS/IF NOT EXISTS` 语法
   - 使用 `INSERT IGNORE` 确保可重复执行

2. **员工登录认证** ✓
   - 员工账号既支持 `T_User(Role=staff, Password_Hash)`，也支持 `T_Staff_Account(Password)`（以后端 `AuthModel.login()` 为准）
   - `/api/me`、`/api/admin/*` 已按 token 的 `role` 做统一鉴权，避免“登录成功但后台 403/无权限”

---

## 演示账号（执行 `database/demo/init_complete_system.sql` 后自动创建/更新）

- 员工（默认绑定一个 DM）：`staff_demo / 123456`
- 员工（与 DM 一一对应）：`staff_<DM_ID> / 123456`（例如 `staff_2001 / 123456`）
- 老板（全局权限）：`郝飞帆 / 123456`

说明：项目里既支持 `T_User(Role=staff, Password_Hash)` 的员工账号，也支持 `T_Staff_Account(Password)` 的员工账号（以后端 `AuthModel.login()` 为准）。

---

## 🚀 部署步骤

### 第一步：执行 SQL 脚本（建议用 `source`，避免中文/换行导致的乱码）

```bash
# 进入项目目录
cd "D:\我的资料\数据库设计及其应用\剧本杀管理系统"

# 1) 结构迁移（首次搭建才需要；已执行过可跳过）
mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source database/migrations/001_add_auth.sql"
mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source database/migrations/002_add_script_profile.sql"
mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source database/migrations/003_update_script_base.sql"
mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source database/migrations/004_enhance_lock_record.sql"

# 2) 演示增强（账号/触发器/视图/存储过程/函数/事件）
mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source database/demo/init_complete_system.sql"

# 3) 可选：扩充场次/历史订单/演示锁位（推荐，用于报表展示）
mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source database/demo/extend_schedule_data.sql"
mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source database/demo/insert_history_orders.sql"
mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source database/demo/optimize_lock_system.sql"
 
```

目录说明：
- 结构迁移脚本位于：`database/migrations/`
- 演示增强/演示数据脚本位于：`database/demo/`

> 如果你希望锁位自动过期：需要 MySQL 开启 `event_scheduler`（可在 MySQL 中执行 `SET GLOBAL event_scheduler=ON;`）。

### 第二步：启动系统

```bash
# 启动后端
cd "D:\我的资料\数据库设计及其应用\剧本杀管理系统"
python app.py

# 启动前端（新终端）
cd frontend-vue
npm install
npm run dev
```

### 第三步：测试登录

1. 打开浏览器访问：`http://localhost:5173`
2. 员工登录：`staff_demo / 123456` → 自动跳转 `/admin`
3. 老板登录：`郝飞帆 / 123456` → `/admin`、`/admin/reports` 可按 DM 下拉筛选
4. 玩家：去 `/register` 注册 → 锁位 → 订单 → 支付（用于演示事务/触发器/锁位转化）
   - 用户名：`staff_demo`
   - 密码：`123456`
3. 登录成功后进入员工后台

---

## 📝 重要说明

1. **所有SQL脚本都可以重复执行**，不会报错
2. **员工账号可能来自两处**：`T_User(Role=staff, Password_Hash)` 或 `T_Staff_Account(Password)`（以后端 `AuthModel.login()` 为准）
3. **锁位超时事件已启用**，每分钟自动过期
4. **历史订单数据已补充**，12月20-26日共38笔订单

---

## ✅ 验证清单

- [ ] 员工可以正常登录（staff_demo/123456）
- [ ] 管理后台可以访问
- [ ] 订单列表显示历史数据
- [ ] 场次数据已扩展到2026年1月15日
- [ ] 锁位功能正常工作

