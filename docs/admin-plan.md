# 剧本杀店务管理系统（Flask + MySQL + Vue）管理后台规划与实现说明

## 1. 项目目标（为什么要做管理后台）

本项目不是“只做个页面”，而是用于展示数据库课程大作业的后端能力：

- 认证与权限：JWT 登录态、角色权限（player / staff / boss）
- 业务链路：锁位 → 预约（生成订单）→ 支付（流水）→ 取消/退款
- 数据一致性：事务、触发器、唯一约束、视图/存储过程/函数
- 可演示性：老板看全局，员工只能看自己带队（DM）的数据

## 2. 权限模型（已落地）

### 2.1 角色定义

- `player`：玩家，只能操作自己的预约/锁位/订单
- `staff`：员工（等价于 DM），只能看到**自己带队**的订单/锁位/场次/报表
- `boss`：老板，能看到全局数据，并支持按 DM 筛选

### 2.2 员工与 DM 的绑定

员工分域通过 `T_User.Ref_ID -> T_DM.DM_ID` 完成：

- staff 登录后，后端会把所有 `/api/admin/*` 数据限制到 `DM_ID = Ref_ID`
- boss 登录后，后端允许 `?dm_id=xxxx` 过滤；不传则为全局

## 3. 页面规划（Vue）

### 3.1 `/admin` 管理后台（订单 + 锁位）

- Tabs：订单列表 / 锁位列表
- boss：显示 DM 列，支持 DM 下拉筛选
- staff：只显示本人 DM 数据（无需筛选）

### 3.2 `/admin/schedules` 场次管理（CRUD）

- 列表：场次时间、房间、DM、剧本、预约数/容量、状态
- boss：可按 DM 筛选、创建/编辑任意 DM 的场次
- staff：只能创建/编辑/取消自己 DM 的场次（后端强校验）

### 3.3 `/admin/reports` 综合报表

- 统计卡：今日/本周/本月营收与订单数、活跃锁位、未来7天上座率
- 热门剧本 Top 5
- 房间利用率
- 锁位转化率（锁→单、单→支付）
- boss 专属：DM 业绩表（场次数、订单数、营收、活跃锁位）

## 4. 后端 API 规划（已实现）

### 4.1 认证

- `POST /api/auth/register`：仅允许注册 player
- `POST /api/auth/login`：player/staff/boss 登录（JWT）
- `GET /api/me`：返回统一字段 `{user_id, username, role, ref_id}`

### 4.2 玩家端

- `GET /api/scripts` / `GET /api/scripts/<id>`
- `GET /api/scripts/<id>/schedules?player_id=<Player_ID>`（含 `User_Booked`、`User_Locked`）
- `POST /api/locks` / `POST /api/locks/<id>/cancel` / `GET /api/my/locks`
- `POST /api/orders` / `POST /api/orders/<id>/pay` / `POST /api/orders/<id>/cancel` / `GET /api/my/orders`

### 4.3 管理端（staff/boss）

- `GET /api/admin/orders`（按 DM 分域；boss 可 `?dm_id=`）
- `GET /api/admin/locks`（按 DM 分域；boss 可 `?dm_id=`）
- `GET/POST/PUT/POST(cancel) /api/admin/schedules...`（按 DM 分域）
- `GET /api/admin/dashboard`（按 DM 分域；统计 + 最近订单 + 即将开始场次）
- `GET /api/admin/reports/top-scripts`（按 DM 分域）
- `GET /api/admin/reports/room-utilization`（按 DM 分域）
- `GET /api/admin/reports/lock-conversion`（按 DM 分域）
- `GET /api/admin/reports/dm-performance`（boss）
- `GET /api/admin/dms`（boss，筛选用）

## 5. 数据库对象（用于报告展示）

`database/demo/init_complete_system.sql` 会创建/确保：

- 触发器：
  - `trg_prevent_duplicate_order`：防重复预约
  - `trg_prevent_duplicate_lock`：防重复锁位 + 自动填充 ExpireTime
- 事件（可选）：`evt_expire_locks`（需要 MySQL event_scheduler 权限）
- 视图：
  - `v_order_detail`：订单全量明细视图
  - `v_lock_detail`：锁位全量明细视图
- 存储过程：
  - `sp_dm_orders(p_dm_id)`：按 DM 查询订单视图
  - `sp_dm_locks(p_dm_id)`：按 DM 查询锁位视图
- 函数：
  - `fn_schedule_occupied(schedule_id)`：计算预约+锁位占用数

## 6. 验收测试建议（最短路径）

1) 执行初始化脚本：`source database/demo/init_complete_system.sql`
2) 登录 boss：`Boss / 123456` → `/admin`、`/admin/reports`（全局+筛选）
3) 登录 staff：`staff_2001 / 123456` → `/admin` 只见本人 DM 数据
4) 玩家：注册 → 锁位 → 在“我的锁位”点“去预约/支付” → 支付 → 订单可见
