<template>
  <main class="main-content">
    <div class="container">
      <!-- 页面标题 -->
      <div class="page-header">
        <h2 class="page-title">探索神秘剧本</h2>
        <p class="page-subtitle">选择你的冒险，开启推理之旅</p>
      </div>

      <!-- 筛选区域 -->
      <div class="filter-section">
        <button
          class="filter-btn"
          :class="{ active: filterStatus === 'all' }"
          @click="filterStatus = 'all'; loadScripts()"
        >
          全部剧本
        </button>
        <button
          class="filter-btn"
          :class="{ active: filterStatus === 'hot' }"
          @click="filterStatus = 'hot'; loadScripts()"
        >
          热门推荐
        </button>
      </div>

      <!-- 剧本列表 -->
      <div v-if="loading" class="loading">正在加载剧本...</div>
      <div v-else-if="scripts.length === 0" class="empty">暂无剧本</div>
      <div v-else class="script-grid">
        <div
          v-for="script in scripts"
          :key="script.Script_ID"
          class="script-card"
          @click="viewDetail(script.Script_ID)"
        >
          <!-- 热门角标 -->
          <div v-if="script.hot_rank" class="hot-rank-badge">
            TOP {{ script.hot_rank }}
          </div>

          <!-- 封面图 -->
          <div class="script-card-image-wrapper">
            <img
              :src="getCoverUrl(script.Cover_Image)"
              class="script-card-image"
              :alt="script.Title"
              @error="handleImageError"
            >
          </div>

          <!-- 剧本信息 -->
          <div class="script-header">
            <h3 class="script-title">{{ script.Title }}</h3>
            <span class="script-type">{{ script.Group_Category || script.Type }}</span>
          </div>

          <!-- 难度星级 -->
          <div v-if="script.Difficulty" class="script-difficulty">
            <span class="difficulty-stars">
              {{ '★'.repeat(script.Difficulty) }}{{ '☆'.repeat(5 - script.Difficulty) }}
            </span>
          </div>

          <!-- 详细信息 -->
          <div class="script-info">
            <div class="info-item">
              <span class="label">人数：</span>
              <span class="value">{{ script.Min_Players }}-{{ script.Max_Players }}人</span>
            </div>
            <div v-if="script.Gender_Config" class="info-item">
              <span class="label">配置：</span>
              <span class="value">{{ script.Gender_Config }}</span>
            </div>
            <div class="info-item">
              <span class="label">价格：</span>
              <span class="value price">¥{{ script.Base_Price }}</span>
            </div>
          </div>

          <button class="btn-primary">查看详情</button>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ScriptAPI } from '@/api'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { showToast } = useToast()

const scripts = ref([])
const loading = ref(false)
const filterStatus = ref('all')

const loadScripts = async () => {
  loading.value = true
  try {
    if (filterStatus.value === 'hot') {
      scripts.value = await ScriptAPI.getHot(10)
    } else {
      scripts.value = await ScriptAPI.getAll()
    }
  } catch (error) {
    showToast(error.message || '加载失败', true)
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

const viewDetail = (scriptId) => {
  router.push(`/scripts/${scriptId}`)
}

onMounted(() => {
  loadScripts()
})
</script>
