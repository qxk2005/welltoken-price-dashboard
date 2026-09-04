<template>
  <div
    v-if="store.editingNoteItem"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-xs select-none p-4"
    @click.self="store.editingNoteItem = null"
  >
    <div
      class="bg-white rounded-2xl shadow-2xl border border-[#E5E5EA] w-full max-w-lg overflow-hidden animate-scale-up"
    >
      <!-- 模态框标题 -->
      <div class="px-5 py-4 border-b border-[#E5E5EA] flex items-center justify-between bg-[#FBFBFD]">
        <div class="flex items-center space-x-2 min-w-0">
          <div class="w-6 h-6 rounded-lg bg-[#34C759]/10 text-[#34C759] flex items-center justify-center font-bold">
            ✎
          </div>
          <h3 class="text-sm font-bold text-[#1D1D1F] truncate">
            编辑用户自定义备注与标签: {{ store.editingNoteItem.model_name }}
          </h3>
        </div>
        <button
          @click="store.editingNoteItem = null"
          class="w-6 h-6 rounded-lg hover:bg-[#F2F2F7] text-[#86868B] hover:text-[#1D1D1F] flex items-center justify-center transition-all cursor-pointer"
        >
          ✕
        </button>
      </div>

      <!-- 输入内容 -->
      <div class="p-5 space-y-4">
        <!-- 标签输入 -->
        <div class="space-y-1.5">
          <label class="text-xs font-semibold text-[#48484A] flex items-center justify-between">
            <span>个性化标签 (逗号分隔)</span>
            <span class="text-[11px] text-[#86868B] font-normal">如: 主力推荐, 内部使用, 测评待定</span>
          </label>
          <input
            type="text"
            v-model="editTags"
            placeholder="例如: 主力推理, 经济省钱, 压测备选"
            class="w-full px-3 py-2 bg-[#F2F2F7] border border-[#E5E5EA] rounded-xl text-xs text-[#1D1D1F] focus:bg-white focus:border-[#0071E3] focus:outline-none transition-all"
          />
        </div>

        <!-- 快捷标签推荐 -->
        <div class="flex items-center flex-wrap gap-1.5">
          <span class="text-[11px] text-[#86868B]">快捷插入:</span>
          <button
            v-for="tag in presetTags"
            :key="tag"
            @click="addTag(tag)"
            type="button"
            class="px-2 py-0.5 rounded-lg border border-[#E5E5EA] bg-[#F9F9FB] hover:bg-[#E8F2FD] hover:border-[#0071E3]/40 text-[11px] text-[#48484A] hover:text-[#0071E3] transition-all cursor-pointer"
          >
            + {{ tag }}
          </button>
        </div>

        <!-- 自定义备注 -->
        <div class="space-y-1.5">
          <label class="text-xs font-semibold text-[#48484A]">
            业务备注说明 (持久化保存，重新抓取价格时不会覆盖)
          </label>
          <textarea
            rows="4"
            v-model="editNotes"
            placeholder="记录此模型在您实际业务中的特点、使用经验、API Key 分组或注意事项..."
            class="w-full p-3 bg-[#F2F2F7] border border-[#E5E5EA] rounded-xl text-xs text-[#1D1D1F] focus:bg-white focus:border-[#0071E3] focus:outline-none transition-all resize-none"
          ></textarea>
        </div>
      </div>

      <!-- 底部操作按钮 -->
      <div class="px-5 py-3 border-t border-[#E5E5EA] bg-[#FBFBFD] flex items-center justify-end space-x-2.5">
        <button
          @click="store.editingNoteItem = null"
          class="px-4 py-1.5 rounded-xl border border-[#E5E5EA] hover:bg-[#F2F2F7] text-[#6E6E73] text-xs font-medium transition-all cursor-pointer"
        >
          取消
        </button>
        <button
          @click="handleSave"
          :disabled="isSaving"
          class="px-5 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-bold transition-all shadow-sm cursor-pointer disabled:opacity-50"
        >
          {{ isSaving ? '保存中...' : '保存更改' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useOfficialPricingStore } from '../stores/officialPricingStore'

const store = useOfficialPricingStore()

const editNotes = ref('')
const editTags = ref('')
const isSaving = ref(false)

const presetTags = ['主力推荐', '生产环境', '低延迟', '长上下文', '待评估', '备用容灾', '高性价比']

watch(
  () => store.editingNoteItem,
  (item) => {
    if (item) {
      editNotes.value = item.custom_notes || ''
      editTags.value = item.user_tags || ''
    }
  },
  { immediate: true }
)

function addTag(tag: string) {
  const current = editTags.value
    .split(/[,，]/)
    .map((t) => t.trim())
    .filter(Boolean)
  if (!current.includes(tag)) {
    current.push(tag)
    editTags.value = current.join(', ')
  }
}

async function handleSave() {
  if (!store.editingNoteItem) return
  isSaving.value = true
  try {
    const success = await store.saveModelNotes(
      store.editingNoteItem.id,
      editNotes.value,
      editTags.value
    )
    if (success) {
      store.editingNoteItem = null
    }
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
@keyframes scaleUp {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
.animate-scale-up {
  animation: scaleUp 0.15s ease-out forwards;
}
</style>
