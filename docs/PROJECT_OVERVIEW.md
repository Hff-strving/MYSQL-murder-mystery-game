# 剧本杀店务管理系统（Flask + MySQL + Vue3）项目概览

本项目用于数据库课程大作业展示：用一个可运行的前后端系统，演示**认证鉴权、角色分域、锁位→下单→支付链路、事务、触发器、视图/存储过程/函数、报表统计**等能力。

## 一、访问入口（本地）

- 前端（Vite）：`http://localhost:5173/`
- 后端（Flask API）：`http://localhost:5000/`

说明：前端已通过 `vite.config.js` 配置代理，页面请求统一走 `/api/...` 转发到后端。

## 二、角色与演示账号

系统角色：

- `player`：玩家（可锁位、下单、支付、查看“我的订单/我的锁位”）
- `staff`：员工/DM（可进入管理后台，但**只能查看自己带队（DM_ID）相关数据**）
- `boss`：老板（可查看全店数据，支持按 DM 筛选，能看综合报表/DM业绩）

演示账号（执行 `database/demo/init_complete_system.sql` 后）：

- 老板：`Boss / 123456`
- 员工：`staff_demo / 123456`（默认绑定一个 DM）
- 玩家：建议从 `/register` 注册；或使用已导入的 `player_3001 / 123456` 等

## 三、前端 UI 页面（Vue Router 路径）

玩家端：

- `/`：剧本大厅（全部/热门切换；展示封面、分类、难度、人数、价格）
- `/scripts/:id`：剧本详情 + 场次列表（展示场次状态；按钮：锁位拼车/立即预约）
- `/orders`：我的订单（玩家专用：支付/取消/查看状态）
- `/my-locks`：我的锁位（玩家专用：查看锁位与过期时间、取消锁位）
- `/profile`：个人中心（查看用户名/角色/user_id/ref_id，退出登录）

登录与注册：

- `/login`：登录（玩家/员工/老板统一入口）
- `/register`：注册（仅玩家）

管理端（员工/老板）：

- `/admin`：管理后台（订单列表/锁位列表 + 汇总指标；老板支持按 DM 筛选）
- `/admin/schedules`：场次管理（CRUD：创建/编辑/取消；下拉选择房间/剧本/DM）
- `/admin/reports`：综合报表（热门剧本Top、房间利用率、锁位转化率、老板专属 DM 业绩；含“数据库对象自检”）

## 四、数据库核心表（逻辑结构）

- `T_User`：认证与角色（`Role=player/staff/boss`，`Ref_ID` 指向 `T_Player` 或 `T_DM`）
- `T_Player`：玩家档案
- `T_DM`：员工/主持人档案
- `T_Room`：房间
- `T_Script`：剧本基础信息（含 `Cover_Image`）
- `T_Script_Profile`：剧本档案（3NF 拆分：分类/难度/时长/简介等）
- `T_Schedule`：场次排期（关联剧本/房间/DM/价格/时间）
- `t_lock_record`：锁位记录（含过期时间与状态流转）
- `T_Order`：订单（支付状态）
- `T_Transaction`：交易流水（支付/退款等记录）

## 五、数据库对象（触发器 / 视图 / 存储过程 / 函数 / 事件）

这些对象由 `database/demo/init_complete_system.sql` 创建，用于展示数据库“服务端能力”与业务约束下沉。

### 1) 触发器（Triggers）

- `trg_prevent_duplicate_order`：防止同一玩家对同一场次重复有效预约（兜底约束）
- `trg_prevent_duplicate_lock`：防止同一玩家对同一场次重复锁位；并自动补齐锁位 `ExpireTime`（默认 15 分钟）

### 2) 视图（Views）

- `v_order_detail`：订单明细视图（订单 + 场次 + 房间 + DM + 剧本联结封装）
- `v_lock_detail`：锁位明细视图（锁位 + 场次 + 房间 + DM + 剧本联结封装）

### 3) 存储过程（Stored Procedures）

- `sp_dm_orders(p_dm_id)`：按 DM 查询订单（员工分域/老板筛选支撑）
- `sp_dm_locks(p_dm_id)`：按 DM 查询锁位（员工分域/老板筛选支撑）

### 4) 函数（Function）

- `fn_schedule_occupied(p_schedule_id)`：计算场次占用人数（已预约 + 有效锁位）

### 5) 事件（Event，可选）

- `evt_expire_locks`：定时将过期锁位置为失效（需要 MySQL `event_scheduler=ON`）

## 六、关键业务与事务一致性

- 锁位：写入 `t_lock_record`，并通过 `ExpireTime` 与状态字段实现“临时占座”。
- 下单：后端事务写入 `T_Order`，若存在锁位则同步把锁位状态更新为“已转订单”，避免重复占用。
- 支付：后端事务同时更新 `T_Order.Pay_Status` 与写入 `T_Transaction`，保证订单与流水一致。
- 取消：后端事务更新订单状态，并释放关联锁位（如存在）。

## 七、SQL 脚本（建议执行顺序）

结构迁移（首次搭建）：

- `database/migrations/001_add_auth.sql`
- `database/migrations/002_add_script_profile.sql`
- `database/migrations/003_update_script_base.sql`
- `database/migrations/004_enhance_lock_record.sql`

演示增强/演示数据（推荐）：

- `database/demo/init_complete_system.sql`
- `database/demo/extend_schedule_data.sql`
- `database/demo/insert_history_orders.sql`
- `database/demo/optimize_lock_system.sql`

提示：已删除 `node_modules` 后，如需再次启动前端，请在 `frontend-vue/` 下执行 `npm install` 再运行 `npm run dev`。
