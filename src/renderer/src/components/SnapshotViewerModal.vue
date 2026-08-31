<template>
  <div
    class="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 animate-fade-in p-4 sm:p-6"
    @click.self="emit('close')"
  >
    <div
      class="bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl w-[1180px] max-w-[96vw] h-[90vh] flex flex-col shadow-[0_25px_60px_rgba(0,0,0,0.2)] overflow-hidden font-sans"
    >
      <!-- 1. 顶部核心工具栏 (Apple 极简浅色高级风) -->
      <div class="px-6 py-4 border-b border-[#E5E5EA] bg-[#FAFAFC] flex-shrink-0 space-y-3">
        <!-- 顶栏第一行：标题、时间戳与关闭按钮 -->
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-9 h-9 rounded-xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center text-lg font-bold shadow-2xs">
              📸
            </div>
            <div>
              <div class="flex items-center space-x-2">
                <h3 class="font-bold text-base text-[#1D1D1F]">
                  定价网页快照与证据链核对
                </h3>
                <span class="px-2 py-0.5 rounded-md bg-[#F2F2F7] border border-[#E5E5EA] text-[11px] font-medium text-[#0071E3]">
                  {{ snapshotData?.site_name || siteName }}
                </span>
                <span v-if="snapshotData?.models_count" class="px-2 py-0.5 rounded-md bg-[#E6F4EA] border border-[#CEEAD6] text-[11px] font-medium text-[#137333]">
                  已收录 {{ snapshotData.models_count }} 款模型
                </span>
              </div>
              <div class="flex items-center space-x-4 text-xs text-[#86868B] mt-0.5">
                <span>快照抓取时间: <strong class="text-[#1D1D1F] font-mono">{{ snapshotData?.fetched_at || '刚刚' }}</strong></span>
                <span v-if="snapshotData?.doc_updated_at">官方文档发布时间: <strong class="text-[#1D1D1F] font-mono">{{ snapshotData.doc_updated_at }}</strong></span>
              </div>
            </div>
          </div>

          <div class="flex items-center space-x-3">
            <!-- 官方原始网页精准跳转按钮 -->
            <button
              @click="openOfficialWebpage"
              class="px-3.5 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] text-white text-xs font-semibold shadow-xs flex items-center space-x-1.5 transition-all cursor-pointer select-none"
              title="在外部浏览器打开官方网页并自动定位到此模型"
            >
              <span>🌐</span>
              <span>跳转至官方原始网页并定位</span>
              <span class="text-[10px] opacity-80 font-mono">↗</span>
            </button>

            <!-- 关闭按钮 -->
            <button
              @click="emit('close')"
              class="w-8 h-8 rounded-full bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F] flex items-center justify-center transition-colors cursor-pointer text-sm font-bold"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- 顶栏第二行：当前核验模型比对卡片与快速搜索定位控制器 -->
        <div class="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-[#E5E5EA]/70">
          <!-- 左侧：当前核验模型价格摘要 -->
          <div class="flex items-center space-x-3 bg-[#FFFFFF] border border-[#E5E5EA] rounded-xl px-3 py-1.5 shadow-2xs">
            <div class="text-xs text-[#86868B] font-medium">核验目标:</div>
            <div class="font-bold text-xs text-[#1D1D1F] font-mono flex items-center space-x-1.5">
              <span>{{ targetModel?.site_model_name || targetModel?.model_name || targetModel?.model_id || '全部模型' }}</span>
              <span v-if="targetModel?.group_name" class="text-[10px] px-1.5 py-0.2 rounded-sm bg-[#F2F2F7] text-[#86868B]">
                {{ targetModel.group_name }}
              </span>
            </div>
            <div v-if="targetModel" class="flex items-center space-x-2 pl-2 border-l border-[#E5E5EA] text-xs font-mono">
              <span class="text-[#34C759] font-bold">
                输入: ¥{{ (targetModel.calculated_input_cny !== undefined ? targetModel.calculated_input_cny : targetModel.input_price_cny || 0).toFixed(4) }}
              </span>
              <span class="text-[#0071E3] font-bold">
                输出: ¥{{ (targetModel.calculated_output_cny !== undefined ? targetModel.calculated_output_cny : targetModel.output_price_cny || 0).toFixed(4) }}
              </span>
            </div>
          </div>

          <!-- 右侧：快照内关键字定位与切换 -->
          <div class="flex items-center space-x-2">
            <div class="relative w-64">
              <input
                v-model="searchQuery"
                @keyup.enter="handleSearch"
                type="text"
                placeholder="在快照中搜索模型/区间..."
                class="w-full bg-[#FFFFFF] border border-[#E5E5EA] focus:border-[#0071E3] focus:ring-1 focus:ring-[#0071E3]/20 rounded-xl px-3 py-1 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:outline-none transition-all font-mono"
              />
              <span
                v-if="searchQuery"
                @click="searchQuery = ''; clearHighlights()"
                class="absolute right-2.5 top-1 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs"
              >
                ✕
              </span>
            </div>

            <!-- 匹配计数与前后跳转 -->
            <div class="flex items-center space-x-1 bg-[#FFFFFF] border border-[#E5E5EA] rounded-xl px-2 py-0.5 text-xs text-[#6E6E73]">
              <span class="font-mono text-[11px] px-1">
                {{ matchCount > 0 ? `${currentMatchIndex + 1}/${matchCount}` : '0 匹配' }}
              </span>
              <button
                @click="navigateMatch(-1)"
                :disabled="matchCount === 0"
                class="px-1.5 py-0.5 rounded hover:bg-[#F2F2F7] disabled:opacity-30 cursor-pointer font-bold"
                title="上一个匹配位置"
              >
                ▲
              </button>
              <button
                @click="navigateMatch(1)"
                :disabled="matchCount === 0"
                class="px-1.5 py-0.5 rounded hover:bg-[#F2F2F7] disabled:opacity-30 cursor-pointer font-bold"
                title="下一个匹配位置"
              >
                ▼
              </button>
            </div>

            <button
              @click="handleSearch"
              class="px-3 py-1 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] text-xs font-semibold cursor-pointer transition-colors"
            >
              定位
            </button>
          </div>
        </div>
      </div>

      <!-- 2. 快照内容主渲染区 (保留排版、表格边框、支持自动高亮与滚动定位) -->
      <div class="flex-1 relative overflow-hidden bg-[#FFFFFF]">
        <!-- 加载状态 -->
        <div v-if="isLoading" class="absolute inset-0 flex flex-col items-center justify-center space-y-3 bg-white/80 z-20">
          <div class="w-8 h-8 border-3 border-[#0071E3] border-t-transparent rounded-full animate-spin"></div>
          <div class="text-xs text-[#6E6E73] font-medium">正在拉取并解析官方定价快照...</div>
        </div>

        <!-- 错误提示 -->
        <div v-else-if="errorMessage" class="absolute inset-0 flex flex-col items-center justify-center space-y-3 p-6 text-center z-20">
          <div class="text-3xl">⚠️</div>
          <div class="text-sm font-bold text-[#1D1D1F]">暂无可用快照</div>
          <div class="text-xs text-[#86868B] max-w-md">{{ errorMessage }}</div>
          <button
            @click="openOfficialWebpage"
            class="mt-2 px-4 py-1.5 rounded-xl bg-[#0071E3] text-white text-xs font-semibold hover:bg-[#0077ED] cursor-pointer"
          >
            直接前往官方原始网页 ↗
          </button>
        </div>

        <!-- 快照 HTML 容器 -->
        <div
          ref="snapshotContainerRef"
          class="w-full h-full overflow-auto p-6 text-[#1D1D1F] snapshot-content select-text"
          v-html="renderedHtml"
        ></div>
      </div>

      <!-- 3. 底部状态指示栏 -->
      <div class="px-6 py-2.5 border-t border-[#E5E5EA] bg-[#FAFAFC] flex-shrink-0 flex items-center justify-between text-xs text-[#86868B]">
        <div class="flex items-center space-x-2">
          <span class="w-2 h-2 rounded-full bg-[#34C759]"></span>
          <span>快照已就绪 · DOM 节点已建立证据链索引</span>
        </div>
        <div class="flex items-center space-x-3">
          <span>提示: 选中的模型行已使用 <span class="bg-[#FEF08A] text-[#854D0E] font-bold px-1.5 py-0.5 rounded border border-[#FDE047]">黄色呼吸光晕</span> 自动居中高亮</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'

const props = defineProps<{
  siteId: number
  siteName?: string
  targetModel?: any
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = useDashboardStore()
const isLoading = ref(true)
const errorMessage = ref('')
const snapshotData = ref<any>(null)
const renderedHtml = ref('')
const snapshotContainerRef = ref<HTMLElement | null>(null)

// 搜索与高亮状态
const searchQuery = ref('')
const matchElements = ref<HTMLElement[]>([])
const currentMatchIndex = ref(0)
const matchCount = computed(() => matchElements.value.length)

// 拉取快照数据
const fetchSnapshot = async () => {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const res = await axios.get(`${store.apiUrl}/api/v1/channels/${props.siteId}/snapshot`)
    snapshotData.value = res.data
    renderedHtml.value = sanitizeAndEnhanceHtml(res.data.raw_html)

    // 初始化搜索词为传入的目标模型名/标识
    if (props.targetModel) {
      const name = props.targetModel.site_model_name || props.targetModel.model_name || props.targetModel.model_id || ''
      // 提取核心关键词 (去掉括号等冗余)
      searchQuery.value = name.split(' ')[0].split('(')[0].trim()
    }

    await nextTick()
    setTimeout(() => {
      handleSearch()
    }, 200)
  } catch (e: any) {
    errorMessage.value = e.response?.data?.detail || e.message || '获取快照失败'
  } finally {
    isLoading.value = false
  }
}

// 清洗并注入美化样式的 HTML
const sanitizeAndEnhanceHtml = (html: string): string => {
  if (!html) return ''
  // 移除所有外部 script、iframe 等危险标签，保留 table、div、section、p、h1-h6
  let clean = html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')

  return clean
}

// 在快照中执行高亮搜索与居中滚动
const handleSearch = () => {
  clearHighlights()
  const q = searchQuery.value.trim().toLowerCase()
  if (!q || !snapshotContainerRef.value) return

  const container = snapshotContainerRef.value
  const foundElements: HTMLElement[] = []

  // 1. 优先搜索表格行 <tr> 和单元格 <td>
  const rows = container.querySelectorAll('tr, li, .pricing-item, [id^="pricing-provider-"]')
  rows.forEach((row) => {
    const text = row.textContent?.toLowerCase() || ''
    if (text.includes(q)) {
      foundElements.push(row as HTMLElement)
    }
  })

  // 2. 如果没在行中找到，搜索全部段落和标题
  if (foundElements.length === 0) {
    const elements = container.querySelectorAll('h1, h2, h3, h4, p, span, td, th')
    elements.forEach((el) => {
      const text = el.textContent?.toLowerCase() || ''
      if (text.includes(q) && el.children.length === 0) {
        foundElements.push(el as HTMLElement)
      }
    })
  }

  matchElements.value = foundElements
  currentMatchIndex.value = 0

  if (matchElements.value.length > 0) {
    highlightCurrentMatch()
  }
}

// 高亮当前匹配项并平滑滚动居中
const highlightCurrentMatch = () => {
  if (matchElements.value.length === 0) return

  // 移除旧的高亮激活样式
  matchElements.value.forEach((el, idx) => {
    if (idx === currentMatchIndex.value) {
      el.classList.add('snapshot-highlight-active')
      el.classList.remove('snapshot-highlight-match')
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    } else {
      el.classList.add('snapshot-highlight-match')
      el.classList.remove('snapshot-highlight-active')
    }
  })
}

// 切换匹配项
const navigateMatch = (delta: number) => {
  if (matchElements.value.length === 0) return
  const total = matchElements.value.length
  currentMatchIndex.value = (currentMatchIndex.value + delta + total) % total
  highlightCurrentMatch()
}

// 清除高亮
const clearHighlights = () => {
  if (!snapshotContainerRef.value) return
  const container = snapshotContainerRef.value
  container.querySelectorAll('.snapshot-highlight-active, .snapshot-highlight-match').forEach((el) => {
    el.classList.remove('snapshot-highlight-active', 'snapshot-highlight-match')
  })
  matchElements.value = []
  currentMatchIndex.value = 0
}

// 跳转到官方原始网页（自动拼接 Text Fragment 协议）
const openOfficialWebpage = () => {
  let url = snapshotData.value?.source_url || props.targetModel?.website || 'https://help.aliyun.com/zh/model-studio/model-pricing'
  const modelKeyword = searchQuery.value.trim() || props.targetModel?.model_id || ''

  if (modelKeyword) {
    // 现代浏览器原生 Text Fragment 协议: #:~:text=Keyword
    // 例如 https://help.aliyun.com/zh/model-studio/model-pricing#:~:text=qwen3-max
    const encodedKeyword = encodeURIComponent(modelKeyword)
    if (url.includes('#')) {
      url = `${url.split('#')[0]}#:~:text=${encodedKeyword}`
    } else {
      url = `${url}#:~:text=${encodedKeyword}`
    }
  }

  window.open(url, '_blank')
}

onMounted(() => {
  fetchSnapshot()
})
</script>

<style>
/* 快照内部排版与表格增强样式 */
.snapshot-content {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: #1D1D1F;
}

.snapshot-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  font-size: 12px;
  background-color: #FFFFFF;
  border: 1px solid #E5E5EA;
  border-radius: 8px;
  overflow: hidden;
}

.snapshot-content th,
.snapshot-content td {
  padding: 8px 12px;
  border: 1px solid #E5E5EA;
  text-align: left;
}

.snapshot-content th {
  background-color: #F2F2F7;
  color: #1D1D1F;
  font-weight: 600;
}

.snapshot-content tr:hover {
  background-color: #F9F9FB;
}

.snapshot-content h1,
.snapshot-content h2,
.snapshot-content h3 {
  color: #1D1D1F;
  font-weight: 700;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
}

.snapshot-content h2 {
  font-size: 16px;
  border-bottom: 2px solid #E5E5EA;
  padding-bottom: 4px;
}

.snapshot-content h3 {
  font-size: 14px;
}

/* 匹配行高亮与呼吸脉冲动画 */
.snapshot-highlight-active {
  background-color: #FEF08A !important;
  border: 2px solid #EAB308 !important;
  border-radius: 6px;
  box-shadow: 0 0 0 4px rgba(234, 179, 8, 0.35);
  animation: pulse-glow 1.8s infinite ease-in-out;
  transition: all 0.3s ease;
}

.snapshot-highlight-match {
  background-color: #FEF9C3 !important;
  border: 1px dashed #FACC15 !important;
  transition: all 0.2s ease;
}

@keyframes pulse-glow {
  0% {
    box-shadow: 0 0 0 3px rgba(234, 179, 8, 0.3);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(234, 179, 8, 0.6);
  }
  100% {
    box-shadow: 0 0 0 3px rgba(234, 179, 8, 0.3);
  }
}
</style>
