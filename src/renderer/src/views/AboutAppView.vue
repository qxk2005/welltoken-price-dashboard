<template>
  <div class="h-full flex flex-col bg-[#F5F5F7] overflow-hidden select-none">
    <!-- 顶部状态栏与标题区 -->
    <div class="bg-white border-b border-[#E5E5EA] px-6 py-4 flex-shrink-0">
      <div class="max-w-5xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <!-- 品牌与版本标识 -->
        <div class="flex items-center space-x-4">
          <!-- Logo 渐变图标 -->
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#0071E3] to-[#42A5F5] flex items-center justify-center text-white shadow-md flex-shrink-0">
            <span class="text-2xl font-black tracking-wider font-sans">W</span>
          </div>

          <div>
            <div class="flex items-center space-x-2.5">
              <h1 class="text-xl font-bold text-[#1D1D1F] tracking-tight font-sans">
                {{ versionInfo.productName }}
              </h1>
              <!-- 当前打包版本号 Badge -->
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold font-mono bg-[#E8F8EE] text-[#34C759] border border-[#34C759]/20 shadow-xs">
                <span class="w-1.5 h-1.5 rounded-full bg-[#34C759] mr-1.5 animate-pulse"></span>
                {{ versionInfo.fullVersion }}
              </span>
              <span class="text-xs text-[#86868B] font-mono">正式打包构建</span>
            </div>
            <p class="text-xs text-[#6E6E73] mt-1 line-clamp-1 max-w-xl">
              {{ versionInfo.description }}
            </p>
          </div>
        </div>

        <!-- 快捷操作按钮组 -->
        <div class="flex items-center space-x-2.5 flex-shrink-0">
          <button
            @click="copyDiagnosticInfo"
            class="px-3 py-1.5 rounded-xl text-xs font-medium border border-[#E5E5EA] bg-white hover:bg-[#F5F5F7] text-[#1D1D1F] active:bg-[#E5E5EA] transition-all flex items-center space-x-1.5 shadow-2xs cursor-pointer"
            title="复制版本号、环境与 Git 构建信息到剪贴板"
          >
            <svg class="w-3.5 h-3.5 text-[#0071E3]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            <span>{{ copySuccess ? '已复制诊断信息' : '复制诊断信息' }}</span>
          </button>

          <a
            :href="versionInfo.homepage"
            target="_blank"
            rel="noopener noreferrer"
            class="px-3 py-1.5 rounded-xl text-xs font-medium border border-[#E5E5EA] bg-white hover:bg-[#F5F5F7] text-[#1D1D1F] active:bg-[#E5E5EA] transition-all flex items-center space-x-1.5 shadow-2xs cursor-pointer"
          >
            <svg class="w-3.5 h-3.5 text-[#24292F]" viewBox="0 0 24 24" fill="currentColor">
              <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
            </svg>
            <span>GitHub 仓库</span>
          </a>

          <a
            :href="`${versionInfo.homepage}/releases`"
            target="_blank"
            rel="noopener noreferrer"
            class="px-3 py-1.5 rounded-xl text-xs font-bold bg-[#0071E3] text-white hover:bg-[#0077ED] active:bg-[#0062C4] transition-all flex items-center space-x-1.5 shadow-sm cursor-pointer"
          >
            <span>检查更新</span>
            <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
          </a>
        </div>
      </div>
    </div>

    <!-- 主体滚动区域：系统诊断卡片 + 结构化更新日志时间轴 -->
    <div class="flex-1 overflow-y-auto p-6 space-y-6">
      <div class="max-w-5xl mx-auto space-y-6">
        <!-- 1. 系统与构建元数据指标卡片群 -->
        <section class="grid grid-cols-2 md:grid-cols-4 gap-3.5">
          <!-- 卡片 1: 当前版本 -->
          <div class="bg-white border border-[#E5E5EA] rounded-2xl p-4 shadow-2xs hover:border-[#0071E3]/30 transition-all">
            <div class="text-[11px] font-medium text-[#86868B] flex items-center justify-between">
              <span>当前打包版本</span>
              <span class="w-2 h-2 rounded-full bg-[#34C759]"></span>
            </div>
            <div class="text-xl font-black font-mono text-[#1D1D1F] mt-1.5">
              {{ versionInfo.fullVersion }}
            </div>
            <div class="text-[10px] font-mono text-[#86868B] mt-1">
              内部代号: {{ versionInfo.version }}
            </div>
          </div>

          <!-- 卡片 2: 构建时间戳 -->
          <div class="bg-white border border-[#E5E5EA] rounded-2xl p-4 shadow-2xs hover:border-[#0071E3]/30 transition-all">
            <div class="text-[11px] font-medium text-[#86868B] flex items-center justify-between">
              <span>编译构建时间</span>
              <svg class="w-3.5 h-3.5 text-[#86868B]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
            </div>
            <div class="text-sm font-bold font-mono text-[#1D1D1F] mt-2 truncate" :title="versionInfo.build.time">
              {{ versionInfo.build.time }}
            </div>
            <div class="text-[10px] text-[#34C759] font-medium mt-1">
              每次打包自动刷新
            </div>
          </div>

          <!-- 卡片 3: Git 提交版本 -->
          <div class="bg-white border border-[#E5E5EA] rounded-2xl p-4 shadow-2xs hover:border-[#0071E3]/30 transition-all">
            <div class="text-[11px] font-medium text-[#86868B] flex items-center justify-between">
              <span>Git 提交哈希</span>
              <svg class="w-3.5 h-3.5 text-[#86868B]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="18" cy="18" r="3"></circle>
                <circle cx="6" cy="6" r="3"></circle>
                <path d="M13 6h3a2 2 0 0 1 2 2v7"></path>
                <line x1="6" y1="9" x2="6" y2="21"></line>
              </svg>
            </div>
            <div class="text-sm font-bold font-mono text-[#0071E3] mt-2 flex items-center space-x-1.5">
              <span>#{{ versionInfo.git.commit }}</span>
              <span class="text-[10px] font-normal text-[#86868B]">({{ versionInfo.git.branch }})</span>
            </div>
            <div class="text-[10px] text-[#86868B] font-mono mt-1 truncate">
              {{ versionInfo.git.date || '主干同步' }}
            </div>
          </div>

          <!-- 卡片 4: 运行环境与核心架构 -->
          <div class="bg-white border border-[#E5E5EA] rounded-2xl p-4 shadow-2xs hover:border-[#0071E3]/30 transition-all">
            <div class="text-[11px] font-medium text-[#86868B] flex items-center justify-between">
              <span>运行架构 / 引擎</span>
              <span class="px-1.5 py-0.2 rounded text-[9px] font-mono bg-[#F2F2F7] text-[#6E6E73]">
                {{ versionInfo.build.platform }}-{{ versionInfo.build.arch }}
              </span>
            </div>
            <div class="text-xs font-bold font-mono text-[#1D1D1F] mt-2 truncate">
              Electron 30 + Vue 3.4
            </div>
            <div class="text-[10px] text-[#86868B] mt-1 font-mono">
              FastAPI + SQLite WAL 就绪
            </div>
          </div>
        </section>

        <!-- 2. 版本变化日志时间轴标题与过滤栏 -->
        <section class="bg-white border border-[#E5E5EA] rounded-2xl p-5 shadow-2xs space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-[#E5E5EA]">
            <div class="flex items-center space-x-2">
              <svg class="w-4 h-4 text-[#0071E3]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <line x1="10" y1="9" x2="8" y2="9"></line>
              </svg>
              <h2 class="text-sm font-bold text-[#1D1D1F] tracking-tight font-sans">
                版本变化日志 (CHANGELOG)
              </h2>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#F2F2F7] text-[#6E6E73]">
                共 {{ versionInfo.changelog.length }} 个版本记录
              </span>
            </div>

            <!-- 搜索与折叠切换 -->
            <div class="flex items-center space-x-2">
              <div class="relative w-48 sm:w-60">
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="搜索版本号或更新内容..."
                  class="w-full bg-[#F5F5F7] border border-[#E5E5EA] focus:border-[#0071E3] rounded-xl px-3 py-1.5 text-xs text-[#1D1D1F] outline-hidden transition-all pl-8"
                />
                <svg class="w-3.5 h-3.5 text-[#86868B] absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <button
                  v-if="searchQuery"
                  @click="searchQuery = ''"
                  class="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#86868B] hover:text-[#1D1D1F] text-xs cursor-pointer"
                >
                  ✕
                </button>
              </div>

              <button
                @click="toggleAll"
                class="px-2.5 py-1.5 rounded-xl text-xs font-medium bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#48484A] transition-colors cursor-pointer whitespace-nowrap"
              >
                {{ allExpanded ? '全部收起' : '全部展开' }}
              </button>
            </div>
          </div>

          <!-- 时间轴列表 -->
          <div class="relative pl-6 space-y-6 before:absolute before:left-2 before:top-3 before:bottom-3 before:w-0.5 before:bg-[#E5E5EA]">
            <div
              v-for="(entry, index) in filteredChangelog"
              :key="entry.version"
              class="relative group"
            >
              <!-- 时间轴节点指示器 -->
              <div
                class="absolute -left-6 top-1.5 w-4 h-4 rounded-full border-2 transition-all flex items-center justify-center bg-white"
                :class="[
                  index === 0
                    ? 'border-[#0071E3] bg-[#0071E3] ring-4 ring-[#0071E3]/20'
                    : 'border-[#86868B] group-hover:border-[#0071E3]'
                ]"
              >
                <span
                  v-if="index === 0"
                  class="w-1.5 h-1.5 rounded-full bg-white animate-pulse"
                ></span>
              </div>

              <!-- 版本卡片外框 -->
              <div
                class="border rounded-2xl transition-all duration-200 overflow-hidden"
                :class="[
                  index === 0
                    ? 'border-[#0071E3]/40 bg-gradient-to-br from-white to-[#F0F8FF]/40 shadow-xs'
                    : 'border-[#E5E5EA] bg-white hover:border-[#D1D1D6]'
                ]"
              >
                <!-- 卡片头部标题栏 -->
                <div
                  @click="toggleVersion(entry.version)"
                  class="p-4 flex items-center justify-between cursor-pointer select-none transition-colors"
                  :class="index === 0 ? 'bg-[#F9FBFF]/80' : 'hover:bg-[#F9F9FB]'"
                >
                  <div class="flex items-center space-x-3 flex-wrap gap-y-1">
                    <!-- 版本 Badge -->
                    <span
                      class="px-2.5 py-0.5 rounded-lg text-xs font-bold font-mono flex items-center space-x-1"
                      :class="[
                        index === 0
                          ? 'bg-[#0071E3] text-white shadow-xs'
                          : 'bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA]'
                      ]"
                    >
                      <span>v{{ entry.version }}</span>
                    </span>

                    <span v-if="index === 0" class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-[#E8F8EE] text-[#34C759] border border-[#34C759]/20">
                      当前打包版本
                    </span>

                    <h3 class="text-xs sm:text-sm font-bold text-[#1D1D1F] font-sans">
                      {{ entry.tag.replace(/^v[\d\.]+\s*/, '') || entry.fullTitle }}
                    </h3>

                    <span v-if="entry.date" class="text-xs text-[#86868B] font-mono">
                      ({{ entry.date }})
                    </span>
                  </div>

                  <!-- 折叠箭头 -->
                  <div class="flex items-center space-x-2 text-[#86868B] flex-shrink-0">
                    <span class="text-[11px] hidden sm:inline">
                      {{ isExpanded(entry.version) ? '收起' : '展开' }}
                    </span>
                    <svg
                      class="w-4 h-4 transform transition-transform duration-200"
                      :class="isExpanded(entry.version) ? 'rotate-180' : 'rotate-0'"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                  </div>
                </div>

                <!-- 卡片折叠内容区 -->
                <div
                  v-show="isExpanded(entry.version)"
                  class="px-4 pb-4 pt-2 border-t border-[#E5E5EA]/70 text-xs text-[#333336] space-y-3.5"
                >
                  <div
                    v-for="(sec, sIdx) in entry.sections"
                    :key="sIdx"
                    class="space-y-1.5"
                  >
                    <h4 class="font-bold text-[#1D1D1F] text-xs flex items-center space-x-1.5 mt-2">
                      <span>{{ sec.title }}</span>
                    </h4>
                    <ul class="space-y-1.5 pl-2">
                      <li
                        v-for="(item, iIdx) in sec.items"
                        :key="iIdx"
                        class="flex items-start space-x-2 text-[12px] leading-relaxed text-[#48484A]"
                      >
                        <span class="w-1.5 h-1.5 rounded-full bg-[#0071E3] mt-1.5 flex-shrink-0"></span>
                        <div class="flex-1" v-html="formatMarkdownLine(item)"></div>
                      </li>
                    </ul>
                  </div>

                  <!-- 兜底纯文本渲染 -->
                  <div
                    v-if="entry.sections.length === 0"
                    class="font-mono text-[11px] text-[#6E6E73] whitespace-pre-wrap bg-[#F5F5F7] p-3 rounded-xl"
                  >
                    {{ entry.rawContent }}
                  </div>
                </div>
              </div>
            </div>

            <!-- 空搜索提示 -->
            <div
              v-if="filteredChangelog.length === 0"
              class="py-12 text-center text-xs text-[#86868B] font-sans"
            >
              未找到与「{{ searchQuery }}」相关的版本更新记录
            </div>
          </div>
        </section>

        <!-- 底部开源许可与致谢卡片 -->
        <div class="text-center text-xs text-[#86868B] py-3 space-y-1 font-mono">
          <div>WellToken Price Dashboard • MIT Open Source License</div>
          <div class="text-[11px] text-[#A1A1A6]">
            Built with Electron, Vite, Vue 3, TailwindCSS, Python FastAPI & SQLite WAL Engine
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { versionInfo } from '../generated/version_info'

const searchQuery = ref('')
const copySuccess = ref(false)

// 默认展开最新版本
const expandedVersions = ref<Record<string, boolean>>({
  [versionInfo.version]: true
})

// 如果有上一个版本，也默认展开
if (versionInfo.changelog[1]) {
  expandedVersions.value[versionInfo.changelog[1].version] = true
}

function isExpanded(ver: string): boolean {
  return !!expandedVersions.value[ver]
}

function toggleVersion(ver: string) {
  expandedVersions.value[ver] = !expandedVersions.value[ver]
}

const allExpanded = computed(() => {
  return versionInfo.changelog.every(c => expandedVersions.value[c.version])
})

function toggleAll() {
  const target = !allExpanded.value
  versionInfo.changelog.forEach(c => {
    expandedVersions.value[c.version] = target
  })
}

const filteredChangelog = computed(() => {
  if (!searchQuery.value.trim()) {
    return versionInfo.changelog
  }
  const q = searchQuery.value.toLowerCase().trim()
  return versionInfo.changelog.filter(c => {
    return (
      c.version.toLowerCase().includes(q) ||
      c.tag.toLowerCase().includes(q) ||
      c.fullTitle.toLowerCase().includes(q) ||
      c.rawContent.toLowerCase().includes(q)
    )
  })
})

function formatMarkdownLine(text: string): string {
  // 简易 Markdown 加粗替换 (**text** -> <strong>text</strong>)
  return text.replace(/\*\*(.*?)\*\*/g, '<strong class="text-[#1D1D1F] font-bold">$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded bg-[#F2F2F7] text-[#0071E3] font-mono text-[11px] border border-[#E5E5EA]">$1</code>')
}

async function copyDiagnosticInfo() {
  const diag = `WellToken Price Dashboard 系统诊断报告
============================================
版本信息: ${versionInfo.fullVersion} (${versionInfo.version})
构建时间: ${versionInfo.build.time}
Git 提交: ${versionInfo.git.commit} (分支: ${versionInfo.git.branch})
运行平台: ${versionInfo.build.platform} (${versionInfo.build.arch})
Node 引擎: ${versionInfo.build.node}
前端技术栈: Electron 30 + Vue 3.4 + Vite 5
后端数据引擎: Python FastAPI + SQLite 3 (WAL)
官方仓库: ${versionInfo.homepage}
============================================`

  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(diag)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = diag
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    copySuccess.value = true
    setTimeout(() => {
      copySuccess.value = false
    }, 2500)
  } catch (e) {
    console.error('复制失败:', e)
  }
}
</script>
