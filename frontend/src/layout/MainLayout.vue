<script setup>
import {
  Clock,
  Connection,
  Cpu,
  DataAnalysis,
  Document,
  Histogram,
  List,
  Monitor,
  Refresh,
  Setting,
  WarningFilled,
} from '@element-plus/icons-vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '../stores/app'

const appStore = useAppStore()
const route = useRoute()
const nowText = ref('')
const campusBg = '/branding/campus-bg.jpg'
const schoolBadgeName = '/branding/school-badge-name.png'

const menuItems = [
  { path: '/dashboard', label: '首页看板', icon: DataAnalysis },
  { path: '/predict', label: '单文本分析', icon: Monitor },
  { path: '/batch', label: '批量分析', icon: Document },
  { path: '/train', label: '模型训练', icon: Cpu },
  { path: '/evaluate', label: '模型评估', icon: Histogram },
  { path: '/review', label: '低置信度复核', icon: Connection },
  { path: '/error-analysis', label: '误判分析', icon: WarningFilled },
  { path: '/models', label: '模型管理', icon: Setting },
  { path: '/history', label: '历史记录', icon: List },
]

const currentMeta = computed(() => route.meta || {})

let timerId = 0

function updateClock() {
  nowText.value = new Date().toLocaleString('zh-CN', { hour12: false })
}

async function refreshSummary() {
  await appStore.fetchSummary()
}

onMounted(async () => {
  updateClock()
  timerId = window.setInterval(updateClock, 1000)
  if (!appStore.activeModel) {
    await refreshSummary()
  }
})

onBeforeUnmount(() => {
  if (timerId) {
    window.clearInterval(timerId)
  }
})
</script>

<template>
  <div class="shell">
    <div class="shell__backdrop" aria-hidden="true">
      <img :src="campusBg" alt="" />
    </div>
    <div class="shell__overlay" aria-hidden="true"></div>
    <aside class="sidebar card-panel">
      <div class="brand">
        <div class="brand__badge">NLP</div>
        <div class="brand__text" v-show="!appStore.collapsed">
          <strong>情感分析可视化系统</strong>
          <span>FastAPI + Vue3</span>
        </div>
      </div>

      <el-menu
        :default-active="route.path"
        :collapse="appStore.collapsed"
        class="sidebar__menu"
        router
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar__footer" v-show="!appStore.collapsed">
        <div class="sidebar__footer-title">系统状态</div>
        <div class="sidebar__footer-value">{{ appStore.activeModelName }}</div>
        <div class="sidebar__footer-meta">累计分析 {{ appStore.overview.total_count }} 条文本</div>
      </div>
    </aside>

    <section class="main">
      <header class="topbar card-panel">
        <el-button class="topbar__toggle" text @click="appStore.toggleSidebar()">切换导航</el-button>
        <div class="topbar__title">
          <h1>{{ currentMeta.title || '中文情感分析可视化系统' }}</h1>
          <p>{{ currentMeta.description || '面向本科毕业设计答辩的分析展示前端。' }}</p>
        </div>
        <div class="topbar__brandmark" aria-hidden="true">
          <img :src="schoolBadgeName" alt="华北师范大学校徽校名" />
        </div>
        <div class="topbar__right">
          <div class="topbar__pill">
            <span>当前模型</span>
            <strong>{{ appStore.activeModelName }}</strong>
          </div>
          <div class="topbar__time">
            <el-icon><Clock /></el-icon>
            <span>{{ nowText }}</span>
          </div>
          <el-button type="primary" plain :icon="Refresh" @click="refreshSummary">刷新概览</el-button>
        </div>
      </header>

      <main class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </section>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  position: relative;
  isolation: isolate;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 24px;
  padding: 24px;
  background: var(--app-bg);
  overflow: hidden;
}

.shell__backdrop,
.shell__overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.shell__backdrop {
  z-index: 0;
}

.shell__backdrop img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
  opacity: 0.58;
  transform: scale(1.04);
  transform-origin: center;
  filter: saturate(1.08) contrast(1.04);
}

.shell__overlay {
  z-index: 1;
  background:
    linear-gradient(180deg, rgba(245, 247, 251, 0.58), rgba(245, 247, 251, 0.5)),
    radial-gradient(circle at top left, rgba(58, 123, 213, 0.1), transparent 32%),
    radial-gradient(circle at right 20%, rgba(83, 105, 248, 0.09), transparent 28%);
}

.sidebar {
  width: 268px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 18px 14px;
  gap: 18px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 8px 18px;
}

.brand__badge {
  width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: linear-gradient(135deg, #2f6bff, #57a3ff);
  color: #fff;
  font-weight: 700;
  letter-spacing: 1px;
  box-shadow: 0 16px 32px rgba(47, 107, 255, 0.24);
}

.brand__text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.brand__text strong {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.brand__text span {
  color: var(--text-secondary);
  font-size: 12px;
}

.sidebar__menu {
  border: 0;
  background: transparent;
}

.sidebar__menu :deep(.el-menu-item) {
  margin-bottom: 8px;
  border-radius: 14px;
  color: var(--text-secondary);
}

.sidebar__menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(47, 107, 255, 0.14), rgba(87, 163, 255, 0.1));
  color: #295df4;
}

.sidebar__footer {
  margin-top: auto;
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(47, 107, 255, 0.1), rgba(47, 107, 255, 0.03));
}

.sidebar__footer-title {
  font-size: 12px;
  color: var(--text-secondary);
}

.sidebar__footer-value {
  margin-top: 10px;
  font-weight: 700;
  line-height: 1.6;
  color: var(--text-primary);
}

.sidebar__footer-meta {
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: 12px;
}

.main {
  min-width: 0;
}

.sidebar,
.main {
  position: relative;
  z-index: 2;
}

.topbar {
  padding: 18px 22px;
  display: grid;
  grid-template-columns: auto minmax(260px, 1fr) minmax(220px, 320px) auto;
  align-items: center;
  gap: 16px;
}

.topbar__title h1 {
  margin: 0;
  font-size: 22px;
  font-family: var(--heading-font);
  color: var(--text-primary);
}

.topbar__title {
  min-width: 0;
  position: relative;
  z-index: 1;
}

.topbar__title p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.topbar__toggle {
  position: relative;
  z-index: 1;
  justify-self: start;
}

.topbar__brandmark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  pointer-events: none;
}

.topbar__brandmark img {
  display: block;
  width: 100%;
  max-height: 48px;
  object-fit: contain;
  opacity: 0.88;
  filter: drop-shadow(0 10px 18px rgba(15, 23, 42, 0.08));
}

.topbar__right {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  justify-content: flex-end;
  position: relative;
  z-index: 1;
}

.topbar__pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(47, 107, 255, 0.08);
  color: #295df4;
  font-size: 13px;
}

.topbar__pill strong {
  color: var(--text-primary);
}

.topbar__time {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.04);
  color: var(--text-secondary);
}

.content {
  margin-top: 24px;
}

.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.22s ease;
}

.fade-transform-enter-from,
.fade-transform-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

@media (max-width: 1200px) {
  .shell {
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .sidebar {
    width: 100%;
  }

  .topbar {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }

  .topbar__brandmark {
    position: static;
    transform: none;
    width: min(72vw, 340px);
    margin: 0 auto;
    align-self: center;
  }

  .topbar__brandmark img {
    max-height: 52px;
  }

  .topbar__right {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
