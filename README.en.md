# Murder Mystery Shop Management (Flask + MySQL + Vue3)

<div align="right">
  <a href="./README.md"><img alt="中文" src="https://img.shields.io/badge/中文-查看-1677ff"></a>
</div>

This is my capstone/course project for **Database Design & Analysis**. The topic is a “Murder Mystery Shop Management System”: a runnable full-stack application that demonstrates database design, constraints, and server-side database capabilities through a complete business flow (**seat locking → ordering → payment → reporting**).

## Tech Stack

- Frontend: Vue 3 + Vite (`frontend-vue/`)
- Backend: Python + Flask (`app.py`)
- Database: MySQL (recommended 5.7+, `utf8mb4`)
- Auth: JWT with 3 roles (player/staff/boss)

## Features

- Auth & authorization: JWT sessions, role-based access control, and staff “DM-scope” data isolation
- Player-side: scripts browsing/details, schedules, seat locking, ordering, payment, order/lock queries
- Admin-side (staff/boss): schedule management, orders/locks list, KPIs, reports (Top scripts, room utilization, lock-to-order conversion, DM performance, etc.)
- Database objects showcase: triggers, views, stored procedures, functions, and optional event scheduler for lock expiration

## Prerequisites

- Python 3.9+
- Node.js 18+ and npm
- MySQL 5.7+ (use `utf8mb4`)

## Quick Start (Local)

1) Configure DB connection

- Edit `database_config.py`: `host/user/password/database`

2) Run SQL scripts

Run migrations in order (first time only):

- `database/migrations/001_add_auth.sql`
- `database/migrations/002_add_script_profile.sql`
- `database/migrations/003_update_script_base.sql`
- `database/migrations/004_enhance_lock_record.sql`

Recommended demo/enhancement scripts:

- `database/demo/init_complete_system.sql`
- `database/demo/extend_schedule_data.sql` (optional)
- `database/demo/insert_history_orders.sql` (optional)
- `database/demo/optimize_lock_system.sql` (optional)

To auto-expire locks, enable MySQL `event_scheduler` (e.g. `SET GLOBAL event_scheduler=ON;`).

3) Start backend

```bash
pip install -r requirements.txt
python app.py
```

Backend: `http://127.0.0.1:5000`

4) Start frontend

```bash
cd frontend-vue
npm install
npm run dev
```

Frontend: `http://127.0.0.1:5173` (proxy `/api -> 5000` is configured)

## Demo Accounts

After running `database/demo/init_complete_system.sql`:

- Boss: `郝飞帆 / 123456`
- Staff: `staff_demo / 123456`
- Player: register via `/register` (or use preloaded `player_3001 / 123456`, etc.)

## Project Structure

- Backend: `app.py`, `models/`, `database.py`, `security_utils.py`
- Frontend (Vue): `frontend-vue/`
- SQL scripts:
  - Schema migrations: `database/migrations/`
  - Demo enhancements / demo data: `database/demo/`
- Cover image sources: `images/`
- Docs: `docs/`
- Design diagrams (CDM/E-R/PDM/dataflow): `docs/design/`

## More Docs

- Deployment: `docs/deploy.md`
- Project overview: `docs/PROJECT_OVERVIEW.md`
- Frontend: `docs/frontend.md`
- Backend: `docs/backend.md`
- Locking design: `docs/lock-design.md`
- Security notes: `docs/security.md`
