## Vue 前端启动指南（frontend-vue）

本项目已淘汰原生 `frontend/`（HTML/CSS/JS）目录，前端统一使用 Vue 版本：`frontend-vue/`。

### 1) 启动后端（Flask）

在项目根目录：

```bash
python app.py
```

默认后端地址：`http://127.0.0.1:5000`

### 2) 启动前端（Vue + Vite）

```bash
cd frontend-vue
npm run dev
```

默认前端地址：`http://127.0.0.1:5173`

说明：
- `vite.config.js` 已配置代理：`/api -> http://127.0.0.1:5000`，前端代码统一以 `/api/...` 访问后端。
- 剧本封面图片放在：`frontend-vue/public/assets/images/`，页面使用 `/assets/images/<Cover_Image>` 引用。

### 3) 常见问题

1. **报错 “LockAPI is not defined”**
   - 原因：打开了旧的原生前端页面（已淘汰）。
   - 解决：使用 `npm run dev` 打开的 `http://127.0.0.1:5173`。

2. **员工端进入管理后台提示“无权限访问”**
   - 管理后台地址：`http://127.0.0.1:5173/admin`（注意是 `:` 不是 `.`）。
   - 先确认你登录的账号角色是 `staff` 或 `boss`（后端接口 `/api/admin/*` 会校验 token 里的 `role`）。
   - 如果你执行过 `database/demo/init_complete_system.sql`，可用演示员工账号：`staff_demo / 123456`。
   - 也可用 DM 对应员工账号：`staff_<DM_ID> / 123456`（例如 `staff_2001 / 123456`）。
   - 老板账号（全局可见）：`郝飞帆 / 123456`。
   - 若修改了数据库角色或权限，请退出登录后重新登录（必要时清空浏览器 `localStorage`）。
