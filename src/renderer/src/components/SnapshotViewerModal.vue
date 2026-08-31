<template>
  <div
    class="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 animate-fade-in p-4 sm:p-6"
    @click.self="emit('close')"
  >
    <div
      class="bg-[#FFFFFF] border border-[#E5E5EA] rounded-3xl w-full max-w-[1240px] h-[88vh] flex flex-col shadow-[0_25px_60px_rgba(0,0,0,0.22)] overflow-hidden transition-all relative"
    >
      <!-- 1. 顶部 Header 状态与控制栏 (Apple 极简浅色高级质感) -->
      <div class="px-6 py-4 border-b border-[#E5E5EA] bg-[#F9F9FB] flex-shrink-0 space-y-3">
        <!-- 上层：标题、来源渠道、文档更新时间、官方直达与关闭 -->
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 rounded-xl bg-[#F3E8FD] text-[#8E24AA] flex items-center justify-center text-base shadow-2xs">
              📸
            </div>
            <div>
              <div class="flex items-center space-x-2">
                <h3 class="font-bold text-sm text-[#1D1D1F]">
                  定价网页快照与证据链核对
                </h3>
                <span class="px-2 py-0.5 rounded-md bg-[#E8F2FD] text-[#0071E3] font-mono text-[11px] font-bold">
                  {{ siteName || '自建渠道' }}
                </span>
                <span v-if="snapshotData?.models_count" class="px-2 py-0.5 rounded-md bg-[#EAF8EE] text-[#34C759] font-mono text-[11px] font-bold">
                  已收录 {{ snapshotData.models_count }} 款模型
                </span>
              </div>
              <div class="text-[11px] text-[#86868B] font-mono mt-0.5 flex items-center space-x-3">
                <span>快照抓取时间: <strong class="text-[#1D1D1F]">{{ formatTime(snapshotData?.fetched_at) }}</strong></span>
                <span v-if="snapshotData?.doc_updated_at">•</span>
                <span v-if="snapshotData?.doc_updated_at">官方文档发布时间: <strong class="text-[#AF52DE]">{{ snapshotData.doc_updated_at }}</strong></span>
              </div>
            </div>
          </div>

          <!-- 右侧操作组 -->
          <div class="flex items-center space-x-2.5">
            <button
              @click="openOfficialWebpage"
              class="px-3.5 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#005BB5] text-white text-xs font-semibold shadow-xs flex items-center space-x-1.5 transition-all cursor-pointer"
              title="打开官方原始网页并自动滚动高亮当前模型"
            >
              <span>🌐</span>
              <span>跳转至官方原始网页并定位 ↗</span>
            </button>
            <button
              @click="emit('close')"
              class="w-7 h-7 rounded-full bg-[#E5E5EA]/80 hover:bg-[#D1D1D6] text-[#6E6E73] hover:text-[#1D1D1F] flex items-center justify-center text-xs transition-colors cursor-pointer"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- 下层：核验目标模型价格对照卡 + 关键词搜索定位工具条 -->
        <div class="flex items-center justify-between pt-1 border-t border-[#E5E5EA]/60 text-xs">
          <!-- 目标核验信息 -->
          <div class="flex items-center space-x-2">
            <span class="text-[#86868B]">核验目标:</span>
            <span v-if="targetModel" class="font-bold font-mono text-[#1D1D1F] px-2 py-0.5 rounded bg-white border border-[#E5E5EA] shadow-2xs">
              {{ targetModel.site_model_name || targetModel.model_name || targetModel.model_id }}
            </span>
            <span v-else class="text-[#6E6E73] font-medium">全部模型</span>

            <!-- 折算价格显示 -->
            <div v-if="targetModel" class="flex items-center space-x-2 text-[11px] font-mono ml-2">
              <span class="px-2 py-0.5 rounded bg-[#EAF8EE] text-[#137333] border border-[#CEEAD6]">
                输入: {{ store.formatCurrency(targetModel.calculated_input_usd) }}
              </span>
              <span class="px-2 py-0.5 rounded bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB]">
                输出: {{ store.formatCurrency(targetModel.calculated_output_usd) }}
              </span>
            </div>
          </div>

          <!-- 快照检索与定位 -->
          <div class="flex items-center space-x-2">
            <div class="relative flex items-center">
              <input
                v-model="searchQuery"
                @keyup.enter="handleSearch"
                type="text"
                placeholder="在快照中搜索模型/区间..."
                class="w-56 bg-white border border-[#E5E5EA] rounded-xl px-3 py-1 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:border-[#0071E3] focus:outline-none transition-all font-mono"
              />
              <span
                v-if="searchQuery"
                @click="searchQuery = ''; clearHighlights()"
                class="absolute right-2 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs"
              >
                ✕
              </span>
            </div>

            <!-- 匹配计数与前后跳转 -->
            <div class="flex items-center space-x-1 text-xs text-[#6E6E73]">
              <span class="font-mono text-[11px] px-1">
                {{ matchCount > 0 ? `${currentMatchIndex + 1}/${matchCount}` : '0 匹配' }}
              </span>
              <button
                @click="navigateMatch(-1)"
                :disabled="matchCount === 0"
                class="px-1.5 py-0.5 rounded hover:bg-[#E5E5EA] disabled:opacity-30 cursor-pointer font-bold"
                title="上一个匹配位置"
              >
                ▲
              </button>
              <button
                @click="navigateMatch(1)"
                :disabled="matchCount === 0"
                class="px-1.5 py-0.5 rounded hover:bg-[#E5E5EA] disabled:opacity-30 cursor-pointer font-bold"
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

      <!-- 2. 快照内容主渲染区 (完全隔离的 iframe 沙箱，彻底杜绝 fixed 顶栏与全局 CSS 污染) -->
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

        <!-- 独立的 iframe 沙箱 -->
        <iframe
          v-show="!isLoading && !errorMessage"
          ref="iframeRef"
          :srcdoc="sanitizedHtmlDoc"
          class="w-full h-full border-0 bg-white"
          sandbox="allow-same-origin"
          @load="onIframeLoad"
        ></iframe>
      </div>

      <!-- 3. 底部状态指示栏 -->
      <div class="px-6 py-2.5 border-t border-[#E5E5EA] bg-[#FAFAFC] flex-shrink-0 flex items-center justify-between text-xs text-[#86868B]">
        <div class="flex items-center space-x-2">
          <span class="w-2 h-2 rounded-full bg-[#34C759]"></span>
          <span>快照已就绪 (沙箱隔离运行) · DOM 节点已建立证据链索引</span>
        </div>
        <div class="flex items-center space-x-3">
          <span>提示: 选中的模型行已使用 <span class="bg-[#FEF08A] text-[#854D0E] font-bold px-1.5 py-0.5 rounded border border-[#FDE047]">黄色呼吸光晕</span> 自动居中高亮</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
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
const rawHtml = ref('')
const iframeRef = ref<HTMLIFrameElement | null>(null)

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
    rawHtml.value = res.data.raw_html || ''

    // 初始化搜索词为传入的目标模型名/标识
    if (props.targetModel) {
      const name = props.targetModel.site_model_name || props.targetModel.model_name || props.targetModel.model_id || ''
      // 提取核心关键词 (去掉括号等冗余)
      searchQuery.value = name.split(' ')[0].split('(')[0].trim()
    }
  } catch (e: any) {
    errorMessage.value = e.response?.data?.detail || e.message || '获取快照失败'
  } finally {
    isLoading.value = false
  }
}

// 构造完全独立的 iframe HTML 文档，剥离全部 script 标签，并注入高亮呼吸动画与清除固定导航栏样式
const sanitizedHtmlDoc = computed(() => {
  if (!rawHtml.value) return ''

  // 1. 彻底移除所有外部与内联 script 标签，防止 React/Next.js 在静态沙箱中发生客户端 Hydration 崩溃
  let html = rawHtml.value
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<noscript\b[^<]*(?:(?!<\/noscript>)<[^<]*)*<\/noscript>/gi, '')

  // 注入专门针对高亮与去噪的样式
  const injectStyles = `
    <style>
      /* 隐藏外部网页自带的固定顶栏和导航，使快照纯粹聚焦在表格内容 */
      header, nav, footer, [class*="header"], [class*="nav-"], [class*="navbar"] {
        display: none !important;
      }
      
      /* 呼吸光晕激活样式 */
      .snapshot-highlight-active {
        background-color: #FEF08A !important;
        outline: 3px solid #EAB308 !important;
        outline-offset: 2px;
        border-radius: 8px;
        box-shadow: 0 0 0 8px rgba(234, 179, 8, 0.45) !important;
        animation: pulse-glow-iframe 1.8s infinite ease-in-out !important;
        transition: all 0.3s ease !important;
      }

      .snapshot-highlight-match {
        background-color: #FEF9C3 !important;
        outline: 2px dashed #FACC15 !important;
        outline-offset: 1px;
        transition: all 0.2s ease !important;
      }

      @keyframes pulse-glow-iframe {
        0% {
          box-shadow: 0 0 0 3px rgba(234, 179, 8, 0.3);
        }
        50% {
          box-shadow: 0 0 0 10px rgba(234, 179, 8, 0.6);
        }
        100% {
          box-shadow: 0 0 0 3px rgba(234, 179, 8, 0.3);
        }
      }

      /* 保证页面滚动平滑与顶部留白 */
      html, body {
        scroll-behavior: smooth;
        padding: 16px !important;
        background: #ffffff !important;
      }
    </style>
  `

  // 如果有 </head> 则在 head 前注入，否则在最前面注入
  if (html.includes('</head>')) {
    html = html.replace('</head>', `${injectStyles}</head>`)
  } else {
    html = injectStyles + html
  }

  return html
})

// iframe 加载完成后的回调
const onIframeLoad = () => {
  const doc = iframeRef.value?.contentDocument
  if (!doc) return

  // 拦截 iframe 内的所有 <a> 点击，防止跳转离开快照
  doc.querySelectorAll('a').forEach((a) => {
    a.addEventListener('click', (e) => {
      e.preventDefault()
      const href = a.getAttribute('href')
      if (href && href.startsWith('http')) {
        window.open(href, '_blank')
      }
    })
  })

  // 自动触发搜索与居中高亮
  setTimeout(() => {
    handleSearch()
  }, 400)
}

// 在 iframe 快照中执行高亮搜索与居中滚动
const handleSearch = () => {
  clearHighlights()
  const q = searchQuery.value.trim().toLowerCase()
  const doc = iframeRef.value?.contentDocument
  if (!q || !doc) return

  // 提取关键词变体 (例如 Qwen/Qwen3-14B -> [qwen/qwen3-14b, qwen3-14b])
  const qVariants = [q]
  if (q.includes('/')) {
    qVariants.push(q.split('/').pop()!.toLowerCase())
  }
  if (q.includes('-')) {
    qVariants.push(q.replace(/-/g, ' ').toLowerCase())
  }

  const isMatch = (text: string) => {
    const lower = text.toLowerCase()
    return qVariants.some((v) => lower.includes(v))
  }

  const foundElements: HTMLElement[] = []

  // 1. 优先搜索行级元素 (硅基流动的 pricing-row 或标准表格 tr)
  const rows = doc.querySelectorAll('[id^="pricing-row-"], tr, li, .pricing-item')
  rows.forEach((row) => {
    const text = row.textContent || ''
    const rowTitle = row.querySelector('a[title]')?.getAttribute('title') || ''
    if (isMatch(text) || isMatch(rowTitle)) {
      foundElements.push(row as HTMLElement)
    }
  })

  // 2. 如果没在行级中找到，搜索所有链接、标题与单元格
  if (foundElements.length === 0) {
    const elements = doc.querySelectorAll('a, td, th, h1, h2, h3, h4, p, span')
    elements.forEach((el) => {
      const text = el.textContent || ''
      const title = el.getAttribute('title') || ''
      if ((isMatch(text) || isMatch(title)) && (el.children.length === 0 || el.tagName === 'A')) {
        const parentRow = el.closest('[id^="pricing-row-"], tr, div') as HTMLElement
        if (parentRow && !foundElements.includes(parentRow)) {
          foundElements.push(parentRow)
        } else if (!foundElements.includes(el as HTMLElement)) {
          foundElements.push(el as HTMLElement)
        }
      }
    })
  }

  matchElements.value = foundElements
  currentMatchIndex.value = 0

  if (matchElements.value.length > 0) {
    highlightCurrentMatch()
  }
}

// 高亮当前匹配项并在 iframe 内平滑滚动居中
const highlightCurrentMatch = () => {
  if (matchElements.value.length === 0) return

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
  const doc = iframeRef.value?.contentDocument
  if (!doc) return
  doc.querySelectorAll('.snapshot-highlight-active, .snapshot-highlight-match').forEach((el) => {
    el.classList.remove('snapshot-highlight-active', 'snapshot-highlight-match')
  })
  matchElements.value = []
  currentMatchIndex.value = 0
}

// 跳转到官方原始网页（自动拼接 Text Fragment 协议）
const openOfficialWebpage = () => {
  let url = snapshotData.value?.source_url || props.targetModel?.website || 'https://siliconflow.cn/pricing'
  const modelKeyword = searchQuery.value.trim() || props.targetModel?.model_id || ''

  if (modelKeyword) {
    // 现代浏览器原生 Text Fragment 协议: #:~:text=Keyword
    const cleanKeyword = encodeURIComponent(modelKeyword)
    if (url.includes('#')) {
      url = url.split('#')[0]
    }
    url = `${url}#:~:text=${cleanKeyword}`
  }

  window.open(url, '_blank')
}

// 格式化抓取时间
const formatTime = (timeStr?: string) => {
  if (!timeStr) return '刚刚'
  try {
    const d = new Date(timeStr)
    if (isNaN(d.getTime())) return timeStr
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return timeStr
  }
}

onMounted(() => {
  fetchSnapshot()
})
</script>
