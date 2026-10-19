<template>
  <Teleport to="body">
    <div v-if="open" class="target-list-backdrop" @click.self="$emit('close')">
      <div class="target-list-dialog" role="dialog" aria-modal="true" aria-label="รายการเป้าหมาย">
        <header class="dialog-head">
          <div>
            <span class="kicker">TARGETS</span>
            <h3><i class="bi bi-list-ul"></i> เลือกรายการเป้าหมาย</h3>
          </div>
          <button type="button" class="icon-btn" title="ปิด" @click="$emit('close')">
            <i class="bi bi-x-lg"></i>
          </button>
        </header>

        <label class="search-field">
          <i class="bi bi-search"></i>
          <input
            ref="searchInput"
            v-model="query"
            type="search"
            placeholder="ค้นหาชื่อเป้าหมาย หรือพิกัด…"
            autocomplete="off"
          />
        </label>

        <div class="dialog-list">
          <button
            v-for="(t, index) in filteredTargets"
            :key="`${t.targetCardId}-${t.coordinateId || index}`"
            type="button"
            class="dialog-item"
            :class="{ active: selectedTargetId === t.targetCardId }"
            @click="pickTarget(t)"
          >
            <span class="item-index">{{ index + 1 }}</span>
            <span class="item-copy">
              <strong>{{ t.label || 'เป้าหมาย' }}</strong>
              <small>
                {{ Number(t.lat).toFixed(4) }}, {{ Number(t.lng).toFixed(4) }}
                <em v-if="selectedTargetId === t.targetCardId"> · กำลังเลือก</em>
              </small>
            </span>
            <i class="bi bi-geo-alt-fill"></i>
          </button>
          <p v-if="!uniqueTargets.length" class="empty">ยังไม่มีเป้าหมายใน scenario นี้</p>
          <p v-else-if="!filteredTargets.length" class="empty">ไม่พบเป้าหมายที่ตรงกับคำค้นหา</p>
        </div>

        <footer class="dialog-foot">
          <small>{{ filteredTargets.length }} / {{ uniqueTargets.length }} รายการ</small>
          <button type="button" class="ghost-btn" @click="$emit('close')">ปิด</button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script>
import { computed, nextTick, ref, watch } from 'vue'

function uniqueTargetMarkers(targets = []) {
  const byId = new Map()
  for (const item of targets) {
    const id = item?.targetCardId
    if (!id) continue
    const existing = byId.get(id)
    if (!existing || (item.isPrimary && !existing.isPrimary)) {
      byId.set(id, item)
    }
  }
  return Array.from(byId.values())
}

export default {
  name: 'TargetListDialog',
  props: {
    open: { type: Boolean, default: false },
    targets: { type: Array, default: () => [] },
    selectedTargetId: { type: String, default: '' },
  },
  emits: ['close', 'select'],
  setup(props, { emit }) {
    const query = ref('')
    const searchInput = ref(null)

    const uniqueTargets = computed(() => uniqueTargetMarkers(props.targets))

    const filteredTargets = computed(() => {
      const q = query.value.trim().toLowerCase()
      if (!q) return uniqueTargets.value
      return uniqueTargets.value.filter((t) => {
        const label = String(t.label || '').toLowerCase()
        const coords = `${t.lat},${t.lng}`
        return label.includes(q) || coords.includes(q)
      })
    })

    function pickTarget(target) {
      emit('select', target)
      emit('close')
    }

    watch(
      () => props.open,
      async (isOpen) => {
        if (!isOpen) return
        query.value = ''
        await nextTick()
        searchInput.value?.focus?.()
      },
    )

    return {
      query,
      searchInput,
      uniqueTargets,
      filteredTargets,
      pickTarget,
    }
  },
}
</script>

<style scoped>
.target-list-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1600;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(2, 8, 16, 0.62);
}

.target-list-dialog {
  display: flex;
  flex-direction: column;
  width: min(520px, 100%);
  max-height: min(72vh, 640px);
  overflow: hidden;
  border: 1px solid #355574;
  border-radius: 14px;
  background: #0b1a2b;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.55);
  color: #e8f1fa;
}

.dialog-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 16px 10px;
  border-bottom: 1px solid #27405a;
}

.kicker {
  display: block;
  color: #6ea8fe;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.dialog-head h3 {
  margin: 2px 0 0;
  font-size: 0.98rem;
}

.icon-btn,
.ghost-btn {
  border: 1px solid #355574;
  border-radius: 8px;
  background: #102336;
  color: #c8ddf3;
}

.icon-btn {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
}

.ghost-btn {
  min-height: 32px;
  padding: 0 12px;
  font-family: inherit;
  font-size: 0.75rem;
  font-weight: 700;
}

.search-field {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 16px 0;
  padding: 0 12px;
  border: 1px solid #355574;
  border-radius: 10px;
  background: #0f2236;
  color: #8fb4d8;
}

.search-field input {
  width: 100%;
  min-height: 40px;
  border: 0;
  outline: 0;
  background: transparent;
  color: #e8f1fa;
  font-family: inherit;
  font-size: 0.86rem;
}

.dialog-list {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 6px;
  margin: 12px 0 0;
  padding: 0 12px;
  overflow: auto;
}

.dialog-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #2c445d;
  border-radius: 10px;
  background: rgba(13, 110, 253, 0.05);
  color: inherit;
  text-align: left;
  font-family: inherit;
}

.dialog-item:hover {
  border-color: #4f86bd;
  background: rgba(13, 110, 253, 0.12);
}

.dialog-item.active {
  border-color: #0d6efd;
  background: rgba(13, 110, 253, 0.2);
}

.item-index {
  display: grid;
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  place-items: center;
  border-radius: 8px;
  background: rgba(110, 168, 254, 0.16);
  color: #8fc0ff;
  font-size: 0.72rem;
  font-weight: 800;
}

.item-copy {
  min-width: 0;
  flex: 1 1 auto;
}

.item-copy strong {
  display: block;
  overflow: hidden;
  font-size: 0.86rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-copy small {
  color: #8fb4d8;
  font-size: 0.7rem;
}

.item-copy em {
  font-style: normal;
  color: #81d9aa;
}

.dialog-item > .bi {
  color: #6ea8fe;
}

.empty {
  margin: 18px 8px;
  color: #8fb4d8;
  font-size: 0.8rem;
  text-align: center;
}

.dialog-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid #27405a;
}

.dialog-foot small {
  color: #8fb4d8;
  font-size: 0.72rem;
}
</style>
