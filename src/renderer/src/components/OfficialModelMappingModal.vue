<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'
import type { OfficialBenchmarkModel, ChannelOfficialMatchItem } from '../types'

const props = defineProps<{
  show: boolean
  channelId: number
  channelName: string
  channelModels: any[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved', payload: { count: number }): void
}>()

const store = useDashboardStore()

// 状态管理
const isLoading = ref(false)
const isSaving = ref(false)
const benchmarks = ref<OfficialBenchmarkModel[]>([])
const mappingList = ref<ChannelOfficialMatchItem[]>([])
const searchQuery = ref('')
const activeFilter = ref<'all' | 'unmatched' | 'matched' | 'discount' | 'premium'>('all')
const selectedProviderFilter = ref<string>('all')

// 汇率
const usdToCnyRate = ref<number>(7.3)

// 加载官方基准模型与自动模糊匹配
const loadData = async () => {
  if (!props.channelId) return
  isLoading.value = true
  try {
    // 准备要匹配的模型列表，如果父组件传入了则优先使用，否则传空让后端直接从数据库查
    const modelsPayload = (props.channelModels && props.channelModels.length > 0)
      ? props.channelModels.map(m => ({
          id: m.id,
          site_model_name: m.site_model_name || m.model_id,
          model_id: m.model_id,
          group_name: m.group_name || '',
          calculated_input_usd: m.calculated_input_usd || 0,
          calculated_output_usd: m.calculated_output_usd || 0
        }))
      : []

    // 1. 并发获取官网第一档基准模型与渠道匹配
    const [benchRes, matchRes] = await Promise.all([
      axios.get(`${store.apiUrl}/api/v1/official-pricing/benchmarks`),
      axios.post(`${store.apiUrl}/api/v1/official-pricing/match-channel-models/${props.channelId}`, {
        models: modelsPayload
      })
    ])

    if (benchRes.data?.benchmarks) {
      benchmarks.value = benchRes.data.benchmarks
      usdToCnyRate.value = benchRes.data.usd_to_cny_rate || 7.3
    }

    if (matchRes.data?.items) {
      mappingList.value = matchRes.data.items
    }
  } catch (err) {
    console.error('加载官网模型映射失败:', err)
  } finally {
    isLoading.value = false
  }
}

watch(
  () => props.show,
  (val) => {
    if (val) {
      searchQuery.value = ''
      activeFilter.value = 'all'
      selectedProviderFilter.value = 'all'
      loadData()
    }
  },
  { immediate: true }
)

// 官网基准模型按 ID 索引
const benchMap = computed(() => {
  const map = new Map<number, OfficialBenchmarkModel>()
  benchmarks.value.forEach(b => map.set(b.id, b))
  return map
})

// 统计数据
const totalCount = computed(() => mappingList.value.length)
const matchedCount = computed(() => mappingList.value.filter(m => m.is_matched && m.official_model_id).length)
const unmatchedCount = computed(() => mappingList.value.filter(m => !m.is_matched || !m.official_model_id).length)

// 计算平均综合折扣
const avgDiscount = computed(() => {
  const discs = mappingList.value
    .filter(m => m.composite_discount !== null && m.composite_discount !== undefined)
    .map(m => m.composite_discount as number)
  if (!discs.length) return null
  return (discs.reduce((a, b) => a + b, 0) / discs.length).toFixed(2)
})

// 手动更新某个模型的映射
const onSelectBenchmark = (item: ChannelOfficialMatchItem, benchIdStr: string) => {
  const benchId = benchIdStr ? parseInt(benchIdStr) : null
  if (!benchId) {
    item.official_model_id = null
    item.official_model_name = ''
    item.official_benchmark = null
    item.is_matched = false
    item.input_discount = null
    item.output_discount = null
    item.composite_discount = null
    return
  }

  const bench = benchMap.value.get(benchId)
  if (bench) {
    item.official_model_id = bench.id
    item.official_model_name = bench.clean_name
    item.official_benchmark = bench
    item.is_matched = true

    // 重新计算折扣
    const inDisc = bench.converted_input_usd > 0
      ? Number((item.calculated_input_usd / bench.converted_input_usd).toFixed(3))
      : 0
    const outDisc = bench.converted_output_usd > 0
      ? Number((item.calculated_output_usd / bench.converted_output_usd).toFixed(3))
      : 0
    item.input_discount = inDisc
    item.output_discount = outDisc
    item.composite_discount = Number(((inDisc * 2 + outDisc) / 3).toFixed(3))
  }
}

// 重新自动模糊匹配
const reMatchAll = async () => {
  isLoading.value = true
  try {
    const res = await axios.post(`${store.apiUrl}/api/v1/official-pricing/match-channel-models/${props.channelId}`, {
      models: props.channelModels.map(m => ({
        id: m.id,
        site_model_name: m.site_model_name || m.model_id,
        model_id: m.model_id,
        group_name: m.group_name || '',
        calculated_input_usd: m.calculated_input_usd || 0,
        calculated_output_usd: m.calculated_output_usd || 0
      }))
    })
    if (res.data?.items) {
      mappingList.value = res.data.items
    }
  } catch (e) {
    console.error('重新模糊匹配失败:', e)
  } finally {
    isLoading.value = false
  }
}

// 全部重置为未映射
const resetAll = () => {
  if (confirm('确定要将当前所有模型的官网映射重置为未匹配吗？')) {
    mappingList.value.forEach(m => {
      m.official_model_id = null
      m.official_model_name = ''
      m.official_benchmark = null
      m.is_matched = false
      m.input_discount = null
      m.output_discount = null
      m.composite_discount = null
    })
  }
}

// 格式化折扣徽章文案与样式
const formatDiscount = (disc: number | null | undefined) => {
  if (disc === null || disc === undefined) return { label: '未核算', class: 'bg-[#F2F2F7] text-[#86868B]' }
  if (disc === 0) return { label: '0折(免费)', class: 'bg-[#E8F8EE] text-[#34C759] border-[#B7EBD0]' }
  if (disc < 1.0) {
    const zhe = (disc * 10).toFixed(1).replace(/\.0$/, '')
    return {
      label: `${zhe}折`,
      class: 'bg-[#E8F8EE] text-[#248A3D] border-[#B7EBD0] font-bold'
    }
  }
  if (disc === 1.0) {
    return { label: '原价(1.0)', class: 'bg-[#E8F2FD] text-[#0071E3] border-[#CCE4FB]' }
  }
  const premium = Math.round((disc - 1.0) * 100)
  return {
    label: `溢价 +${premium}%`,
    class: 'bg-[#FFF3E0] text-[#E65100] border-[#FFE0B2] font-semibold'
  }
}

// 筛选过滤列表
const filteredList = computed(() => {
  let list = mappingList.value

  // 1. 状态筛选
  if (activeFilter.value === 'unmatched') {
    list = list.filter(m => !m.is_matched || !m.official_model_id)
  } else if (activeFilter.value === 'matched') {
    list = list.filter(m => m.is_matched && m.official_model_id)
  } else if (activeFilter.value === 'discount') {
    list = list.filter(m => typeof m.composite_discount === 'number' && m.composite_discount < 1.0)
  } else if (activeFilter.value === 'premium') {
    list = list.filter(m => typeof m.composite_discount === 'number' && m.composite_discount > 1.0)
  }

  // 2. 厂商筛选
  if (selectedProviderFilter.value !== 'all') {
    list = list.filter(m => {
      const p = m.official_benchmark?.provider || ''
      return p.toLowerCase() === selectedProviderFilter.value.toLowerCase()
    })
  }

  // 3. 关键字搜索
  if (searchQuery.value.trim()) {
    const kw = searchQuery.value.trim().toLowerCase()
    list = list.filter(m =>
      m.channel_model_name.toLowerCase().includes(kw) ||
      (m.official_model_name && m.official_model_name.toLowerCase().includes(kw)) ||
      (m.group_name && m.group_name.toLowerCase().includes(kw))
    )
  }

  return list
})

// 保存映射
const saveMappings = async () => {
  isSaving.value = true
  try {
    const payload = {
      mappings: mappingList.value.map(item => ({
        channel_model_id: item.channel_model_id,
        channel_model_name: item.channel_model_name,
        official_model_id: item.official_model_id || null,
        official_model_name: item.official_model_name || '',
        group_name: item.group_name || ''
      }))
    }

    const res = await axios.post(`${store.apiUrl}/api/v1/official-pricing/save-channel-mappings/${props.channelId}`, payload)
    if (res.data?.status === 'success') {
      emit('saved', { count: res.data.saved_mappings_count || 0 })
      emit('close')
    }
  } catch (err: any) {
    alert(`保存模型映射失败: ${err?.response?.data?.detail || err.message}`)
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-200">
    <div class="bg-white rounded-2xl shadow-2xl border border-[#E5E5EA] w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden">
      
      <!-- 1. 顶部 Header -->
      <div class="px-6 py-4 border-b border-[#E5E5EA] bg-[#FBFBFD] flex items-center justify-between flex-shrink-0">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-[#E8F2FD] border border-[#CCE4FB] flex items-center justify-center text-xl shadow-2xs">
            🎯
          </div>
          <div>
            <div class="flex items-center space-x-2">
              <h3 class="text-base font-bold text-[#1D1D1F]">模型官网映射与真实价格对账</h3>
              <span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB]">
                {{ channelName }}
              </span>
            </div>
            <p class="text-xs text-[#86868B] mt-0.5">
              自动匹配当前供应商的所有模型与官网标准库（第一档无阶梯基准价），实时校验代理商是否真实打折或虚高溢价
            </p>
          </div>
        </div>

        <button
          @click="emit('close')"
          class="w-8 h-8 rounded-full bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#86868B] hover:text-[#1D1D1F] flex items-center justify-center text-sm font-bold transition-colors cursor-pointer"
        >
          ✕
        </button>
      </div>

      <!-- 2. 四维统计看板与操作栏 -->
      <div class="px-6 py-3 border-b border-[#E5E5EA] bg-white grid grid-cols-4 gap-3 flex-shrink-0">
        <!-- 总模型 -->
        <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] flex items-center justify-between">
          <div>
            <div class="text-[10px] text-[#86868B] font-semibold uppercase">当前渠道模型总数</div>
            <div class="text-lg font-bold font-mono text-[#1D1D1F] mt-0.5">{{ totalCount }} 款</div>
          </div>
          <span class="text-xl opacity-60">📋</span>
        </div>

        <!-- 已匹配 -->
        <div class="p-2.5 rounded-xl bg-[#E8F8EE]/60 border border-[#B7EBD0] flex items-center justify-between">
          <div>
            <div class="text-[10px] text-[#248A3D] font-semibold uppercase">已成功映射官网</div>
            <div class="text-lg font-bold font-mono text-[#248A3D] mt-0.5">{{ matchedCount }} 款</div>
          </div>
          <span class="text-xl">✅</span>
        </div>

        <!-- 待确认 -->
        <div class="p-2.5 rounded-xl bg-[#FFF9E6] border border-[#FFE082] flex items-center justify-between">
          <div>
            <div class="text-[10px] text-[#B78103] font-semibold uppercase">待确认/未匹配</div>
            <div class="text-lg font-bold font-mono text-[#B78103] mt-0.5">{{ unmatchedCount }} 款</div>
          </div>
          <span class="text-xl">⚠️</span>
        </div>

        <!-- 真实平均折扣 -->
        <div class="p-2.5 rounded-xl bg-[#F0F4FF] border border-[#C7D7FE] flex items-center justify-between">
          <div>
            <div class="text-[10px] text-[#3538CD] font-semibold uppercase">相对官网综合折扣</div>
            <div class="text-lg font-bold font-mono text-[#3538CD] mt-0.5">
              {{ avgDiscount ? `${(Number(avgDiscount) * 10).toFixed(1)} 折` : '待核算' }}
            </div>
          </div>
          <span class="text-xl">💱</span>
        </div>
      </div>

      <!-- 3. 筛选、过滤与搜索控制区 -->
      <div class="px-6 py-2.5 bg-[#F9F9FB] border-b border-[#E5E5EA] flex items-center justify-between flex-wrap gap-2 flex-shrink-0">
        <!-- 分类胶囊 -->
        <div class="inline-flex p-0.5 rounded-xl bg-[#E5E5EA]/70 border border-[#D1D1D6]/60 text-xs">
          <button
            @click="activeFilter = 'all'"
            class="px-3 py-1 rounded-lg font-medium transition-all"
            :class="activeFilter === 'all' ? 'bg-white text-[#1D1D1F] shadow-2xs font-semibold' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
          >
            全部 ({{ totalCount }})
          </button>
          <button
            @click="activeFilter = 'unmatched'"
            class="px-3 py-1 rounded-lg font-medium transition-all flex items-center space-x-1"
            :class="activeFilter === 'unmatched' ? 'bg-white text-[#B78103] shadow-2xs font-semibold' : 'text-[#6E6E73] hover:text-[#B78103]'"
          >
            <span>待确认</span>
            <span class="px-1.5 py-0.2 rounded-full text-[10px] bg-[#FFF3D6] text-[#B78103] font-bold">{{ unmatchedCount }}</span>
          </button>
          <button
            @click="activeFilter = 'matched'"
            class="px-3 py-1 rounded-lg font-medium transition-all"
            :class="activeFilter === 'matched' ? 'bg-white text-[#248A3D] shadow-2xs font-semibold' : 'text-[#6E6E73] hover:text-[#248A3D]'"
          >
            已匹配 ({{ matchedCount }})
          </button>
          <button
            @click="activeFilter = 'discount'"
            class="px-3 py-1 rounded-lg font-medium transition-all"
            :class="activeFilter === 'discount' ? 'bg-white text-[#34C759] shadow-2xs font-semibold' : 'text-[#6E6E73] hover:text-[#34C759]'"
          >
            真打折 (&lt;1.0)
          </button>
          <button
            @click="activeFilter = 'premium'"
            class="px-3 py-1 rounded-lg font-medium transition-all"
            :class="activeFilter === 'premium' ? 'bg-white text-[#E65100] shadow-2xs font-semibold' : 'text-[#6E6E73] hover:text-[#E65100]'"
          >
            溢价模型 (&gt;1.0)
          </button>
        </div>

        <!-- 右侧：搜索框与重新匹配 -->
        <div class="flex items-center space-x-2">
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索渠道或官网模型..."
              class="w-64 pl-8 pr-3 py-1.5 rounded-xl bg-white border border-[#E5E5EA] text-xs focus:outline-none focus:border-[#0071E3] transition-colors"
            />
            <span class="absolute left-2.5 top-1.5 text-xs text-[#86868B]">🔍</span>
          </div>

          <button
            @click="reMatchAll"
            :disabled="isLoading"
            class="px-3 py-1.5 rounded-xl bg-white hover:bg-[#F2F2F7] text-[#0071E3] border border-[#CCE4FB] text-xs font-semibold transition-colors flex items-center space-x-1 shadow-2xs cursor-pointer"
            title="重置并重新执行智能模糊打分"
          >
            <span>🔄</span>
            <span>重新模糊匹配</span>
          </button>
        </div>
      </div>

      <!-- 4. 核心对照大表格 -->
      <div class="flex-1 overflow-y-auto min-h-0 relative">
        <div v-if="isLoading" class="absolute inset-0 bg-white/70 backdrop-blur-2xs flex items-center justify-center z-10">
          <div class="flex flex-col items-center space-y-2">
            <div class="w-8 h-8 border-3 border-[#0071E3] border-t-transparent rounded-full animate-spin"></div>
            <span class="text-xs text-[#6E6E73] font-medium">正在检索官网第一档模型并执行模糊匹配...</span>
          </div>
        </div>

        <table class="w-full text-left border-collapse">
          <thead class="sticky top-0 bg-[#F2F2F7] border-b border-[#E5E5EA] text-[11px] text-[#86868B] font-semibold uppercase tracking-wider z-5">
            <tr>
              <th class="py-2.5 px-4 w-12 text-center">状态</th>
              <th class="py-2.5 px-4 w-64">渠道原生模型 / 分组</th>
              <th class="py-2.5 px-3 w-40 text-right">渠道实际折算价</th>
              <th class="py-2.5 px-4 w-72">映射的官网标准模型 (第一档)</th>
              <th class="py-2.5 px-3 w-40 text-right">官网第一档基准价</th>
              <th class="py-2.5 px-4 w-44 text-center">真实折扣 / 溢价率</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[#E5E5EA] text-xs">
            <tr
              v-for="(item, idx) in filteredList"
              :key="idx"
              class="hover:bg-[#FBFBFD] transition-colors"
              :class="!item.is_matched ? 'bg-[#FFFDF5]' : ''"
            >
              <!-- 1. 匹配状态 -->
              <td class="py-3 px-4 text-center">
                <span
                  v-if="item.is_matched && item.official_model_id"
                  class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-[#E8F8EE] text-[#248A3D] text-[11px] font-bold"
                  title="已完成官网标准映射"
                >
                  ✓
                </span>
                <span
                  v-else
                  class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-[#FFF3D6] text-[#B78103] text-[11px] font-bold animate-pulse"
                  title="尚未匹配，请手动选择"
                >
                  ?
                </span>
              </td>

              <!-- 2. 渠道原生模型与分组 -->
              <td class="py-3 px-4">
                <div class="font-bold text-[#1D1D1F] font-mono text-xs break-all">
                  {{ item.channel_model_name }}
                </div>
                <div class="flex items-center space-x-1.5 mt-0.5">
                  <span
                    v-if="item.group_name"
                    class="px-1.5 py-0.2 rounded text-[10px] font-mono bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7]"
                  >
                    {{ item.group_name }}
                  </span>
                  <span v-if="item.is_auto_matched" class="text-[10px] text-[#34C759] font-medium flex items-center">
                    <span>⚡ 智能匹配</span>
                    <span v-if="item.match_score" class="ml-1 opacity-70">({{ Math.round(item.match_score * 100) }}%)</span>
                  </span>
                </div>
              </td>

              <!-- 3. 渠道实际折算价 (USD 与 CNY) -->
              <td class="py-3 px-3 text-right font-mono">
                <div class="text-[#1D1D1F] font-bold">
                  ${{ item.calculated_input_usd.toFixed(4) }}
                  <span class="text-[10px] text-[#86868B] font-normal">/ ${{ item.calculated_output_usd.toFixed(4) }}</span>
                </div>
                <div class="text-[10px] text-[#86868B]">
                  ¥{{ (item.calculated_input_usd * usdToCnyRate).toFixed(3) }} / ¥{{ (item.calculated_output_usd * usdToCnyRate).toFixed(3) }}
                </div>
              </td>

              <!-- 4. 映射的官网标准模型 (下拉选择器) -->
              <td class="py-3 px-4">
                <div class="relative">
                  <select
                    :value="item.official_model_id || ''"
                    @change="onSelectBenchmark(item, ($event.target as HTMLSelectElement).value)"
                    class="w-full px-2.5 py-1.5 rounded-xl border text-xs font-mono transition-all focus:outline-none focus:ring-2 focus:ring-[#0071E3]/20"
                    :class="item.official_model_id
                      ? 'bg-white border-[#CCE4FB] text-[#1D1D1F] font-medium'
                      : 'bg-[#FFF9E6] border-[#FFE082] text-[#B78103] font-bold'"
                  >
                    <option value="">-- [未映射: 保持渠道原生] --</option>
                    <optgroup
                      v-for="prov in ['alibaba', 'anthropic', 'deepseek', 'google', 'minimax', 'moonshotai', 'openai', 'zhipuai']"
                      :key="prov"
                      :label="`【${prov.toUpperCase()} 官方标准】`"
                    >
                      <option
                        v-for="b in benchmarks.filter(b => b.provider === prov)"
                        :key="b.id"
                        :value="b.id"
                      >
                        {{ b.clean_name }} (基准: ${{ b.converted_input_usd }}/${{ b.converted_output_usd }})
                      </option>
                    </optgroup>
                  </select>
                </div>
              </td>

              <!-- 5. 官网第一档基准价 -->
              <td class="py-3 px-3 text-right font-mono">
                <template v-if="item.official_benchmark">
                  <div class="text-[#0071E3] font-bold">
                    ${{ item.official_benchmark.converted_input_usd }}
                    <span class="text-[10px] text-[#86868B] font-normal">/ ${{ item.official_benchmark.converted_output_usd }}</span>
                  </div>
                  <div class="text-[10px] text-[#86868B]">
                    {{ item.official_benchmark.currency === 'CNY' ? `原厂: ¥${item.official_benchmark.official_input_price}/¥${item.official_benchmark.official_output_price}` : `¥${item.official_benchmark.converted_input_cny}/¥${item.official_benchmark.converted_output_cny}` }}
                  </div>
                </template>
                <template v-else>
                  <span class="text-[#AEAEB2] text-[11px]">- 未关联官网 -</span>
                </template>
              </td>

              <!-- 6. 真实折扣 / 溢价率 -->
              <td class="py-3 px-4 text-center">
                <template v-if="item.official_benchmark && item.composite_discount !== null">
                  <div class="inline-flex items-center space-x-1.5">
                    <span
                      class="px-2.5 py-0.5 rounded-full text-xs border shadow-2xs font-mono"
                      :class="formatDiscount(item.composite_discount).class"
                      :title="`输入单价: ${(item.input_discount! * 10).toFixed(1)}折 | 输出单价: ${(item.output_discount! * 10).toFixed(1)}折`"
                    >
                      {{ formatDiscount(item.composite_discount).label }}
                    </span>
                  </div>
                  <!-- 输入/输出分别展示 -->
                  <div class="text-[10px] text-[#86868B] font-mono mt-0.5">
                    入: {{ (item.input_discount! * 10).toFixed(1) }}折 · 出: {{ (item.output_discount! * 10).toFixed(1) }}折
                  </div>
                </template>
                <template v-else>
                  <span class="text-[11px] text-[#C7C7CC]">-</span>
                </template>
              </td>
            </tr>

            <tr v-if="filteredList.length === 0">
              <td colspan="6" class="py-12 text-center text-xs text-[#86868B]">
                未检索到符合条件的模型条目
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 5. 底部操作栏 -->
      <div class="px-6 py-3.5 border-t border-[#E5E5EA] bg-[#FBFBFD] flex items-center justify-between flex-shrink-0">
        <div class="flex items-center space-x-2">
          <button
            @click="resetAll"
            class="px-3 py-1.5 rounded-xl bg-white hover:bg-[#F2F2F7] text-[#FF3B30] border border-[#E5E5EA] text-xs font-semibold transition-colors cursor-pointer"
          >
            全部重置
          </button>
          <span class="text-xs text-[#86868B]">
            提示: 保存后将把第一档官网基准价格与真实折扣同步至全网比价与供应商模型列表中
          </span>
        </div>

        <div class="flex items-center space-x-3">
          <button
            @click="emit('close')"
            class="px-4 py-2 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] text-xs font-semibold transition-colors cursor-pointer"
          >
            取消
          </button>
          <button
            @click="saveMappings"
            :disabled="isSaving"
            class="px-5 py-2 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-bold transition-all shadow-sm flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
          >
            <span v-if="isSaving" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            <span>{{ isSaving ? '正在计算并保存...' : `保存映射并生效 (${matchedCount}/${totalCount})` }}</span>
          </button>
        </div>
      </div>

    </div>
  </div>
</template>
