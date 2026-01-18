<template>
  <main class="main-content">
    <div class="container">
      <div class="page-header">
        <h2 class="page-title">我的订单</h2>
      </div>

      <div v-if="loading" class="loading">正在加载订单...</div>
      <div v-else-if="orders.length === 0" class="empty">暂无订单</div>
      <div v-else id="ordersList" class="orders-list">
        <div
          v-for="order in orders"
          :key="order.Order_ID"
          class="order-card"
        >
          <div class="order-header">
            <span class="order-id">订单号：{{ order.Order_ID }}</span>
            <span class="order-status" :class="getStatusClass(order.Pay_Status)">
              {{ getStatusText(order.Pay_Status) }}
            </span>
          </div>
          <div class="order-body">
            <div class="order-item">
              <span class="order-label">剧本名称</span>
              <span class="order-value">{{ order.Script_Title }}</span>
            </div>
            <div class="order-item">
              <span class="order-label">场次时间</span>
              <span class="order-value">{{ formatDateTime(order.Start_Time) }}</span>
            </div>
            <div class="order-item">
              <span class="order-label">房间</span>
              <span class="order-value">{{ order.Room_Name || '未知' }}</span>
            </div>
            <div class="order-item">
              <span class="order-label">订单金额</span>
              <span class="order-value price">¥{{ order.Amount }}</span>
            </div>
            <div class="order-item">
              <span class="order-label">创建时间</span>
              <span class="order-value">{{ formatDateTime(order.Create_Time) }}</span>
            </div>
          </div>
          <div class="order-actions">
            <button
              v-if="order.Pay_Status === 0"
              class="btn-primary"
              @click="payOrder(order.Order_ID)"
            >
              立即支付
            </button>
            <button
              v-if="order.Pay_Status === 0"
              class="btn-cancel"
              @click="cancelOrder(order.Order_ID)"
            >
              取消预约
            </button>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { OrderAPI } from '@/api'
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()

const orders = ref([])
const loading = ref(true)

const loadOrders = async () => {
  loading.value = true
  try {
    orders.value = await OrderAPI.getMyOrders()
  } catch (error) {
    showToast(error.message || '加载订单失败', true)
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

const getStatusText = (status) => {
  const statusMap = {
    0: '待支付',
    1: '已支付',
    2: '已退款',
    3: '已取消'
  }
  return statusMap[status] || '未知'
}

const getStatusClass = (status) => {
  const classMap = {
    0: 'status-unpaid',
    1: 'status-paid',
    2: 'status-refunded',
    3: 'status-cancelled'
  }
  return classMap[status] || ''
}

const payOrder = async (orderId) => {
  try {
    await OrderAPI.pay(orderId, 1)
    showToast('支付成功！')
    loadOrders()
  } catch (error) {
    showToast(error.message || '支付失败', true)
  }
}

const cancelOrder = async (orderId) => {
  if (!confirm('确定要取消此预约吗？取消后将释放该场次的位置。')) {
    return
  }

  try {
    await OrderAPI.cancel(orderId)
    showToast('预约已取消')
    setTimeout(() => loadOrders(), 1000)
  } catch (error) {
    showToast(error.message || '取消失败', true)
  }
}

onMounted(() => {
  loadOrders()
})
</script>
