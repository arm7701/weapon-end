<template>
  <div v-if="isExpanded" class="simulator-backdrop" @click="toggleExpanded"></div>

  <section class="simulator-window" :class="{ expanded: isExpanded }">
    <header class="simulator-header">
      <div class="simulator-title">
        <span class="simulator-title-icon"><i class="bi bi-bullseye"></i></span>
        <div>
          <strong>Mission Simulator</strong>
          <small>ตรวจสอบวงรัศมีทำลายล้างแต่ละจุดเป้าหมาย · แสดงกล่อง 3D และวงรอบข้างตลอดเวลา</small>
        </div>
      </div>
      <div class="simulator-status">
        <span class="status-dot" :class="{ active: hasPoints }"></span>
        {{ !hasPoints ? 'WAITING TARGET' : isPlaying ? `POINT ${currentPointIndex + 1}/${targetPoints.length}` : 'INSPECT' }}
      </div>
      <button
        class="simulator-icon-button"
        type="button"
        :title="isExpanded ? 'ย่อหน้าจอ' : 'ขยายหน้าจอ'"
        @click="toggleExpanded"
      >
        <i class="bi" :class="isExpanded ? 'bi-fullscreen-exit' : 'bi-arrows-fullscreen'"></i>
      </button>
    </header>

    <div class="simulator-stage">
      <!-- Dedicated 3D Cesium Viewport (Isolated from Main Map) -->
      <div ref="cesiumMount" class="sim-cesium-mount" aria-label="หน้าจอตรวจสอบวงรัศมีแต่ละจุดเป้าหมาย"></div>

      <!-- Empty State Overlay when no targets exist yet -->
      <div v-if="!hasPoints" class="sim-empty-overlay">
        <div class="sim-empty-box">
          <i class="bi bi-bullseye"></i>
          <strong>ยังไม่มีจุดเป้าหมายใน Scenario นี้</strong>
          <small>เมื่อปักหมุดเป้าหมายหรือสร้างกล่อง 3D ระบบจะแสดงกล่อง 3D ค้างไว้ตลอด และให้คุณเลือกดูวงรัศมีของแต่ละจุดเป้าหมายได้ที่นี่</small>
        </div>
      </div>

      <!-- HUD Overlays inside 3D viewport (Shown ONLY when expanded full screen) -->
      <template v-if="isExpanded">
        <!-- Top-Left HUD: Target Point Selector & Active Point Info -->
        <div v-if="activePoint" class="hud-badge hud-top-left">
          <div class="hud-target-header">
            <span>จุดเป้าหมาย {{ currentPointIndex + 1 }} / {{ targetPoints.length }}</span>
            <div v-if="targetPoints.length > 1" class="hud-target-cycle-btns">
              <button type="button" title="จุดเป้าหมายก่อนหน้า" @click.stop="stepPoint(-1)">
                <i class="bi bi-chevron-left"></i>
              </button>
              <button type="button" title="จุดเป้าหมายถัดไป" @click.stop="stepPoint(1)">
                <i class="bi bi-chevron-right"></i>
              </button>
            </div>
          </div>

          <select
            v-if="targetPoints.length > 1"
            class="hud-point-select"
            :value="currentPointIndex"
            @change="selectPointByIndex(Number($event.target.value))"
          >
            <option v-for="(pt, idx) in targetPoints" :key="pt.pointKey" :value="idx">
              {{ idx + 1 }}. {{ pt.label }}
            </option>
          </select>
          <strong v-else>{{ activePoint.label }}</strong>

          <small class="hud-sub">
            อาวุธ: {{ activePoint.effectProduct || 'ค่าเริ่มต้น (JMEM)' }}
            <template v-if="activePoint.effectN"> · N={{ activePoint.effectN }}</template>
          </small>
        </div>

        <!-- Bottom-Left HUD: Blast Radius Rings Breakdown for Active Target Point -->
        <div v-if="activePoint && activePoint.zones.length" class="hud-badge hud-bottom-left">
          <span>วงรัศมีจุดนี้ ({{ activePoint.zones.length }} ระยะ)</span>
          <div class="hud-zone-pills">
            <span
              v-for="(z, idx) in activePoint.zones"
              :key="idx"
              class="hud-zone-pill"
              :title="z.label"
            >
              <i class="zone-dot" :style="{ background: z.color }"></i>
              {{ z.radiusM.toFixed(1) }} ม.
            </span>
          </div>
        </div>

        <!-- Bottom-Right HUD: 3D Box Status & Camera Heading (Without Duration) -->
        <div class="hud-badge hud-bottom-right">
          <span>3D BOX: {{ boxCount }} จุด · มุม {{ orbitDegrees }}°</span>
        </div>
      </template>
    </div>

    <!-- Non-expanded: Clean UI Bar Below 3D Stage -->
    <div v-if="!isExpanded && activePoint" class="sim-details-bar">
      <!-- Target Selector Row -->
      <div class="sim-target-row">
        <div class="sim-target-head">
          <span class="sim-target-title">
            <i class="bi bi-geo-alt-fill"></i> จุดเป้าหมาย {{ currentPointIndex + 1 }} / {{ targetPoints.length }}
          </span>
          <div v-if="targetPoints.length > 1" class="sim-target-nav">
            <button type="button" title="จุดเป้าหมายก่อนหน้า" @click.stop="stepPoint(-1)">
              <i class="bi bi-chevron-left"></i>
            </button>
            <button type="button" title="จุดเป้าหมายถัดไป" @click.stop="stepPoint(1)">
              <i class="bi bi-chevron-right"></i>
            </button>
          </div>
        </div>

        <select
          v-if="targetPoints.length > 1"
          class="sim-point-select"
          :value="currentPointIndex"
          @change="selectPointByIndex(Number($event.target.value))"
        >
          <option v-for="(pt, idx) in targetPoints" :key="pt.pointKey" :value="idx">
            {{ idx + 1 }}. {{ pt.label }}
          </option>
        </select>
        <strong v-else class="sim-point-name">{{ activePoint.label }}</strong>

        <div class="sim-weapon-info">
          <span>อาวุธ: {{ activePoint.effectProduct || 'ค่าเริ่มต้น (JMEM)' }}<template v-if="activePoint.effectN"> · N={{ activePoint.effectN }}</template></span>
          <span v-if="boxCount" class="sim-box-tag">3D BOX: {{ boxCount }} จุด</span>
        </div>
      </div>

      <!-- Blast Radius Rings Row -->
      <div v-if="activePoint.zones.length" class="sim-radius-row">
        <span class="sim-radius-label">วงรัศมีจุดนี้ ({{ activePoint.zones.length }} ระยะ):</span>
        <div class="sim-zone-pills">
          <span
            v-for="(z, idx) in activePoint.zones"
            :key="idx"
            class="sim-zone-pill"
            :title="z.label"
          >
            <i class="zone-dot" :style="{ background: z.color }"></i>
            {{ z.radiusM.toFixed(1) }} ม.
          </span>
        </div>
      </div>
    </div>

    <footer class="simulator-controls">
      <button
        type="button"
        class="control-button primary"
        :class="{ active: isPlaying }"
        title="เล่น (หมุนดูวงรัศมีแต่ละจุดเป้าหมายอัตโนมัติ)"
        aria-label="เล่น"
        :disabled="isPlaying"
        @click="startPlayback"
      >
        <i class="bi bi-play-fill"></i>
        <span>Play</span>
      </button>
      <button
        type="button"
        class="control-button stop"
        :class="{ active: !isPlaying }"
        title="หยุด"
        aria-label="หยุด"
        :disabled="!isPlaying"
        @click="stopPlayback"
      >
        <i class="bi bi-stop-fill"></i>
        <span>หยุด</span>
      </button>
      <button
        type="button"
        class="control-button camera"
        :class="{ captured: isCaptured }"
        :title="isCaptured ? 'บันทึกภาพหน้าจอเรียบร้อย' : 'แคปหน้าจอ Mission Sim'"
        aria-label="แคปหน้าจอ Mission Sim"
        @click="captureScreen"
      >
        <i class="bi" :class="isCaptured ? 'bi-check-lg' : 'bi-camera'"></i>
        <span>{{ isCaptured ? 'บันทึกแล้ว' : 'แคปหน้าจอ' }}</span>
      </button>
      <span v-if="isExpanded" class="control-hint">ESC เพื่อปิดหน้าจอขยาย</span>
    </footer>
  </section>
</template>

<script>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const POINT_DWELL_SEC = 10.0
const ORBIT_RAD_PER_SEC = 0.32

let cesiumLoadPromise = null

function ensureCesiumLoaded() {
  if (typeof window !== 'undefined' && window.Cesium) {
    return Promise.resolve(window.Cesium)
  }
  if (cesiumLoadPromise) return cesiumLoadPromise

  cesiumLoadPromise = new Promise((resolve, reject) => {
    const baseUrl = `${(import.meta.env.BASE_URL || '/').replace(/\/?$/, '/')}cesium-static/`
    window.CESIUM_BASE_URL = baseUrl

    if (!document.querySelector('link[data-sim-cesium-css]')) {
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = `${baseUrl}Widgets/widgets.css`
      link.setAttribute('data-sim-cesium-css', '1')
      document.head.appendChild(link)
    }

    const script = document.createElement('script')
    script.src = `${baseUrl}Cesium.js`
    script.async = true
    script.onload = () => {
      if (window.Cesium) resolve(window.Cesium)
      else reject(new Error('Cesium failed to initialize'))
    }
    script.onerror = () => reject(new Error('Failed to load Cesium.js'))
    document.head.appendChild(script)
  })
  return cesiumLoadPromise
}

function computeFootprintPolygon(lat, lng, lengthM, widthM, heightM, headingDeg = 0) {
  const L = Math.max(2, Number(lengthM) || 0)
  const W = Math.max(2, Number(widthM) || 0)
  const H = Math.max(0, Number(heightM) || 0)
  if (!L || !W) return null

  const headingRad = ((Number(headingDeg) || 0) * Math.PI) / 180
  const cosH = Math.cos(headingRad)
  const sinH = Math.sin(headingRad)
  const halfL = L / 2
  const halfW = W / 2
  const metersPerDegLat = 111320
  const metersPerDegLng = Math.max(1, 111320 * Math.cos((lat * Math.PI) / 180))

  const localCorners = [
    [halfL, -halfW],
    [halfL, halfW],
    [-halfL, halfW],
    [-halfL, -halfW],
  ]
  const polygon = localCorners.map(([along, across]) => {
    const northM = along * cosH - across * sinH
    const eastM = along * sinH + across * cosH
    return [lat + northM / metersPerDegLat, lng + eastM / metersPerDegLng]
  })
  return {
    polygon,
    lengthM: L,
    widthM: W,
    heightM: H > 0 ? H : 10,
    headingDeg: Number(headingDeg) || 0,
  }
}

function normalizeZones(effectRadii) {
  const raw = Array.isArray(effectRadii) ? effectRadii.filter((z) => Number(z?.radiusM) > 0) : []
  if (raw.length) {
    return raw
      .map((z) => ({
        zone: z.zone || '',
        label: z.label || z.zone || '',
        radiusM: Number(z.radiusM),
        color: z.color || '#FF6B35',
      }))
      .sort((a, b) => a.radiusM - b.radiusM)
  }
  return [
    { zone: 'r1', label: 'Lethal Blast', radiusM: 15, color: '#FF3B30' },
    { zone: 'r2', label: 'Severe Blast (1.5×)', radiusM: 22.5, color: '#FF9500' },
    { zone: 'r3', label: 'Fragmentation (2.0×)', radiusM: 30, color: '#FFD60A' },
  ]
}

function buildCirclePositions(Cesium, lat, lng, radiusM, heightM = 0.35, segments = 64) {
  const enu = Cesium.Transforms.eastNorthUpToFixedFrame(
    Cesium.Cartesian3.fromDegrees(lng, lat, heightM),
  )
  const positions = []
  for (let i = 0; i <= segments; i++) {
    const angle = (i / segments) * Math.PI * 2
    const local = new Cesium.Cartesian3(
      radiusM * Math.sin(angle),
      radiusM * Math.cos(angle),
      0,
    )
    positions.push(Cesium.Matrix4.multiplyByPoint(enu, local, new Cesium.Cartesian3()))
  }
  return positions
}

function pointAtAzimuth(Cesium, lat, lng, radiusM, azimuthDeg, heightM = 1.2) {
  const enu = Cesium.Transforms.eastNorthUpToFixedFrame(
    Cesium.Cartesian3.fromDegrees(lng, lat, heightM),
  )
  const rad = (azimuthDeg * Math.PI) / 180
  const local = new Cesium.Cartesian3(radiusM * Math.sin(rad), radiusM * Math.cos(rad), 0)
  return Cesium.Matrix4.multiplyByPoint(enu, local, new Cesium.Cartesian3())
}

export default {
  name: 'SimulatorDemo',
  props: {
    targets: { type: Array, default: () => [] },
    selectedTargetId: { type: String, default: '' },
    formData: { type: Object, default: () => ({}) },
    scenarioId: { type: String, default: '' },
  },
  setup(props) {
    const cesiumMount = ref(null)
    const isPlaying = ref(true)
    const isPaused = ref(false)
    const isExpanded = ref(false)
    const elapsed = ref(0)
    const currentPointIndex = ref(0)
    const orbitHeadingRad = ref(0)

    let viewer = null
    let boxesDataSource = null
    let radiusDataSource = null
    let animationFrame = null
    let previousTime = 0
    let pointDwellElapsed = 0
    let resizeObserver = null
    let lastBoxesSignature = ''
    let lastRadiusSignature = ''

    // 1. รายการกล่อง 3D ทั้งหมดที่สร้างจากฟังก์ชันกำหนดขนาดเป้าหมาย (แสดงค้างไว้ตลอดเวลา)
    const persistent3DBoxes = computed(() => {
      const byCard = new Map()
      for (const item of props.targets || []) {
        if (!item || item.lat == null || item.lng == null) continue
        const cardId = item.targetCardId || item.coordinateId || `${item.lat},${item.lng}`
        if (!byCard.has(cardId) || (item.isPrimary && !byCard.get(cardId).isPrimary)) {
          byCard.set(cardId, item)
        }
      }

      const boxes = []
      for (const [cardId, item] of byCard.entries()) {
        const isSelectedCard = props.selectedTargetId && cardId === props.selectedTargetId
        const fd = isSelectedCard ? props.formData || {} : {}
        const customL = Number(fd.targetLength)
        const customW = Number(fd.targetWidth)
        const customH = Number(fd.targetHeight)
        const customHeading = Number(fd.targetHeading)

        let fp = item.footprint
        if (customL > 0 && customW > 0) {
          fp = computeFootprintPolygon(
            Number(item.lat),
            Number(item.lng),
            customL,
            customW,
            customH > 0 ? customH : fp?.heightM || 10,
            Number.isFinite(customHeading) ? customHeading : fp?.headingDeg || 0,
          )
        } else if (fp && Array.isArray(fp.polygon) && fp.polygon.length >= 3) {
          fp = {
            ...fp,
            heightM: Number(fp.heightM) > 0 ? Number(fp.heightM) : 10,
          }
        } else {
          fp = null
        }

        if (fp) {
          boxes.push({
            cardId,
            label: item.label || 'พื้นที่เป้าหมาย 3D',
            lat: Number(item.lat),
            lng: Number(item.lng),
            footprint: fp,
          })
        }
      }
      return boxes
    })

    // 2. รายการแต่ละจุดเป้าหมาย (สำหรับสลับดูวงรัศมีของแต่ละจุดเป้าหมาย)
    const targetPoints = computed(() => {
      const list = []
      for (const item of props.targets || []) {
        if (!item || item.lat == null || item.lng == null) continue
        const zones = normalizeZones(item.effectRadii)
        const maxRadiusM = Math.max(...zones.map((z) => z.radiusM), Number(item.radiusM) || 0, 20)
        list.push({
          pointKey: item.coordinateId || `${item.targetCardId}-${item.pointIndex || 0}`,
          targetCardId: item.targetCardId || '',
          coordinateId: item.coordinateId || '',
          label: item.label || 'จุดเป้าหมาย',
          lat: Number(item.lat),
          lng: Number(item.lng),
          radiusM: Number(item.radiusM) || 0,
          effectProduct: item.effectProduct || '',
          effectWeightLb: item.effectWeightLb || 500,
          effectN: item.effectN || 1,
          zones,
          maxRadiusM,
        })
      }
      return list
    })

    const hasPoints = computed(() => targetPoints.value.length > 0)
    const boxCount = computed(() => persistent3DBoxes.value.length)

    const activePoint = computed(() => {
      if (!targetPoints.value.length) return null
      const idx = Math.max(0, Math.min(currentPointIndex.value, targetPoints.value.length - 1))
      return targetPoints.value[idx]
    })

    const formattedTime = computed(() => {
      const totalSeconds = Math.floor(elapsed.value)
      const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0')
      const seconds = String(totalSeconds % 60).padStart(2, '0')
      return `${minutes}:${seconds}`
    })

    const orbitDegrees = computed(() => {
      const deg = Math.round(((orbitHeadingRad.value * 180) / Math.PI) % 360)
      return (deg + 360) % 360
    })

    function createEsriImagery(Cesium) {
      const base = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile'
      return new Cesium.UrlTemplateImageryProvider({
        url: `${base}/{z}/{y}/{x}`,
        maximumLevel: 17,
        tileDiscardPolicy: new Cesium.DiscardMissingTileImagePolicy({
          missingImageUrl: `${base}/19/0/0`,
          pixelsToCheck: [
            new Cesium.Cartesian2(0, 0),
            new Cesium.Cartesian2(255, 0),
            new Cesium.Cartesian2(0, 255),
            new Cesium.Cartesian2(255, 255),
            new Cesium.Cartesian2(128, 12),
            new Cesium.Cartesian2(12, 128),
          ],
        }),
      })
    }

    async function initViewer() {
      if (viewer || !cesiumMount.value) return
      try {
        const Cesium = await ensureCesiumLoaded()
        if (!cesiumMount.value) return
        const imagery = createEsriImagery(Cesium)
        const opts = {
          animation: false,
          timeline: false,
          fullscreenButton: false,
          vrButton: false,
          geocoder: false,
          homeButton: false,
          infoBox: false,
          selectionIndicator: false,
          sceneModePicker: false,
          baseLayerPicker: false,
          navigationHelpButton: false,
          terrainProvider: new Cesium.EllipsoidTerrainProvider(),
          requestRenderMode: false,
          contextOptions: {
            webgl: { alpha: false, preserveDrawingBuffer: true },
          },
        }
        if (Cesium.ImageryLayer) {
          opts.baseLayer = new Cesium.ImageryLayer(imagery)
        } else {
          opts.imageryProvider = imagery
        }
        viewer = new Cesium.Viewer(cesiumMount.value, opts)
        if (viewer._cesiumWidget?._creditContainer) {
          viewer._cesiumWidget._creditContainer.style.display = 'none'
        }
        viewer.scene.globe.depthTestAgainstTerrain = false

        boxesDataSource = new Cesium.CustomDataSource('sim-persistent-3d-boxes')
        radiusDataSource = new Cesium.CustomDataSource('sim-active-point-radii')
        viewer.dataSources.add(boxesDataSource)
        viewer.dataSources.add(radiusDataSource)

        renderPersistent3DBoxes(true)
        renderActivePointRadii(true)
      } catch (err) {
        console.warn('Simulator 3D viewer init warning:', err)
      }
    }

    // วาดกล่อง 3D ทุกจุดค้างไว้ตลอดเวลา (ไม่ถูกลบเมื่อสลับจุดเป้าหมาย)
    function renderPersistent3DBoxes(force = false) {
      if (!viewer || !boxesDataSource || !window.Cesium) return
      const Cesium = window.Cesium
      const activeCardId = activePoint.value?.targetCardId || ''

      const sig = JSON.stringify({
        boxes: persistent3DBoxes.value,
        activeCardId,
      })
      if (!force && sig === lastBoxesSignature) return
      lastBoxesSignature = sig

      boxesDataSource.entities.removeAll()

      for (const box of persistent3DBoxes.value) {
        const fp = box.footprint
        if (!fp || !Array.isArray(fp.polygon) || fp.polygon.length < 3) continue

        const flatDeg = []
        fp.polygon.forEach(([plat, plng]) => {
          flatDeg.push(plng, plat)
        })
        const heightM = Math.max(1, Number(fp.heightM) || 10)
        const isCurrent = box.cardId === activeCardId

        boxesDataSource.entities.add({
          position: Cesium.Cartesian3.fromDegrees(box.lng, box.lat, heightM),
          polygon: {
            hierarchy: Cesium.Cartesian3.fromDegreesArray(flatDeg),
            height: 0,
            extrudedHeight: heightM,
            material: Cesium.Color.fromCssColorString(isCurrent ? '#38BDF8' : '#0EA5E9').withAlpha(
              isCurrent ? 0.45 : 0.34,
            ),
            outline: true,
            outlineColor: Cesium.Color.fromCssColorString(isCurrent ? '#FFD700' : '#7DD3FC').withAlpha(0.95),
            outlineWidth: isCurrent ? 2.5 : 1.5,
          },
          label: {
            text: `กล่อง 3D: ${Number(fp.lengthM).toFixed(0)}×${Number(fp.widthM).toFixed(0)}×${Number(heightM).toFixed(0)} ม. (${Math.round(fp.headingDeg || 0)}°)`,
            font: "600 10.5px 'IBM Plex Sans Thai', 'Inter', sans-serif",
            fillColor: Cesium.Color.fromCssColorString('#FEF08A'),
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 3,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -8),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
        })
      }
    }

    // วาดวงรัศมีและโดม 3D ทั้งของจุดเป้าหมายที่เลือก และวงรัศมีของจุดเป้าหมายอื่นรอบข้าง (ไม่ซ่อนวงอื่น)
    function renderActivePointRadii(resetCamera = false) {
      if (!viewer || !radiusDataSource || !window.Cesium) return
      const Cesium = window.Cesium
      const activePt = activePoint.value
      const points = targetPoints.value || []

      if (!activePt && !points.length) {
        radiusDataSource.entities.removeAll()
        lastRadiusSignature = ''
        return
      }

      const sig = JSON.stringify({
        activeKey: activePt?.pointKey,
        points: points.map((p) => ({
          key: p.pointKey,
          lat: p.lat,
          lng: p.lng,
          zones: p.zones,
        })),
      })
      if (!resetCamera && sig === lastRadiusSignature) return
      lastRadiusSignature = sig

      radiusDataSource.entities.removeAll()

      // วาดทุกจุดเป้าหมาย: จุดที่กำลังดู (Active) จะเด่นชัดเป็นพิเศษ ส่วนจุดเป้าหมายอื่นรอบๆ จะแสดงวงรัศมีค้างไว้ตลอดไม่ซ่อน
      for (const pt of points) {
        const isActive = activePt && pt.pointKey === activePt.pointKey
        const centerCartesian = Cesium.Cartesian3.fromDegrees(pt.lng, pt.lat, 0)

        // 1. จุดศูนย์กลางเป้าหมาย (Center Pin)
        radiusDataSource.entities.add({
          position: Cesium.Cartesian3.fromDegrees(pt.lng, pt.lat, 1.0),
          point: {
            pixelSize: isActive ? 10 : 7,
            color: Cesium.Color.fromCssColorString(isActive ? '#EF4444' : '#F97316'),
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: isActive ? 2 : 1.5,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
          label: {
            text: pt.label,
            font: isActive
              ? "700 11.5px 'IBM Plex Sans Thai', 'Inter', sans-serif"
              : "600 10px 'IBM Plex Sans Thai', 'Inter', sans-serif",
            fillColor: isActive ? Cesium.Color.WHITE : Cesium.Color.fromCssColorString('#E2E8F0'),
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 3,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            verticalOrigin: Cesium.VerticalOrigin.TOP,
            pixelOffset: new Cesium.Cartesian2(0, isActive ? 10 : 8),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
        })

        // 2. วาดวงรัศมีแต่ละโซน
        const zones = pt.zones || []
        zones.forEach((zone, zIdx) => {
          const r = Math.max(1, Number(zone.radiusM) || 10)
          const cssColor = zone.color || '#FF6B35'
          const cColor = Cesium.Color.fromCssColorString(cssColor)

          // 2.1 เส้นวงรัศมีบนพื้นดิน (Ground Radius Ring)
          radiusDataSource.entities.add({
            polyline: {
              positions: buildCirclePositions(Cesium, pt.lat, pt.lng, r, 0.4, 72),
              width: isActive ? 2.5 : 1.8,
              material: cColor.withAlpha(isActive ? 0.95 : 0.70),
            },
          })

          // 2.2 พื้นวงกลมโปร่งแสงบนพื้นดิน
          radiusDataSource.entities.add({
            position: centerCartesian,
            ellipse: {
              semiMajorAxis: r,
              semiMinorAxis: r,
              height: 0.2,
              material: cColor.withAlpha(
                isActive
                  ? Math.max(0.05, 0.14 - zIdx * 0.025)
                  : Math.max(0.02, 0.06 - zIdx * 0.015),
              ),
            },
          })

          // 2.3 โดมรัศมี 3D ครึ่งทรงกลม
          radiusDataSource.entities.add({
            position: centerCartesian,
            ellipsoid: {
              radii: new Cesium.Cartesian3(r, r, r),
              maximumCone: Cesium.Math.PI_OVER_TWO,
              material: cColor.withAlpha(
                isActive
                  ? Math.max(0.08, 0.18 - zIdx * 0.03)
                  : Math.max(0.02, 0.06 - zIdx * 0.015),
              ),
              outline: true,
              outlineColor: cColor.withAlpha(isActive ? 0.42 : 0.22),
              slicePartitions: 24,
              stackPartitions: 12,
            },
          })

          // 2.4 ป้ายกำกับระยะรัศมี
          if (isActive) {
            const labelAzimuth = 45 + zIdx * 28
            radiusDataSource.entities.add({
              position: pointAtAzimuth(Cesium, pt.lat, pt.lng, r, labelAzimuth, 1.5),
              label: {
                text: `R${zIdx + 1}: ${r.toFixed(1)} ม.`,
                font: "700 10.5px 'IBM Plex Sans Thai', 'Inter', monospace",
                fillColor: cColor,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 3,
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                disableDepthTestDistance: Number.POSITIVE_INFINITY,
              },
            })
          } else if (zIdx === zones.length - 1) {
            // สำหรับจุดรอบข้าง แสดงระยะรัศมีนอกสุดกำกับไว้
            radiusDataSource.entities.add({
              position: pointAtAzimuth(Cesium, pt.lat, pt.lng, r, 45, 1.2),
              label: {
                text: `${r.toFixed(0)} ม.`,
                font: "600 9.5px 'IBM Plex Sans Thai', 'Inter', monospace",
                fillColor: cColor.withAlpha(0.85),
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 2.5,
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                disableDepthTestDistance: Number.POSITIVE_INFINITY,
              },
            })
          }
        })
      }

      renderPersistent3DBoxes(true)
      updateOrbitCamera()
    }

    function updateOrbitCamera() {
      if (!viewer || !window.Cesium) return
      const pt = activePoint.value
      if (!pt) return
      const Cesium = window.Cesium

      const center = Cesium.Cartesian3.fromDegrees(pt.lng, pt.lat, 0)
      const matchingBox = persistent3DBoxes.value.find((b) => b.cardId === pt.targetCardId)
      const fpDiag = matchingBox?.footprint
        ? Math.hypot(matchingBox.footprint.lengthM || 30, matchingBox.footprint.widthM || 20)
        : 36
      const rangeM = Math.max(pt.maxRadiusM * 2.8, fpDiag * 2.6, 110)
      const pitchRad = Cesium.Math.toRadians(-32)

      try {
        viewer.camera.lookAt(
          center,
          new Cesium.HeadingPitchRange(orbitHeadingRad.value, pitchRad, rangeM),
        )
      } catch {
        /* ignore camera timing */
      }
    }

    function selectPointByIndex(idx) {
      const count = targetPoints.value.length
      if (!count) return
      currentPointIndex.value = Math.max(0, Math.min(idx, count - 1))
      pointDwellElapsed = 0
      renderActivePointRadii(true)
    }

    function stepPoint(offset) {
      const count = targetPoints.value.length
      if (!count) return
      currentPointIndex.value = (currentPointIndex.value + offset + count) % count
      pointDwellElapsed = 0
      renderActivePointRadii(true)
    }

    const animate = (timestamp) => {
      if (!previousTime) previousTime = timestamp
      const dt = Math.min((timestamp - previousTime) / 1000, 0.1)
      previousTime = timestamp

      if (isPlaying.value && hasPoints.value) {
        elapsed.value += dt
        pointDwellElapsed += dt
        orbitHeadingRad.value = (orbitHeadingRad.value + ORBIT_RAD_PER_SEC * dt) % (Math.PI * 2)

        if (targetPoints.value.length > 1 && pointDwellElapsed >= POINT_DWELL_SEC) {
          pointDwellElapsed = 0
          currentPointIndex.value = (currentPointIndex.value + 1) % targetPoints.value.length
          renderActivePointRadii(true)
        } else {
          updateOrbitCamera()
        }
      }

      animationFrame = window.requestAnimationFrame(animate)
    }

    const startPlayback = () => {
      isPlaying.value = true
      isPaused.value = false
      previousTime = performance.now()
    }

    const pausePlayback = () => {
      isPlaying.value = false
      isPaused.value = true
    }

    const stopPlayback = () => {
      isPlaying.value = false
      isPaused.value = false
    }

    const restart = () => {
      elapsed.value = 0
      pointDwellElapsed = 0
      orbitHeadingRad.value = 0
      currentPointIndex.value = 0
      isPlaying.value = true
      isPaused.value = false
      previousTime = performance.now()
      renderActivePointRadii(true)
    }

    const isCaptured = ref(false)
    const captureScreen = () => {
      if (!cesiumMount.value) return
      try {
        viewer?.render?.()
        const glCanvas = cesiumMount.value.querySelector('canvas')
        if (!glCanvas) return
        const link = document.createElement('a')
        link.download = `mission-sim-${new Date().toISOString().replace(/[:.]/g, '-')}.png`
        link.href = glCanvas.toDataURL('image/png')
        link.click()
        isCaptured.value = true
        setTimeout(() => {
          isCaptured.value = false
        }, 1500)
      } catch (err) {
        console.warn('Capture failed:', err)
      }
    }

    const toggleExpanded = async () => {
      isExpanded.value = !isExpanded.value
      document.body.style.overflow = isExpanded.value ? 'hidden' : ''
      await nextTick()
      try {
        viewer?.resize?.()
        updateOrbitCamera()
      } catch {
        /* ignore */
      }
    }

    const handleKeydown = (event) => {
      if (event.key === 'Escape' && isExpanded.value) toggleExpanded()
    }

    // อัปเดตกล่อง 3D ทันทีเมื่อข้อมูลขนาดเป้าหมายเปลี่ยน (แสดงค้างไว้ตลอด)
    watch(
      persistent3DBoxes,
      () => {
        renderPersistent3DBoxes(false)
        updateOrbitCamera()
      },
      { deep: true },
    )

    // อัปเดตจุดเป้าหมายและวงรัศมีเมื่อรายการเป้าหมายเปลี่ยน
    watch(
      targetPoints,
      (pts) => {
        if (!pts.length) {
          currentPointIndex.value = 0
          renderActivePointRadii(true)
          return
        }
        if (currentPointIndex.value >= pts.length) {
          currentPointIndex.value = 0
        }
        renderActivePointRadii(false)
      },
      { deep: true },
    )

    // เมื่อผู้ใช้คลิกเลือกเป้าหมายบนแผนที่หลัก ให้สลับมาดูวงรัศมีของจุดเป้าหมายนั้นทันที
    watch(
      () => props.selectedTargetId,
      (id) => {
        if (!id || !targetPoints.value.length) return
        const idx = targetPoints.value.findIndex((p) => p.targetCardId === id)
        if (idx >= 0 && idx !== currentPointIndex.value) {
          currentPointIndex.value = idx
          pointDwellElapsed = 0
          renderActivePointRadii(true)
        }
      },
    )

    onMounted(async () => {
      window.addEventListener('keydown', handleKeydown)
      await initViewer()
      if (cesiumMount.value) {
        resizeObserver = new ResizeObserver(() => {
          try {
            viewer?.resize?.()
            updateOrbitCamera()
          } catch {
            /* ignore */
          }
        })
        resizeObserver.observe(cesiumMount.value)
      }
      animationFrame = window.requestAnimationFrame(animate)
    })

    onUnmounted(() => {
      if (animationFrame) window.cancelAnimationFrame(animationFrame)
      resizeObserver?.disconnect()
      window.removeEventListener('keydown', handleKeydown)
      document.body.style.overflow = ''
      try {
        viewer?.destroy?.()
      } catch {
        /* ignore */
      }
      viewer = null
    })

    return {
      cesiumMount,
      isPlaying,
      isPaused,
      isExpanded,
      hasPoints,
      boxCount,
      targetPoints,
      activePoint,
      currentPointIndex,
      orbitDegrees,
      formattedTime,
      selectPointByIndex,
      stepPoint,
      startPlayback,
      pausePlayback,
      stopPlayback,
      restart,
      captureScreen,
      isCaptured,
      toggleExpanded,
    }
  },
}
</script>

<style scoped>
.simulator-backdrop { position: fixed; inset: 0; z-index: 1390; background: rgba(0, 0, 0, 0.82); backdrop-filter: blur(4px); }
.simulator-window { overflow: hidden; border: 1px solid #345f91; border-radius: 10px; background: #07111d; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.34); }
.simulator-window.expanded { position: fixed; inset: 28px; z-index: 1400; display: flex; flex-direction: column; border-radius: 14px; box-shadow: 0 24px 80px rgba(0, 0, 0, 0.72); }
.simulator-header { display: flex; align-items: center; gap: 10px; min-height: 52px; padding: 8px 10px; border-bottom: 1px solid #294765; background: linear-gradient(90deg, #0b1c30, #102945); }
.simulator-title { display: flex; align-items: center; min-width: 0; gap: 8px; }
.simulator-title-icon { display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 8px; background: rgba(13, 110, 253, 0.2); color: #6ea8fe; }
.simulator-title div { display: flex; min-width: 0; flex-direction: column; }
.simulator-title strong { color: #e7f1ff; font-size: 0.8rem; }
.simulator-title small { color: #849bb5; font-size: 0.62rem; }
.simulator-status { display: inline-flex; align-items: center; gap: 6px; margin-left: auto; color: #8fa6bc; font: 600 0.6rem monospace; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: #718090; }
.status-dot.active { background: #36d28b; box-shadow: 0 0 8px rgba(54, 210, 139, 0.8); }
.simulator-icon-button { display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border: 1px solid #355574; border-radius: 7px; background: #0c1d2e; color: #a9c9ed; }
.simulator-icon-button:hover { border-color: #0d6efd; background: #0d6efd; color: white; }
.simulator-stage { position: relative; height: 240px; min-height: 180px; background: #06111f; overflow: hidden; }
.expanded .simulator-stage { flex: 1; height: auto; }
.sim-cesium-mount { position: absolute; inset: 0; width: 100%; height: 100%; }
.sim-empty-overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; padding: 16px; background: radial-gradient(circle at center, rgba(10, 32, 54, 0.88), rgba(6, 17, 31, 0.96)); text-align: center; pointer-events: none; }
.sim-empty-box { display: flex; flex-direction: column; align-items: center; gap: 6px; max-width: 240px; color: #9ab4ce; }
.sim-empty-box i { font-size: 1.5rem; color: #6ea8fe; opacity: 0.85; }
.sim-empty-box strong { color: #e2eefb; font-size: 0.78rem; }
.sim-empty-box small { color: #7f9ab5; font-size: 0.66rem; line-height: 1.45; }
.hud-badge { position: absolute; display: flex; flex-direction: column; gap: 3px; padding: 5px 8px; border: 1px solid rgba(95, 152, 207, 0.36); border-radius: 6px; background: rgba(4, 14, 25, 0.84); backdrop-filter: blur(4px); pointer-events: none; z-index: 5; }
.hud-badge span { color: #7890a8; font: 600 0.54rem 'IBM Plex Sans Thai', 'Inter', monospace; letter-spacing: 0.03em; }
.hud-badge strong { color: #e2f0ff; font: 600 0.68rem 'IBM Plex Sans Thai', 'Inter', sans-serif; }
.hud-sub { color: #9ec5fe; font-size: 0.6rem; }
.hud-top-left { top: 8px; left: 8px; max-width: 75%; pointer-events: auto; }
.hud-target-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.hud-target-cycle-btns { display: inline-flex; gap: 3px; }
.hud-target-cycle-btns button { display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; padding: 0; border: 1px solid rgba(110, 168, 254, 0.35); border-radius: 4px; background: rgba(13, 110, 253, 0.18); color: #cfe2ff; font-size: 0.58rem; cursor: pointer; }
.hud-target-cycle-btns button:hover { background: #0d6efd; color: #fff; }
.hud-point-select { width: 100%; padding: 2px 6px; border: 1px solid rgba(110, 168, 254, 0.4); border-radius: 4px; background: rgba(9, 25, 45, 0.92); color: #e2f0ff; font: 600 0.65rem 'IBM Plex Sans Thai', 'Inter', sans-serif; outline: none; cursor: pointer; }
.hud-bottom-left { left: 8px; bottom: 8px; }
.hud-zone-pills { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 2px; }
.hud-zone-pill { display: inline-flex; align-items: center; gap: 4px; color: #dbeafe; font: 600 0.58rem 'IBM Plex Sans Thai', 'Inter', monospace; }
.zone-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; }
.hud-bottom-right { right: 8px; bottom: 8px; text-align: right; }

.sim-details-bar {
  padding: 8px 10px;
  background: #091725;
  border-top: 1px solid #1e3a5f;
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.sim-target-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sim-target-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.sim-target-title {
  color: #7dd3fc;
  font: 600 0.64rem 'IBM Plex Sans Thai', 'Inter', monospace;
  display: flex;
  align-items: center;
  gap: 4px;
}
.sim-target-nav {
  display: inline-flex;
  gap: 3px;
}
.sim-target-nav button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: 1px solid rgba(110, 168, 254, 0.35);
  border-radius: 4px;
  background: rgba(13, 110, 253, 0.18);
  color: #cfe2ff;
  font-size: 0.62rem;
  cursor: pointer;
  transition: all 0.15s ease;
}
.sim-target-nav button:hover {
  background: #0d6efd;
  color: #fff;
}
.sim-point-select {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid rgba(110, 168, 254, 0.35);
  border-radius: 5px;
  background: rgba(9, 25, 45, 0.95);
  color: #e2f0ff;
  font: 600 0.7rem 'IBM Plex Sans Thai', 'Inter', sans-serif;
  outline: none;
  cursor: pointer;
}
.sim-point-name {
  color: #e2f0ff;
  font: 600 0.72rem 'IBM Plex Sans Thai', 'Inter', sans-serif;
  padding: 2px 0;
}
.sim-weapon-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  color: #9ec5fe;
  font-size: 0.62rem;
}
.sim-box-tag {
  display: inline-block;
  padding: 1px 5px;
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 4px;
  color: #7dd3fc;
  font: 600 0.58rem monospace;
}
.sim-radius-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 4px;
  border-top: 1px dashed rgba(53, 85, 116, 0.4);
}
.sim-radius-label {
  color: #94a3b8;
  font: 600 0.6rem 'IBM Plex Sans Thai', 'Inter', monospace;
}
.sim-zone-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.sim-zone-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 4px;
  color: #f1f5f9;
  font: 600 0.62rem 'IBM Plex Sans Thai', 'Inter', monospace;
}

.simulator-controls { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-top: 1px solid #1e3a5f; background: #06111f; }

:global(body.light-theme .simulator-window) { border-color: #b7cadc; background: #ffffff; box-shadow: 0 7px 20px rgba(31, 65, 98, 0.13); }
:global(body.light-theme .simulator-header) { border-bottom-color: #c7d6e4; background: linear-gradient(90deg, #ffffff, #eaf2fa); }
:global(body.light-theme .simulator-title strong) { color: #18344d; }
:global(body.light-theme .simulator-title small),
:global(body.light-theme .simulator-status) { color: #637b91; }
:global(body.light-theme .simulator-icon-button) { border-color: #b9cad9; background: #ffffff; color: #315f88; }
:global(body.light-theme .sim-details-bar) { background: #f8fafc; border-top-color: #cbd5e1; }
:global(body.light-theme .sim-target-title) { color: #0284c7; }
:global(body.light-theme .sim-point-select) { background: #ffffff; border-color: #94a3b8; color: #0f172a; }
:global(body.light-theme .sim-point-name) { color: #0f172a; }
:global(body.light-theme .sim-weapon-info) { color: #475569; }
:global(body.light-theme .sim-radius-row) { border-top-color: #e2e8f0; }
:global(body.light-theme .sim-radius-label) { color: #64748b; }
:global(body.light-theme .sim-zone-pill) { background: #f1f5f9; border-color: #cbd5e1; color: #1e293b; }
:global(body.light-theme .simulator-controls) { border-top-color: #cbd5e1; background: #f1f5f9; }

.control-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  height: 30px;
  padding: 0 14px;
  border: 1px solid #355574;
  border-radius: 6px;
  background: #102236;
  color: #c4d7ea;
  font-family: inherit;
  font-size: 0.74rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}
.control-button:hover:not(:disabled) { border-color: #5e92cc; background: #173451; color: white; }
.control-button.primary { border-color: #0d6efd; background: #0d6efd; color: white; }
.control-button.primary:hover:not(:disabled) { background: #0b5ed7; border-color: #0a58ca; }
.control-button.stop { border-color: #a04a53; color: #ff7e87; }
.control-button.stop:hover:not(:disabled) { background: #b63844; color: #ffffff; }
.control-button.stop.active { background: #b63844; color: #ffffff; border-color: #dc3545; }
.control-button.camera {
  border-color: #2e557b;
  color: #79b8ff;
  background: #0d2137;
}
.control-button.camera:hover:not(:disabled) {
  border-color: #5e92cc;
  background: #173b67;
  color: #ffffff;
}
.control-button.camera.captured {
  border-color: #198754;
  background: #198754;
  color: #ffffff;
}
.control-button:disabled { cursor: not-allowed; opacity: 0.5; }
:global(body.light-theme .control-button) { background: #ffffff; border-color: #cbd5e1; color: #334155; }
:global(body.light-theme .control-button.primary) { background: #0d6efd; border-color: #0d6efd; color: #ffffff; }
:global(body.light-theme .control-button.stop) { border-color: #fca5a5; color: #dc2626; }
:global(body.light-theme .control-button.stop.active) { background: #dc2626; color: #ffffff; }
:global(body.light-theme .control-button.camera) {
  background: #f0f7ff;
  border-color: #bfdbfe;
  color: #1d4ed8;
}
:global(body.light-theme .control-button.camera:hover:not(:disabled)) {
  background: #dbeafe;
  border-color: #93c5fd;
  color: #1e40af;
}
:global(body.light-theme .control-button.camera.captured) {
  background: #16a34a;
  border-color: #16a34a;
  color: #ffffff;
}

.control-hint { margin-left: auto; color: #617890; font-size: 0.58rem; }
@media (max-width: 600px) { .simulator-window.expanded { inset: 8px; } .control-hint { display: none; } }
</style>
