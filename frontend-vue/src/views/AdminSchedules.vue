<template>
  <main class="main-content">
    <div class="container">
      <div class="page-header">
        <h2 class="page-title">场次管理</h2>
        <button class="btn btn-primary" @click="openCreateModal">新增场次</button>
      </div>

      <!-- 筛选条件 -->
      <div class="filters">
        <input type="date" v-model="filters.date" placeholder="选择日期" class="filter-input">
        <select v-if="authStore.isBoss" v-model="filters.dm_id" class="filter-select">
          <option value="">全部DM</option>
          <option v-for="dm in dms" :key="dm.DM_ID" :value="String(dm.DM_ID)">
            {{ dm.Name }}（{{ dm.DM_ID }}）
          </option>
        </select>
        <select v-model="filters.status" class="filter-select">
          <option value="">全部状态</option>
          <option value="0">待开始</option>
          <option value="1">已完成</option>
          <option value="2">已取消</option>
        </select>
        <button class="btn btn-secondary" @click="loadSchedules">查询</button>
      </div>

      <!-- 场次列表 -->
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>场次ID</th>
              <th>剧本</th>
              <th>房间</th>
              <th>DM</th>
              <th>开始时间</th>
              <th>价格</th>
              <th>预约/容量</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="schedule in schedules" :key="schedule.Schedule_ID">
              <td>{{ schedule.Schedule_ID }}</td>
              <td>{{ schedule.Script_Title }}</td>
              <td>{{ schedule.Room_Name }}</td>
              <td>{{ schedule.DM_Name }}</td>
              <td>{{ formatDateTime(schedule.Start_Time) }}</td>
              <td>¥{{ schedule.Real_Price }}</td>
              <td>{{ schedule.Booked_Count }}/{{ schedule.Max_Players }}</td>
              <td>
                <span :class="getStatusClass(schedule.Status)">
                  {{ getStatusText(schedule.Status) }}
                </span>
              </td>
              <td>
                <button class="btn-link" @click="editSchedule(schedule)">编辑</button>
                <button class="btn-link danger" @click="cancelSchedule(schedule.Schedule_ID)"
                        v-if="schedule.Status === 0">取消</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 创建/编辑场次模态框 -->
      <div v-if="showCreateModal || showEditModal" class="modal-overlay" @click.self="closeModals">
        <div class="modal-content">
          <h3>{{ showEditModal ? '编辑场次' : '新增场次' }}</h3>
          <form @submit.prevent="submitSchedule">
            <div class="form-group">
              <label>剧本</label>
              <select v-model="scheduleForm.script_id" required class="form-input">
                <option value="" disabled>请选择剧本</option>
                <option v-for="s in scripts" :key="s.Script_ID" :value="String(s.Script_ID)">
                  {{ s.Title }}（{{ s.Script_ID }}）
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>房间</label>
              <select v-model="scheduleForm.room_id" required class="form-input">
                <option value="" disabled>请选择房间</option>
                <option v-for="r in rooms" :key="r.Room_ID" :value="String(r.Room_ID)">
                  {{ r.Room_Name }}（{{ r.Room_ID }}）
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>带队 DM</label>
              <template v-if="authStore.isBoss">
                <select v-model="scheduleForm.dm_id" required class="form-input">
                  <option value="" disabled>请选择 DM</option>
                  <option v-for="dm in dms" :key="dm.DM_ID" :value="String(dm.DM_ID)">
                    {{ dm.Name }}（{{ dm.DM_ID }}）
                  </option>
                </select>
              </template>
              <template v-else>
                <input type="text" :value="`DM_ID = ${authStore.refId}`" disabled class="form-input">
              </template>
            </div>
            <div class="form-group">
              <label>开始时间</label>
              <input type="datetime-local" v-model="scheduleForm.start_time" required class="form-input">
            </div>
            <div class="form-group">
              <label>结束时间</label>
              <input type="datetime-local" v-model="scheduleForm.end_time" required class="form-input">
            </div>
            <div class="form-group">
              <label>价格</label>
              <input type="number" step="0.01" v-model="scheduleForm.real_price" required class="form-input">
            </div>
            <div class="form-actions">
              <button type="button" class="btn btn-secondary" @click="closeModals">取消</button>
              <button type="submit" class="btn btn-primary">保存</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ScheduleAPI, AdminAPI, ScriptAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()
const authStore = useAuthStore()

const schedules = ref([])
const dms = ref([])
const scripts = ref([])
const rooms = ref([])
const filters = ref({
  date: '',
  status: '',
  dm_id: ''
})

const showCreateModal = ref(false)
const showEditModal = ref(false)
const currentScheduleId = ref(null)

const scheduleForm = ref({
  script_id: '',
  room_id: '',
  dm_id: '',
  start_time: '',
  end_time: '',
  real_price: ''
})

const loadMeta = async () => {
  try {
    const [scriptList, roomList] = await Promise.all([
      ScriptAPI.getAll(),
      AdminAPI.getRooms()
    ])
    scripts.value = scriptList
    rooms.value = roomList
  } catch (error) {
    showToast(error.message || '加载基础数据失败（剧本/房间）', true)
  }
}

const openCreateModal = () => {
  currentScheduleId.value = null
  scheduleForm.value = {
    script_id: '',
    room_id: '',
    dm_id: '',
    start_time: '',
    end_time: '',
    real_price: ''
  }
  showCreateModal.value = true
}

const loadSchedules = async () => {
  try {
    const params = {}
    if (filters.value.date) params.date = filters.value.date
    if (filters.value.status !== '') params.status = filters.value.status
    if (authStore.isBoss && filters.value.dm_id) params.dm_id = Number(filters.value.dm_id)

    schedules.value = await ScheduleAPI.getAll(params)
  } catch (error) {
    showToast(error.message || '加载场次失败', true)
  }
}

const submitSchedule = async () => {
  try {
    const toMysqlDatetime = (v) => {
      if (!v) return v
      const s = String(v)
      if (s.includes('T')) return `${s.replace('T', ' ')}:00`
      return s
    }

    const payload = {
      script_id: Number(scheduleForm.value.script_id),
      room_id: Number(scheduleForm.value.room_id),
      start_time: toMysqlDatetime(scheduleForm.value.start_time),
      end_time: toMysqlDatetime(scheduleForm.value.end_time),
      real_price: Number(scheduleForm.value.real_price)
    }

    // 只有老板需要显式传 dm_id；员工端由后端按 token 自动分域
    if (authStore.isBoss) {
      payload.dm_id = Number(scheduleForm.value.dm_id)
    }

    if (showEditModal.value) {
      await ScheduleAPI.update(currentScheduleId.value, payload)
      showToast('场次更新成功')
    } else {
      await ScheduleAPI.create(payload)
      showToast('场次创建成功')
    }
    closeModals()
    loadSchedules()
  } catch (error) {
    showToast(error.message || '操作失败', true)
  }
}

const editSchedule = (schedule) => {
  currentScheduleId.value = schedule.Schedule_ID
  scheduleForm.value = {
    script_id: String(schedule.Script_ID),
    room_id: String(schedule.Room_ID),
    dm_id: String(schedule.DM_ID),
    start_time: schedule.Start_Time.replace(' ', 'T').slice(0, 16),
    end_time: schedule.End_Time.replace(' ', 'T').slice(0, 16),
    real_price: schedule.Real_Price
  }
  showEditModal.value = true
}

const cancelSchedule = async (scheduleId) => {
  if (!confirm('确定要取消该场次吗？')) return

  try {
    await ScheduleAPI.cancel(scheduleId)
    showToast('场次已取消')
    loadSchedules()
  } catch (error) {
    showToast(error.message || '取消失败', true)
  }
}

const closeModals = () => {
  showCreateModal.value = false
  showEditModal.value = false
  scheduleForm.value = {
    script_id: '',
    room_id: '',
    dm_id: '',
    start_time: '',
    end_time: '',
    real_price: ''
  }
}

const formatDateTime = (datetime) => {
  return datetime ? datetime.slice(0, 16).replace('T', ' ') : ''
}

const getStatusText = (status) => {
  const statusMap = { 0: '待开始', 1: '已完成', 2: '已取消' }
  return statusMap[status] || '未知'
}

const getStatusClass = (status) => {
  const classMap = { 0: 'status-pending', 1: 'status-success', 2: 'status-cancelled' }
  return classMap[status] || ''
}

onMounted(() => {
  loadMeta()
  if (authStore.isBoss) {
    AdminAPI.getDMs().then((list) => { dms.value = list }).catch(() => {})
  }
  loadSchedules()
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 600;
  color: #333;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
}

.filter-input, .filter-select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-link {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  margin-right: 0.5rem;
}

.btn-link.danger {
  color: #dc3545;
}

.status-pending {
  color: #ffc107;
  font-weight: 500;
}

.status-success {
  color: #28a745;
  font-weight: 500;
}

.status-cancelled {
  color: #dc3545;
  font-weight: 500;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}
</style>
