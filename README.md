<div align="right">
  <img alt="中文" src="https://img.shields.io/badge/中文-当前-1677ff">
  <a href="./README.en.md"><img alt="English" src="https://img.shields.io/badge/English-View-2ea44f"></a>
</div>

# 剧本杀店务管理系统（Flask + MySQL + Vue3）

这是我《数据库设计与分析》（数据库设计及其应用）课程的结课大作业/实验项目。题目方向为“剧本杀店务管理系统”：用一个可运行的前后端系统，将数据库设计、约束与服务端能力（事务/触发器/视图/存储过程/函数/事件）落到具体业务链路中（锁位→下单→支付→报表）。

## 技术栈

- 前端：Vue 3 + Vite（目录：`frontend-vue/`）
- 后端：Python + Flask（入口：`app.py`）
- 数据库：MySQL（建议 5.7+，字符集 `utf8mb4`）
- 鉴权：JWT（player/staff/boss 三类角色）

## 功能概览

- 统一登录与鉴权：JWT 登录态、按角色与“DM 分域”限制数据范围
- 玩家端：剧本列表/详情、场次查看、锁位、下单、支付、订单/锁位查询
- 管理端（员工/老板）：场次管理、订单与锁位列表、统计指标、综合报表（热门剧本 Top、房间利用率、锁位转化率、DM 业绩等）
- 数据库对象演示：触发器（防重复锁位/下单）、视图（订单/锁位明细）、存储过程（按 DM 查询）、函数（场次占用人数）、事件（定时过期锁位，可选）

## 运行前置条件

- Python 3.9+（建议使用 venv）
- Node.js 18+ 与 npm（用于前端）
- MySQL 5.7+（需启用/使用 `utf8mb4`）

## 本地启动（推荐路径）

1) 配置数据库连接

- 修改 `database_config.py`：`host/user/password/database`
- 建议不要使用弱密码；生产/展示环境可改为读取环境变量（项目当前为课程演示配置）

2) 执行 SQL 脚本

按顺序执行迁移脚本（首次搭建）：

- `database/migrations/001_add_auth.sql`
- `database/migrations/002_add_script_profile.sql`
- `database/migrations/003_update_script_base.sql`
- `database/migrations/004_enhance_lock_record.sql`

推荐执行演示增强/演示数据（账号 + 触发器/视图/存储过程/函数/事件）：

- `database/demo/init_complete_system.sql`
- `database/demo/extend_schedule_data.sql`（可选）
- `database/demo/insert_history_orders.sql`（可选）
- `database/demo/optimize_lock_system.sql`（可选）

> 若希望锁位自动过期：需要 MySQL 开启 `event_scheduler`（例如 `SET GLOBAL event_scheduler=ON;`）。

3) 启动后端（Flask）

```bash
pip install -r requirements.txt
python app.py
```

后端默认：`http://127.0.0.1:5000`

4) 启动前端（Vue + Vite）

```bash
cd frontend-vue
npm install
npm run dev
```

前端默认：`http://127.0.0.1:5173`（已配置 `/api -> 5000` 代理）

## 演示账号

执行 `database/demo/init_complete_system.sql` 后可使用：

- 老板：`boss / 123456`
- 员工：`staff_demo / 123456`
- 玩家：建议从 `/register` 注册（或使用脚本内已导入的 `player_3001 / 123456` 等）

## 目录结构

- 后端：`app.py`、`models/`、`database.py`、`security_utils.py`
- 前端（Vue）：`frontend-vue/`
- SQL 脚本：`database/migrations/`、`database/demo/`
- 文档：`docs/`（部署、前后端启动、锁位设计、安全说明等）
- 设计图：`docs/design/`（CDM/E-R/PDM/数据流图）
- 图片素材：`images/`、`frontend-vue/public/assets/images/`

## 更多文档

- 部署与验收：`docs/deploy.md`
- 项目概览：`docs/PROJECT_OVERVIEW.md`
- 前端启动：`docs/frontend.md`
- 后端启动：`docs/backend.md`
- 锁位机制：`docs/lock-design.md`
- 安全说明：`docs/security.md`
