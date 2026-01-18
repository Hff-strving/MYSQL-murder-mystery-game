<template>
  <main class="main-content">
    <div class="container">
      <div class="page-header">
        <h2 class="page-title">综合报表</h2>
      </div>

      <div class="role-tip">
        <span v-if="authStore.isBoss">老板视角：可查看全局数据，并支持按 DM 筛选。</span>
        <span v-else>员工视角：仅展示你本人带队（DM 分域）的数据（后端按 token 自动限制）。</span>
      </div>

      <div class="filters">
        <label class="filter-label">日期</label>
        <input type="date" v-model="startDate" class="filter-input">
        <span class="filter-sep">-</span>
        <input type="date" v-model="endDate" class="filter-input">

        <template v-if="authStore.isBoss">
          <span class="filter-sep">|</span>
          <label class="filter-label">DM</label>
          <select v-model="selectedDmId" class="filter-select">
            <option value="">全部DM</option>
            <option v-for="dm in dms" :key="dm.DM_ID" :value="String(dm.DM_ID)">
              {{ dm.Name }}（{{ dm.DM_ID }}）
            </option>
          </select>
        </template>

        <button class="btn-refresh" @click="reloadAll">刷新</button>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">💰</div>
          <div class="stat-info">
            <div class="stat-label">今日营收</div>
            <div class="stat-value">￥{{ dashboard.today_revenue || 0 }}</div>
            <div class="stat-sub">订单数: {{ dashboard.today_orders || 0 }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">📈</div>
          <div class="stat-info">
            <div class="stat-label">本周营收</div>
            <div class="stat-value">￥{{ dashboard.week_revenue || 0 }}</div>
            <div class="stat-sub">订单数: {{ dashboard.week_orders || 0 }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">🧾</div>
          <div class="stat-info">
            <div class="stat-label">本月营收</div>
            <div class="stat-value">￥{{ dashboard.month_revenue || 0 }}</div>
            <div class="stat-sub">订单数: {{ dashboard.month_orders || 0 }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">🔒</div>
          <div class="stat-info">
            <div class="stat-label">活跃锁位</div>
            <div class="stat-value">{{ dashboard.active_locks || 0 }}</div>
            <div class="stat-sub">未来7天上座率: {{ dashboard.occupancy_rate || 0 }}%</div>
          </div>
        </div>
      </div>

      <div class="report-section">
        <h3 class="section-title">热门剧本 Top 5</h3>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>排名</th>
                <th>剧本名称</th>
                <th>订单数</th>
                <th>总营收</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(script, index) in topScripts" :key="script.Script_ID">
                <td>{{ index + 1 }}</td>
                <td>{{ script.Title }}</td>
                <td>{{ script.order_count }}</td>
                <td>￥{{ script.total_revenue || 0 }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="report-section">
        <h3 class="section-title">房间利用率</h3>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>房间</th>
                <th>场次总数</th>
                <th>已完成</th>
                <th>已支付订单</th>
                <th>利用率(%)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="room in rooms" :key="room.Room_ID">
                <td>{{ room.Room_Name }}</td>
                <td>{{ room.total_schedules }}</td>
                <td>{{ room.completed_schedules }}</td>
                <td>{{ room.paid_orders }}</td>
                <td>{{ room.utilization_rate }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="report-section">
        <h3 class="section-title">锁位转化率</h3>
        <div class="conversion-grid">
          <div class="conversion-card">
            <div class="conversion-label">锁位总数</div>
            <div class="conversion-value">{{ lockConv.total_locks || 0 }}</div>
          </div>
          <div class="conversion-card">
            <div class="conversion-label">转订单锁位</div>
            <div class="conversion-value">{{ lockConv.converted_locks || 0 }}</div>
          </div>
          <div class="conversion-card">
            <div class="conversion-label">锁→单转化率</div>
            <div class="conversion-value">{{ lockConv.lock_to_order_rate || 0 }}%</div>
          </div>
          <div class="conversion-card">
            <div class="conversion-label">单→支付转化率</div>
            <div class="conversion-value">{{ lockConv.order_to_pay_rate || 0 }}%</div>
          </div>
        </div>
      </div>

      <div v-if="authStore.isBoss" class="report-section">
        <h3 class="section-title">DM业绩</h3>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>DM</th>
                <th>场次数</th>
                <th>订单数</th>
                <th>已支付</th>
                <th>营收</th>
                <th>活跃锁位</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in dmPerf" :key="row.DM_ID">
                <td>{{ row.DM_Name }}</td>
                <td>{{ row.schedule_count }}</td>
                <td>{{ row.order_count }}</td>
                <td>{{ row.paid_orders }}</td>
                <td>￥{{ row.revenue || 0 }}</td>
                <td>{{ row.active_locks }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="report-section">
        <h3 class="section-title">后端能力自检（数据库对象）</h3>
        <div v-if="!dbObjects" class="empty">正在加载...</div>
        <div v-else class="db-objects">
          <div class="db-meta">
            <span>DB：{{ dbObjects.schema }}</span>
            <span>Role ENUM：{{ dbObjects.objects.role_enum }}</span>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>类型</th>
                  <th>名称</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="[name, ok] in Object.entries(dbObjects.objects.triggers)" :key="'trg_'+name">
                  <td>触发器</td>
                  <td>{{ name }}</td>
                  <td><span :class="ok ? 'ok' : 'bad'">{{ ok ? 'OK' : '缺失' }}</span></td>
                </tr>
                <tr v-for="[name, ok] in Object.entries(dbObjects.objects.views)" :key="'view_'+name">
                  <td>视图</td>
                  <td>{{ name }}</td>
                  <td><span :class="ok ? 'ok' : 'bad'">{{ ok ? 'OK' : '缺失' }}</span></td>
                </tr>
                <tr v-for="[name, ok] in Object.entries(dbObjects.objects.procedures)" :key="'proc_'+name">
                  <td>存储过程</td>
                  <td>{{ name }}</td>
                  <td><span :class="ok ? 'ok' : 'bad'">{{ ok ? 'OK' : '缺失' }}</span></td>
                </tr>
                <tr v-for="[name, ok] in Object.entries(dbObjects.objects.functions)" :key="'fn_'+name">
                  <td>函数</td>
                  <td>{{ name }}</td>
                  <td><span :class="ok ? 'ok' : 'bad'">{{ ok ? 'OK' : '缺失' }}</span></td>
                </tr>
                <tr v-for="[name, ok] in Object.entries(dbObjects.objects.events)" :key="'evt_'+name">
                  <td>事件</td>
                  <td>{{ name }}</td>
                  <td><span :class="ok ? 'ok' : 'bad'">{{ ok ? 'OK' : '缺失/未创建' }}</span></td>
                </tr>
                <tr v-for="[name, ok] in Object.entries(dbObjects.objects.indexes)" :key="'idx_'+name">
                  <td>关键索引</td>
                  <td>{{ name }}</td>
                  <td><span :class="ok ? 'ok' : 'bad'">{{ ok ? 'OK' : '缺失' }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="db-note">
            提示：触发器用于“防重复预约/防重复锁位”，函数/视图/存储过程用于写报告展示；订单创建/支付/取消在后端使用事务确保一致性。
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ReportAPI, AdminAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()
const authStore = useAuthStore()

const dashboard = ref({})
const topScripts = ref([])
const rooms = ref([])
const lockConv = ref({})
const dmPerf = ref([])
const dbObjects = ref(null)

const dms = ref([])
const selectedDmId = ref('')
const startDate = ref('')
const endDate = ref('')

const loadDMs = async () => {
  try {
    dms.value = await AdminAPI.getDMs()
  } catch (error) {
    showToast(error.message || '加载DM列表失败', true)
  }
}

const loadDbObjects = async () => {
  try {
    dbObjects.value = await AdminAPI.getDbObjects()
  } catch (error) {
    showToast(error.message || '加载数据库对象自检失败', true)
  }
}

const loadDashboard = async () => {
  try {
    const params = selectedDmId.value ? { dm_id: Number(selectedDmId.value) } : {}
    dashboard.value = await ReportAPI.getDashboard(params)
  } catch (error) {
    showToast(error.message || '加载统计数据失败', true)
  }
}

const loadTopScripts = async () => {
  try {
    const params = selectedDmId.value
      ? { limit: 5, dm_id: Number(selectedDmId.value) }
      : { limit: 5 }
    topScripts.value = await ReportAPI.getTopScripts(params)
  } catch (error) {
    showToast(error.message || '加载热门剧本失败', true)
  }
}

const loadRoomUtilization = async () => {
  try {
    const params = {}
    if (startDate.value) params.start = startDate.value
    if (endDate.value) params.end = endDate.value
    if (selectedDmId.value) params.dm_id = Number(selectedDmId.value)
    rooms.value = await ReportAPI.getRoomUtilization(params)
  } catch (error) {
    showToast(error.message || '加载房间利用率失败', true)
  }
}

const loadLockConversion = async () => {
  try {
    const params = {}
    if (startDate.value) params.start = startDate.value
    if (endDate.value) params.end = endDate.value
    if (selectedDmId.value) params.dm_id = Number(selectedDmId.value)
    lockConv.value = await ReportAPI.getLockConversion(params)
  } catch (error) {
    showToast(error.message || '加载锁位转化率失败', true)
  }
}

const loadDMPerformance = async () => {
  if (!authStore.isBoss) return
  try {
    const params = {}
    if (startDate.value) params.start = startDate.value
    if (endDate.value) params.end = endDate.value
    dmPerf.value = await ReportAPI.getDMPerformance(params)
  } catch (error) {
    showToast(error.message || '加载DM业绩失败', true)
  }
}

const reloadAll = () => {
  loadDashboard()
  loadTopScripts()
  loadRoomUtilization()
  loadLockConversion()
  loadDMPerformance()
  loadDbObjects()
}

onMounted(() => {
  if (authStore.isBoss) {
    loadDMs()
  }
  reloadAll()
})

watch([selectedDmId, startDate, endDate], () => {
  reloadAll()
})
</script>

<style scoped>
.main-content {
  padding: 2rem;
  min-height: 100vh;
  background: #f5f5f5;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 1rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 600;
  color: #333;
}

.role-tip {
  margin-bottom: 0.75rem;
  color: #666;
  font-size: 0.95rem;
}

.filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
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

.filter-sep {
  color: #999;
}

.filter-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: 600;
  color: #333;
}

.stat-sub {
  font-size: 0.85rem;
  color: #999;
  margin-top: 0.25rem;
}

.report-section {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 1rem;
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: #f8f9fa;
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #555;
  border-bottom: 2px solid #dee2e6;
}

.data-table td {
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
}

.conversion-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.db-meta {
  display: flex;
  gap: 1rem;
  margin: 0 0 0.75rem 0;
  color: #666;
  font-size: 0.9rem;
}

.db-note {
  margin-top: 0.75rem;
  color: #666;
  font-size: 0.9rem;
}

.ok {
  color: #28a745;
  font-weight: 600;
}

.bad {
  color: #dc3545;
  font-weight: 600;
}

.conversion-card {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
}

.conversion-label {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.conversion-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: #333;
}
</style>
