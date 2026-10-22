<template>
  <!-- Single root so Analysis layout can size the panel reliably -->
  <div class="map-panel-root" :class="{ expanded: isExpanded }">
    <div v-if="isExpanded" class="map-backdrop" @click="toggleExpanded"></div>

    <section ref="panelElement" class="map-panel" :class="{ expanded: isExpanded }">
      <header class="map-toolbar">
        <div class="map-title">
          <span class="map-title-icon"><i class="bi bi-globe-asia-australia"></i></span>
          <div class="map-title-text">
            <strong>แผนที่ปฏิบัติการ</strong>
            <small>{{ mapReady ? 'Desktop Cesium map' : 'กำลังโหลดแผนที่…' }}</small>
          </div>
        </div>

        <div class="map-target-nav" aria-label="เลื่อนเป้าหมาย">
          <button
            type="button"
            class="map-target-nav-btn nav-arrow"
            title="เป้าหมายก่อนหน้า"
            :disabled="!canNavigateTargets"
            @click="selectPrevTarget"
          >
            <i class="bi bi-chevron-left"></i>
          </button>
          <div class="map-target-current">
            <strong :title="currentTargetLabel">{{ currentTargetLabel }}</strong>
            <small v-if="uniqueTargets.length">{{ targetNavIndex + 1 }} / {{ uniqueTargets.length }}</small>
            <small v-else>ยังไม่มีเป้าหมาย</small>
          </div>
          <button
            type="button"
            class="map-target-nav-btn nav-arrow"
            title="เป้าหมายถัดไป"
            :disabled="!canNavigateTargets"
            @click="selectNextTarget"
          >
            <i class="bi bi-chevron-right"></i>
          </button>
          <button
            type="button"
            class="map-target-nav-btn list-btn import-btn"
            title="นำเข้าเป้าหมายหลายรายการ (Import Targets)"
            aria-label="นำเข้าเป้าหมาย (Import Targets)"
            :disabled="!scenarioId"
            @click="openImportDialog"
          >
            <i class="bi bi-file-earmark-arrow-up"></i>
            <span class="btn-text-full">นำเข้า (Import)</span>
            <span class="btn-text-short">นำเข้า</span>
          </button>
          <button
            type="button"
            class="map-target-nav-btn list-btn"
            title="รายการเป้าหมายทั้งหมด"
            aria-label="รายการเป้าหมายทั้งหมด"
            :disabled="!uniqueTargets.length"
            @click="openTargetDialog"
          >
            <i class="bi bi-list-ul"></i>
            <span class="btn-text-full">รายการเป้าหมาย</span>
            <span class="btn-text-short">รายการ</span>
          </button>
        </div>

        <div class="map-toolbar-actions">
          <span class="map-live" :class="{ online: !!scenarioId && mapReady }">
            <i></i> {{ scenarioId ? (mapReady ? 'LIVE' : 'LOADING') : 'NO SCENARIO' }}
          </span>
          <button type="button" class="map-expand-button" :title="isExpanded ? 'ย่อหน้าต่างแผนที่' : 'ขยายเต็มหน้าจอ'" @click="toggleExpanded">
            <i class="bi" :class="isExpanded ? 'bi-fullscreen-exit' : 'bi-arrows-fullscreen'"></i>
          </button>
        </div>
      </header>

      <div v-if="jmemBannerText" class="map-jmem-banner" title="สรุปสินค้าจาก JMEM ของเป้าหมายที่เลือก">
        <i class="bi bi-lightning-charge-fill"></i>
        <div class="map-jmem-copy">
          <strong>{{ jmemBannerText.title }}</strong>
          <small>{{ jmemBannerText.subtitle }}</small>
        </div>
        <em>{{ jmemBannerText.hint }}</em>
      </div>

      <div class="map-workspace">
        <div class="map-container">
          <div class="floating-toolbar" @click.stop>
            <button type="button" :class="{ active: interactionMode === 'select' }" @click="setMode('select')">
              <i class="bi bi-cursor"></i><span>เลือก</span>
            </button>
            <button type="button" :class="{ active: interactionMode === 'place-target' }" @click="setMode('place-target')">
              <i class="bi bi-geo-alt"></i><span>เป้า</span>
            </button>
            <button type="button" :class="{ active: interactionMode === 'place-blue' }" @click="setMode('place-blue')">
              <i class="bi bi-circle-fill blue"></i><span>Blue</span>
            </button>
            <button type="button" :class="{ active: interactionMode === 'place-red' }" @click="setMode('place-red')">
              <i class="bi bi-circle-fill red"></i><span>Red</span>
            </button>
            <button type="button" :class="{ active: interactionMode === 'measure' }" @click="setMode('measure')">
              <i class="bi bi-rulers"></i><span>วัด</span>
            </button>
            <button type="button" :class="{ active: interactionMode === 'pick' }" @click="setMode('pick')">
              <i class="bi bi-crosshair"></i><span>พิกัด</span>
            </button>
            <button type="button" :class="{ active: detectionPanelOpen }" @click="toggleDetectionPanel">
              <i class="bi bi-radar"></i><span>Detect</span>
            </button>
            <button type="button" @click="clearMeasure"><i class="bi bi-eraser"></i><span>ล้าง</span></button>
            <button type="button" @click="reloadLayers"><i class="bi bi-arrow-clockwise"></i><span>รีเฟรช</span></button>
            <button type="button" :class="{ active: layerMenuOpen }" @click.stop="toggleLayerMenu">
              <i class="bi bi-layers"></i><span>ชั้น</span>
            </button>
          </div>

          <div v-if="detectionPanelOpen" class="detection-panel" @click.stop>
            <div class="panel-head">
              <strong>Building / Object Detection</strong>
              <small>แผนที่เดียวกับโปรแกรมเดิม · YOLO building-seg.pt</small>
            </div>
            <label>
              โมเดล
              <select v-model="detectionModel">
                <option v-for="m in detectionModels" :key="m" :value="m">{{ m }}</option>
              </select>
            </label>
            <label>
              รัศมี (ม.)
              <input v-model.number="detectionRadiusM" type="range" min="20" max="300" step="10" />
              <em>{{ detectionRadiusM }} ม.</em>
            </label>
            <label>
              Zoom capture
              <input v-model.number="detectionZoom" type="range" min="1" max="4" step="1" />
              <em>{{ detectionZoom }}</em>
            </label>
            <p v-if="!selectedTargetId" class="hint">เลือกเป้าหมายบนแผนที่ก่อนรัน detection</p>
            <p v-else-if="detectionMessage" class="hint">{{ detectionMessage }}</p>
            <button
              type="button"
              class="run-btn"
              :disabled="detecting || !selectedTargetId || !scenarioId || !mapReady"
              @click="runDetection"
            >
              <i class="bi" :class="detecting ? 'bi-hourglass-split' : 'bi-play-fill'"></i>
              {{ detecting ? 'กำลังตรวจจับ…' : 'Run Detection' }}
            </button>
          </div>

          <div v-if="layerMenuOpen" class="layer-menu-panel" @click.stop>
            <div class="panel-head">
              <strong>Layer Control</strong>
              <small>เปิด/ปิดชั้นข้อมูลแบบ desktop</small>
            </div>
            <button
              v-for="layer in layers"
              :key="layer.key"
              type="button"
              class="layer-row"
              @click="toggleLayer(layer.key)"
            >
              <span class="layer-indicator" :class="{ active: layer.enabled }"></span>
              <span>{{ layer.label }}</span>
              <i class="bi" :class="layer.enabled ? 'bi-check2-square' : 'bi-square'"></i>
            </button>
            <div class="panel-head basemap-head">
              <strong>แผนที่ฐาน</strong>
            </div>
            <button
              v-for="basemap in basemapOptions"
              :key="basemap.id"
              type="button"
              class="layer-row"
              @click="selectBasemap(basemap.id)"
            >
              <span class="layer-indicator" :class="{ active: basemapId === basemap.id }"></span>
              <span>{{ basemap.label }}</span>
              <i class="bi" :class="basemapId === basemap.id ? 'bi-record-circle' : 'bi-circle'"></i>
            </button>
          </div>

          <iframe
            ref="mapFrame"
            class="map-frame"
            title="MAAP Cesium Map"
            :src="mapSrc"
            @load="onFrameLoad"
          ></iframe>

          <div v-if="!mapReady && !loadError" class="map-state">
            <span class="map-loader"></span>
            <strong>กำลังเปิดแผนที่ Cesium (ตัวเดียวกับโปรแกรมเดิม)</strong>
          </div>
          <div v-else-if="loadError" class="map-state error">
            <strong>{{ loadError }}</strong>
          </div>

          <div class="mode-chip">
            <i class="bi bi-info-circle"></i>
            <span>{{ modeHint }}</span>
            <em v-if="measureDistanceM != null">{{ formatDistanceMeters(measureDistanceM) }}</em>
          </div>
        </div>
      </div>

      <footer class="map-info">
        <span>ใช้ cesium_map.html ชุดเดียวกับ desktop</span>
        <small>{{ statusText }}</small>
      </footer>
    </section>

    <TargetListDialog
      :open="targetDialogOpen"
      :targets="layerData.targets"
      :selected-target-id="selectedTargetId"
      @close="closeTargetDialog"
      @select="onPickTargetFromList"
    />

    <TargetBulkImportDialog
      :open="importDialogOpen"
      :scenario-id="scenarioId"
      @close="closeImportDialog"
      @imported="onTargetsImported"
      @error="(msg) => emit('error', msg)"
    />
  </div>
</template>

<script>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { listResource, createResource, uploadForm } from '../services/api'
import TargetListDialog from './TargetListDialog.vue'
import TargetBulkImportDialog from './TargetBulkImportDialog.vue'

const EFFECT_DOMES_STORAGE_KEY = 'maap.map.effectDomes'
const BASEMAP_STORAGE_KEY = 'maap.map.basemap'
const CESIUM_ION_TOKEN = String(import.meta.env.VITE_CESIUM_ION_TOKEN || '').trim()
const BASEMAP_OPTIONS = [
  ...(CESIUM_ION_TOKEN ? [{ id: 'bing_aerial', label: 'ดาวเทียม Bing (ละเอียดสูง)' }] : []),
  { id: 'esri_world_imagery', label: 'ดาวเทียม Esri' },
  { id: 'open_topo_map', label: 'ภูมิประเทศ (OpenTopoMap)' },
  { id: 'rtaf_50k', label: 'RTAF 1:50K' },
  { id: 'rtaf_250k', label: 'RTAF 1:250K' },
]
const DEFAULT_BASEMAP = BASEMAP_OPTIONS[0].id
const MAP_SRC = `${(import.meta.env.BASE_URL || '/').replace(/\/?$/, '/') }map/cesium_map.html`

function detectionCaptureRadiusM(radiusM, zoomLevel = 4) {
  const zoom = Math.max(1, Math.min(4, zoomLevel))
  const marginFactor = 1.0 + (4 + 1 - zoom) * 0.25
  return Math.max(Math.round(radiusM * marginFactor), radiusM + 20)
}

export default {
  name: 'MapPanel',
  components: { TargetListDialog, TargetBulkImportDialog },
  props: {
    scenarioId: { type: String, default: '' },
    selectedTargetId: { type: String, default: '' },
    selectedWingId: { type: String, default: '' },
    selectedTransportId: { type: String, default: '' },
    latitude: { type: Number, default: 15.0 },
    longitude: { type: Number, default: 100.0 },
    jmemSummary: { type: Object, default: null },
  },
  emits: [
    'select-target',
    'select-wing',
    'select-depot',
    'select-transport',
    'select-team',
    'coords-picked',
    'layers-loaded',
    'target-created',
    'targets-imported',
    'team-created',
    'detection-complete',
    'error',
  ],
  setup(props, { emit }) {
    const panelElement = ref(null)
    const mapFrame = ref(null)
    const mapSrc = MAP_SRC
    const isExpanded = ref(false)
    const mapReady = ref(false)
    const frameLoaded = ref(false)
    const loadError = ref('')
    const layerMenuOpen = ref(false)
    const detectionPanelOpen = ref(false)
    const detecting = ref(false)
    const detectionRadiusM = ref(120)
    const detectionZoom = ref(4)
    const detectionModel = ref('Building Detector')
    const detectionModels = ref(['Building Detector', 'Vehicle Detector', 'Structure Segmentation'])
    const detectionMessage = ref('')
    const interactionMode = ref('select')
    const measureDistanceM = ref(null)
    const targetDialogOpen = ref(false)
    const importDialogOpen = ref(false)
    const layerData = ref({
      targets: [],
      wings: [],
      depots: [],
      detections: [],
      teamMarkers: [],
      groundTransports: [],
    })
    const layers = ref([
      { key: 'borders', label: 'ขอบเขต ปท.', enabled: true },
      { key: 'targets', label: 'เป้าหมาย', enabled: true },
      { key: 'organizations', label: 'กองบิน', enabled: true },
      { key: 'depots', label: 'คลัง', enabled: true },
      { key: 'detections', label: 'Detection', enabled: true },
      { key: 'teams', label: 'Blue / Red', enabled: true },
      { key: 'ground_transport', label: 'ขนส่ง', enabled: true },
      {
        key: 'effect_domes',
        label: 'โดมรัศมี (ฝาชี)',
        enabled: localStorage.getItem(EFFECT_DOMES_STORAGE_KEY) !== '0',
      },
    ])

    const modeHint = computed(() => {
      switch (interactionMode.value) {
        case 'place-target':
          return 'คลิกแผนที่เพื่อสร้างเป้าหมาย'
        case 'place-blue':
          return 'คลิกเพื่อวางหน่วย Blue'
        case 'place-red':
          return 'คลิกเพื่อวางหน่วย Red'
        case 'measure':
          return 'โหมดวัดระยะ (แผนที่ desktop)'
        case 'pick':
          return 'โหมดหยิบพิกัด'
        case 'detect':
          return 'เลือกเป้าหมาย แล้วกด Run Detection'
        default:
          return 'โหมดเลือก'
      }
    })

    const uniqueTargets = computed(() => {
      const byId = new Map()
      for (const item of layerData.value.targets || []) {
        const id = item?.targetCardId
        if (!id) continue
        const existing = byId.get(id)
        if (!existing || (item.isPrimary && !existing.isPrimary)) {
          byId.set(id, item)
        }
      }
      return Array.from(byId.values())
    })

    const targetNavIndex = computed(() => {
      if (!props.selectedTargetId) return -1
      return uniqueTargets.value.findIndex((t) => t.targetCardId === props.selectedTargetId)
    })

    const currentTargetLabel = computed(() => {
      if (!uniqueTargets.value.length) return 'ยังไม่มีเป้าหมาย'
      const idx = targetNavIndex.value
      if (idx >= 0) return uniqueTargets.value[idx].label || `เป้าหมาย ${idx + 1}`
      return 'ยังไม่ได้เลือกเป้าหมาย'
    })

    const canNavigateTargets = computed(() => uniqueTargets.value.length > 1)

    const jmemBannerText = computed(() => {
      const summary = props.jmemSummary
      if (summary?.productName) {
        const parts = [
          summary.weightText,
          summary.nRequired != null ? `N=${summary.nRequired}` : '',
          summary.pdText ? `Pd ${summary.pdText}` : '',
        ].filter(Boolean)
        return {
          title: `JMEM / สินค้า: ${summary.productName}`,
          subtitle: parts.join(' · '),
          hint: summary.hint || 'วงสีบนแผนที่คือรัศมีผลกระทบของสินค้านี้จาก JMEM',
        }
      }
      // Fallback จากชั้นแผนที่ (effect radii) เมื่อยังไม่มี summary จากแผง JMEM
      if (!props.selectedTargetId) return null
      const marker = uniqueTargets.value.find((t) => t.targetCardId === props.selectedTargetId)
      if (!marker?.effectProduct) return null
      return {
        title: `JMEM / สินค้า: ${marker.effectProduct}`,
        subtitle: [
          marker.effectWeightLb != null ? `${Math.round(marker.effectWeightLb)} lb` : '',
          marker.effectN != null ? `N=${marker.effectN}` : '',
        ]
          .filter(Boolean)
          .join(' · '),
        hint: 'วงสีบนแผนที่คือรัศมีผลกระทบของสินค้านี้จาก JMEM',
      }
    })

    const statusText = computed(() => {
      const d = layerData.value
      return `${d.targets.length} เป้า · ${d.detections.length} detection · ${d.teamMarkers.length} หน่วย`
    })

    function selectTargetByOffset(offset) {
      const list = uniqueTargets.value
      if (!list.length) return
      const current = targetNavIndex.value
      const base = current >= 0 ? current : 0
      const next = (base + offset + list.length) % list.length
      emit('select-target', list[next])
    }

    function selectPrevTarget() {
      selectTargetByOffset(-1)
    }

    function selectNextTarget() {
      selectTargetByOffset(1)
    }

    function onPickTargetFromList(target) {
      if (!target) return
      emit('select-target', target)
    }

    function openTargetDialog() {
      targetDialogOpen.value = true
    }

    function closeTargetDialog() {
      targetDialogOpen.value = false
    }

    function openImportDialog() {
      importDialogOpen.value = true
    }

    function closeImportDialog() {
      importDialogOpen.value = false
    }

    async function onTargetsImported({ successCount }) {
      await reloadLayers()
      emit('targets-imported', { successCount })
    }

    function highlightIngress(payload) {
      const api = getMapApi()
      if (!api?.highlightIngressCorridor) return
      const targetId = payload?.targetCardId || props.selectedTargetId
      if (!targetId) return
      api.highlightIngressCorridor(
        targetId,
        payload?.coordinateId || null,
        payload?.rank || null,
      )
    }

    function highlightDetection(objectId) {
      const api = getMapApi()
      if (!api?.highlightDetectionObject || !objectId) return
      api.highlightDetectionObject(objectId)
    }

    function formatDistanceMeters(meters) {
      return `${Math.round(meters).toLocaleString('th-TH')} ม.`
    }

    function getMapApi() {
      return mapFrame.value?.contentWindow?.maapMap || null
    }

    function applyLayerVisibility() {
      const api = getMapApi()
      if (!api?.setLayerVisibility) return
      const visibility = {
        routes: true,
        readiness: true,
      }
      layers.value.forEach((layer) => {
        visibility[layer.key] = layer.enabled
      })
      api.setLayerVisibility(visibility)
    }

    function pushLayersToMap() {
      const api = getMapApi()
      if (!api || !mapReady.value) return
      const data = layerData.value
      api.setTargetMarkers?.(data.targets || [])
      api.setAssetLayers?.({
        organizations: (data.wings || []).map((w) => ({
          ...w,
          entityType: w.entityType || 'air_wing',
          readiness: 'wing',
        })),
        depots: data.depots || [],
        routes: [],
        deploymentLinks: [],
      })
      api.setDetectedObjects?.(data.detections || [])
      api.setTeamMarkers?.(data.teamMarkers || [])
      api.setGroundTransportRoutes?.(data.groundTransports || [])
      applyLayerVisibility()
      if (props.selectedTargetId) {
        api.highlightTarget?.(props.selectedTargetId)
      }
    }

    async function reloadLayers() {
      if (!props.scenarioId) {
        layerData.value = {
          targets: [],
          wings: [],
          depots: [],
          detections: [],
          teamMarkers: [],
          groundTransports: [],
        }
        pushLayersToMap()
        emit('layers-loaded', layerData.value)
        return
      }
      try {
        const query = {}
        if (props.selectedTransportId) query.transport_id = props.selectedTransportId
        const data = await listResource('/map/layers', {
          scenario_id: props.scenarioId,
          ...query,
        })
        layerData.value = {
          targets: data.targets || [],
          wings: data.wings || [],
          depots: data.depots || [],
          detections: data.detections || [],
          teamMarkers: data.teamMarkers || [],
          groundTransports: data.groundTransports || [],
        }
        pushLayersToMap()
        emit('layers-loaded', layerData.value)
      } catch (err) {
        loadError.value = err.message || 'โหลดชั้นแผนที่ไม่สำเร็จ'
        emit('error', loadError.value)
      }
    }

    function setMode(mode) {
      interactionMode.value = mode
      detectionPanelOpen.value = mode === 'detect'
      layerMenuOpen.value = false
      const api = getMapApi()
      if (!api) return
      api.setMeasureMode?.(mode === 'measure')
      api.setPickCoordMode?.(
        mode === 'pick' ||
          mode === 'place-target' ||
          mode === 'place-blue' ||
          mode === 'place-red',
      )
      api.setDetectionAddMode?.(false)
    }

    function toggleDetectionPanel() {
      detectionPanelOpen.value = !detectionPanelOpen.value
      interactionMode.value = detectionPanelOpen.value ? 'detect' : 'select'
      layerMenuOpen.value = false
      setMode(interactionMode.value)
    }

    function toggleLayerMenu() {
      layerMenuOpen.value = !layerMenuOpen.value
      if (layerMenuOpen.value) detectionPanelOpen.value = false
    }

    const storedBasemap = localStorage.getItem(BASEMAP_STORAGE_KEY)
    const basemapId = ref(
      BASEMAP_OPTIONS.some((b) => b.id === storedBasemap) ? storedBasemap : DEFAULT_BASEMAP,
    )

    async function selectBasemap(id) {
      const api = getMapApi()
      basemapId.value = id
      localStorage.setItem(BASEMAP_STORAGE_KEY, id)
      if (!api?.setBasemap) return
      const applied = await api.setBasemap(id)
      if (applied && applied !== id) {
        const fallback = BASEMAP_OPTIONS.some((b) => b.id === applied) ? applied : 'esri_world_imagery'
        basemapId.value = fallback
        const label = BASEMAP_OPTIONS.find((b) => b.id === id)?.label || id
        emit('error', `เปิดแผนที่ฐาน ${label} ไม่สำเร็จ จึงใช้ภาพดาวเทียม Esri แทน`)
      }
    }

    function toggleLayer(key) {
      const layer = layers.value.find((l) => l.key === key)
      if (!layer) return
      layer.enabled = !layer.enabled
      if (key === 'effect_domes') {
        localStorage.setItem(EFFECT_DOMES_STORAGE_KEY, layer.enabled ? '1' : '0')
      }
      applyLayerVisibility()
    }

    function clearMeasure() {
      getMapApi()?.clearMeasure?.()
      measureDistanceM.value = null
    }

    let resizeObserver = null

    function resizeMapViewer() {
      try {
        const win = mapFrame.value?.contentWindow
        const frame = mapFrame.value
        if (frame) {
          // Force iframe layout to match container before Cesium measures it.
          frame.style.height = '100%'
          frame.style.width = '100%'
        }
        win?.viewer?.resize?.()
        win?.viewer?.scene?.requestRender?.()
      } catch {
        /* ignore cross-frame timing */
      }
    }

    function toggleExpanded() {
      isExpanded.value = !isExpanded.value
      nextTick(() => {
        resizeMapViewer()
        const api = getMapApi()
        if (api && props.selectedTargetId) api.highlightTarget?.(props.selectedTargetId)
      })
    }

    async function captureIframeSquareBlob() {
      const win = mapFrame.value?.contentWindow
      const doc = mapFrame.value?.contentDocument
      if (!win?.Cesium || !doc) throw new Error('แผนทยังไม่พร้อม')
      const canvas = doc.querySelector('canvas')
      if (!canvas) throw new Error('ไม่พบ canvas แผนที่')
      const viewer = win.viewer || win.maapViewer
      // Prefer scene from global if exposed; otherwise render via requestAnimationFrame
      if (win.viewer?.scene) {
        win.viewer.scene.requestRenderMode = false
        win.viewer.resize()
        win.viewer.render()
      }
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))
      const size = Math.min(canvas.width, canvas.height)
      const sx = Math.floor((canvas.width - size) / 2)
      const sy = Math.floor((canvas.height - size) / 2)
      const offscreen = document.createElement('canvas')
      offscreen.width = size
      offscreen.height = size
      const ctx = offscreen.getContext('2d', { willReadFrequently: true })
      ctx.drawImage(canvas, sx, sy, size, size, 0, 0, size, size)
      const sample = ctx.getImageData(Math.floor(size / 2), Math.floor(size / 2), 1, 1).data
      if (sample[0] + sample[1] + sample[2] < 8) {
        throw new Error('จับภาพแผนที่ได้เป็นสีดำ — รอภาพโหลดแล้วลองใหม่')
      }
      return new Promise((resolve, reject) => {
        offscreen.toBlob(
          (b) => (b ? resolve(b) : reject(new Error('จับภาพไม่สำเร็จ'))),
          'image/png',
        )
      })
    }

    async function runDetection(customOptions = {}) {
      if (!props.scenarioId || !props.selectedTargetId) {
        emit('error', 'เลือก scenario และเป้าหมายก่อนรัน detection')
        return
      }
      const radiusVal = customOptions?.radiusM || detectionRadiusM.value
      const zoomVal = customOptions?.zoom || detectionZoom.value
      const modelVal = customOptions?.model || detectionModel.value
      const targetCoordId = customOptions?.coordinateId || props.selectedCoordinateId

      let target = null
      if (targetCoordId) {
        target = layerData.value.targets.find(
          (t) => t.targetCardId === props.selectedTargetId && t.coordinateId === targetCoordId,
        )
      }
      if (!target) {
        target =
          layerData.value.targets.find(
            (t) => t.targetCardId === props.selectedTargetId && t.isPrimary,
          ) || layerData.value.targets.find((t) => t.targetCardId === props.selectedTargetId)
      }
      if (!target?.coordinateId) {
        emit('error', 'ไม่พบพิกัดของเป้าหมาย')
        return
      }
      const api = getMapApi()
      if (!api) {
        emit('error', 'แผนที่ยังไม่พร้อม')
        return
      }
      detecting.value = true
      detectionMessage.value = 'กำลังจัดมุมกล้องรอบเป้าหมาย…'
      try {
        const captureRadius = detectionCaptureRadiusM(
          radiusVal,
          zoomVal,
        )
        api.setDetectionCaptureMode?.(true)
        api.fitToDetectionArea?.(target.lat, target.lng, captureRadius)
        detectionMessage.value = `รอโหลดภาพ (view ${captureRadius} ม.)…`
        await new Promise((r) => setTimeout(r, 3200 + zoomVal * 350))
        detectionMessage.value = `กำลังจับภาพและประมวลผลด้วย ${modelVal}…`
        const blob = await captureIframeSquareBlob()
        const form = new FormData()
        form.append('scenario_id', props.scenarioId)
        form.append('target_card_id', target.targetCardId)
        form.append('target_coordinate_id', target.coordinateId)
        form.append('model_name', modelVal)
        form.append('radius_m', String(radiusVal))
        form.append('zoom_level', String(zoomVal))
        form.append('image', blob, `${target.targetCardId}.png`)
        const result = await uploadForm('/detection-runs/execute', form)
        detectionMessage.value =
          result.message || `พบ ${result.objectCount || 0} วัตถุ — ตีกรอบตามความเสี่ยงแล้ว`
        api.setDetectionCaptureMode?.(false)
        api.restoreMapLayersAfterDetection?.()
        await reloadLayers()
        api.highlightTarget?.(target.targetCardId)
        emit('detection-complete', result)
        return result
      } catch (err) {
        detectionMessage.value = err.message || 'Detection ล้มเหลว'
        emit('error', detectionMessage.value)
        getMapApi()?.setDetectionCaptureMode?.(false)
        getMapApi()?.restoreMapLayersAfterDetection?.()
        throw err
      } finally {
        detecting.value = false
      }
    }

    async function handleMapEvent(name, args) {
      if (name === 'select_target' && args[0]) {
        const t = layerData.value.targets.find((x) => x.targetCardId === args[0])
        emit('select-target', {
          targetCardId: args[0],
          coordinateId: t?.coordinateId || '',
          label: t?.label || '',
          lat: t?.lat,
          lng: t?.lng,
        })
        return
      }
      if (name === 'select_entity') {
        const entityType = args[0]
        const entityId = args[1]
        if (entityType === 'air_wing' || entityType === 'wing') {
          const w = layerData.value.wings.find((x) => x.entityId === entityId)
          emit('select-wing', {
            entityId,
            label: w?.label || '',
            lat: w?.lat,
            lng: w?.lng,
          })
        } else if (entityType === 'wing_depot' || entityType === 'depot') {
          const d = layerData.value.depots.find((x) => x.entityId === entityId)
          emit('select-depot', {
            entityId,
            label: d?.label || '',
            lat: d?.lat,
            lng: d?.lng,
            wingId: d?.wingId,
          })
        } else if (entityType === 'ground_transport' || entityType === 'transport') {
          emit('select-transport', { id: entityId })
        } else if (entityType === 'risk_object') {
          highlightDetection(entityId)
        }
        return
      }
      if (name === 'detection_select' && args[0]) {
        highlightDetection(args[0])
        return
      }
      if (name === 'pick_coord' && args.length >= 2) {
        const lat = Number(args[0])
        const lng = Number(args[1])
        emit('coords-picked', { lat, lng })
        if (interactionMode.value === 'place-target' && props.scenarioId) {
          try {
            const label = window.prompt(
              'ชื่อเป้าหมาย',
              `เป้าหมาย ${layerData.value.targets.length + 1}`,
            )
            if (!label) return
            const created = await createResource('/targets', {
              scenario_id: props.scenarioId,
              label,
              coordinates: [{ label: 'P1', map_lat: lat, map_lng: lng, is_primary: true }],
            })
            await reloadLayers()
            const coordId = created?.coordinates?.[0]?.id || ''
            const targetPayload = {
              targetCardId: created?.id || '',
              coordinateId: coordId,
              lat,
              lng,
              label: created?.label || label,
            }
            emit('target-created', targetPayload)
            emit('select-target', targetPayload)
            if (created?.id) {
              getMapApi()?.highlightTarget?.(created.id)
            }
            setMode('select')
          } catch (err) {
            emit('error', err.message || 'สร้างเป้าหมายไม่สำเร็จ')
          }
          return
        }
        if (
          (interactionMode.value === 'place-blue' || interactionMode.value === 'place-red') &&
          props.scenarioId
        ) {
          const side = interactionMode.value === 'place-blue' ? 'blue' : 'red'
          try {
            const label = window.prompt(
              `ชื่อหน่วย ${side.toUpperCase()}`,
              `${side.toUpperCase()}-1`,
            )
            if (!label) return
            await createResource('/team-markers', {
              scenario_id: props.scenarioId,
              side,
              unit_type: 'generic',
              label,
              map_lat: lat,
              map_lng: lng,
            })
            emit('team-created', { side, lat, lng })
            await reloadLayers()
            setMode('select')
          } catch (err) {
            emit('error', err.message || 'วางหน่วยไม่สำเร็จ')
          }
        }
        return
      }
      if (name === 'target_create_at' && args.length >= 2) {
        // same as pick for place-target if map emits this
        await handleMapEvent('pick_coord', args)
        return
      }
      if (name === 'team_marker_place' && props.scenarioId) {
        const side = args[0]
        const unitType = args.length >= 4 ? args[1] : 'generic'
        const lat = Number(args.length >= 4 ? args[2] : args[1])
        const lng = Number(args.length >= 4 ? args[3] : args[2])
        if (interactionMode.value === 'place-blue' || interactionMode.value === 'place-red' || side) {
          try {
            const finalSide =
              interactionMode.value === 'place-blue'
                ? 'blue'
                : interactionMode.value === 'place-red'
                  ? 'red'
                  : side
            const label = window.prompt(
              `ชื่อหน่วย ${String(finalSide).toUpperCase()}`,
              `${String(finalSide).toUpperCase()}-1`,
            )
            if (!label) return
            await createResource('/team-markers', {
              scenario_id: props.scenarioId,
              side: finalSide,
              unit_type: unitType || 'generic',
              label,
              map_lat: lat,
              map_lng: lng,
            })
            emit('team-created', { side: finalSide, lat, lng })
            await reloadLayers()
            setMode('select')
          } catch (err) {
            emit('error', err.message || 'วางหน่วยไม่สำเร็จ')
          }
        }
        return
      }
      if (name === 'measure_update') {
        measureDistanceM.value = Number(args[0] || 0)
      }
    }

    function activateMapApi(api) {
      if (!api || mapReady.value) {
        if (api) {
          nextTick(() => resizeMapViewer())
          setTimeout(resizeMapViewer, 200)
        }
        return
      }
      mapReady.value = true
      frameLoaded.value = true
      loadError.value = ''
      api.setCesiumIonToken?.(CESIUM_ION_TOKEN)
      selectBasemap(basemapId.value)
      api.setWingIconUrl?.(
        `${(import.meta.env.BASE_URL || '/').replace(/\/?$/, '/') }map/icons/airport.png`,
      )
      reloadLayers()
      const lat = Number(props.latitude) || 15
      const lng = Number(props.longitude) || 100
      api.fitToTarget?.(lat, lng, 2_500_000)
      nextTick(() => resizeMapViewer())
      setTimeout(resizeMapViewer, 200)
      setTimeout(resizeMapViewer, 800)
    }

    function onMessage(event) {
      const data = event.data
      if (!data || data.source !== 'maap-map') return
      if (data.type === 'map-ready') {
        activateMapApi(getMapApi())
        return
      }
      if (data.type === 'map-error') {
        loadError.value = data.message || 'เปิดแผนที่ Cesium ไม่สำเร็จ'
        emit('error', loadError.value)
        return
      }
      if (data.type === 'map-event') {
        handleMapEvent(data.name, data.args || [])
      }
    }

    function onFrameLoad() {
      frameLoaded.value = true
      // MAP_READY may already have fired; poll briefly for maapMap
      let tries = 0
      const timer = setInterval(() => {
        tries += 1
        const api = getMapApi()
        if (api) {
          clearInterval(timer)
          activateMapApi(api)
        } else if (tries > 50) {
          clearInterval(timer)
          if (!mapReady.value) {
            loadError.value =
              'โหลด Cesium map ไม่สำเร็จ — เปิด /map/cesium_map.html โดยตรงเพื่อดู error'
            emit('error', loadError.value)
          }
        }
      }, 200)
    }

    function onKeydown(e) {
      if (e.key === 'Escape' && isExpanded.value) toggleExpanded()
    }

    watch(() => props.scenarioId, () => reloadLayers())
    watch(
      () => props.selectedTargetId,
      (id) => {
        const api = getMapApi()
        if (!api || !id) return
        api.highlightTarget?.(id)
        const t = layerData.value.targets.find((x) => x.targetCardId === id)
        if (t) api.fitToTarget?.(t.lat, t.lng, t.detectionRadiusM || 800)
      },
    )

    onMounted(() => {
      window.addEventListener('message', onMessage)
      window.addEventListener('keydown', onKeydown)
      window.addEventListener('resize', resizeMapViewer)
      nextTick(() => {
        if (panelElement.value) {
          resizeObserver = new ResizeObserver(() => resizeMapViewer())
          resizeObserver.observe(panelElement.value)
        }
      })
    })
    onUnmounted(() => {
      window.removeEventListener('message', onMessage)
      window.removeEventListener('keydown', onKeydown)
      window.removeEventListener('resize', resizeMapViewer)
      resizeObserver?.disconnect()
    })

    return {
      panelElement,
      mapFrame,
      mapSrc,
      isExpanded,
      mapReady,
      frameLoaded,
      loadError,
      layerMenuOpen,
      detectionPanelOpen,
      detecting,
      detectionRadiusM,
      detectionZoom,
      detectionModel,
      detectionModels,
      detectionMessage,
      interactionMode,
      modeHint,
      uniqueTargets,
      targetNavIndex,
      currentTargetLabel,
      canNavigateTargets,
      jmemBannerText,
      selectPrevTarget,
      selectNextTarget,
      targetDialogOpen,
      openTargetDialog,
      closeTargetDialog,
      importDialogOpen,
      openImportDialog,
      closeImportDialog,
      onTargetsImported,
      onPickTargetFromList,
      layerData,
      statusText,
      measureDistanceM,
      layers,
      basemapOptions: BASEMAP_OPTIONS,
      basemapId,
      selectBasemap,
      setMode,
      toggleDetectionPanel,
      toggleLayerMenu,
      toggleLayer,
      clearMeasure,
      reloadLayers,
      highlightIngress,
      highlightDetection,
      runDetection,
      detecting,
      toggleExpanded,
      onFrameLoad,
      formatDistanceMeters,
    }
  },
}
</script>

<style scoped>
.map-panel-root {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}
.map-panel-root.expanded {
  position: fixed;
  inset: 12px;
  z-index: 1400;
  width: auto;
  height: auto;
  min-height: 0;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.55);
}
.map-panel {
  container-type: inline-size;
  container-name: mappanel;
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: #07111f;
  color: var(--text);
}
.map-panel.expanded {
  border-radius: 12px;
}
.map-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1350;
  background: rgba(0, 0, 0, 0.45);
}
.map-toolbar {
  position: relative;
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 12px;
  border-bottom: 1px solid var(--border);
  background: rgba(8, 20, 40, 0.95);
  min-width: 0;
  box-sizing: border-box;
}
.map-title {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 0 0 auto;
}
.map-title-icon {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  border-radius: 8px;
  background: rgba(13, 110, 253, 0.18);
  color: #6ea8fe;
}
.map-title-text {
  min-width: 0;
}
.map-title strong {
  display: block;
  font-size: 0.84rem;
  white-space: nowrap;
}
.map-title small {
  display: block;
  color: var(--muted);
  font-size: 0.68rem;
  white-space: nowrap;
}
.map-target-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex: 1 1 auto;
  min-width: 0;
  max-width: 580px;
  margin: 0 4px;
}
.map-target-nav-btn {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  border: 1px solid #355574;
  border-radius: 8px;
  background: #0f2236;
  color: #c8ddf3;
  cursor: pointer;
  transition: all 0.15s ease;
}
.map-target-nav-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.map-target-nav-btn:not(:disabled):hover {
  border-color: #4f86bd;
  background: #143049;
}
.map-target-nav-btn.list-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  width: auto;
  min-width: 30px;
  height: 30px;
  flex: 0 0 auto;
  padding: 0 9px;
  font-size: 0.74rem;
  font-weight: 700;
  white-space: nowrap;
}
.map-target-nav-btn.list-btn .btn-text-short {
  display: none;
}
.map-target-nav-btn.list-btn .btn-text-full {
  display: inline;
}
.map-target-nav-btn.list-btn i {
  font-size: 0.85rem;
  color: #6ea8fe;
}
.map-target-nav-btn.list-btn:hover:not(:disabled) i {
  color: #ffffff;
}
.map-target-nav-btn.import-btn {
  border-color: #2e6194;
  background: #112d4a;
  color: #d8e8f8;
}
.map-target-nav-btn.import-btn:hover:not(:disabled) {
  border-color: #4b91f7;
  background: #19436e;
  color: #ffffff;
}
.map-target-current {
  min-width: 48px;
  max-width: 160px;
  flex: 0 1 140px;
  padding: 3px 8px;
  border: 1px solid rgba(81, 140, 201, 0.35);
  border-radius: 9px;
  background: rgba(13, 40, 68, 0.88);
  text-align: center;
}
.map-target-current strong {
  display: block;
  overflow: hidden;
  color: #f3f8ff;
  font-size: 0.88rem;
  font-weight: 800;
  letter-spacing: 0.01em;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.map-target-current small {
  display: block;
  margin-top: 1px;
  color: #8fb4d8;
  font-size: 0.65rem;
  font-weight: 700;
  white-space: nowrap;
}
.map-toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  margin-left: auto;
}
.map-live {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #94a3b8;
  font-size: 0.68rem;
  font-weight: 700;
  white-space: nowrap;
}
.map-live.online {
  color: #81d9aa;
}
.map-live i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

/* Container Queries for responsive map toolbar inside flexible panels */
@container mappanel (max-width: 920px) {
  .map-title small {
    display: none;
  }
  .map-target-nav-btn.list-btn .btn-text-full {
    display: none;
  }
  .map-target-nav-btn.list-btn .btn-text-short {
    display: inline;
  }
  .map-target-nav-btn.list-btn {
    padding: 0 7px;
  }
}
@container mappanel (max-width: 740px) {
  .map-title-icon {
    display: none;
  }
  .map-toolbar {
    gap: 6px;
    padding: 5px 8px;
  }
  .map-target-nav {
    gap: 4px;
    margin: 0 2px;
  }
  .map-target-current {
    flex: 0 1 110px;
    max-width: 120px;
    padding: 2px 6px;
  }
  .map-target-current strong {
    font-size: 0.8rem;
  }
  .map-toolbar-actions {
    gap: 5px;
  }
  .map-live {
    font-size: 0.62rem;
  }
}
@container mappanel (max-width: 580px) {
  .map-title-text strong {
    display: none;
  }
  .map-title-icon {
    display: grid;
  }
  .map-target-nav-btn.list-btn .btn-text-short {
    display: none;
  }
  .map-target-nav-btn.list-btn {
    padding: 0;
    width: 30px;
  }
  .map-target-current {
    flex: 0 1 80px;
    max-width: 90px;
  }
}

/* Fallback media queries */
@media (max-width: 1100px) {
  .map-title small {
    display: none;
  }
}
@media (max-width: 900px) {
  .map-target-nav-btn.list-btn .btn-text-full {
    display: none;
  }
  .map-target-nav-btn.list-btn .btn-text-short {
    display: inline;
  }
}
@media (max-width: 680px) {
  .map-target-nav-btn.list-btn .btn-text-short {
    display: none;
  }
  .map-target-nav-btn.list-btn {
    padding: 0;
    width: 30px;
  }
}
.map-jmem-banner {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  border-bottom: 1px solid rgba(251, 191, 36, 0.28);
  background: linear-gradient(90deg, rgba(120, 53, 15, 0.55), rgba(8, 20, 40, 0.92));
  color: #fde68a;
}
.map-jmem-banner > .bi {
  flex: 0 0 auto;
  color: #fbbf24;
  font-size: 0.95rem;
}
.map-jmem-copy {
  min-width: 0;
  flex: 1 1 auto;
}
.map-jmem-copy strong {
  display: block;
  overflow: hidden;
  color: #fff7ed;
  font-size: 0.78rem;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.map-jmem-copy small {
  display: block;
  color: #fcd34d;
  font-size: 0.66rem;
  font-weight: 700;
}
.map-jmem-banner em {
  flex: 0 1 42%;
  max-width: 360px;
  color: #fde68a;
  font-size: 0.66rem;
  font-style: normal;
  line-height: 1.3;
  text-align: right;
}
@media (max-width: 720px) {
  .map-jmem-banner {
    align-items: flex-start;
    flex-wrap: wrap;
  }
  .map-jmem-banner em {
    flex: 1 1 100%;
    max-width: none;
    text-align: left;
  }
}
.map-expand-button {
  width: 34px;
  height: 34px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--control-bg);
  color: var(--text);
}
.map-workspace {
  position: relative;
  display: flex;
  flex: 1 1 0;
  flex-direction: column;
  width: 100%;
  min-height: 0;
  overflow: hidden;
}
.map-container {
  position: relative;
  flex: 1 1 0;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}
.map-frame {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
  display: block;
  background: #020b07;
}
.floating-toolbar {
  position: absolute;
  top: 12px;
  left: 50%;
  z-index: 20;
  display: flex;
  gap: 4px;
  padding: 5px;
  border: 1px solid rgba(110, 168, 254, 0.35);
  border-radius: 12px;
  background: rgba(7, 17, 31, 0.92);
  transform: translateX(-50%);
}
.floating-toolbar button {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 52px;
  padding: 6px 7px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #cbd5e1;
  font-size: 0.62rem;
}
.floating-toolbar button.active,
.floating-toolbar button:hover {
  background: rgba(13, 110, 253, 0.28);
  color: #fff;
}
.floating-toolbar .blue {
  color: #60a5fa;
}
.floating-toolbar .red {
  color: #f87171;
}
.detection-panel,
.layer-menu-panel {
  position: absolute;
  z-index: 25;
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: rgba(7, 17, 31, 0.96);
}
.detection-panel {
  top: 68px;
  left: 12px;
  width: min(280px, calc(100% - 24px));
  border-color: rgba(34, 211, 238, 0.45);
}
.layer-menu-panel {
  top: 68px;
  left: 50%;
  width: 240px;
  transform: translateX(-50%);
}
.panel-head strong {
  display: block;
  font-size: 0.82rem;
}
.panel-head small,
.hint {
  color: var(--muted);
  font-size: 0.68rem;
}
.detection-panel label {
  display: grid;
  gap: 4px;
  color: #cbd5e1;
  font-size: 0.72rem;
}
.detection-panel em {
  color: #67e8f9;
  font-style: normal;
  font-weight: 700;
}
.run-btn,
.layer-row {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 0;
  border-radius: 8px;
  color: #fff;
}
.run-btn {
  justify-content: center;
  min-height: 36px;
  background: #0891b2;
  font-size: 0.78rem;
  font-weight: 700;
}
.run-btn:disabled {
  opacity: 0.55;
}
.layer-row {
  width: 100%;
  padding: 7px 8px;
  background: transparent;
  color: var(--text);
  font-size: 0.75rem;
}
.layer-row:hover {
  background: rgba(13, 110, 253, 0.15);
}
.layer-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #475569;
}
.layer-indicator.active {
  background: #22c55e;
}
.basemap-head {
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}
.mode-chip {
  position: absolute;
  left: 12px;
  bottom: 12px;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: rgba(7, 17, 31, 0.92);
  color: #cbd5e1;
  font-size: 0.72rem;
}
.mode-chip em {
  color: #ffd84d;
  font-style: normal;
  font-weight: 700;
}
.map-state {
  position: absolute;
  inset: 0;
  z-index: 15;
  display: grid;
  place-content: center;
  gap: 8px;
  background: rgba(7, 17, 31, 0.72);
  text-align: center;
}
.map-state.error {
  color: #fca5a5;
}
.map-loader {
  width: 28px;
  height: 28px;
  margin: 0 auto;
  border: 3px solid rgba(110, 168, 254, 0.25);
  border-top-color: #6ea8fe;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.map-info {
  display: flex;
  flex: 0 0 auto;
  gap: 10px;
  align-items: center;
  padding: 7px 12px;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.68rem;
}
</style>
