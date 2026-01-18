import http from '@/utils/http'

// 认证相关API
export const AuthAPI = {
  // 用户登录
  login(username, password) {
    return http.post('/auth/login', { username, password })
  },

  // 用户注册
  register(username, phone, password, role = 'player') {
    return http.post('/auth/register', { username, phone, password, role })
  },

  // 获取当前用户信息
  getCurrentUser() {
    return http.get('/me')
  }
}

// 剧本相关API
export const ScriptAPI = {
  // 获取所有剧本
  getAll(status = null) {
    return http.get('/scripts', { params: { status } })
  },

  // 获取热门剧本
  getHot(limit = 10) {
    return http.get('/scripts/hot', { params: { limit } })
  },

  // 获取剧本详情
  getById(id) {
    return http.get(`/scripts/${id}`)
  }
}

// 场次相关API
export const ScheduleAPI = {
  // 获取剧本的场次列表
  getByScript(scriptId, playerId = null) {
    const params = playerId ? { player_id: playerId } : {}
    return http.get(`/scripts/${scriptId}/schedules`, { params })
  },

  // 获取所有场次（员工）
  getAll(filters = {}) {
    return http.get('/admin/schedules', { params: filters })
  },

  // 创建场次（员工）
  create(data) {
    return http.post('/admin/schedules', data)
  },

  // 更新场次（员工）
  update(scheduleId, data) {
    return http.put(`/admin/schedules/${scheduleId}`, data)
  },

  // 取消场次（员工）
  cancel(scheduleId) {
    return http.post(`/admin/schedules/${scheduleId}/cancel`)
  }
}

// 订单相关API
export const OrderAPI = {
  // 创建订单
  create(scheduleId) {
    return http.post('/orders', { schedule_id: scheduleId })
  },

  // 支付订单
  pay(orderId, channel = 1) {
    return http.post(`/orders/${orderId}/pay`, { channel })
  },

  // 取消订单
  cancel(orderId) {
    return http.post(`/orders/${orderId}/cancel`)
  },

  // 获取我的订单
  getMyOrders() {
    return http.get('/my/orders')
  },

  // 获取所有订单（员工）
  getAdminOrders(params = {}) {
    return http.get('/admin/orders', { params })
  }
}

// 锁位相关API
export const LockAPI = {
  // 创建锁位
  create(scheduleId) {
    return http.post('/locks', { schedule_id: scheduleId })
  },

  // 取消锁位
  cancel(lockId) {
    return http.post(`/locks/${lockId}/cancel`)
  },

  // 获取我的锁位
  getMyLocks() {
    return http.get('/my/locks')
  },

  // 获取所有锁位（员工）
  getAdminLocks(params = {}) {
    return http.get('/admin/locks', { params })
  }
}

// 管理端辅助 API
export const AdminAPI = {
  // 获取 DM 列表（老板筛选用）
  getDMs() {
    return http.get('/admin/dms')
  },

  // 获取房间列表（员工/老板：用于场次创建下拉）
  getRooms() {
    return http.get('/admin/rooms')
  },

  // 数据库对象自检（触发器/视图/存储过程/函数/事件/索引）
  getDbObjects() {
    return http.get('/admin/db-objects')
  }
}

// 报表相关API
export const ReportAPI = {
  // 获取仪表盘统计
  getDashboard(params = {}) {
    return http.get('/admin/dashboard', { params })
  },

  // 获取热门剧本Top N
  getTopScripts(params = {}) {
    return http.get('/admin/reports/top-scripts', { params })
  },

  // 房间利用率
  getRoomUtilization(params = {}) {
    return http.get('/admin/reports/room-utilization', { params })
  },

  // 锁位转化率
  getLockConversion(params = {}) {
    return http.get('/admin/reports/lock-conversion', { params })
  },

  // DM 业绩（老板）
  getDMPerformance(params = {}) {
    return http.get('/admin/reports/dm-performance', { params })
  }
}
