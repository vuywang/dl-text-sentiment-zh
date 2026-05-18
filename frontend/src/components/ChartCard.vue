<script setup>
import { BarChart, GaugeChart, HeatmapChart, LineChart, PieChart, RadarChart } from 'echarts/charts'
import { GridComponent, LegendComponent, RadarComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, useSlots, watch } from 'vue'

use([
  BarChart,
  GaugeChart,
  HeatmapChart,
  LineChart,
  PieChart,
  RadarChart,
  GridComponent,
  LegendComponent,
  RadarComponent,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
])

const props = defineProps({
  title: {
    type: String,
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
  height: {
    type: String,
    default: '320px',
  },
  option: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  empty: {
    type: Boolean,
    default: false,
  },
  emptyText: {
    type: String,
    default: '暂无图表数据',
  },
})

const slots = useSlots()
const chartRef = ref(null)
let chartInstance = null

const hasSlot = computed(() => Boolean(slots.default))
const shouldUseSlot = computed(() => hasSlot.value && !props.option && !props.empty)

function renderChart() {
  if (shouldUseSlot.value || props.loading || props.empty || !props.option || !chartRef.value) {
    return
  }
  if (!chartInstance) {
    chartInstance = init(chartRef.value)
  }
  chartInstance.setOption(props.option, true)
}

function handleResize() {
  chartInstance?.resize()
}

watch(
  () => props.option,
  async () => {
    await nextTick()
    renderChart()
  },
  { deep: true }
)

watch(
  () => props.empty,
  async () => {
    await nextTick()
    renderChart()
  }
)

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  await nextTick()
  renderChart()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<template>
  <div class="chart-card card-panel">
    <div class="chart-card__header">
      <div>
        <h3>{{ title }}</h3>
        <p v-if="description">{{ description }}</p>
      </div>
      <slot name="extra" />
    </div>

    <div v-if="loading" class="chart-card__state" :style="{ height }">
      <el-skeleton animated :rows="5" />
    </div>
    <div v-else-if="shouldUseSlot" class="chart-card__slot" :style="{ minHeight: height }">
      <slot />
    </div>
    <div v-else-if="empty" class="chart-card__state" :style="{ height }">
      <el-empty :description="emptyText" />
    </div>
    <div v-else ref="chartRef" class="chart-card__canvas" :style="{ height }"></div>
  </div>
</template>

<style scoped>
.chart-card {
  padding: 22px;
}

.chart-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.chart-card__header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.chart-card__header p {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.chart-card__canvas,
.chart-card__state,
.chart-card__slot {
  width: 100%;
}

.chart-card__slot {
  display: flex;
  align-items: stretch;
}
</style>
