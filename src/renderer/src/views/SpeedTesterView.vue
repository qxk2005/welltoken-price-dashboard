<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- 顶部测速控制台面板 (苹果灰白卡片) -->
    <div class="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="text-sm font-bold text-[#1D1D1F]">⚡ 渠道性能实测配置 (基于 token-speed-tester)</span>
        </div>
        <button
          :disabled="store.isSpeedTesting || selectedSiteIds.length === 0"
          @click="startTest"
          class="text-xs px-5 py-2 rounded-xl bg-[#34C759] hover:bg-[#2FB34F] active:bg-[#289B43] disabled:opacity-50 text-white font-bold shadow-sm transition-all flex items-center space-x-2"
        >
          <span v-if="store.isSpeedTesting" class="animate-spin">🌀</span>
          <span>{{ store.isSpeedTesting ? '正在并发实测中...' : '▶ 开始批量并发实测' }}</span>
        </button>
      </div>

      <div class="grid grid-cols-12 gap-3 text-xs items-center">
        <!-- 目标渠道多选 -->
        <div class="col-span-5 flex items-center space-x-2">
          <span class="text-[#6E6E73] font-medium whitespace-nowrap">目标渠道:</span>
          <div class="flex-1 flex flex-wrap gap-1.5 max-h-16 overflow-y-auto p-1.5 rounded-xl bg-[#F2F2F7] border border-[#E5E5EA]">
            <label
              v-for="site in store.activeSites"
              :key="site.id"
              class="flex items-center space-x-1 px-2 py-0.5 rounded-md bg-[#FFFFFF] border border-[#E5E5EA] text-[#1D1D1F] cursor-pointer text-[11px]"
            >
              <input type="checkbox" :value="site.id" v-model="selectedSiteIds" class="rounded text-[#0071E3]" />
              <span>{{ site.name }}</span>
            </label>
          </div>
        </div>

        <!-- 测试模型 -->
        <div class="col-span-3 flex items-center space-x-2">
          <span class="text-[#6E6E73] font-medium whitespace-nowrap">测试模型:</span>
          <select
            v-model="targetModel"
            class="flex-1 bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-2.5 py-1.5 text-[#1D1D1F] font-mono focus:outline-none"
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
          <span class="text-[#6E6E73] font-medium whitespace-nowrap">Prompt 模板:</span>
          <select
            v-model="promptType"
            class="flex-1 bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-2.5 py-1.5 text-[#1D1D1F] focus:outline-none"
          >
            <option value="standard">标准 500 字生成 + 真实性防作弊探针</option>
            <option value="reasoning">复杂逻辑数理推理 (测试 Think 耗时)</option>
            <option value="code">Python 算法代码生成 (高密度吐字测试)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 中部：实时流式测速看板 + 实时吐字日志 (左右分栏) -->
    <div class="grid grid-cols-12 gap-3 flex-1 overflow-hidden min-h-0">
      <!-- 左侧：多渠道并发流式仪表盘 (7列) -->
      <div class="col-span-7 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-2 overflow-hidden">
        <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-2">
          <span class="font-bold text-xs text-[#1D1D1F]">📡 实时并发测速仪表板 (Real-time Stream)</span>
          <span class="text-[10px] text-[#86868B] font-mono">首字耗时 (TTFT) • 生成速率 (TPS) • 流畅度</span>
        </div>

        <div class="flex-1 overflow-y-auto space-y-2 pr-1">
          <div
            v-for="site in store.activeSites.filter((s) => selectedSiteIds.includes(s.id))"
            :key="site.id"
            class="p-3 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-2"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <span class="w-2 h-2 rounded-full" :class="getStreamStatusColor(site.id)"></span>
                <span class="font-bold text-xs text-[#1D1D1F]">{{ site.name }}</span>
                <span class="text-[10px] text-[#86868B] font-mono">({{ site.site_type }})</span>
              </div>
              <div class="flex items-center space-x-3 text-xs font-mono">
                <div>
                  <span class="text-[#86868B] text-[10px]">TTFT:</span>
                  <strong class="text-[#0071E3] ml-1">{{ getStreamTTFT(site.id) }}</strong>
                </div>
                <div>
                  <span class="text-[#86868B] text-[10px]">瞬时 TPS:</span>
                  <strong class="text-[#34C759] ml-1">{{ getStreamTPS(site.id) }}</strong>
                </div>
              </div>
            </div>

            <!-- 流式生成内容实时预览 -->
            <div class="p-2 rounded-lg bg-[#FFFFFF] border border-[#E5E5EA] font-mono text-[11px] text-[#6E6E73] h-12 overflow-y-auto leading-relaxed">
              {{ getStreamContent(site.id) || '等待测试指令...' }}
            </div>
          </div>

          <div v-if="selectedSiteIds.length === 0" class="py-12 text-center text-xs text-[#86868B]">
            请在上方勾选至少 1 个渠道进行实测
          </div>
        </div>
      </div>

      <!-- 右侧：全局测速日志控制台 (5列) -->
      <div class="col-span-5 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-2 overflow-hidden">
        <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-2">
          <span class="font-bold text-xs text-[#1D1D1F]">📋 实测运行日志流水</span>
          <button @click="store.speedLogMessages = []" class="text-[10px] text-[#0071E3] hover:underline">清空日志</button>
        </div>

        <div class="flex-1 bg-[#F9F9FB] border border-[#E5E5EA] rounded-xl p-2.5 overflow-y-auto font-mono text-[10.5px] space-y-1">
          <div
            v-for="(msg, idx) in store.speedLogMessages"
            :key="idx"
            class="text-[#1D1D1F] leading-tight"
          >
            {{ msg }}
          </div>
          <div v-if="store.speedLogMessages.length === 0" class="text-[#86868B] py-6 text-center">
            暂无测速日志
          </div>
        </div>
      </div>
    </div>

    <!-- 底部：历史测速成绩排行榜 -->
    <div class="h-44 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden">
      <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-1.5">
        <span class="font-bold text-xs text-[#1D1D1F]">🏆 渠道性能实测历史总排行榜</span>
        <button @click="store.fetchSpeedTestHistory" class="text-[10px] text-[#0071E3] hover:underline">刷新排行</button>
      </div>

      <div class="flex-1 overflow-y-auto pr-1 mt-1">
        <table class="w-full text-xs text-left">
          <thead class="text-[11px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA]">
            <tr>
              <th class="py-1.5 px-2">排名</th>
              <th class="py-1.5 px-2">中转站点</th>
              <th class="py-1.5 px-2">测试模型</th>
              <th class="py-1.5 px-2 text-right">首字延迟 (TTFT)</th>
              <th class="py-1.5 px-2 text-right">平均生成速率 (TPS)</th>
              <th class="py-1.5 px-2 text-right">总耗时</th>
              <th class="py-1.5 px-2 text-center">综合评级</th>
              <th class="py-1.5 px-2 text-center">状态</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[#E5E5EA]/60 font-mono text-[11px]">
            <tr v-for="(rec, idx) in store.speedTestHistory" :key="rec.id" class="hover:bg-[#F5F5F7]">
              <td class="py-2 px-2 font-bold" :class="getRankColor(idx)">#{{ idx + 1 }}</td>
              <td class="py-2 px-2 text-[#1D1D1F] font-sans font-medium">{{ rec.site_name }}</td>
              <td class="py-2 px-2 text-[#0071E3]">{{ rec.model_id }}</td>
              <td class="py-2 px-2 text-right text-[#34C759] font-bold">{{ rec.ttft_ms }} ms</td>
              <td class="py-2 px-2 text-right text-[#0071E3] font-bold">{{ rec.tps }} tps</td>
              <td class="py-2 px-2 text-right text-[#6E6E73]">{{ rec.total_duration_ms }} ms</td>
              <td class="py-2 px-2 text-center">
                <span class="px-1.5 py-0.2 rounded font-bold text-[10px]" :class="getScoreBadge(rec.score)">
                  {{ rec.score >= 90 ? 'A+ 极速' : rec.score >= 75 ? 'A 优秀' : 'B 普通' }}
                </span>
              </td>
              <td class="py-2 px-2 text-center font-sans">
                <span class="text-[#34C759] font-bold" v-if="rec.is_passed">通过</span>
                <span class="text-[#FF3B30] font-bold" v-else>超时/作弊</span>
              </td>
            </tr>
            <tr v-if="store.speedTestHistory.length === 0">
              <td colspan="8" class="py-6 text-center text-xs text-[#86868B] font-sans">暂无实测成绩记录</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDashboardStore } from '../stores/dashboardStore'

const store = useDashboardStore()
const selectedSiteIds = ref<number[]>([])
const targetModel = ref('deepseek-v3')
const promptType = ref('standard')

onMounted(() => {
  if (store.activeSites.length > 0) {
    selectedSiteIds.value = store.activeSites.slice(0, 3).map((s) => s.id)
  }
})

const startTest = () => {
  if (selectedSiteIds.value.length === 0) return
  store.runSpeedTest(selectedSiteIds.value, targetModel.value, promptType.value)
}

const getStreamEvent = (siteId: number) => store.currentSpeedStream[siteId]

const getStreamStatusColor = (siteId: number) => {
  const ev = getStreamEvent(siteId)
  if (!ev) return 'bg-[#AEAEB2]'
  if (ev.event === 'start') return 'bg-[#FF9500] animate-ping'
  if (ev.event === 'token') return 'bg-[#34C759] animate-pulse'
  if (ev.event === 'complete') return 'bg-[#0071E3]'
  if (ev.event === 'error') return 'bg-[#FF3B30]'
  return 'bg-[#AEAEB2]'
}

const getStreamTTFT = (siteId: number) => {
  const ev = getStreamEvent(siteId)
  return ev?.ttft_ms ? `${ev.ttft_ms} ms` : '-'
}

const getStreamTPS = (siteId: number) => {
  const ev = getStreamEvent(siteId)
  return ev?.instant_tps ? `${ev.instant_tps} tps` : '-'
}

const getStreamContent = (siteId: number) => {
  const ev = getStreamEvent(siteId)
  return ev?.full_text_snapshot || ''
}

const getRankColor = (idx: number) => {
  if (idx === 0) return 'text-[#FF9500]'
  if (idx === 1) return 'text-[#8E8E93]'
  if (idx === 2) return 'text-[#AF52DE]'
  return 'text-[#86868B]'
}

const getScoreBadge = (score: number) => {
  if (score >= 90) return 'bg-[#E6F4EA] text-[#137333] border border-[#CEEAD6]'
  if (score >= 75) return 'bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB]'
  return 'bg-[#F2F2F7] text-[#6E6E73]'
}
</script>
