<template>
  <div class="analysis-page">
    <Header />

    <div
      class="main-container"
      :class="{
        'sidebar-collapsed': sidebarCollapsed,
        'right-panel-collapsed': rightPanelCollapsed,
      }"
    >
      <div class="sidebar-col">
        <Sidebar
          :key="`sidebar-${sidebarRefreshKey}`"
          :collapsed="sidebarCollapsed"
          :target-draft="targetDraft"
          @toggle-sidebar="toggleSidebar"
          @reset-target="resetTargetData"
          @reset-all="refreshData"
          @priority-change="currentTargetPriority = $event"
          @ai-analysis="handleAIAnalysis"
          @save-target="handleSaveTarget"
          @form-change="onSidebarFormChange"
        />
      </div>

      <div class="map-col">
        <div class="scenario-bar">
          <label>
            <span>Scenario</span>
            <select v-model="selectedScenarioId">
              <option value="">— เลือก scenario —</option>
              <option v-for="s in scenarios" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </label>
          <small v-if="mapError" class="map-error">{{ mapError }}</small>
          <small v-else-if="!selectedScenarioId">เลือก scenario เพื่อโหลดชั้นแผนที่แบบ desktop</small>
          <small v-else>{{ layerSummary }}</small>
        </div>

        <div class="map-shell">
          <MapDetailSidebar
            :collapsed="mapSidebarCollapsed"
            :targets="layerData.targets"
            :wings="layerData.wings"
            :transports="layerData.groundTransports"
            :detections="layerData.detections"
            :selected-target-id="selectedTargetId"
            :selected-coordinate-id="selectedCoordinateId"
            :selected-wing-id="selectedWingId"
            :selected-transport-id="selectedTransportId"
            @toggle="mapSidebarCollapsed = !mapSidebarCollapsed"
            @select-target="onSelectTarget"
            @select-wing="onSelectWing"
            @select-transport="onSelectTransport"
            @jmem-updated="onJmemUpdated"
            @jmem-error="onMapError"
            @view-ingress="onViewIngress"
            @detection-deleted="onDetectionDeleted"
            @select-detection="onSelectDetection"
            @detection-error="onMapError"
          />
          <div class="map-panel-wrap">
            <MapPanel
              ref="mapPanelRef"
              :key="`map-${mapRefreshKey}`"
              :scenario-id="selectedScenarioId"
              :selected-target-id="selectedTargetId"
              :selected-wing-id="selectedWingId"
              :selected-transport-id="selectedTransportId"
              :latitude="currentLatitude"
              :longitude="currentLongitude"
              :jmem-summary="jmemMapSummary"
              @select-target="onSelectTarget"
              @select-wing="onSelectWing"
              @select-transport="onSelectTransport"
              @select-depot="onSelectDepot"
              @select-team="onSelectTeam"
              @coords-picked="onCoordsPicked"
              @layers-loaded="onLayersLoaded"
              @target-created="() => displayResetNotice('สร้างเป้าหมายบนแผนที่แล้ว')"
              @targets-imported="(r) => displayResetNotice(`นำเข้าเป้าหมาย ${r?.successCount || 0} รายการแล้ว`)"
              @team-created="() => displayResetNotice('วางหน่วยบนแผนที่แล้ว')"
              @detection-complete="(r) => displayResetNotice(r?.message || 'Detection เสร็จแล้ว')"
              @error="onMapError"
            />
          </div>
        </div>
      </div>

      <div class="right-col">
        <RightPanel
          :key="`right-${rightRefreshKey}`"
          :collapsed="rightPanelCollapsed"
          :target-priority="currentTargetPriority"
          :form-data="currentFormData"
          :recommendations-data="jmemRecommendations"
          :analysis-text="jmemAnalysisText"
          :scenario-id="selectedScenarioId"
          :targets="layerData.targets"
          :selected-target-id="selectedTargetId"
          @toggle-panel="toggleRightPanel"
          @save-data="handleSaveData"
        />
      </div>
    </div>

    <div v-if="showResetNotice" class="reset-notice" role="status">
      <i class="bi bi-check-circle-fill"></i>
      <span>{{ resetNoticeMessage }}</span>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import Header from '../components/Header.vue'
import Sidebar from '../components/Sidebar.vue'
import MapPanel from '../components/MapPanel.vue'
import MapDetailSidebar from '../components/MapDetailSidebar.vue'
import RightPanel from '../components/RightPanel.vue'
import { apiJson, listResource, updateResource } from '../services/api'
import {
  buildJmemAnalysisText,
  formDraftToTargetUpdate,
  jmemProductsToRecommendations,
  targetApiToFormDraft,
} from '../utils/targetFormMapper'

const SCENARIO_STORAGE_KEY = 'weaponeering.activeScenarioId'

export default {
  name: 'AnalysisView',
  components: {
    Header,
    Sidebar,
    MapPanel,
    MapDetailSidebar,
    RightPanel,
  },
  setup() {
    const scenarios = ref([])
    const selectedScenarioId = ref(localStorage.getItem(SCENARIO_STORAGE_KEY) || '')
    const mapPanelRef = ref(null)
    const layerData = ref({
      targets: [],
      wings: [],
      depots: [],
      detections: [],
      teamMarkers: [],
      groundTransports: [],
    })
    const selectedTargetId = ref('')
    const selectedCoordinateId = ref('')
    const selectedWingId = ref('')
    const selectedTransportId = ref('')
    const mapError = ref('')
    const mapSidebarCollapsed = ref(false)

    const currentLatitude = ref(16.8661)
    const currentLongitude = ref(100.9948)
    const sidebarCollapsed = ref(true)
    const rightPanelCollapsed = ref(false)
    const currentTargetPriority = ref('')
    const currentFormData = ref({})
    const targetDraft = ref(null)
    const loadedTargetCard = ref(null)
    const jmemRecommendations = ref(null)
    const jmemAnalysisText = ref('')
    const sidebarRefreshKey = ref(0)
    const mapRefreshKey = ref(0)
    const rightRefreshKey = ref(0)
    const showResetNotice = ref(false)
    const resetNoticeMessage = ref('')
    let resetNoticeTimer = null

    const layerSummary = computed(() => {
      const d = layerData.value
      return `${d.targets.length} เป้า · ${d.wings.length} กองบิน · ${d.detections.length} detection · ${d.teamMarkers.length} หน่วย · ${d.groundTransports.length} ขนส่ง`
    })

    const jmemMapSummary = computed(() => {
      const list = jmemRecommendations.value
      if (!Array.isArray(list) || !list.length) return null
      const top = list[0]
      if (!top?.item) return null
      const pdPct = Number.isFinite(Number(top.pd))
        ? `${(Number(top.pd) * 100).toFixed(1)}%`
        : '—'
      return {
        productName: top.item,
        weightText: top.size || '',
        nRequired: Number(top.qty) || 1,
        pdText: pdPct,
        hint: 'วงสีบนแผนที่คือรัศมีผลกระทบของสินค้านี้จาก JMEM',
      }
    })

    const toggleSidebar = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
    }

    const toggleRightPanel = () => {
      rightPanelCollapsed.value = !rightPanelCollapsed.value
    }

    const handleAIAnalysis = async (analysisData) => {
      const done = analysisData?.done
      const fail = analysisData?.fail
      try {
        const targetId = selectedTargetId.value || analysisData?.id || targetDraft.value?.id
        if (!targetId) throw new Error('เลือกเป้าหมายก่อนบันทึกและวิเคราะห์')

        // 1) Save form edits first (like desktop edit-then-calc)
        const updateBody = formDraftToTargetUpdate(analysisData, loadedTargetCard.value)
        if (updateBody) {
          const saved = await updateResource('/targets', targetId, updateBody)
          loadedTargetCard.value = saved
          const draft = targetApiToFormDraft(saved, {
            lat: analysisData.latitude,
            lng: analysisData.longitude,
          })
          targetDraft.value = draft
          currentFormData.value = { ...currentFormData.value, ...(draft || {}) }
        }

        // 2) JMEM + AI product advisor (desktop product_advisor)
        const advice = await apiJson(`/jmem/targets/${targetId}/ai-advise?apply=true`, {
          method: 'POST',
        })
        if (advice?.jmem) {
          jmemRecommendations.value = jmemProductsToRecommendations(advice.jmem.products || [])
          jmemAnalysisText.value = [
            advice.analysis_text || '',
            '',
            '— JMEM summary —',
            buildJmemAnalysisText(targetDraft.value || currentFormData.value, advice.jmem),
          ]
            .filter(Boolean)
            .join('\n')
        }
        currentLatitude.value = analysisData.latitude ?? currentLatitude.value
        currentLongitude.value = analysisData.longitude ?? currentLongitude.value
        currentTargetPriority.value = analysisData.targetPriority || currentTargetPriority.value
        mapRefreshKey.value += 1
        displayResetNotice(
          advice?.recommendation?.product_name
            ? `AI แนะนำ ${advice.recommendation.product_name} (บันทึกแล้ว)`
            : 'คำนวณ JMEM / AI เสร็จแล้ว',
        )
        done?.()
      } catch (err) {
        mapError.value = err.message || 'วิเคราะห์ไม่สำเร็จ'
        fail?.(err)
      }
    }

    const handleSaveTarget = async (formPayload) => {
      const done = formPayload?.done
      const fail = formPayload?.fail
      try {
        const targetId = selectedTargetId.value || formPayload?.id || targetDraft.value?.id
        if (!targetId) throw new Error('เลือกเป้าหมายก่อนบันทึก')
        const updateBody = formDraftToTargetUpdate(formPayload, loadedTargetCard.value)
        const saved = await updateResource('/targets', targetId, updateBody)
        loadedTargetCard.value = saved
        const draft = targetApiToFormDraft(saved, {
          lat: formPayload.latitude,
          lng: formPayload.longitude,
        })
        targetDraft.value = draft
        currentFormData.value = { ...currentFormData.value, ...(draft || {}) }
        if (draft?.latitude != null) currentLatitude.value = draft.latitude
        if (draft?.longitude != null) currentLongitude.value = draft.longitude

        // Recalculate JMEM with saved values
        const jmem = await apiJson(`/jmem/targets/${targetId}`).catch(() => null)
        if (jmem?.products) {
          jmemRecommendations.value = jmemProductsToRecommendations(jmem.products)
          jmemAnalysisText.value = buildJmemAnalysisText(draft, jmem)
        }
        mapRefreshKey.value += 1
        displayResetNotice('บันทึกข้อมูลเป้าหมายและคำนวณ JMEM แล้ว')
        done?.()
      } catch (err) {
        mapError.value = err.message || 'บันทึกไม่สำเร็จ'
        fail?.(err)
      }
    }

    const handleSaveData = (formData) => {
      currentFormData.value = formData || {}
      displayResetNotice('บันทึกข้อมูลในเครื่องแล้ว')
    }

    const displayResetNotice = (message) => {
      resetNoticeMessage.value = message
      showResetNotice.value = true
      if (resetNoticeTimer) window.clearTimeout(resetNoticeTimer)
      resetNoticeTimer = window.setTimeout(() => {
        showResetNotice.value = false
      }, 2200)
    }

    const clearSelection = () => {
      selectedTargetId.value = ''
      selectedCoordinateId.value = ''
      selectedWingId.value = ''
      selectedTransportId.value = ''
      targetDraft.value = null
      loadedTargetCard.value = null
      jmemRecommendations.value = null
      jmemAnalysisText.value = ''
    }

    const onSidebarFormChange = (form) => {
      currentFormData.value = { ...currentFormData.value, ...(form || {}) }
    }

    const loadTargetIntoPanels = async (marker) => {
      const targetId = marker?.targetCardId
      if (!targetId) return
      try {
        const [card, jmem] = await Promise.all([
          apiJson(`/targets/${targetId}`),
          apiJson(`/jmem/targets/${targetId}`).catch(() => null),
        ])
        const draft = targetApiToFormDraft(card, marker)
        loadedTargetCard.value = card
        targetDraft.value = draft
        currentFormData.value = { ...currentFormData.value, ...(draft || {}) }
        if (draft?.targetPriority) {
          currentTargetPriority.value = draft.targetPriority
        }
        if (jmem?.products?.length) {
          jmemRecommendations.value = jmemProductsToRecommendations(jmem.products)
          jmemAnalysisText.value = buildJmemAnalysisText(draft, jmem)
        } else {
          jmemRecommendations.value = []
          jmemAnalysisText.value = buildJmemAnalysisText(draft, jmem)
        }
        rightPanelCollapsed.value = false
        displayResetNotice(`โหลดข้อมูลเป้าหมาย: ${card.label || targetId}`)
      } catch (err) {
        mapError.value = err.message || 'โหลดข้อมูลเป้าหมายไม่สำเร็จ'
      }
    }

    const onSelectTarget = (t) => {
      selectedTargetId.value = t.targetCardId || ''
      selectedCoordinateId.value = t.coordinateId || ''
      selectedWingId.value = ''
      selectedTransportId.value = ''
      if (t.lat != null) currentLatitude.value = t.lat
      if (t.lng != null) currentLongitude.value = t.lng
      loadTargetIntoPanels(t)
    }

    const onSelectWing = (w) => {
      selectedWingId.value = w.entityId || ''
      selectedTargetId.value = ''
      selectedCoordinateId.value = ''
      selectedTransportId.value = ''
      targetDraft.value = null
      jmemRecommendations.value = null
      jmemAnalysisText.value = ''
      if (w.lat != null) currentLatitude.value = w.lat
      if (w.lng != null) currentLongitude.value = w.lng
    }

    const onSelectDepot = (d) => {
      if (d.wingId) {
        selectedWingId.value = d.wingId
        selectedTargetId.value = ''
        selectedCoordinateId.value = ''
        selectedTransportId.value = ''
        targetDraft.value = null
        jmemRecommendations.value = null
        jmemAnalysisText.value = ''
      }
      if (d.lat != null) currentLatitude.value = d.lat
      if (d.lng != null) currentLongitude.value = d.lng
    }

    const onSelectTransport = (r) => {
      selectedTransportId.value = r.id || ''
      selectedTargetId.value = ''
      selectedCoordinateId.value = ''
      selectedWingId.value = ''
      targetDraft.value = null
      jmemRecommendations.value = null
      jmemAnalysisText.value = ''
    }

    const onJmemUpdated = (payload) => {
      const top = payload?.products?.[0]
      if (payload?.products?.length) {
        jmemRecommendations.value = jmemProductsToRecommendations(payload.products)
        jmemAnalysisText.value = buildJmemAnalysisText(targetDraft.value || currentFormData.value, payload)
      }
      mapPanelRef.value?.reloadLayers?.()
      if (top) {
        displayResetNotice(
          `JMEM: ${top.product_name} · Pd ${(top.pd_base * 100).toFixed(1)}% · N=${top.n_required}`,
        )
      } else {
        displayResetNotice('อัปเดตสินค้า/JMEM แล้ว')
      }
    }

    const onViewIngress = (payload) => {
      mapPanelRef.value?.highlightIngress?.(payload)
    }

    const onDetectionDeleted = async (item) => {
      await mapPanelRef.value?.reloadLayers?.()
      displayResetNotice(`ลบอาคาร detection แล้ว${item?.label ? `: ${item.label}` : ''}`)
    }

    const onSelectDetection = (item) => {
      mapPanelRef.value?.highlightDetection?.(item?.id)
    }

    const onSelectTeam = (m) => {
      if (m.lat != null) currentLatitude.value = m.lat
      if (m.lng != null) currentLongitude.value = m.lng
      displayResetNotice(`เลือกหน่วย ${m.label || m.side}`)
    }

    const onCoordsPicked = (coords) => {
      currentLatitude.value = coords.lat
      currentLongitude.value = coords.lng
      currentFormData.value = {
        ...currentFormData.value,
        latitude: coords.lat,
        longitude: coords.lng,
      }
      displayResetNotice(`หยิบพิกัด ${coords.lat.toFixed(5)}, ${coords.lng.toFixed(5)}`)
    }

    const onLayersLoaded = (data) => {
      layerData.value = data || layerData.value
      mapError.value = ''
      maybeSelectDefaultTarget(layerData.value.targets)
    }

    const uniqueTargetMarkers = (targets = []) => {
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

    const maybeSelectDefaultTarget = (targets = []) => {
      const unique = uniqueTargetMarkers(targets)
      if (!unique.length) return
      const stillValid = unique.some((t) => t.targetCardId === selectedTargetId.value)
      if (selectedTargetId.value && stillValid) return
      onSelectTarget(unique[0])
    }

    const onMapError = (message) => {
      mapError.value = message || 'ข้อผิดพลาดแผนที่'
    }

    const resetTargetData = () => {
      currentTargetPriority.value = ''
      currentFormData.value = {}
      targetDraft.value = null
      jmemRecommendations.value = null
      jmemAnalysisText.value = ''
      clearSelection()
      sidebarRefreshKey.value += 1
      displayResetNotice('ล้างข้อมูลเป้าหมายและกลับสู่ค่าเริ่มต้นแล้ว')
    }

    const refreshData = () => {
      currentLatitude.value = 16.8661
      currentLongitude.value = 100.9948
      rightPanelCollapsed.value = false
      currentTargetPriority.value = ''
      currentFormData.value = {}
      targetDraft.value = null
      jmemRecommendations.value = null
      jmemAnalysisText.value = ''
      clearSelection()
      sidebarRefreshKey.value += 1
      mapRefreshKey.value += 1
      rightRefreshKey.value += 1
      displayResetNotice('ล้างข้อมูลทั้งหมดและกลับสู่ค่าเริ่มต้นแล้ว')
    }

    const loadScenarios = async () => {
      try {
        scenarios.value = (await listResource('/scenarios')) || []
        if (
          selectedScenarioId.value &&
          !scenarios.value.some((s) => s.id === selectedScenarioId.value)
        ) {
          selectedScenarioId.value = ''
        }
        if (!selectedScenarioId.value && scenarios.value.length === 1) {
          selectedScenarioId.value = scenarios.value[0].id
        }
      } catch (err) {
        mapError.value = err.message || 'โหลด scenarios ไม่สำเร็จ'
      }
    }

    onMounted(loadScenarios)

    watch(selectedScenarioId, (id) => {
      if (id) localStorage.setItem(SCENARIO_STORAGE_KEY, id)
      else localStorage.removeItem(SCENARIO_STORAGE_KEY)
      clearSelection()
    })

    onUnmounted(() => {
      if (resetNoticeTimer) window.clearTimeout(resetNoticeTimer)
    })

    return {
      scenarios,
      selectedScenarioId,
      mapPanelRef,
      layerData,
      layerSummary,
      selectedTargetId,
      selectedCoordinateId,
      selectedWingId,
      selectedTransportId,
      mapError,
      mapSidebarCollapsed,
      currentLatitude,
      currentLongitude,
      sidebarCollapsed,
      rightPanelCollapsed,
      currentTargetPriority,
      currentFormData,
      targetDraft,
      jmemRecommendations,
      jmemAnalysisText,
      jmemMapSummary,
      sidebarRefreshKey,
      mapRefreshKey,
      rightRefreshKey,
      showResetNotice,
      resetNoticeMessage,
      toggleSidebar,
      toggleRightPanel,
      handleAIAnalysis,
      handleSaveTarget,
      handleSaveData,
      resetTargetData,
      refreshData,
      onSelectTarget,
      onSelectWing,
      onSelectDepot,
      onSelectTransport,
      onSelectTeam,
      onCoordsPicked,
      onLayersLoaded,
      onMapError,
      onJmemUpdated,
      onViewIngress,
      onDetectionDeleted,
      onSelectDetection,
      onSidebarFormChange,
      displayResetNotice,
    }
  },
}
</script>

<style scoped>
.analysis-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg);
  color: var(--text);
}

.main-container {
  --left-column: 300px;
  --right-column: 350px;
  display: grid;
  grid-template-columns: var(--left-column) minmax(0, 1fr) var(--right-column);
  gap: 15px;
  padding: 15px;
  flex: 1;
  overflow: hidden;
  transition: grid-template-columns 0.24s ease;
}

.main-container.sidebar-collapsed {
  --left-column: 64px;
}

.main-container.right-panel-collapsed {
  --right-column: 64px;
}

.sidebar-col,
.map-col,
.right-col {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.sidebar-col {
  background: var(--panel-bg);
}

.map-col {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  background: var(--panel-bg);
}

.scenario-bar {
  flex: 0 0 auto;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  padding: 8px 10px;
  border-bottom: 1px solid var(--border);
  background: rgba(13, 110, 253, 0.06);
}

.scenario-bar label {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 0.78rem;
}

.scenario-bar select {
  min-width: 180px;
  padding: 5px 8px;
  border: 1px solid var(--border);
  border-radius: 7px;
  background: var(--control-bg);
  color: var(--text);
}

.scenario-bar small {
  color: var(--muted);
  font-size: 0.7rem;
}

.map-error {
  color: #f87171 !important;
}

.map-shell {
  display: flex;
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
}

.map-panel-wrap {
  position: relative;
  flex: 1 1 0;
  min-width: 0;
  min-height: 0;
  height: auto;
  overflow: hidden;
}

.map-panel-wrap :deep(.map-panel-root) {
  position: absolute;
  inset: 0;
  width: auto;
  height: auto;
  min-height: 0;
}

.map-panel-wrap :deep(.map-panel) {
  position: relative;
  inset: auto;
  width: 100%;
  height: 100%;
  min-height: 0;
}

.right-col {
  background: var(--panel-bg);
}

.reset-notice {
  position: fixed;
  right: 22px;
  bottom: 22px;
  z-index: 1250;
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 46px;
  padding: 10px 15px;
  border: 1px solid rgba(25, 135, 84, 0.62);
  border-radius: 10px;
  background: #102c21;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.38);
  color: #81d9aa;
  font-size: 0.82rem;
  font-weight: 500;
  animation: resetNoticeIn 0.22s ease-out;
}

:global(body.light-theme .analysis-page) {
  background: #edf3f9;
}
:global(body.light-theme .main-container) {
  background: #edf3f9;
}
:global(body.light-theme .sidebar-col),
:global(body.light-theme .map-col),
:global(body.light-theme .right-col) {
  border: 1px solid #cad7e4;
  background: #ffffff;
  box-shadow: 0 5px 16px rgba(31, 65, 98, 0.1);
}
:global(body.light-theme .reset-notice) {
  border-color: #75bd96;
  background: #ebf8f1;
  color: #147044;
}

@keyframes resetNoticeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1400px) {
  .main-container {
    --left-column: 250px;
    --right-column: 300px;
  }
}

@media (max-width: 992px) {
  .analysis-page {
    height: 100dvh;
    min-height: 100dvh;
    overflow: hidden;
  }

  .main-container {
    display: grid;
    grid-template-columns: 270px minmax(440px, 1fr) 310px;
    gap: 10px;
    padding: 10px;
    overflow-x: auto;
    overflow-y: hidden;
    overscroll-behavior-x: contain;
    scroll-snap-type: x proximity;
    -webkit-overflow-scrolling: touch;
  }

  .main-container.sidebar-collapsed {
    grid-template-columns: 64px minmax(440px, 1fr) 310px;
  }

  .main-container.right-panel-collapsed {
    grid-template-columns: 270px minmax(440px, 1fr) 64px;
  }

  .main-container.sidebar-collapsed.right-panel-collapsed {
    grid-template-columns: 64px minmax(440px, 1fr) 64px;
  }

  .sidebar-col,
  .map-col,
  .right-col {
    min-width: 0;
    min-height: 0;
    max-height: none;
    overflow: hidden;
    scroll-snap-align: start;
  }

  .reset-notice {
    right: 12px;
    bottom: 12px;
    left: 12px;
    justify-content: center;
  }
}

@media (max-width: 600px) {
  .main-container {
    grid-template-columns: 270px minmax(420px, 1fr) 300px;
    gap: 8px;
    padding: 6px;
  }

  .main-container.sidebar-collapsed {
    grid-template-columns: 64px minmax(420px, 1fr) 300px;
  }

  .main-container.right-panel-collapsed {
    grid-template-columns: 270px minmax(420px, 1fr) 64px;
  }

  .main-container.sidebar-collapsed.right-panel-collapsed {
    grid-template-columns: 64px minmax(420px, 1fr) 64px;
  }

  .sidebar-col,
  .map-col,
  .right-col {
    border-radius: 10px;
  }
}
</style>
