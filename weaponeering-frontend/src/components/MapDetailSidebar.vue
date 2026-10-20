<template>
  <aside class="map-detail-sidebar" :class="{ collapsed }">
    <header>
      <div v-if="!collapsed">
        <span class="kicker">MAP DETAIL</span>
        <h3><i class="bi bi-list-ul"></i> รายการบนแผนที่</h3>
      </div>
      <button type="button" class="icon-btn" @click="$emit('toggle')" :title="collapsed ? 'ขยายรายการบนแผนที่' : 'ย่อรายการบนแผนที่'">
        <i class="bi" :class="collapsed ? 'bi-chevron-right' : 'bi-chevron-left'"></i>
      </button>
    </header>

    <div v-if="!collapsed" class="sidebar-body">
      <div class="tabs">
        <button type="button" :class="{ active: tab === 'targets' }" @click="tab = 'targets'">
          เป้าหมาย <em>{{ uniqueTargetCount }}</em>
        </button>
        <button type="button" :class="{ active: tab === 'transport' }" @click="tab = 'transport'">
          ขนส่ง <em>{{ transports.length }}</em>
        </button>
        <button type="button" :class="{ active: tab === 'wings' }" @click="tab = 'wings'">
          กองบิน <em>{{ wings.length }}</em>
        </button>
      </div>

      <div v-if="tab === 'targets'" class="targets-panel">
        <button type="button" class="list-open-btn" @click="targetDialogOpen = true">
          <i class="bi bi-list-ul"></i>
          <span>
            <strong>List เป้าหมาย</strong>
            <small>ค้นหาและเลือกเป้าหมาย</small>
          </span>
          <em>{{ uniqueTargetCount }}</em>
        </button>
        <p v-if="!uniqueTargetCount" class="empty">ยังไม่มีเป้าหมายใน scenario นี้</p>
      </div>

      <div v-else-if="tab === 'transport'" class="list">
        <button
          v-for="r in transports"
          :key="r.id"
          type="button"
          class="list-item"
          :class="{ active: selectedTransportId === r.id }"
          @click="$emit('select-transport', r)"
        >
          <strong>{{ r.label }}</strong>
          <small>{{ Math.round(r.distanceM / 1000) }} km · {{ Math.round(r.durationMin) }} นาที</small>
        </button>
        <p v-if="!transports.length" class="empty">ยังไม่มีเส้นทางขนส่ง</p>
      </div>

      <div v-else class="list">
        <button
          v-for="w in wings"
          :key="w.entityId"
          type="button"
          class="list-item"
          :class="{ active: selectedWingId === w.entityId }"
          @click="$emit('select-wing', w)"
        >
          <strong>{{ w.label }}</strong>
          <small>{{ w.lat.toFixed(4) }}, {{ w.lng.toFixed(4) }}</small>
        </button>
        <p v-if="!wings.length" class="empty">ยังไม่มีกองบินที่มีพิกัด</p>
      </div>

      <div v-if="selectedSummary" class="selection-card">
        <span class="kicker">SELECTED</span>
        <strong>{{ selectedSummary.title }}</strong>
        <small>{{ selectedSummary.subtitle }}</small>
      </div>

      <TargetJmemPanel
        v-if="selectedTargetId"
        :target-id="selectedTargetId"
        :coordinate-id="selectedCoordinateId"
        @updated="$emit('jmem-updated', $event)"
        @error="$emit('jmem-error', $event)"
      />

      <TargetDetectionListPanel
        :detections="detections"
        :selected-target-id="selectedTargetId"
        :selected-coordinate-id="selectedCoordinateId"
        :detecting="detecting"
        @deleted="$emit('detection-deleted', $event)"
        @select-object="$emit('select-detection', $event)"
        @error="$emit('detection-error', $event)"
        @run-detection="$emit('run-detection', $event)"
      />

      <TargetRiskDirectionPanel
        :targets="targets"
        :selected-target-id="selectedTargetId"
        :selected-coordinate-id="selectedCoordinateId"
        @view-ingress="$emit('view-ingress', $event)"
      />
    </div>

    <TargetListDialog
      :open="targetDialogOpen"
      :targets="targets"
      :selected-target-id="selectedTargetId"
      @close="targetDialogOpen = false"
      @select="$emit('select-target', $event)"
    />
  </aside>
</template>

<script>
import { computed, ref } from 'vue'
import TargetJmemPanel from './TargetJmemPanel.vue'
import TargetListDialog from './TargetListDialog.vue'
import TargetRiskDirectionPanel from './TargetRiskDirectionPanel.vue'
import TargetDetectionListPanel from './TargetDetectionListPanel.vue'

export default {
  name: 'MapDetailSidebar',
  components: {
    TargetJmemPanel,
    TargetListDialog,
    TargetRiskDirectionPanel,
    TargetDetectionListPanel,
  },
  props: {
    collapsed: { type: Boolean, default: false },
    targets: { type: Array, default: () => [] },
    wings: { type: Array, default: () => [] },
    transports: { type: Array, default: () => [] },
    detections: { type: Array, default: () => [] },
    selectedTargetId: { type: String, default: '' },
    selectedCoordinateId: { type: String, default: '' },
    selectedWingId: { type: String, default: '' },
    selectedTransportId: { type: String, default: '' },
    detecting: { type: Boolean, default: false },
  },
  emits: [
    'toggle',
    'select-target',
    'select-wing',
    'select-transport',
    'jmem-updated',
    'jmem-error',
    'view-ingress',
    'detection-deleted',
    'select-detection',
    'detection-error',
    'run-detection',
  ],
  setup(props) {
    const tab = ref('targets')
    const targetDialogOpen = ref(false)

    const uniqueTargetCount = computed(() => {
      const ids = new Set()
      for (const item of props.targets || []) {
        if (item?.targetCardId) ids.add(item.targetCardId)
      }
      return ids.size
    })

    const selectedSummary = computed(() => {
      if (props.selectedTargetId) {
        const t = props.targets.find((x) => x.targetCardId === props.selectedTargetId)
        if (t) return { title: t.label, subtitle: 'เป้าหมาย' }
      }
      if (props.selectedTransportId) {
        const r = props.transports.find((x) => x.id === props.selectedTransportId)
        if (r) return { title: r.label, subtitle: 'ขนส่งภาคพื้น' }
      }
      if (props.selectedWingId) {
        const w = props.wings.find((x) => x.entityId === props.selectedWingId)
        if (w) return { title: w.label, subtitle: 'กองบิน' }
      }
      return null
    })

    return { tab, targetDialogOpen, uniqueTargetCount, selectedSummary }
  },
}
</script>

<style scoped>
.map-detail-sidebar {
  display: flex;
  flex-direction: column;
  flex: 0 0 280px;
  width: 280px;
  height: 100%;
  min-height: 0;
  border-right: 1px solid var(--border);
  background: var(--panel-bg);
  color: var(--text);
}

.map-detail-sidebar.collapsed {
  flex-basis: 52px;
  width: 52px;
}

.map-detail-sidebar.collapsed header {
  justify-content: center;
  padding: 12px 6px;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid var(--border);
}

.kicker {
  display: block;
  color: #6ea8fe;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

h3 {
  margin: 2px 0 0;
  font-size: 0.92rem;
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--control-bg);
  color: var(--text);
}

.sidebar-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  padding: 10px;
  overflow: auto;
}

.tabs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  margin-bottom: 10px;
}

.tabs button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 7px 4px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
  font-size: 0.68rem;
}

.tabs button.active {
  background: #0d6efd;
  border-color: #0d6efd;
  color: #fff;
}

.tabs em {
  font-style: normal;
  opacity: 0.85;
}

.targets-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.list-open-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 12px;
  border: 1px solid #355574;
  border-radius: 10px;
  background: rgba(13, 110, 253, 0.12);
  color: var(--text);
  text-align: left;
  font-family: inherit;
}

.list-open-btn > .bi {
  color: #6ea8fe;
  font-size: 1.05rem;
}

.list-open-btn span {
  display: flex;
  min-width: 0;
  flex: 1 1 auto;
  flex-direction: column;
  gap: 1px;
}

.list-open-btn strong {
  font-size: 0.82rem;
}

.list-open-btn small {
  color: var(--muted);
  font-size: 0.68rem;
}

.list-open-btn em {
  display: grid;
  place-items: center;
  min-width: 28px;
  height: 28px;
  padding: 0 7px;
  border-radius: 999px;
  background: rgba(13, 110, 253, 0.22);
  color: #9ec5fe;
  font-style: normal;
  font-size: 0.72rem;
  font-weight: 800;
}

.list {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 6px;
  overflow: auto;
}

.list-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 9px 10px;
  border: 1px solid var(--border);
  border-radius: 9px;
  background: rgba(13, 110, 253, 0.04);
  color: var(--text);
  text-align: left;
}

.list-item.active {
  border-color: #0d6efd;
  background: rgba(13, 110, 253, 0.18);
}

.list-item strong {
  font-size: 0.78rem;
}

.list-item small,
.empty {
  color: var(--muted);
  font-size: 0.68rem;
}

.selection-card {
  margin-top: 10px;
  padding: 10px;
  border: 1px solid rgba(255, 216, 77, 0.35);
  border-radius: 10px;
  background: rgba(255, 216, 77, 0.08);
}

.selection-card strong {
  display: block;
  margin-top: 2px;
  font-size: 0.82rem;
}

.selection-card small {
  color: var(--muted);
}
</style>
