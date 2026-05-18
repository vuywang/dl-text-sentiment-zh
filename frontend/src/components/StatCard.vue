<script setup>
const props = defineProps({
  title: {
    type: String,
    default: '',
  },
  value: {
    type: [String, Number],
    default: '--',
  },
  subtitle: {
    type: String,
    default: '',
  },
  accent: {
    type: String,
    default: '#2f6bff',
  },
  icon: {
    type: Object,
    default: null,
  },
})
</script>

<template>
  <div class="stat-card card-panel">
    <div class="stat-card__icon" :style="{ background: `linear-gradient(135deg, ${accent}, rgba(255,255,255,0.92))` }">
      <el-icon v-if="icon"><component :is="icon" /></el-icon>
    </div>
    <div class="stat-card__content">
      <div class="stat-card__title">{{ title }}</div>
      <div class="stat-card__value">{{ value }}</div>
      <div class="stat-card__subtitle">{{ subtitle || '数据来自系统实时统计' }}</div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 18px;
  min-height: 136px;
  padding: 22px;
}

.stat-card::after {
  content: '';
  position: absolute;
  inset: auto -10% -45% auto;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: rgba(47, 107, 255, 0.08);
}

.stat-card__icon {
  position: relative;
  z-index: 1;
  width: 56px;
  height: 56px;
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24px;
  box-shadow: 0 18px 30px rgba(47, 107, 255, 0.18);
}

.stat-card__content {
  position: relative;
  z-index: 1;
}

.stat-card__title {
  color: var(--text-secondary);
  font-size: 14px;
}

.stat-card__value {
  margin-top: 10px;
  font-size: 30px;
  line-height: 1.1;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--number-font);
}

.stat-card__subtitle {
  margin-top: 10px;
  color: var(--text-secondary);
  font-size: 12px;
}
</style>
