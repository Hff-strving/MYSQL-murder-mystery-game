<template>
  <main class="main-content">
    <div class="container">
      <div class="page-header">
        <h2 class="page-title">我的锁位</h2>
      </div>

      <div v-if="loading" class="loading">正在加载锁位...</div>
      <div v-else-if="locks.length === 0" class="empty">暂无锁位记录</div>
      <div v-else class="locks-list">
        <div
          v-for="lock in locks"
          :key="lock.LockID"
          class="lock-card"
        >
          <div class="lock-header">
            <span class="lock-id">锁位ID：{{ lock.LockID }}</span>
            <span class="lock-status" :class="getLockStatusClass(lock.Status)">
              {{ getLockStatusText(lock.Status) }}
            </span>
          </div>
          <div class="lock-body">
            <div class="lock-item">
              <span class="lock-label">剧本名称</span>
              <span class="lock-value">{{ lock.Script_Title }}</span>
            </div>
            <div class="lock-item">
              <span class="lock-label">场次时间</span>
              <span class="lock-value">{{ formatDateTime(lock.Start_Time) }}</span>
            </div>
            <div class="lock-item">
              <span class="lock-label">房间</span>
              <span class="lock-value">{{ lock.Room_Name }}</span>
            </div>
            <div class="lock-item">
              <span class="lock-label">锁定时间</span>
              <span class="lock-value">{{ formatDateTime(lock.LockTime) }}</span>
            </div>
            <div class="lock-item">
              <span class="lock-label">过期时间</span>
              <span class="lock-value">{{ formatDateTime(lock.ExpireTime) }}</span>
            </div>
          </div>
          <div class="lock-actions">
            <button
              v-if="lock.Status === 0"
              class="btn-primary"
              @click="createOrderFromLock(lock.Schedule_ID)"
            >
              去预约/支付
            </button>
            <button
              v-if="lock.Status === 0"
              class="btn-cancel"
              @click="cancelLock(lock.LockID)"
            >
              取消锁位
            </button>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { LockAPI } from '@/api'
import { OrderAPI } from '@/api'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()
const router = useRouter()

const locks = ref([])
const loading = ref(true)

const loadLocks = async () => {
  loading.value = true
  try {
    locks.value = await LockAPI.getMyLocks()
  } catch (error) {
    showToast(error.message || '加载锁位失败', true)
  } finally {
    loading.value = false
  }
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

const getLockStatusText = (status) => {
  const statusMap = {
    0: '锁定中',
    1: '已转订单',
    2: '已释放',
    3: '已过期'
  }
  return statusMap[status] || '未知'
}

const getLockStatusClass = (status) => {
  const classMap = {
    0: 'status-locked',
    1: 'status-converted',
    2: 'status-released',
    3: 'status-expired'
  }
  return classMap[status] || ''
}

const cancelLock = async (lockId) => {
  if (!confirm('确定要取消此锁位吗？')) {
    return
  }

  try {
    await LockAPI.cancel(lockId)
    showToast('锁位已取消')
    setTimeout(() => loadLocks(), 1000)
  } catch (error) {
    showToast(error.message || '取消失败', true)
  }
}

const createOrderFromLock = async (scheduleId) => {
  try {
    await OrderAPI.create(scheduleId)
    showToast('已生成订单，请完成支付')
    setTimeout(() => router.push('/orders'), 800)
  } catch (error) {
    showToast(error.message || '创建订单失败', true)
  }
}

onMounted(() => {
  loadLocks()
})
</script>
