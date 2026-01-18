<template>
  <main class="main-content">
    <div class="container">
      <div v-if="loading" class="loading">正在加载...</div>
      <div v-else-if="script" id="scriptDetail">
        <!-- 剧本详情 -->
        <div class="script-detail-header">
          <img
            :src="getCoverUrl(script.Cover_Image)"
            id="scriptCover"
            class="script-detail-cover"
            :alt="script.Title"
            @error="handleImageError"
          >
          <div class="script-detail-info">
            <h2 id="scriptTitle" class="script-detail-title">{{ script.Title }}</h2>
            <div class="script-meta">
              <div class="meta-item">
                <span class="meta-label">分类：</span>
                <span id="scriptType">{{ script.Group_Category || script.Type }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">人数：</span>
                <span id="scriptPlayers">{{ script.Gender_Config || `${script.Min_Players}-${script.Max_Players}人` }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">时长：</span>
                <span id="scriptDuration">{{ getDuration(script) }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">价格：</span>
                <span id="scriptPrice" class="price">¥{{ script.Base_Price }}</span>
              </div>
              <div v-if="script.Difficulty" class="meta-item">
                <span class="meta-label">难度：</span>
                <span id="scriptDifficulty">{{ '★'.repeat(script.Difficulty) }}{{ '☆'.repeat(5 - script.Difficulty) }}</span>
              </div>
            </div>
            <div v-if="script.Synopsis" class="script-synopsis">
              <h3>剧本简介</h3>
              <p id="scriptSynopsis">{{ script.Synopsis }}</p>
            </div>
          </div>
        </div>

        <!-- 场次列表 -->
        <div class="schedules-section">
          <h3>可预约场次</h3>
          <div v-if="schedules.length === 0" class="empty">暂无可预约场次</div>
          <div v-else id="schedulesList" class="schedules-list">
            <div
              v-for="schedule in schedules"
              :key="schedule.Schedule_ID"
              class="schedule-card"
            >
              <div class="schedule-info">
                <div class="schedule-item">
                  <span class="schedule-label">开始时间</span>
                  <span class="schedule-value">{{ formatDateTime(schedule.Start_Time) }}</span>
                </div>
                <div class="schedule-item">
                  <span class="schedule-label">房间</span>
                  <span class="schedule-value">{{ schedule.Room_Name }}</span>
                </div>
                <div class="schedule-item">
                  <span class="schedule-label">主持人</span>
                  <span class="schedule-value">{{ schedule.DM_Name }}</span>
                </div>
                <div class="schedule-item">
                  <span class="schedule-label">价格</span>
                  <span class="schedule-value price">¥{{ schedule.Real_Price }}</span>
                </div>
                <div class="schedule-item">
                  <span class="schedule-label">状态</span>
                  <span class="schedule-value">
                    <span :class="getStatusClass(schedule)">{{ getStatusText(schedule) }}</span>
                    ({{ getTotalOccupied(schedule) }}/{{ schedule.Max_Players }})
                  </span>
                </div>
              </div>
              <div class="schedule-actions">
                <button
                  v-if="canBook(schedule)"
                  class="btn-primary"
                  @click="bookSchedule(schedule.Schedule_ID)"
                >
                  立即预约
                </button>
                <button
                  v-if="canLock(schedule)"
                  class="btn-cancel"
                  @click="lockSchedule(schedule.Schedule_ID)"
                >
                  锁位拼车
                </button>
                <button v-if="!canBook(schedule) && !canLock(schedule)" class="btn-primary" disabled>
                  {{ getButtonText(schedule) }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ScriptAPI, ScheduleAPI, OrderAPI, LockAPI } from '@/api'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { showToast } = useToast()

const script = ref(null)
const schedules = ref([])
const loading = ref(true)

const scriptId = computed(() => route.params.id)

const loadData = async () => {
  loading.value = true
  try {
    const playerId = authStore.isPlayer ? authStore.refId : null
    const [scriptData, schedulesData] = await Promise.all([
      ScriptAPI.getById(scriptId.value),
      ScheduleAPI.getByScript(scriptId.value, playerId)
    ])
    script.value = scriptData
    schedules.value = schedulesData
  } catch (error) {
    showToast(error.message || '加载失败', true)
    setTimeout(() => router.push('/'), 2000)
  } finally {
    loading.value = false
  }
}

const getCoverUrl = (coverImage) => {
  return coverImage ? `/assets/images/${coverImage}` : '/assets/images/default.jpg'
}

const handleImageError = (e) => {
  e.target.src = '/assets/images/default.jpg'
}

const getDuration = (script) => {
  if (script.Duration_Min_Minutes && script.Duration_Max_Minutes) {
    const minHours = (script.Duration_Min_Minutes / 60).toFixed(1)
    const maxHours = (script.Duration_Max_Minutes / 60).toFixed(1)
    return `${minHours}-${maxHours}小时`
  }
  return '约4小时'
}

const formatDateTime = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getTotalOccupied = (schedule) => {
  return (schedule.Booked_Count || 0) + (schedule.Locked_Count || 0)
}

const getStatusText = (schedule) => {
  const userBooked = schedule.User_Booked > 0
  const userLocked = schedule.User_Locked > 0
  const isFull = getTotalOccupied(schedule) >= schedule.Max_Players

  if (userBooked) return '✓ 已预约'
  if (userLocked) return '您已锁位'
  if (isFull) return '已满'
  if (schedule.Locked_Count > 0) return `已锁${schedule.Locked_Count}位`
  return '可预约'
}

const getStatusClass = (schedule) => {
  const userBooked = schedule.User_Booked > 0
  const userLocked = schedule.User_Locked > 0
  const isFull = getTotalOccupied(schedule) >= schedule.Max_Players

  if (userBooked) return 'status-badge status-booked'
  if (userLocked) return 'status-badge status-locked'
  if (isFull) return 'status-badge status-full'
  if (schedule.Locked_Count > 0) return 'status-badge status-locked'
  return 'status-badge status-available'
}

const canBook = (schedule) => {
  if (!authStore.isPlayer) return false
  const userBooked = schedule.User_Booked > 0
  const isFull = getTotalOccupied(schedule) >= schedule.Max_Players
  return !userBooked && !isFull
}

const getButtonText = (schedule) => {
  if (!authStore.isPlayer) return '仅玩家可预约'
  if (schedule.User_Booked > 0) return '您已预约此场次'
  if (schedule.User_Locked > 0) return '您已锁位，可直接预约'
  return '已满'
}

const canLock = (schedule) => {
  if (!authStore.isPlayer) return false
  const userBooked = schedule.User_Booked > 0
  const userLocked = schedule.User_Locked > 0
  const isFull = getTotalOccupied(schedule) >= schedule.Max_Players
  return !userBooked && !userLocked && !isFull
}

const lockSchedule = async (scheduleId) => {
  try {
    await LockAPI.create(scheduleId)
    showToast('锁位成功！15分钟内请完成支付')
    setTimeout(() => router.push('/my-locks'), 1500)
  } catch (error) {
    showToast(error.message || '锁位失败', true)
  }
}

const bookSchedule = async (scheduleId) => {
  try {
    await OrderAPI.create(scheduleId)
    showToast('预约成功！')
    setTimeout(() => router.push('/orders'), 1500)
  } catch (error) {
    showToast(error.message || '预约失败', true)
  }
}

onMounted(() => {
  loadData()
})
</script>
