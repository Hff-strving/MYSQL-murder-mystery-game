# 锁位机制设计方案（t_lock_record）

## 1. 业务场景

锁位用于“拼车/占位”：玩家在正式生成订单前，先锁定一个场次名额（默认 15 分钟），避免并发抢占导致超卖。

典型流程：

1) 玩家在详情页看到某个场次 → 点击“锁位拼车”
2) 系统写入 `t_lock_record`（Status=0，ExpireTime=Now+15min）
3) 玩家在锁位有效期内点击“去预约/支付”（生成订单）
4) 锁位转订单（Status=1），后续以订单占位为准
5) 超时未操作 → 锁位过期（Status=3）或被统计逻辑视作无效

## 2. 状态机

`t_lock_record.Status` 约定：

- `0`：锁定中（有效，ExpireTime > NOW）
- `1`：已转订单（由锁位生成订单后标记）
- `2`：已释放（玩家主动取消）
- `3`：已过期（ExpireTime < NOW 或事件任务更新）

## 3. 表结构（当前项目使用）

字段（以现库为准）：

- `LockID`：主键（无自增时由后端生成）
- `Schedule_ID`：场次
- `Player_ID`：玩家
- `LockTime`：锁定时间
- `ExpireTime`：过期时间
- `Status`：状态（见上）

## 4. 一致性与并发控制

### 4.1 防重复锁位

数据库触发器（`database/demo/init_complete_system.sql`）：

- `trg_prevent_duplicate_lock`：同一玩家同一场次，禁止重复插入 Status=0 的锁位

后端也会做同样的业务校验（双保险）。

### 4.2 防超卖

锁位与订单都占用名额：

- 已预约（订单）：`T_Order.Pay_Status IN (0,1)`
- 有效锁位：`t_lock_record.Status=0 AND ExpireTime>NOW()`

后端创建订单与创建锁位都会检查“预约数 + 有效锁位数 < Max_Players”。

### 4.3 锁位过期

两种方案：

- **逻辑过期**：所有统计/展示只认 `ExpireTime>NOW()`，无需后台任务
- **事件过期（可选）**：`evt_expire_locks` 每分钟把超时锁位置为 Status=3（需要 MySQL `event_scheduler` 权限）

## 5. 与订单的联动

### 5.1 锁位转订单

当玩家对同一场次创建订单时：

- 插入 `T_Order`
- 若存在有效锁位（Status=0），更新为 `Status=1`（已转订单）

该过程在后端用事务保证一致性。

### 5.2 取消锁位/取消订单

- 取消锁位：更新 `t_lock_record.Status=2`
- 取消订单：更新 `T_Order.Pay_Status=3`（已取消）或 `2`（已退款）

## 6. 前端交互（Vue）

- 详情页：显示场次状态（可预约/已满/已锁位/已预约）
- 我的锁位：对 `Status=0` 显示按钮：
  - “去预约/支付”（调用创建订单，跳转订单页）
  - “取消锁位”

## 7. 快速验证 SQL

- 查看锁位状态分布：  
  `SELECT Status, COUNT(*) FROM t_lock_record GROUP BY Status;`

- 查看某个场次当前占用：  
  `SELECT fn_schedule_occupied(4011) AS occupied;`
