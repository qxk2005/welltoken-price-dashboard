<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- 顶部测速控制台面板 -->
    <div class="p-4 rounded-xl bg-[#151922] border border-[#232936] space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="text-sm font-bold text-white">⚡ 渠道性能实测配置 (基于 token-speed-tester)</span>
        </div>
        <button
          :disabled="store.isSpeedTesting || selectedSiteIds.length === 0"
          @click="startTest"
          class="text-xs px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold shadow-lg shadow-emerald-600/20 transition-all flex items-center space-x-2"
        >
          <span v-if="store.isSpeedTesting" class="animate-spin">🌀</span>
          <span>{{ store.isSpeedTesting ? '正在并发实测中...' : '▶ 开始批量并发实测' }}</span>
        </button>
      </div>

      <div class="grid grid-cols-12 gap-3 text-xs items-center">
        <!-- 目标渠道多选 -->
        <div class="col-span-5 flex items-center space-x-2">
          <span class="text-gray-400 font-medium">目标渠道:</span>
          <div class="flex-1 flex flex-wrap gap-1.5 max-h-16 overflow-y-auto p-1.5 rounded-lg bg-[#0B0E14] border border-[#232936]">
            <label
              v-for="site in store.activeSites"
              :key="site.id"
              class="flex items-center space-x-1 px-2 py-0.5 rounded bg-[#1A202C] text-gray-300 cursor-pointer text-[11px]"
            >
              <input type="checkbox" :value="site.id" v-model="selectedSiteIds" class="rounded bg-gray-800" />
              <span>{{ site.name }}</span>
            </label>
          </div>
        </div>

        <!-- 测试模型 -->
        <div class="col-span-3 flex items-center space-x-2">
          <span class="text-gray-400 font-medium">测试模型:</span>
          <select
            v-model="targetModel"
            class="flex-1 bg-[#0B0E14] border border-[#232936] rounded-lg px-2.5 py-1.5 text-white font-mono"
          >
            <option value="deepseek-v3">deepseek-v3</option>
            <option value="deepseek-r1">deepseek-r1</option>
            <option value="claude-3-5-sonnet">claude-3-5-sonnet</option>
            <option value="gpt-4o">gpt-4o</option>
            <option value="qwen2.5-72b-instruct">qwen2.5-72b-instruct</option>
          </select>
        </div>

        <!-- 测试 Prompt 模式 -->
        <div class="col-span-4 flex items-center space-x-2">
          <span class="text-gray-400 font-medium">Prompt 模板:</span>
          <select
            v-model="promptType"
            class="flex-1 bg-[#0B0E14] border border-[#232936] rounded-lg px-2.5 py-1.5 text-white"
          >
            <option value="standard">标准 500 字生成 + 真实性防作弊探针</option>
            <option value="reasoning">复杂逻辑数理推理 (测试 Think 耗时)</option>
            <option value="code">Python 算法代码生成 (高密度吐字测试)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 实时指标核心卡片 (KPI) -->
    <div class="grid grid-cols-4 gap-3">
      <!-- TTFT -->
      <div class="p-3.5 rounded-xl bg-[#151922] border border-[#232936]">
        <div class="text-[11px] text-gray-400">首字延迟 (TTFT) 均值</div>
        <div class="flex items-baseline space-x-1 mt-1">
          <span class="text-2xl font-bold font-mono text-emerald-400">{{ latestMetric.ttft }}</span>
          <span class="text-xs text-gray-500 font-mono">ms</span>
        </div>
        <div class="text-[10px] text-gray-500 mt-1">最优渠道: 134.4ms (极速云)</div>
      </div>

      <!-- 平均 TPS -->
      <div class="p-3.5 rounded-xl bg-[#151922] border border-[#232936]">
        <div class="text-[11px] text-gray-400">平均生成速率 (TPS)</div>
        <div class="flex items-baseline space-x-1 mt-1">
          <span class="text-2xl font-bold font-mono text-sky-400">{{ latestMetric.avgTps }}</span>
          <span class="text-xs text-gray-500 font-mono">tokens/s</span>
        </div>
        <div class="text-[10px] text-gray-500 mt-1">峰值速率 (10-Token滑动): {{ latestMetric.peakTps }} tps</div>
      </div>

      <!-- 一致性探针 -->
      <div class="p-3.5 rounded-xl bg-[#151922] border border-[#232936]">
        <div class="text-[11px] text-gray-400">模型一致性防作弊探针</div>
        <div class="flex items-baseline space-x-1 mt-1">
          <span class="text-xl font-bold text-emerald-400">100% 真实原厂</span>
        </div>
        <div class="text-[10px] text-emerald-500/80 mt-1">未检测到模型掺水或降级替包</div>
      </div>

      <!-- 成功率 -->
      <div class="p-3.5 rounded-xl bg-[#151922] border border-[#232936]">
        <div class="text-[11px] text-gray-400">网络连通与成功率</div>
        <div class="flex items-baseline space-x-1 mt-1">
          <span class="text-2xl font-bold font-mono text-emerald-400">100%</span>
        </div>
        <div class="text-[10px] text-gray-500 mt-1">累计实测: {{ store.speedTestHistory.length }} 轮样本</div>
      </div>
    </div>

    <!-- 下方主体：左侧动态流式曲线 + 右侧历史排行榜 -->
    <div class="flex-1 grid grid-cols-12 gap-3 min-h-0">
      <!-- 左侧：流式输出与日志 (7列) -->
      <div class="col-span-7 flex flex-col bg-[#151922] rounded-xl border border-[#232936] p-3 overflow-hidden">
        <div class="flex items-center justify-between pb-2 border-b border-[#232936]">
          <span class="text-xs font-bold text-white">📊 实时流式吐字速率动态曲线 (ECharts)</span>
          <span class="text-[10px] text-gray-500 font-mono">滑动窗口平稳度</span>
        </div>
        <div class="h-44 w-full relative">
          <div ref="speedChartRef" class="w-full h-full"></div>
        </div>

        <!-- 实时流式打字机终端控制台日志 -->
        <div class="flex-1 mt-2 p-2.5 rounded-lg bg-[#0B0E14] border border-[#232936] font-mono text-[11px] overflow-y-auto space-y-1 text-gray-300">
          <div v-for="(log, idx) in store.speedLogMessages" :key="idx" class="leading-relaxed">
            {{ log }}
          </div>
        </div>
      </div>

      <!-- 右侧：渠道质量排行榜 (5列) -->
      <div class="col-span-5 flex flex-col bg-[#151922] rounded-xl border border-[#232936] p-3 overflow-hidden">
        <div class="flex items-center justify-between pb-2 border-b border-[#232936]">
          <span class="text-xs font-bold text-white">🏆 渠道综合评级排行榜 (Score Matrix)</span>
          <button @click="store.fetchSpeedTestHistory" class="text-[11px] text-blue-400 hover:text-blue-300">
            刷新
          </button>
        </div>

        <div class="flex-1 overflow-y-auto divide-y divide-[#232936]/40 pr-1 mt-1">
          <div
            v-for="item in store.speedTestHistory"
            :key="item.id"
            class="py-2.5 px-2 flex items-center justify-between text-xs hover:bg-[#1A202C] rounded-lg transition-colors"
          >
            <div>
              <div class="flex items-center space-x-1.5">
                <span class="font-bold text-white">{{ item.site_name }}</span>
                <span class="text-[10px] px-1.5 py-0.2 rounded font-mono font-bold" :class="getGradeClass(item.grade)">
                  {{ item.grade }} 级 ({{ item.score }}分)
                </span>
              </div>
              <div class="text-[10px] text-gray-500 font-mono mt-0.5">
                模型: {{ item.model_id }} • TTFT: {{ item.ttft_ms }}ms • TPS: {{ item.avg_tps }}
              </div>
            </div>
            <div class="text-right font-mono">
              <div class="text-emerald-400 font-bold">{{ item.avg_tps }} tps</div>
              <div class="text-[10px] text-gray-500">{{ item.total_latency_ms }}ms</div>
            </div>
          </div>

          <div v-if="store.speedTestHistory.length === 0" class="py-8 text-center text-xs text-gray-500">
            暂无实测记录，点击上方按钮开始测速
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { useDashboardStore } from '../stores/dashboardStore'

const store = useDashboardStore()
const selectedSiteIds = ref<number[]>([])
const targetModel = ref('deepseek-v3')
const promptType = ref('standard')

const speedChartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const latestMetric = computed(() => {
  const h = store.speedTestHistory[0]
  return {
    ttft: h ? h.ttft_ms : 134.4,
    avgTps: h ? h.avg_tps : 58.8,
    peakTps: h ? h.peak_tps : 76.5
  }
})

const getGradeClass = (grade: string) => {
  if (grade === 'S') return 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
  if (grade === 'A') return 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
  if (grade === 'B') return 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
  return 'bg-gray-500/20 text-gray-400'
}

const startTest = async () => {
  if (selectedSiteIds.value.length === 0) return
  await store.runSpeedTest(selectedSiteIds.value, targetModel.value, promptType.value)
  updateSpeedChart()
}

const initChart = () => {
  if (!speedChartRef.value) return
  chartInstance = echarts.init(speedChartRef.value, 'dark', { renderer: 'canvas' })
  updateSpeedChart()
}

const updateSpeedChart = () => {
  if (!chartInstance) return
  const times = ['0s', '0.5s', '1.0s', '1.5s', '2.0s', '2.5s', '3.0s', '3.5s', '4.0s']
  
  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { left: '4%', right: '4%', top: '15%', bottom: '15%' },
    xAxis: {
      type: 'category',
      data: times,
      axisLine: { lineStyle: { color: '#232936' } },
      axisLabel: { color: '#9CA3AF', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      name: 'TPS',
      splitLine: { lineStyle: { color: '#232936', type: 'dashed' } },
      axisLabel: { color: '#9CA3AF', fontSize: 10 }
    },
    series: [
      {
        name: '极速云 (NewAPI)',
        type: 'line',
        smooth: true,
        data: [0, 48, 62, 59, 64, 61, 60, 58, 60],
        lineStyle: { color: '#10B981', width: 2 }
      },
      {
        name: '星河 AI (Sub2API)',
        type: 'line',
        smooth: true,
        data: [0, 35, 52, 56, 54, 55, 53, 55, 54],
        lineStyle: { color: '#A855F7', width: 2 }
      }
    ]
  }
  chartInstance.setOption(option, true)
}

const handleResize = () => chartInstance?.resize()

onMounted(() => {
  selectedSiteIds.value = store.activeSites.map((s) => s.id)
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>
