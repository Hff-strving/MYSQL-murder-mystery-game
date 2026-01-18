<template>
  <main class="main-content">
    <div class="container">
      <div class="page-header">
        <h2 class="page-title">管理后台</h2>
        <p class="page-subtitle">{{ authStore.isBoss ? '老板全局管理面板' : '员工专用管理面板（仅显示本人带队数据）' }}</p>
      </div>

      <!-- 老板：按DM筛选 -->
      <div v-if="authStore.isBoss" class="filters">
        <label class="filter-label">按DM筛选</label>
        <select v-model="selectedDmId" class="filter-select">
          <option value="">全部DM</option>
          <option v-for="dm in dms" :key="dm.DM_ID" :value="String(dm.DM_ID)">
            {{ dm.Name }}（{{ dm.DM_ID }}）
          </option>
        </select>
        <button class="btn-refresh" @click="reloadAll">刷新</button>
      </div>

      <!-- 错误提示 Banner -->
      <div v-if="errorMessage" class="error-banner">
        <div class="error-content">
          <span class="error-icon">⚠️</span>
          <div class="error-text">
            <strong>加载失败：</strong>{{ errorMessage }}
          </div>
          <button class="error-close" @click="errorMessage = ''">✕</button>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">📋</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalOrders }}</div>
            <div class="stat-label">总订单数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">✅</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.paidOrders }}</div>
            <div class="stat-label">已支付订单</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">💰</div>
          <div class="stat-info">
            <div class="stat-value">¥{{ stats.totalRevenue }}</div>
            <div class="stat-label">总营收</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">🔒</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.activeLocks }}</div>
            <div class="stat-label">活跃锁位</div>
          </div>
        </div>
      </div>

      <!-- 标签页切换 -->
      <div class="tabs">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'orders' }"
          @click="activeTab = 'orders'"
        >
          订单管理
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'locks' }"
          @click="activeTab = 'locks'"
        >
          锁位管理
        </button>
      </div>

      <!-- 订单列表 -->
      <div v-if="activeTab === 'orders'" class="admin-section">
        <h3>订单列表</h3>
        <div v-if="loadingOrders" class="loading">正在加载...</div>
        <div v-else-if="orders.length === 0" class="empty">暂无订单</div>
        <div v-else class="admin-table">
          <table>
            <thead>
              <tr>
                <th>订单ID</th>
                <th>玩家ID</th>
                <th>剧本</th>
                <th v-if="authStore.isBoss">DM</th>
                <th>场次时间</th>
                <th>房间</th>
                <th>金额</th>
                <th>状态</th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.Order_ID">
                <td>{{ order.Order_ID }}</td>
                <td>{{ order.Player_ID }}</td>
                <td>{{ order.Script_Title }}</td>
                <td v-if="authStore.isBoss">{{ order.DM_Name }}</td>
                <td>{{ formatDateTime(order.Start_Time) }}</td>
                <td>{{ order.Room_Name || '未知' }}</td>
                <td class="price">¥{{ order.Amount }}</td>
                <td>
                  <span :class="getOrderStatusClass(order.Pay_Status)">
                    {{ getOrderStatusText(order.Pay_Status) }}
                  </span>
                </td>
                <td>{{ formatDateTime(order.Create_Time) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 锁位列表 -->
      <div v-if="activeTab === 'locks'" class="admin-section">
        <h3>锁位列表</h3>
        <div v-if="loadingLocks" class="loading">正在加载...</div>
        <div v-else-if="locks.length === 0" class="empty">暂无锁位</div>
        <div v-else class="admin-table">
          <table>
            <thead>
              <tr>
                <th>锁位ID</th>
                <th>玩家</th>
                <th>剧本</th>
                <th v-if="authStore.isBoss">DM</th>
                <th>场次时间</th>
                <th>房间</th>
                <th>锁定时间</th>
                <th>过期时间</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lock in locks" :key="lock.LockID">
                <td>{{ lock.LockID }}</td>
                <td>{{ lock.Player_Name }}</td>
                <td>{{ lock.Script_Title }}</td>
                <td v-if="authStore.isBoss">{{ lock.DM_Name }}</td>
                <td>{{ formatDateTime(lock.Start_Time) }}</td>
                <td>{{ lock.Room_Name }}</td>
                <td>{{ formatDateTime(lock.LockTime) }}</td>
                <td>{{ formatDateTime(lock.ExpireTime) }}</td>
                <td>
                  <span :class="getLockStatusClass(lock.Status)">
                    {{ getLockStatusText(lock.Status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { OrderAPI, LockAPI, AdminAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

const { showToast } = useToast()
const authStore = useAuthStore()

const activeTab = ref('orders')
const orders = ref([])
const locks = ref([])
const loadingOrders = ref(false)
const loadingLocks = ref(false)
const errorMessage = ref('')
const dms = ref([])
const selectedDmId = ref('')

const stats = computed(() => {
  const totalOrders = orders.value.length
  const paidOrders = orders.value.filter(o => o.Pay_Status === 1).length
  const totalRevenue = orders.value
    .filter(o => o.Pay_Status === 1)
    .reduce((sum, o) => sum + parseFloat(o.Amount), 0)
    .toFixed(2)
  const activeLocks = locks.value.filter(l => l.Status === 0).length

  return { totalOrders, paidOrders, totalRevenue, activeLocks }
})

const loadOrders = async () => {
  loadingOrders.value = true
  try {
    const params = authStore.isBoss && selectedDmId.value ? { dm_id: Number(selectedDmId.value) } : {}
    orders.value = await OrderAPI.getAdminOrders(params)
    console.log('[AdminDashboard] 订单加载成功:', orders.value.length, '条')
  } catch (error) {
    const errMsg = `订单接口错误 - ${error.message || '未知错误'}`
    errorMessage.value = errMsg
    console.error('[AdminDashboard] 订单加载失败:', error)
    showToast(errMsg, true)
  } finally {
    loadingOrders.value = false
  }
}

const loadLocks = async () => {
  loadingLocks.value = true
  try {
    const params = authStore.isBoss && selectedDmId.value ? { dm_id: Number(selectedDmId.value) } : {}
    locks.value = await LockAPI.getAdminLocks(params)
    console.log('[AdminDashboard] 锁位加载成功:', locks.value.length, '条')
  } catch (error) {
    const errMsg = `锁位接口错误 - ${error.message || '未知错误'}`
    errorMessage.value = errMsg
    console.error('[AdminDashboard] 锁位加载失败:', error)
    showToast(errMsg, true)
  } finally {
    loadingLocks.value = false
  }
}

const formatDateTime = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getOrderStatusText = (status) => {
  const map = { 0: '待支付', 1: '已支付', 2: '已退款', 3: '已取消' }
  return map[status] || '未知'
}

const getOrderStatusClass = (status) => {
  const map = { 0: 'status-unpaid', 1: 'status-paid', 2: 'status-refunded', 3: 'status-cancelled' }
  return map[status] || ''
}

const getLockStatusText = (status) => {
  const map = { 0: '锁定中', 1: '已转订单', 2: '已释放', 3: '已过期' }
  return map[status] || '未知'
}

const getLockStatusClass = (status) => {
  const map = { 0: 'status-locked', 1: 'status-converted', 2: 'status-released', 3: 'status-expired' }
  return map[status] || ''
}

onMounted(() => {
  if (authStore.isBoss) {
    AdminAPI.getDMs().then((list) => { dms.value = list }).catch(() => {})
  }
  loadOrders()
  loadLocks()
})

const reloadAll = () => {
  loadOrders()
  loadLocks()
}

watch(selectedDmId, () => {
  reloadAll()
})
</script>

<style scoped>
.error-banner {
  background: #fee;
  border: 2px solid #f44;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  animation: slideDown 0.3s ease;
}

.error-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.error-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.error-text {
  flex: 1;
  color: #c00;
  font-size: 0.95rem;
}

.error-text strong {
  font-weight: 600;
}

.error-close {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #999;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  transition: color 0.2s;
}

.error-close:hover {
  color: #333;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.filters {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  margin-bottom: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.filter-label {
  font-weight: 600;
  color: #555;
}

.filter-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  min-width: 240px;
}

.btn-refresh {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: #f8f9fa;
  cursor: pointer;
}
</style>
