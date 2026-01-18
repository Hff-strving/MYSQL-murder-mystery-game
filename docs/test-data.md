# 剧本杀店务管理系统 - 测试数据说明

## 📊 数据概览

当前推荐的“演示数据”以以下脚本为准（均可重复执行）：

- `database/demo/init_complete_system.sql`：创建/更新演示账号 + 触发器/视图/存储过程/函数（用于报告展示）
- `database/demo/extend_schedule_data.sql`：扩充 2026 年的场次数据（用于场次管理与报表）
- `database/demo/insert_history_orders.sql`：导入历史订单（用于热门推荐与报表统计）
- `database/demo/optimize_lock_system.sql`：演示锁位索引 + 演示锁位数据

`insert_test_data.sql` 属于早期版本（包含旧表 `T_Lock_Record`），容易与当前锁位表 `t_lock_record` 混淆；该文件已从项目中移除，避免误执行。

### 数据统计
- **房间**: 5个主题房间（迷雾森林厅、古堡密室、民国风情馆等）
- **剧本**: 12个热门剧本（年轮、云使、长安疑云等）
- **DM**: 6位主持人（不同星级）
- **玩家**: 50位玩家（丰富的昵称）
- **排期**: 22场次（覆盖未来一周）
- **订单**: 30笔订单（包含已支付、待支付、已退款）
- **流水**: 29条交易记录（支付和退款）
- **锁位记录**: 5条锁位记录（模拟并发场景）

---

## 🚀 使用方法

### 方法一：MySQL Workbench
1. 打开 MySQL Workbench
2. 连接到你的数据库
3. 依次打开并执行以下脚本（推荐顺序）：
   - `database/demo/init_complete_system.sql`
   - `database/demo/extend_schedule_data.sql`
   - `database/demo/insert_history_orders.sql`
   - `database/demo/optimize_lock_system.sql`
4. 点击执行按钮（闪电图标）
5. 查看执行结果（每个脚本末尾都有校验输出）

### 方法二：命令行（推荐：用 `source` 避免乱码）
```bash
mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source database/demo/init_complete_system.sql"
mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source database/demo/extend_schedule_data.sql"
mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source database/demo/insert_history_orders.sql"
mysql -u root -p --default-character-set=utf8mb4 -D "剧本杀店务管理系统" -e "source database/demo/optimize_lock_system.sql"
```

### 方法三：分段执行（排错用）
如果一次性执行遇到问题，可以先只执行：
1. `database/demo/init_complete_system.sql`（账号/触发器/视图/存储过程/函数）
2. 再执行 `database/demo/extend_schedule_data.sql`（场次）
3. 最后执行 `database/demo/insert_history_orders.sql`、`database/demo/optimize_lock_system.sql`（报表/锁位演示数据）

---

## 📋 数据特点

### 1. 业务场景完整
- **已满员场次**: 场次4001（6人）、场次4002（7人）、场次4007（6人）
- **部分预约场次**: 场次4003（3人）
- **待拼车场次**: 其他场次
- **退款场景**: 订单5027（已支付后退款）
- **待支付订单**: 订单5025、5029

### 2. 时间跨度合理
- 排期时间：2025年12月27日 - 2026年1月2日
- 订单创建时间：提前3-7天预约
- 支付时间：订单创建后1-2分钟内完成

### 3. 数据关联完整
- 所有订单都关联到具体的玩家和场次
- 所有已支付订单都有对应的流水记录
- 退款订单有支付和退款两条流水

---

## 🔍 数据验证查询

脚本末尾包含了多个验证查询，执行后可以查看：

1. **各表数据统计** - 确认数据插入数量
2. **热门剧本排行** - 查看哪些剧本最受欢迎
3. **订单状态分布** - 查看待支付、已支付、已退款的数量和金额
4. **DM工作量统计** - 查看每位DM的排期数量
5. **未来可预约场次** - 查看可以预约的场次列表

---

## ⚠️ 注意事项

1. **执行顺序**: 建议先执行 `database/demo/init_complete_system.sql`，再执行其它演示数据脚本
2. **数据清理**: 若要重新演示，可清空订单/锁位相关表或直接换一个新的数据库实例
3. **时间字段**: 演示数据包含未来/历史日期是为了方便报表展示，如需调整请统一修改

---

## 🎯 下一步

数据插入完成后，你可以：
1. 执行验证查询，确认数据正确性
2. 开始后端API开发，连接数据库
3. 测试各种业务场景（预约、支付、退款等）
4. 为前端界面准备真实数据展示

