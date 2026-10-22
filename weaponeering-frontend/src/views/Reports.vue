<template>
  <div class="reports-page">
    <Header />
    
    <div class="reports-container">
      <div class="container-fluid report-shell">
        <div class="report-top-row">
          <div class="report-heading">
            <div>
              <span class="report-kicker">REPORTING CENTER</span>
              <h2><i class="bi bi-database-check"></i> Report Data Log</h2>
              <p>รายการเป้าหมายและประวัติการวิเคราะห์ข้อมูล</p>
            </div>
            <span class="report-live"><i></i> DATA ONLINE</span>
          </div>

          <section class="summary-bar dashboard-panel dashboard-panel-top" aria-label="สรุปข้อมูลเป้าหมาย">
            <header class="dashboard-panel-header">
              <div><small>สรุปข้อมูลเป้าหมาย</small><strong><i class="bi bi-pie-chart me-1"></i>ภาพรวมเป้าหมาย</strong></div>
              <span><i class="bi bi-activity"></i> LIVE</span>
            </header>

            <div class="dashboard-content">
              <div class="dashboard-chart-group importance-dashboard">
                <article class="source-rings-chart importance-rings-chart" aria-label="สัดส่วนความสำคัญเป้าหมาย">
                  <svg viewBox="0 0 150 150" role="img">
                    <g v-for="(level, index) in importanceStats" :key="level.key">
                      <circle class="source-ring-track" cx="75" cy="75" :r="60 - (index * 13)" />
                      <circle
                        class="source-ring-progress"
                        cx="75" cy="75"
                        :r="60 - (index * 13)"
                        pathLength="100"
                        :stroke="level.color"
                        :stroke-dasharray="`${level.percent} ${100 - level.percent}`"
                      />
                    </g>
                  </svg>
                  <div class="source-rings-center importance-rings-center">
                    <strong>{{ dashboardTotal }}</strong>
                    <span>เป้าหมายทั้งหมด</span>
                  </div>
                </article>

                <div class="dashboard-legend">
                  <span class="legend-section-title"><i class="bi bi-flag-fill"></i> ความสำคัญ</span>
                  <div class="legend-row key-legend">
                    <span class="legend-icon"><i class="bi bi-exclamation-diamond"></i></span>
                    <div><small>สำคัญสูง</small><strong>{{ importanceCounts.key }} รายการ</strong></div>
                    <em>{{ importancePercent.key }}%</em>
                  </div>
                  <div class="legend-row medium-legend">
                    <span class="legend-icon"><i class="bi bi-dash-circle"></i></span>
                    <div><small>สำคัญ</small><strong>{{ importanceCounts.medium }} รายการ</strong></div>
                    <em>{{ importancePercent.medium }}%</em>
                  </div>
                  <div class="legend-row general-legend">
                    <span class="legend-icon"><i class="bi bi-check-circle"></i></span>
                    <div><small>ทั่วไป</small><strong>{{ importanceCounts.general }} รายการ</strong></div>
                    <em>{{ importancePercent.general }}%</em>
                  </div>
                  <div class="legend-updated">
                    <i class="bi bi-clock-history"></i>
                    <div><small>อัปเดตล่าสุด</small><strong>{{ lastUpdated }}</strong></div>
                  </div>
                </div>
              </div>

              <div class="dashboard-chart-group source-dashboard">
                <article class="source-rings-chart" aria-label="สัดส่วนแหล่งที่มาเป้าหมาย">
                  <svg viewBox="0 0 150 150" role="img">
                    <g v-for="(source, index) in sourceStats" :key="source.name">
                      <circle class="source-ring-track" cx="75" cy="75" :r="62 - (index * 9)" />
                      <circle
                        class="source-ring-progress"
                        cx="75" cy="75"
                        :r="62 - (index * 9)"
                        pathLength="100"
                        :stroke="source.color"
                        :stroke-dasharray="`${source.percent} ${100 - source.percent}`"
                      />
                    </g>
                  </svg>
                  <div class="source-rings-center">
                    <strong>{{ dashboardTotal }}</strong>
                    <span>รวมทุกแหล่ง</span>
                  </div>
                </article>

                <div class="source-summary">
                  <span class="legend-section-title"><i class="bi bi-broadcast-pin"></i> แหล่งที่มา</span>
                  <div v-for="source in sourceStats" :key="source.name" class="source-summary-row">
                    <span class="source-color" :style="{ backgroundColor: source.color, color: source.color }"></span>
                    <i :class="sourceIcon(source.name)"></i>
                    <span :title="source.name">{{ source.name }}</span>
                    <strong>{{ source.count }}</strong>
                    <em :style="{ color: source.color }">{{ source.percent }}%</em>
                  </div>
                </div>
              </div>

              <div class="dashboard-chart-group weapon-dashboard" aria-label="สรุปการใช้อาวุธ">
                <div class="weapon-dashboard-head">
                  <span class="legend-section-title"><i class="bi bi-rocket-takeoff"></i> สรุปการใช้อาวุธ</span>
                  <small>{{ weaponSummary.targetCount }} เป้าหมาย · {{ weaponSummary.aimPointCount }} จุดเล็ง</small>
                </div>

                <div class="weapon-stat-grid">
                  <div class="weapon-stat">
                    <small>อาวุธรวม</small>
                    <strong>{{ formatNumber(weaponSummary.totals.quantity) }}<span>ลูก</span></strong>
                  </div>
                  <div class="weapon-stat">
                    <small>ชนิดสินค้า</small>
                    <strong>{{ weaponSummary.productCount }}<span>รายการ</span></strong>
                  </div>
                  <div class="weapon-stat" :title="`${formatNumber(weaponSummary.totals.weightLb)} lb`">
                    <small>น้ำหนักรวม</small>
                    <strong>{{ formatWeight(weaponSummary.totals.weightLb) }}<span>lb</span></strong>
                  </div>
                  <div class="weapon-stat">
                    <small>ค่าใช้จ่ายรวม</small>
                    <strong>{{ weaponSummary.hasCost ? formatNumber(weaponSummary.totals.cost) : '—' }}</strong>
                  </div>
                </div>

                <div class="weapon-product-list">
                  <div v-if="loading && !weaponSummary.productCount" class="weapon-empty">
                    <i class="bi bi-hourglass-split"></i> กำลังคำนวณ…
                  </div>
                  <div v-else-if="!weaponSummary.productCount" class="weapon-empty">
                    <i class="bi bi-inbox"></i> ยังไม่มีสินค้าที่จัดสรรให้เป้าหมาย
                  </div>
                  <template v-else>
                    <div
                      v-for="product in weaponSummary.topProducts"
                      :key="product.productId || product.productName"
                      class="weapon-product-row"
                      :title="`${product.productName}: ${product.quantity} ลูก · ${product.targetCount} เป้าหมาย · ${product.aimPoints} จุดเล็ง`"
                    >
                      <span class="weapon-product-name">{{ product.productName }}</span>
                      <span class="weapon-product-bar">
                        <i :style="{ width: `${product.percent}%`, backgroundColor: product.color, color: product.color }"></i>
                      </span>
                      <strong>{{ formatNumber(product.quantity) }}</strong>
                      <em :style="{ color: product.color }">{{ product.percent }}%</em>
                    </div>
                    <small v-if="weaponSummary.moreProducts" class="weapon-more">
                      + อีก {{ weaponSummary.moreProducts }} รายการ (ดูใน PDF/Word ภาพรวม)
                    </small>
                  </template>
                </div>

                <div v-if="weaponSummary.targetCount" class="weapon-selection">
                  <div class="weapon-selection-bar">
                    <i
                      v-for="item in weaponSummary.selection.filter(s => s.count)"
                      :key="item.key"
                      :style="{ width: `${item.percent}%`, backgroundColor: item.color }"
                      :title="`${item.label}: ${item.count}`"
                    ></i>
                  </div>
                  <div class="weapon-selection-legend">
                    <span v-for="item in weaponSummary.selection.filter(s => s.count)" :key="item.key">
                      <b :style="{ backgroundColor: item.color }"></b>{{ item.label }} {{ item.count }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>

        <section class="filter-bar" aria-label="ค้นหาและกรองเป้าหมาย">
          <div class="filter-field">
            <label for="scenario-filter"><i class="bi bi-folder2-open"></i> Scenario</label>
            <select
              id="scenario-filter"
              class="form-select form-select-sm scenario-select"
              :value="selectedScenarioId"
              :disabled="loading"
              @change="onScenarioChange"
            >
              <option value="">— เลือก Scenario —</option>
              <option v-for="s in scenarios" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>
          <div class="filter-field">
            <label for="source-filter"><i class="bi bi-broadcast-pin"></i> แหล่งที่มาเป้าหมาย</label>
            <div class="custom-filter-dropdown">
              <button id="source-filter" type="button" class="custom-filter-toggle" @click.stop="toggleFilterDropdown('source')">
                <i :class="selectedFilterIcon('source')"></i><span>{{ selectedFilterLabel('source') }}</span><i class="bi bi-chevron-down"></i>
              </button>
              <div v-if="openFilterDropdown === 'source'" class="filter-dropdown-menu" @click.stop>
                <button type="button" :class="{ active: !filters.source }" @click="selectFilter('source', '')"><i class="bi bi-grid"></i><span>ทั้งหมด</span></button>
                <button v-for="source in sourceOptions" :key="source" type="button" :class="{ active: filters.source === source }" @click="selectFilter('source', source)">
                  <i :class="sourceIcon(source)"></i><span>{{ source }}</span><i v-if="filters.source === source" class="bi bi-check-lg"></i>
                </button>
              </div>
            </div>
          </div>
          <div class="filter-field">
            <label for="type-filter"><i class="bi bi-buildings"></i> ประเภทเป้าหมาย</label>
            <div class="custom-filter-dropdown">
              <button id="type-filter" type="button" class="custom-filter-toggle" @click.stop="toggleFilterDropdown('type')">
                <i :class="selectedFilterIcon('type')"></i><span>{{ selectedFilterLabel('type') }}</span><i class="bi bi-chevron-down"></i>
              </button>
              <div v-if="openFilterDropdown === 'type'" class="filter-dropdown-menu" @click.stop>
                <button type="button" :class="{ active: !filters.type }" @click="selectFilter('type', '')"><i class="bi bi-grid"></i><span>ทั้งหมด</span></button>
                <button v-for="type in typeOptions" :key="type" type="button" :class="{ active: filters.type === type }" @click="selectFilter('type', type)">
                  <i :class="targetTypeIcon(type)"></i><span>{{ type }}</span><i v-if="filters.type === type" class="bi bi-check-lg"></i>
                </button>
              </div>
            </div>
          </div>
          <div class="filter-field">
            <label for="importance-filter"><i class="bi bi-flag"></i> ความสำคัญเป้าหมาย</label>
            <div class="custom-filter-dropdown">
              <button id="importance-filter" type="button" class="custom-filter-toggle" @click.stop="toggleFilterDropdown('importance')">
                <i :class="selectedFilterIcon('importance')"></i><span>{{ selectedFilterLabel('importance') }}</span><i class="bi bi-chevron-down"></i>
              </button>
              <div v-if="openFilterDropdown === 'importance'" class="filter-dropdown-menu" @click.stop>
                <button type="button" :class="{ active: !filters.importance }" @click="selectFilter('importance', '')"><i class="bi bi-grid"></i><span>ทั้งหมด</span></button>
                <button v-for="level in importanceOptions" :key="level.value" type="button" :class="{ active: filters.importance === level.value }" @click="selectFilter('importance', level.value)">
                  <i :class="level.icon"></i><span>{{ level.label }}</span><i v-if="filters.importance === level.value" class="bi bi-check-lg"></i>
                </button>
              </div>
            </div>
          </div>
          <div class="filter-field date-filter">
            <label><i class="bi bi-calendar-range"></i> วัน เวลา</label>
            <div class="date-range">
              <div class="date-input-wrap" @pointerdown.prevent="openDatePicker">
                <i class="bi bi-calendar-event"></i>
                <input v-model="filters.startDate" type="date" lang="th-TH" :class="{ 'is-empty': !filters.startDate }" aria-label="วันที่เริ่มต้น รูปแบบวันเดือนปี" />
                <span v-if="!filters.startDate" class="date-format-placeholder">วว/ดด/ปป</span>
              </div>
              <span>–</span>
              <div class="date-input-wrap" @pointerdown.prevent="openDatePicker">
                <i class="bi bi-calendar-check"></i>
                <input v-model="filters.endDate" type="date" lang="th-TH" :class="{ 'is-empty': !filters.endDate }" aria-label="วันที่สิ้นสุด รูปแบบวันเดือนปี" />
                <span v-if="!filters.endDate" class="date-format-placeholder">วว/ดด/ปป</span>
              </div>
            </div>
          </div>
          <div class="filter-field search-filter">
            <label for="text-search"><i class="bi bi-search"></i> ค้นหา</label>
            <div class="search-input-wrap">
              <i class="bi bi-search"></i>
              <input id="text-search" v-model.trim="filters.query" type="search" placeholder="ค้นหาชื่อเป้าหมาย..." />
            </div>
          </div>
          <button type="button" class="clear-filter-button" :disabled="!hasActiveFilters" @click="clearFilters">
            <i class="bi bi-arrow-counterclockwise"></i><span>เคลียร์ฟิลเตอร์</span>
          </button>
        </section>

        <div class="row report-data-row">
          <div class="col-12">
            <div class="card">
              <div class="card-header bg-primary text-white report-list-header">
                <h5 class="card-title mb-0">
                  <i class="bi bi-list-ul"></i> รายการเป้าหมาย
                  <small v-if="loading" class="ms-2 opacity-75">กำลังโหลด…</small>
                  <small v-else-if="loadError" class="ms-2 text-warning">{{ loadError }}</small>
                </h5>
                <div class="scenario-summary-actions" title="สรุปสินค้า/อาวุธที่ใช้และจำนวนรวมของทุกเป้าหมายใน Scenario">
                  <span><i class="bi bi-clipboard-data"></i> รายงานภาพรวม Scenario</span>
                  <button
                    type="button"
                    class="btn btn-sm btn-light"
                    :disabled="!selectedScenarioId || loading || !!exportingScenario"
                    @click="exportScenarioSummary('pdf')"
                  >
                    <i class="bi" :class="exportingScenario === 'pdf' ? 'bi-hourglass-split' : 'bi-file-earmark-pdf'"></i> PDF
                  </button>
                  <button
                    type="button"
                    class="btn btn-sm btn-light"
                    :disabled="!selectedScenarioId || loading || !!exportingScenario"
                    @click="exportScenarioSummary('word')"
                  >
                    <i class="bi" :class="exportingScenario === 'word' ? 'bi-hourglass-split' : 'bi-file-earmark-word'"></i> Word
                  </button>
                </div>
              </div>
              <div class="card-body">
                <div v-if="loading" class="alert alert-secondary">
                  กำลังโหลดเป้าหมายจากระบบ…
                </div>
                <div v-else-if="!selectedScenarioId" class="alert alert-warning">
                  เลือก Scenario เพื่อแสดงรายการเป้าหมายสำหรับออกรายงาน
                </div>
                <div v-else-if="filteredReports.length === 0" class="alert alert-info">
                  {{ reports.length === 0
                    ? 'ยังไม่มีเป้าหมายใน Scenario นี้ — เพิ่มเป้าหมายในหน้า Analysis ก่อน'
                    : 'ไม่พบข้อมูลที่ตรงกับตัวกรอง' }}
                </div>
                <div v-else class="report-table-block">
                  <div class="table-responsive">
                    <table class="table data-log-table">
                    <thead class="table-light">
                      <tr>
                        <th><i class="bi bi-list-ol"></i> ลำดับ</th>
                        <th><i class="bi bi-crosshair"></i> เป้าหมาย</th>
                        <th><i class="bi bi-broadcast-pin"></i> แหล่งที่มา</th>
                        <th><i class="bi bi-buildings"></i> ประเภท</th>
                        <th><i class="bi bi-flag"></i> ความสำคัญ</th>
                        <th><i class="bi bi-calendar3"></i> วันที่</th>
                        <th><span class="visually-hidden">เมนูรายการ</span></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(report, idx) in paginatedReports" :key="report.id" title="เปิดผลการวิเคราะห์" @click="openAnalysisResult(report)">
                        <td class="sequence-cell"><span>{{ ((currentPage - 1) * effectivePageSize) + idx + 1 }}</span></td>
                        <td class="target-cell">
                          <div class="target-data">
                            <span class="table-data-icon target-icon"><i :class="targetTypeIcon(report.type)"></i></span>
                            <div><strong>{{ report.target }}</strong><small>ID: {{ report.shortId || String(report.id).slice(0, 8) }}</small></div>
                          </div>
                        </td>
                        <td><span class="data-with-icon"><span class="table-data-icon source-icon"><i :class="sourceIcon(report.source)"></i></span>{{ report.source }}</span></td>
                        <td><span class="data-with-icon"><span class="table-data-icon type-icon"><i :class="targetTypeIcon(report.type)"></i></span>{{ report.type }}</span></td>
                        <td><span class="importance-badge" :class="report.importance"><i :class="importanceIcon(report.importance)"></i>{{ importanceLabels[report.importance] }}</span></td>
                        <td><span class="date-pill"><i class="bi bi-calendar3"></i>{{ formatDate(report.date) }}</span></td>
                        <td class="action-cell">
                          <div class="row-actions">
                          <button class="btn btn-sm btn-outline-primary" @click.stop="viewReport(report.id)">
                            <i class="bi bi-eye"></i> ดู
                          </button>
                          <div class="dropdown report-export-dropdown">
                            <button
                              class="btn btn-sm btn-outline-success dropdown-toggle"
                              type="button"
                              data-bs-toggle="dropdown"
                              data-bs-boundary="viewport"
                              data-bs-popper-config='{"strategy":"fixed"}'
                              aria-expanded="false"
                              aria-label="ส่งออกรายงาน"
                              @click.stop
                            >
                              <i class="bi bi-download"></i> นำออก
                            </button>
                            <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end export-format-dropdown" @click.stop>
                              <li class="export-dropdown-header">
                                <strong>รูปแบบเอกสาร</strong>
                                <small>เลือกประเภทไฟล์สำหรับรายงานฉบับทางการ</small>
                              </li>
                              <li>
                                <button class="dropdown-item export-format-option" type="button" @click.stop="exportReports('pdf', report)">
                                  <span class="export-format-icon pdf"><i class="bi bi-file-earmark-pdf"></i></span>
                                  <span><strong>PDF</strong><small>เอกสารพร้อมพิมพ์และจัดเก็บ</small></span>
                                </button>
                              </li>
                              <li>
                                <button class="dropdown-item export-format-option" type="button" @click.stop="exportReports('word', report)">
                                  <span class="export-format-icon word"><i class="bi bi-file-earmark-word"></i></span>
                                  <span><strong>Word</strong><small>เอกสารสำหรับแก้ไขและนำเสนอ</small></span>
                                </button>
                              </li>
                            </ul>
                          </div>
                          <button class="btn btn-sm btn-outline-danger" @click.stop="requestDeleteReport(report)">
                            <i class="bi bi-trash"></i> ลบ
                          </button>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                    </table>
                  </div>
                  <nav class="table-pagination" aria-label="เปลี่ยนหน้ารายการบันทึกข้อมูล">
                    <div class="pagination-info">
                      <span class="pagination-summary"><i class="bi bi-list-check"></i> แสดง {{ paginationStart }}–{{ paginationEnd }} จาก {{ filteredReports.length }} รายการ</span>
                      <label class="page-size-control">
                        <span>แสดงต่อหน้า</span>
                        <input v-model.number="pageSize" class="pagination-size-input" type="number" min="1" max="100" inputmode="numeric" aria-label="จำนวนรายการต่อหน้า" @change="normalizePageSize" @keydown.enter.prevent="normalizePageSize" />
                        <span>รายการ</span>
                      </label>
                    </div>
                    <div class="pagination-buttons">
                      <button type="button" :disabled="currentPage === 1" aria-label="หน้าก่อนหน้า" @click="setPage(currentPage - 1)"><i class="bi bi-chevron-left"></i></button>
                      <button v-for="page in pageNumbers" :key="page" type="button" :class="{ active: currentPage === page }" :aria-current="currentPage === page ? 'page' : undefined" @click="setPage(page)">{{ page }}</button>
                      <button type="button" :disabled="currentPage === totalPages" aria-label="หน้าถัดไป" @click="setPage(currentPage + 1)"><i class="bi bi-chevron-right"></i></button>
                    </div>
                  </nav>
                </div>
              </div>
            </div>
          </div>

        </div>

        <div v-if="selectedReport" class="analysis-modal-backdrop" @click.self="closeAnalysisResult">
          <section class="analysis-result-modal" role="dialog" aria-modal="true" aria-labelledby="analysis-result-title">
            <header class="analysis-result-header">
              <div class="analysis-result-title">
                <span><i class="bi bi-cpu"></i></span>
                <div><small>AI ANALYSIS</small><h3 id="analysis-result-title">ผลการวิเคราะห์เป้าหมาย</h3></div>
              </div>
              <button type="button" class="analysis-modal-close" aria-label="ปิด" @click="closeAnalysisResult"><i class="bi bi-x-lg"></i></button>
            </header>

            <div class="analysis-result-body">
              <div class="analysis-target-banner">
                <span class="analysis-target-icon"><i :class="targetTypeIcon(selectedReport.type)"></i></span>
                <div><small>TARGET ID: {{ selectedReport.shortId || String(selectedReport.id).slice(0, 8) }}</small><strong>{{ selectedReport.target }}</strong><span>{{ selectedReport.source }} · {{ selectedReport.type }}</span></div>
                <span class="importance-badge" :class="selectedReport.importance"><i :class="importanceIcon(selectedReport.importance)"></i>{{ importanceLabels[selectedReport.importance] }}</span>
              </div>

              <div class="analysis-metric-grid">
                <article><span class="metric-icon confidence"><i class="bi bi-speedometer2"></i></span><div><small>AI Confidence</small><strong>{{ selectedReport.confidence }}%</strong></div></article>
                <article><span class="metric-icon weapon"><i class="bi bi-bullseye"></i></span><div><small>Recommendation</small><strong>{{ selectedReport.recommendation }}</strong></div></article>
                <article><span class="metric-icon probability"><i class="bi bi-percent"></i></span><div><small>Pk</small><strong>{{ selectedReport.pk }}</strong></div></article>
                <article><span class="metric-icon accuracy"><i class="bi bi-crosshair2"></i></span><div><small>CEP</small><strong>{{ selectedReport.cep }}</strong></div></article>
              </div>

              <div class="analysis-detail-grid">
                <div class="analysis-detail-card">
                  <h4><i class="bi bi-clipboard-data"></i> รายละเอียดการวิเคราะห์</h4>
                  <dl>
                    <div><dt>ประเภทเป้าหมาย</dt><dd>{{ selectedReport.type }}</dd></div>
                    <div><dt>ผลที่ต้องการ</dt><dd>{{ selectedReport.effect }}</dd></div>
                    <div><dt>วันที่วิเคราะห์</dt><dd>{{ formatDate(selectedReport.date) }}</dd></div>
                    <div><dt>สถานะข้อมูล</dt><dd><span class="analysis-ready"><i class="bi bi-check-circle-fill"></i> พร้อมใช้งาน</span></dd></div>
                  </dl>
                </div>
                <div class="analysis-summary-card">
                  <h4><i class="bi bi-stars"></i> Analysis Summary</h4>
                  <p>{{ selectedReport.analysis }}</p>
                  <div class="analysis-advice"><i class="bi bi-lightbulb"></i><span>ควรตรวจสอบสภาพอากาศและข้อจำกัดพื้นที่ก่อนดำเนินการ</span></div>
                </div>
              </div>
            </div>

            <footer class="analysis-result-footer">
              <span><i class="bi bi-calendar3"></i> {{ selectedReport.date }}</span>
              <button type="button" @click="closeAnalysisResult"><i class="bi bi-check-lg"></i> ปิดหน้าต่าง</button>
            </footer>
          </section>
        </div>

        <div v-if="reportPendingDelete" class="delete-modal-backdrop" @click.self="cancelDeleteReport">
          <section class="delete-confirm-modal" role="dialog" aria-modal="true" aria-labelledby="delete-confirm-title">
            <button type="button" class="delete-modal-close" aria-label="ปิด" @click="cancelDeleteReport"><i class="bi bi-x-lg"></i></button>
            <span class="delete-warning-icon"><i class="bi bi-trash3"></i></span>
            <small>DELETE REPORT</small>
            <h3 id="delete-confirm-title">ยืนยันการลบข้อมูล</h3>
            <p>คุณต้องการลบรายการเป้าหมายนี้หรือไม่?</p>
            <div class="delete-target-preview">
              <span><i :class="targetTypeIcon(reportPendingDelete.type)"></i></span>
              <div><strong>{{ reportPendingDelete.target }}</strong><small>{{ reportPendingDelete.shortId || String(reportPendingDelete.id).slice(0, 8) }} · {{ reportPendingDelete.type }}</small></div>
            </div>
            <div class="delete-warning-note"><i class="bi bi-exclamation-triangle"></i><span>ข้อมูลที่ลบแล้วจะไม่สามารถเรียกคืนได้</span></div>
            <footer>
              <button type="button" class="delete-cancel-button" @click="cancelDeleteReport"><i class="bi bi-x-circle"></i> ยกเลิก</button>
              <button type="button" class="delete-confirm-button" @click="requestFinalDeleteConfirmation"><i class="bi bi-trash3"></i> ลบข้อมูล</button>
            </footer>
          </section>
        </div>

        <div v-if="showFinalDeleteConfirm" class="delete-modal-backdrop final-delete-backdrop" @click.self="closeFinalDeleteConfirmation">
          <section class="delete-confirm-modal final-delete-modal" role="alertdialog" aria-modal="true" aria-labelledby="final-delete-title">
            <span class="delete-warning-icon final-warning-icon"><i class="bi bi-exclamation-octagon"></i></span>
            <small>FINAL CONFIRMATION</small>
            <h3 id="final-delete-title">ยืนยันการลบอีกครั้ง</h3>
            <p>โปรดตรวจสอบก่อนดำเนินการ รายการนี้จะถูกลบอย่างถาวร</p>
            <div class="final-delete-target"><i class="bi bi-crosshair"></i><strong>{{ reportPendingDelete?.target }}</strong></div>
            <footer>
              <button type="button" class="delete-cancel-button" @click="closeFinalDeleteConfirmation"><i class="bi bi-arrow-left"></i> ย้อนกลับ</button>
              <button type="button" class="delete-confirm-button final-confirm-button" @click="confirmDeleteReport"><i class="bi bi-check-lg"></i> ยืนยันลบถาวร</button>
            </footer>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onActivated, onBeforeUnmount } from 'vue'
import { notifyDataChanged, onDataChanged, SCENARIO_STORAGE_KEY } from '../services/dataSync'
import Header from '../components/Header.vue'
import { exportService } from '../services/exportService'
import { deleteResource, listResource } from '../services/api'
import {
  fetchScenarioInfo,
  fetchScenarioReportItems,
  fetchScenarioSummary,
} from '../services/reportDataService'
import {
  buildTargetExportPayload,
  targetCardToReportRow,
} from '../utils/reportExportMapper'
import { buildJmemAnalysisText } from '../utils/targetFormMapper'
import { buildScenarioSummary } from '../utils/reportData'


export default {
  name: 'ReportsView',
  components: {
    Header
  },
  setup() {
    const reports = ref([])
    const reportItems = ref([])
    const exportingScenario = ref('')
    const scenarios = ref([])
    const selectedScenarioId = ref(localStorage.getItem(SCENARIO_STORAGE_KEY) || '')
    const loading = ref(false)
    const loadError = ref('')

    const filters = ref({
      source: '',
      type: '',
      importance: '',
      startDate: '',
      endDate: '',
      query: ''
    })
    const openFilterDropdown = ref('')
    const selectedReport = ref(null)
    const reportPendingDelete = ref(null)
    const showFinalDeleteConfirm = ref(false)
    const currentPage = ref(1)
    const pageSize = ref(10)
    const effectivePageSize = computed(() => {
      const value = Number(pageSize.value)
      return Number.isFinite(value) && value >= 1 ? Math.min(100, Math.floor(value)) : 10
    })

    const importanceLabels = {
      key: 'สำคัญสูง',
      medium: 'สำคัญ',
      general: 'ทั่วไป'
    }

    const importanceOptions = [
      { value: 'key', label: 'สำคัญสูง', icon: 'bi bi-exclamation-diamond' },
      { value: 'medium', label: 'สำคัญ', icon: 'bi bi-dash-circle' },
      { value: 'general', label: 'ทั่วไป', icon: 'bi bi-check-circle' }
    ]

    const sourceOptions = computed(() => [...new Set(reports.value.map(report => report.source))])
    const typeOptions = computed(() => [...new Set(reports.value.map(report => report.type))])

    const filteredReports = computed(() => {
      const query = filters.value.query.toLocaleLowerCase('th-TH')
      return reports.value.filter(report => {
        const matchesQuery = !query || [report.target, report.source, report.type, report.status]
          .some(value => value.toLocaleLowerCase('th-TH').includes(query))
        return (!filters.value.source || report.source === filters.value.source)
          && (!filters.value.type || report.type === filters.value.type)
          && (!filters.value.importance || report.importance === filters.value.importance)
          && (!filters.value.startDate || report.dateValue >= filters.value.startDate)
          && (!filters.value.endDate || report.dateValue <= filters.value.endDate)
          && matchesQuery
      })
    })

    const totalPages = computed(() => Math.max(1, Math.ceil(filteredReports.value.length / effectivePageSize.value)))
    const paginatedReports = computed(() => {
      const start = (currentPage.value - 1) * effectivePageSize.value
      return filteredReports.value.slice(start, start + effectivePageSize.value)
    })
    const pageNumbers = computed(() => Array.from({ length: totalPages.value }, (_, index) => index + 1))
    const paginationStart = computed(() => filteredReports.value.length ? ((currentPage.value - 1) * effectivePageSize.value) + 1 : 0)
    const paginationEnd = computed(() => Math.min(currentPage.value * effectivePageSize.value, filteredReports.value.length))
    const setPage = (page) => { currentPage.value = Math.min(Math.max(page, 1), totalPages.value) }
    const normalizePageSize = () => {
      const value = Number(pageSize.value)
      pageSize.value = Number.isFinite(value) ? Math.min(100, Math.max(1, Math.floor(value))) : 10
      currentPage.value = 1
    }

    watch(filters, () => { currentPage.value = 1 }, { deep: true })
    watch(pageSize, () => { currentPage.value = 1 })

    const dashboardTotal = computed(() => filteredReports.value.length)

    const importanceCounts = computed(() => ({
      key: filteredReports.value.filter(report => report.importance === 'key').length,
      medium: filteredReports.value.filter(report => report.importance === 'medium').length,
      general: filteredReports.value.filter(report => report.importance === 'general').length
    }))

    const importancePercent = computed(() => {
      const total = dashboardTotal.value || 1
      return {
        key: Math.round((importanceCounts.value.key / total) * 100),
        medium: Math.round((importanceCounts.value.medium / total) * 100),
        general: Math.round((importanceCounts.value.general / total) * 100)
      }
    })

    const importanceStats = computed(() => [
      { key: 'key', count: importanceCounts.value.key, percent: importancePercent.value.key, color: '#f36b1c' },
      { key: 'medium', count: importanceCounts.value.medium, percent: importancePercent.value.medium, color: '#ffde45' },
      { key: 'general', count: importanceCounts.value.general, percent: importancePercent.value.general, color: '#2fb3c3' }
    ])

    const sourceColors = ['#f36b1c', '#ffde45', '#d9dde1', '#2fb3c3', '#4d86d9']
    const sourceStats = computed(() => {
      const total = dashboardTotal.value || 1
      return sourceOptions.value.map((name, index) => {
        const count = filteredReports.value.filter(report => report.source === name).length
        return { name, count, percent: Math.round((count / total) * 100), color: sourceColors[index % sourceColors.length] }
      })
    })

    const sourceLead = computed(() => sourceStats.value.reduce(
      (highest, source) => source.percent > highest.percent ? source : highest,
      { percent: 0, color: '#7f93a8' }
    ))
    const sourceTotal = computed(() => sourceStats.value.filter(source => source.count > 0).length)

    const buildRingGradient = (segments, total) => {
      if (!total) return 'conic-gradient(from -90deg, #26384a 0 100%)'
      const activeSegments = segments.filter(segment => segment.count > 0)
      if (activeSegments.length === 1) return `conic-gradient(from -90deg, ${activeSegments[0].color} 0 100%)`

      let cursor = 0
      const colors = []
      activeSegments.forEach(segment => {
        const portion = (segment.count / total) * 100
        const end = cursor + portion
        const gap = Math.min(0.8, portion * 0.12)
        colors.push(
          `#02070d ${cursor}% ${cursor + gap}%`,
          `${segment.color} ${cursor + gap}% ${end - gap}%`,
          `#02070d ${end - gap}% ${end}%`
        )
        cursor = end
      })
      return `conic-gradient(from -90deg, ${colors.join(', ')})`
    }

    const summaryRingStyle = computed(() => {
      const importanceSegments = [
        { count: importanceCounts.value.key, color: '#f36b1c' },
        { count: importanceCounts.value.medium, color: '#ffde45' },
        { count: importanceCounts.value.general, color: '#2fb3c3' }
      ]
      return {
        '--outer-ring': buildRingGradient(importanceSegments, dashboardTotal.value),
        '--source-ring': buildRingGradient(sourceStats.value, dashboardTotal.value)
      }
    })

    const lastUpdated = computed(() => filteredReports.value[0]?.date.split(' ')[0] || '-')

    const WEAPON_COLORS = ['#6ea8fe', '#f36b1c', '#ffde45', '#2fb3c3', '#b598eb']
    const WEAPON_PRODUCT_LIMIT = 4
    const weaponSummary = computed(() => {
      const visibleIds = new Set(filteredReports.value.map(report => report.id))
      const summary = buildScenarioSummary({
        items: reportItems.value.filter(item => visibleIds.has(item.card?.id)),
      })
      const totalQuantity = summary.totals.quantity || 0
      const products = summary.products.map((product, index) => ({
        ...product,
        color: WEAPON_COLORS[index % WEAPON_COLORS.length],
        percent: totalQuantity ? Math.round((product.quantity / totalQuantity) * 100) : 0,
      }))
      const selectionCounts = { confirmed: 0, partial: 0, recommended: 0, none: 0 }
      summary.targets.forEach(target => { selectionCounts[target.selection] += 1 })
      const targetTotal = summary.targetCount || 1
      const selection = [
        { key: 'confirmed', label: 'ยืนยันแล้ว', color: '#36d28b' },
        { key: 'partial', label: 'เลือกบางจุด', color: '#ffde45' },
        { key: 'recommended', label: 'แนะนำ JMEM', color: '#6ea8fe' },
        { key: 'none', label: 'ยังไม่มีสินค้า', color: '#7f93a8' },
      ].map(item => ({
        ...item,
        count: selectionCounts[item.key],
        percent: (selectionCounts[item.key] / targetTotal) * 100,
      }))
      return {
        targetCount: summary.targetCount,
        aimPointCount: summary.aimPointCount,
        totals: summary.totals,
        productCount: products.length,
        topProducts: products.slice(0, WEAPON_PRODUCT_LIMIT),
        moreProducts: Math.max(0, products.length - WEAPON_PRODUCT_LIMIT),
        hasCost: summary.totals.cost > 0,
        selection,
      }
    })

    const formatNumber = (value, digits = 0) => Number(value || 0).toLocaleString('th-TH', {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    })
    const formatWeight = (lb) => {
      const value = Number(lb) || 0
      return value >= 10000 ? `${formatNumber(value / 1000, 1)}k` : formatNumber(value)
    }

    const hasActiveFilters = computed(() => Object.values(filters.value).some(Boolean))

    const clearFilters = () => {
      filters.value = { source: '', type: '', importance: '', startDate: '', endDate: '', query: '' }
      openFilterDropdown.value = ''
    }

    const formatDate = (date) => date?.split(' ')[0] || '-'

    const targetTypeIcon = (type) => ({
      อาคาร: 'bi bi-building',
      สะพาน: 'bi bi-signpost-split',
      บังเกอร์: 'bi bi-bricks',
      คูเลน: 'bi bi-arrows-expand',
      รันเวย์: 'bi bi-airplane-engines',
      เรือ: 'bi bi-water',
      คลังอาวุธ: 'bi bi-box-seam',
      คลังเชื้อเพลิง: 'bi bi-fuel-pump',
      เรดาร์: 'bi bi-broadcast-pin',
      โรงเก็บเครื่องบิน: 'bi bi-houses'
    }[type] || 'bi bi-geo-alt')

    const importanceIcon = (importance) => ({
      key: 'bi bi-exclamation-diamond',
      medium: 'bi bi-dash-circle',
      general: 'bi bi-check-circle'
    }[importance] || 'bi bi-flag')

    const sourceIcon = (source) => ({
      เป้าหมายร่วม: 'bi bi-people',
      'เป้าหมาย ทอ.': 'bi bi-airplane',
      'เป้าหมาย กกล.สุรนารี': 'bi bi-shield-plus',
      เป้าหมายทางลึก: 'bi bi-shield-check',
      'อื่นๆ': 'bi bi-three-dots'
    }[source] || 'bi bi-broadcast-pin')

    const selectedFilterLabel = (key) => {
      if (!filters.value[key]) return 'ทั้งหมด'
      return key === 'importance' ? importanceLabels[filters.value[key]] : filters.value[key]
    }

    const selectedFilterIcon = (key) => {
      const value = filters.value[key]
      if (!value) return 'bi bi-grid'
      if (key === 'source') return sourceIcon(value)
      if (key === 'type') return targetTypeIcon(value)
      return importanceIcon(value)
    }

    const toggleFilterDropdown = (key) => {
      openFilterDropdown.value = openFilterDropdown.value === key ? '' : key
    }

    const selectFilter = (key, value) => {
      filters.value[key] = value
      openFilterDropdown.value = ''
    }

    const openDatePicker = (event) => {
      const input = event.currentTarget.querySelector('input[type="date"]')
      if (!input) return
      if (typeof input.showPicker === 'function') {
        try { input.showPicker() } catch (_) { /* browser already opened the picker */ }
      } else {
        input.click()
      }
    }

    async function loadScenarios() {
      try {
        scenarios.value = (await listResource('/scenarios')) || []
        if (
          selectedScenarioId.value &&
          !scenarios.value.some((s) => s.id === selectedScenarioId.value)
        ) {
          selectedScenarioId.value = ''
          localStorage.removeItem(SCENARIO_STORAGE_KEY)
        }
        if (!selectedScenarioId.value && scenarios.value.length === 1) {
          selectedScenarioId.value = scenarios.value[0].id
          localStorage.setItem(SCENARIO_STORAGE_KEY, selectedScenarioId.value)
        }
      } catch (err) {
        loadError.value = err.message || 'โหลด scenarios ไม่สำเร็จ'
        scenarios.value = []
      }
    }

    async function loadTargets() {
      if (!selectedScenarioId.value) {
        reports.value = []
        reportItems.value = []
        loadError.value = ''
        return
      }
      loading.value = true
      loadError.value = ''
      try {
        const scenarioId = selectedScenarioId.value
        const [items, scenario] = await Promise.all([
          fetchScenarioReportItems(scenarioId),
          fetchScenarioInfo(scenarioId),
        ])
        const scenarioName = scenario?.name || scenarios.value.find((s) => s.id === scenarioId)?.name || ''
        reportItems.value = items
        reports.value = items
          .map(({ card, draft, jmem }) => targetCardToReportRow(card, jmem, draft, {
            scenarioName,
            analysisText: jmem?.products?.length && draft ? buildJmemAnalysisText(draft, jmem) : '',
          }))
          .filter(Boolean)
        currentPage.value = 1
      } catch (err) {
        reports.value = []
        reportItems.value = []
        loadError.value = err.message || 'โหลดเป้าหมายไม่สำเร็จ'
      } finally {
        loading.value = false
      }
    }

    function onScenarioChange(event) {
      const id = event.target.value || ''
      selectedScenarioId.value = id
      if (id) localStorage.setItem(SCENARIO_STORAGE_KEY, id)
      else localStorage.removeItem(SCENARIO_STORAGE_KEY)
      loadTargets()
    }

    const buildAnalysisReport = (report) => {
      const snapshot = report.exportSnapshot
      if (snapshot) {
        const extra = Object.fromEntries(snapshot.extraRows || [])
        return {
          ...report,
          confidence: String(extra['AI Confidence'] || report.confidence || '').replace('%', '') || '—',
          recommendation: snapshot.mainRow?.weapon || report.recommendation || '—',
          pk: extra['Pk Value'] || report.pk || '—',
          cep: extra['CEP Value'] || report.cep || '—',
          effect: snapshot.mainRow?.desiredEffect || report.effect || '—',
          analysis: snapshot.analysisText || report.analysis || extra['ผลการวิเคราะห์ AI'] || '',
          details: snapshot.mainRow?.details || report.details,
          imageName: extra['ชื่อไฟล์รูปภาพ'] || report.imageName,
          imagePreview: snapshot.images?.target || report.imagePreview,
          latitude: snapshot.targetInfo?.latitude ?? report.latitude,
          longitude: snapshot.targetInfo?.longitude ?? report.longitude,
        }
      }
      return {
        ...report,
        confidence: report.confidence || '—',
        recommendation: report.recommendation || '—',
        pk: report.pk || '—',
        cep: report.cep || '—',
        effect: report.effect || '—',
        analysis: report.analysis || report.details || '',
      }
    }

    const openAnalysisResult = (report) => {
      selectedReport.value = buildAnalysisReport(report)
    }

    const closeAnalysisResult = () => { selectedReport.value = null }

    const viewReport = (id) => {
      const report = reports.value.find(r => r.id === id)
      if (report) openAnalysisResult(report)
    }

    const requestDeleteReport = (report) => {
      reportPendingDelete.value = report
      showFinalDeleteConfirm.value = false
    }
    const cancelDeleteReport = () => {
      showFinalDeleteConfirm.value = false
      reportPendingDelete.value = null
    }
    const requestFinalDeleteConfirmation = () => {
      if (reportPendingDelete.value) showFinalDeleteConfirm.value = true
    }
    const closeFinalDeleteConfirmation = () => { showFinalDeleteConfirm.value = false }
    const confirmDeleteReport = async () => {
      if (!reportPendingDelete.value) return
      const pending = reportPendingDelete.value
      try {
        if (pending.fromApi) {
          await deleteResource('/targets', pending.id)
        }
        reports.value = reports.value.filter(report => report.id !== pending.id)
      } catch (error) {
        console.error('Unable to delete target/report', error)
        alert(error.message || 'ลบเป้าหมายไม่สำเร็จ')
      } finally {
        showFinalDeleteConfirm.value = false
        reportPendingDelete.value = null
      }
    }

    const sanitizeFilename = (value) => String(value || 'report')
      .trim()
      .replace(/[\\/:*?"<>|]+/g, '')
      .replace(/\s+/g, '_')

    const buildReportExportData = (report) => {
      if (report.exportSnapshot) return report.exportSnapshot
      return buildTargetExportPayload({
        formData: {
          label: report.target,
          selectedTargetSource: report.source,
          targetType: report.type,
          targetDetails: report.details || report.analysis || '',
          imageName: report.imageName,
          imagePreview: report.imagePreview,
          latitude: report.latitude,
          longitude: report.longitude,
        },
        recommendations: report.summary?.recommendations || [],
        analysisText: report.summary?.analysis || report.analysis || '',
        priority: report.importance,
      })
    }

    const exportReports = async (format, report = null) => {
      if (!report) return

      const date = new Date().toISOString().split('T')[0]
      const filename = `report_${sanitizeFilename(report.target)}_${date}`
      const exportData = buildReportExportData(report)

      try {
        if (format === 'pdf') {
          await exportService.exportToPDF(exportData, `${filename}.pdf`)
          alert('นำออก PDF สำเร็จ')
          return
        }

        if (format === 'word') {
          await exportService.exportToWord(exportData, `${filename}.docx`)
          alert('นำออก Word สำเร็จ')
          return
        }

        alert('ไม่พบรูปแบบไฟล์ที่รองรับ')
      } catch (error) {
        console.error('Report Export Error:', error)
        alert(`เกิดข้อผิดพลาดในการนำออก: ${error.message}`)
      }
    }

    const exportScenarioSummary = async (format) => {
      if (!selectedScenarioId.value || exportingScenario.value) return
      exportingScenario.value = format
      try {
        const summary = await fetchScenarioSummary(selectedScenarioId.value, reportItems.value.length ? reportItems.value : null)
        const date = new Date().toISOString().split('T')[0]
        const filename = `scenario_summary_${sanitizeFilename(summary.scenarioName)}_${date}`
        if (format === 'pdf') await exportService.exportScenarioToPDF(summary, `${filename}.pdf`)
        else await exportService.exportScenarioToWord(summary, `${filename}.docx`)
      } catch (error) {
        console.error('Scenario Summary Export Error:', error)
        alert(`เกิดข้อผิดพลาดในการนำออกภาพรวม: ${error.message}`)
      } finally {
        exportingScenario.value = ''
      }
    }

    const refreshData = async () => {
      await loadScenarios()
      await loadTargets()
    }

    const closeFilterDropdown = () => { openFilterDropdown.value = '' }
    const handleKeydown = (event) => {
      if (event.key !== 'Escape') return
      if (showFinalDeleteConfirm.value) {
        closeFinalDeleteConfirmation()
        return
      }
      closeAnalysisResult()
      cancelDeleteReport()
    }
    let isRefreshing = false
    const refreshViewData = async () => {
      if (isRefreshing) return
      isRefreshing = true
      try {
        const storedId = localStorage.getItem(SCENARIO_STORAGE_KEY)
        if (storedId && storedId !== selectedScenarioId.value) {
          selectedScenarioId.value = storedId
        }
        await refreshData()
      } catch (err) {
        console.warn('Reports refreshViewData error:', err)
      } finally {
        isRefreshing = false
      }
    }

    onMounted(async () => {
      document.addEventListener('click', closeFilterDropdown)
      window.addEventListener('keydown', handleKeydown)
      await refreshData()
    })

    onActivated(async () => {
      await refreshViewData()
    })

    const unsubSync = onDataChanged(async () => {
      await refreshViewData()
    })

    onBeforeUnmount(() => {
      document.removeEventListener('click', closeFilterDropdown)
      window.removeEventListener('keydown', handleKeydown)
      unsubSync()
    })

    return {
      reports,
      scenarios,
      selectedScenarioId,
      loading,
      loadError,
      filters,
      openFilterDropdown,
      selectedReport,
      reportPendingDelete,
      showFinalDeleteConfirm,
      filteredReports,
      paginatedReports,
      currentPage,
      pageSize,
      effectivePageSize,
      totalPages,
      pageNumbers,
      paginationStart,
      paginationEnd,
      sourceOptions,
      typeOptions,
      importanceCounts,
      importancePercent,
      importanceLabels,
      importanceOptions,
      importanceStats,
      sourceStats,
      sourceLead,
      sourceTotal,
      dashboardTotal,
      lastUpdated,
      weaponSummary,
      formatNumber,
      formatWeight,
      summaryRingStyle,
      hasActiveFilters,
      clearFilters,
      setPage,
      normalizePageSize,
      formatDate,
      targetTypeIcon,
      importanceIcon,
      sourceIcon,
      selectedFilterLabel,
      selectedFilterIcon,
      toggleFilterDropdown,
      selectFilter,
      openDatePicker,
      openAnalysisResult,
      closeAnalysisResult,
      viewReport,
      requestDeleteReport,
      cancelDeleteReport,
      requestFinalDeleteConfirmation,
      closeFinalDeleteConfirmation,
      confirmDeleteReport,
      exportReports,
      exportScenarioSummary,
      exportingScenario,
      refreshData,
      onScenarioChange,
    }
  }
}
</script>

<style scoped>
.reports-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #000000;
}

.reports-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0 16px;
}

.report-shell {
  max-width: 1800px;
  padding-right: 22px;
  padding-left: 22px;
}

.report-top-row {
  display: grid;
  grid-template-columns: minmax(300px, 360px) minmax(680px, 1fr);
  align-items: stretch;
  gap: 0;
  margin-bottom: 10px;
  background: #000000;
  justify-content: start;
}

.report-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 0;
  padding: 10px 20px 10px 4px;
  border: 0;
  border-radius: 0;
  background: #000000;
}

.report-kicker {
  color: #5e9bea;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-shadow: 0 0 10px rgba(94, 155, 234, 0.5);
}

.report-heading h2 {
  margin: 2px 0 1px;
  color: #f4f8ff;
  font-size: 2.05rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  text-shadow: 0 4px 14px rgba(0, 0, 0, 0.7);
}

.report-heading h2 i {
  margin-right: 7px;
  color: #6ea8fe;
}

.report-heading p {
  margin: 0;
  color: #9cb0c5;
  font-size: 0.88rem;
  font-weight: 500;
}

.report-live {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 9px;
  border: 1px solid rgba(54, 210, 139, 0.34);
  border-radius: 999px;
  background: rgba(54, 210, 139, 0.08);
  color: #72dca9;
  font-size: 0.62rem;
  font-weight: 700;
  white-space: nowrap;
}

.report-live i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #36d28b;
  box-shadow: 0 0 8px rgba(54, 210, 139, 0.8);
}

.summary-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  overflow: hidden;
  padding: 10px 4px 18px;
}

.summary-item {
  position: relative;
  display: flex;
  width: clamp(132px, 10vw, 154px);
  min-width: 132px;
  aspect-ratio: 1;
  align-items: center;
  justify-content: center;
  justify-self: center;
  flex-direction: column;
  gap: 7px;
  overflow: hidden;
  padding: 18px;
  border: 1px solid #2d435b;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 25%, #172d44, #0c1826 68%);
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.28);
  text-align: center;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.summary-item::before {
  position: absolute;
  inset: 6px;
  border: 1px solid rgba(51, 132, 231, 0.36);
  border-radius: 50%;
  background: transparent;
  content: '';
  pointer-events: none;
}

.summary-item:hover {
  border-color: #47739f;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.36);
  transform: translateY(-2px);
}

.summary-icon {
  display: inline-flex;
  flex: 0 0 38px;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(13, 110, 253, 0.16);
  color: #68a5f4;
  font-size: 1rem;
}

.summary-item > div {
  display: flex;
  min-width: 0;
  align-items: center;
  flex-direction: column;
}

.summary-item small {
  color: #8495a9;
  font-size: 0.63rem;
  white-space: nowrap;
}

.summary-item strong {
  color: #edf5ff;
  font-size: 1.15rem;
  line-height: 1.2;
}

.summary-item.key-target .summary-icon { background: rgba(220, 53, 69, 0.16); color: #ff6b79; }
.summary-item.medium-target .summary-icon { background: rgba(255, 193, 7, 0.15); color: #ffd04c; }
.summary-item.general-target .summary-icon { background: rgba(25, 135, 84, 0.16); color: #54d395; }
.summary-item.updated .summary-icon { background: rgba(111, 66, 193, 0.17); color: #ae8bf2; }
.summary-item.key-target::before { border-color: rgba(220, 53, 69, 0.52); }
.summary-item.medium-target::before { border-color: rgba(255, 193, 7, 0.5); }
.summary-item.general-target::before { border-color: rgba(25, 135, 84, 0.54); }
.summary-item.updated::before { border-color: rgba(122, 79, 199, 0.58); }
.summary-item .updated-date { font-size: 0.84rem; white-space: nowrap; }

.summary-wheel {
  position: relative;
  width: clamp(350px, 38vw, 440px);
  max-width: 100%;
  aspect-ratio: 1;
  border-radius: 50%;
  filter: drop-shadow(0 18px 34px rgba(0, 0, 0, 0.48));
  isolation: isolate;
}

.summary-wheel::before {
  position: absolute;
  inset: 0;
  z-index: -2;
  border-radius: 50%;
  background: conic-gradient(
    from -90deg,
    #dc3545 0 var(--key-stop),
    #ffc107 var(--key-stop) var(--medium-stop),
    #198754 var(--medium-stop) 100%
  );
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.18), 0 0 28px rgba(40, 116, 194, 0.2);
  content: '';
}

.summary-wheel::after {
  position: absolute;
  inset: 13px;
  z-index: -1;
  border: 1px solid #304b66;
  border-radius: 50%;
  background:
    radial-gradient(circle at 50% 42%, rgba(32, 72, 111, 0.48), transparent 45%),
    radial-gradient(circle, #101f30 0 53%, #0b1623 74%);
  box-shadow: inset 0 0 45px rgba(0, 0, 0, 0.55);
  content: '';
}

.wheel-center {
  position: absolute;
  top: 50%;
  left: 50%;
  z-index: 3;
  display: flex;
  width: 150px;
  height: 150px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  border: 1px solid #41688f;
  border-radius: 50%;
  background: radial-gradient(circle at 40% 30%, #1c3956, #0d1a28 72%);
  box-shadow: 0 0 0 7px rgba(13, 110, 253, 0.08), 0 12px 30px rgba(0, 0, 0, 0.48);
  transform: translate(-50%, -50%);
}

.wheel-main-icon {
  display: inline-flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  margin-bottom: 3px;
  border-radius: 50%;
  background: rgba(13, 110, 253, 0.2);
  color: #79b2fb;
  font-size: 1rem;
}

.wheel-center small { color: #8ca7c1; font-size: 0.6rem; font-weight: 700; letter-spacing: 0.12em; }
.wheel-center strong { color: #ffffff; font-size: 2.15rem; line-height: 1.05; text-shadow: 0 0 16px rgba(110, 168, 254, 0.48); }
.wheel-center > span:last-child { color: #5c7894; font-size: 0.52rem; font-weight: 700; letter-spacing: 0.1em; }

.wheel-stat {
  position: absolute;
  z-index: 4;
  display: flex;
  width: 126px;
  min-height: 62px;
  align-items: center;
  gap: 7px;
  padding: 8px 10px;
  border: 1px solid #334e69;
  border-radius: 13px;
  background: rgba(9, 22, 35, 0.94);
  box-shadow: 0 7px 18px rgba(0, 0, 0, 0.38);
  backdrop-filter: blur(8px);
}

.wheel-stat-icon {
  display: inline-flex;
  flex: 0 0 29px;
  width: 29px;
  height: 29px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 0.82rem;
}

.wheel-stat > div { display: grid; grid-template-columns: auto auto; align-items: baseline; column-gap: 5px; }
.wheel-stat small { grid-column: 1 / -1; color: #849ab0; font-size: 0.53rem; font-weight: 700; white-space: nowrap; }
.wheel-stat strong { color: #f1f7fd; font-size: 1rem; line-height: 1; }
.wheel-stat em { color: #6f879e; font-size: 0.58rem; font-style: normal; }

.key-stat { top: 8%; left: 50%; border-color: rgba(220, 53, 69, 0.55); transform: translateX(-50%); }
.medium-stat { top: 50%; right: 3%; border-color: rgba(255, 193, 7, 0.5); transform: translateY(-50%); }
.general-stat { bottom: 8%; left: 50%; border-color: rgba(25, 135, 84, 0.58); transform: translateX(-50%); }
.updated-stat { top: 50%; left: 3%; border-color: rgba(122, 79, 199, 0.58); transform: translateY(-50%); }
.key-stat .wheel-stat-icon { background: rgba(220, 53, 69, 0.18); color: #ff6f7c; }
.medium-stat .wheel-stat-icon { background: rgba(255, 193, 7, 0.17); color: #ffd455; }
.general-stat .wheel-stat-icon { background: rgba(25, 135, 84, 0.2); color: #56d49a; }
.updated-stat .wheel-stat-icon { background: rgba(122, 79, 199, 0.2); color: #b598eb; }
.updated-stat strong { font-size: 0.66rem; white-space: nowrap; }

.dashboard-panel {
  display: flex;
  height: 100%;
  min-height: 350px;
  align-items: stretch;
  justify-content: flex-start;
  flex-direction: column;
  margin: 0;
  padding: 0;
  overflow: hidden;
  border: 1px solid #334d68;
  border-radius: 10px;
  background:
    radial-gradient(circle at 30% 25%, rgba(36, 89, 139, 0.22), transparent 42%),
    #0c1724;
  box-shadow: 0 9px 26px rgba(0, 0, 0, 0.38);
}

.dashboard-panel-top {
  min-height: 154px;
  border: 0;
  border-left: 1px solid #35506d;
  border-radius: 0;
  background: #000000;
  box-shadow: none;
}

.dashboard-panel-top .dashboard-panel-header {
  display: none;
}

.dashboard-panel-top .dashboard-content {
  justify-content: flex-start;
  gap: 18px;
  padding: 7px 10px 7px 16px;
}

.dashboard-panel.dashboard-panel-top .summary-wheel {
  flex-basis: 154px;
  width: 154px;
  max-width: 154px;
  filter: drop-shadow(0 8px 14px rgba(0, 0, 0, 0.7));
}

.dashboard-panel.dashboard-panel-top .summary-wheel::before {
  background: var(--outer-ring);
  box-shadow:
    inset 7px 7px 12px rgba(255, 255, 255, 0.2),
    inset -9px -10px 16px rgba(0, 0, 0, 0.34),
    0 0 0 1px rgba(255, 255, 255, 0.1);
}

.dashboard-panel.dashboard-panel-top .summary-wheel::after {
  inset: 24px;
  border: 6px solid #f3f5f7;
  background: var(--source-ring);
  box-shadow:
    inset 5px 5px 9px rgba(255, 255, 255, 0.2),
    inset -7px -8px 12px rgba(0, 0, 0, 0.3),
    0 0 10px rgba(255, 255, 255, 0.14);
}

.dashboard-panel.dashboard-panel-top .wheel-center {
  width: 56px;
  height: 56px;
  border: 0;
  background: radial-gradient(circle at 38% 30%, #183550, #07111c 72%);
  box-shadow: 0 0 0 5px #f3f5f7, inset 0 0 12px rgba(0, 0, 0, 0.55);
}

.dashboard-panel.dashboard-panel-top .wheel-center > * { display: none; }

.dashboard-panel-top .wheel-center strong {
  font-size: 1.18rem;
}

.dashboard-panel-top .wheel-main-icon {
  width: 18px;
  height: 18px;
  margin-bottom: 0;
  font-size: 0.56rem;
}

.dashboard-panel-top .wheel-center small {
  font-size: 0.4rem;
  letter-spacing: 0.03em;
}

.dashboard-panel-top .wheel-center > span:last-child {
  font-size: 0.38rem;
}

.dashboard-panel.dashboard-panel-top .wheel-center small,
.dashboard-panel.dashboard-panel-top .wheel-center strong,
.dashboard-panel.dashboard-panel-top .wheel-center > span:last-child {
  display: block;
  line-height: 1.05;
  text-align: center;
}

.dashboard-panel.dashboard-panel-top .wheel-center small { font-size: 0.36rem; letter-spacing: 0; }
.dashboard-panel.dashboard-panel-top .wheel-center strong { color: #ffffff; font-size: 1.28rem; text-shadow: 0 0 9px rgba(110, 168, 254, 0.75); }
.dashboard-panel.dashboard-panel-top .wheel-center > span:last-child { color: #8da5bc; font-size: 0.32rem; letter-spacing: 0; }

.dashboard-panel-top .dashboard-legend {
  display: flex;
  min-width: 200px;
  max-width: 250px;
  flex-direction: column;
  gap: 4px;
}

.dashboard-panel-top .legend-row,
.dashboard-panel-top .legend-updated {
  margin: 0;
  min-height: 29px;
  padding: 3px 7px;
  border-radius: 3px;
  background: #0b1a29;
}

.dashboard-panel-top .legend-row {
  grid-template-columns: 22px minmax(0, 1fr) auto;
  gap: 6px;
}

.dashboard-panel-top .legend-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-size: 0.58rem;
}

.dashboard-panel-top .legend-row > div {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.dashboard-panel-top .legend-row small,
.dashboard-panel-top .legend-row strong,
.dashboard-panel-top .legend-row em,
.dashboard-panel-top .legend-updated small,
.dashboard-panel-top .legend-updated strong {
  font-size: 0.66rem;
}

.dashboard-panel-top .legend-updated {
  gap: 6px;
  border-color: #28345b;
  background: #15182f;
}

.dashboard-panel-top .key-legend .legend-icon { background: rgba(243, 107, 28, 0.18); color: #f36b1c; }
.dashboard-panel-top .medium-legend .legend-icon { background: rgba(255, 222, 69, 0.18); color: #ffde45; }
.dashboard-panel-top .general-legend .legend-icon { background: rgba(47, 179, 195, 0.18); color: #2fb3c3; }
.dashboard-panel-top .key-legend em { color: #f36b1c; }
.dashboard-panel-top .medium-legend em { color: #ffde45; }
.dashboard-panel-top .general-legend em { color: #2fb3c3; }

.legend-section-title {
  display: flex;
  align-items: center;
  gap: 5px;
  min-height: 14px;
  color: #7090af;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.source-summary {
  display: flex;
  min-width: 210px;
  max-width: 270px;
  flex: 1;
  flex-direction: column;
  gap: 3px;
}

.source-summary-row {
  display: grid;
  min-height: 23px;
  grid-template-columns: 5px 18px minmax(0, 1fr) auto 31px;
  align-items: center;
  gap: 5px;
  padding: 2px 6px;
  border: 1px solid #223950;
  border-radius: 3px;
  background: #091725;
  color: #d9e5f1;
  font-size: 0.64rem;
}

.source-summary-row > i { color: #ffffff; text-align: center; }
.source-summary-row > span:nth-of-type(2) { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.source-summary-row strong { color: #ffffff; font-size: 0.68rem; }
.source-summary-row em { color: #7e9bb8; font-size: 0.62rem; font-style: normal; font-weight: 700; text-align: right; }
.source-color { width: 5px; height: 15px; border-radius: 4px; box-shadow: 0 0 5px currentColor; }

.dashboard-panel-top .dashboard-content {
  display: grid;
  grid-template-columns: repeat(2, minmax(345px, 1fr)) minmax(360px, 1.15fr);
  gap: 6px;
}

.dashboard-chart-group {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: center;
  gap: 9px;
  padding: 6px;
  border: 1px solid #172c40;
  border-radius: 9px;
  background: linear-gradient(135deg, rgba(24, 49, 73, 0.48), rgba(4, 12, 20, 0.66));
}

.dashboard-panel.dashboard-panel-top .summary-wheel {
  flex-basis: 126px;
  width: 126px;
  max-width: 126px;
}

.dashboard-panel.dashboard-panel-top .summary-wheel::after {
  inset: 18px;
  border: 1px solid #29455f;
  background: radial-gradient(circle at 38% 30%, #17344e, #06101a 74%);
  box-shadow: inset 0 0 16px rgba(0, 0, 0, 0.66);
}

.dashboard-panel.dashboard-panel-top .wheel-center {
  width: 82px;
  height: 82px;
  background: transparent;
  box-shadow: none;
}

.dashboard-panel.dashboard-panel-top .wheel-center small { font-size: 0.43rem; }
.dashboard-panel.dashboard-panel-top .wheel-center strong { font-size: 1.75rem; }
.dashboard-panel.dashboard-panel-top .wheel-center > span:last-child { font-size: 0.38rem; }

.dashboard-chart-group .dashboard-legend {
  min-width: 190px;
  max-width: 220px;
  flex: 0 1 220px;
}

.dashboard-chart-group .legend-row > div {
  justify-content: flex-start;
  gap: 7px;
}

.source-rings-chart {
  position: relative;
  width: 136px;
  height: 136px;
  flex: 0 0 136px;
  filter: drop-shadow(0 8px 14px rgba(0, 0, 0, 0.68));
}

.source-rings-chart svg { display: block; width: 100%; height: 100%; }
.source-ring-track { fill: none; stroke: #1a2b3d; stroke-width: 5; }
.source-ring-progress {
  fill: none;
  stroke-width: 5;
  stroke-linecap: round;
  transform: rotate(-90deg);
  transform-origin: 50% 50%;
  transition: stroke-dasharray 0.35s ease, stroke 0.35s ease;
  filter: drop-shadow(0 0 3px currentColor);
}

.source-rings-center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  pointer-events: none;
}

.source-rings-center strong { color: #ffffff; font-size: 1.45rem; line-height: 1; text-shadow: 0 0 9px rgba(110, 168, 254, 0.8); }
.source-rings-center strong small { margin-left: 1px; font-size: 0.58rem; }
.source-rings-center span { margin-top: 3px; color: #8197ad; font-size: 0.4rem; }
.source-dashboard .source-summary { min-width: 190px; max-width: 220px; flex: 0 1 220px; }
.source-dashboard .source-summary { order: 1; }
.source-dashboard .source-rings-chart { order: 2; }
.source-dashboard { justify-content: center; }
.source-dashboard { order: 1; }
.importance-dashboard { order: 2; }
.importance-rings-center strong { color: #f4f8ff; }
.importance-rings-center span { color: #91a8be; }

.weapon-dashboard {
  order: 3;
  align-items: stretch;
  justify-content: flex-start;
  flex-direction: column;
  gap: 5px;
  padding: 7px 9px;
}

.weapon-dashboard-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.weapon-dashboard-head small { color: #7e9bb8; font-size: 0.6rem; white-space: nowrap; }

.weapon-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 4px;
}

.weapon-stat {
  display: flex;
  min-width: 0;
  flex-direction: column;
  padding: 3px 6px;
  border: 1px solid #223950;
  border-radius: 3px;
  background: #091725;
}

.weapon-stat small { overflow: hidden; color: #7e9bb8; font-size: 0.56rem; text-overflow: ellipsis; white-space: nowrap; }
.weapon-stat strong { overflow: hidden; color: #ffffff; font-size: 0.92rem; line-height: 1.2; text-overflow: ellipsis; white-space: nowrap; }
.weapon-stat strong span { margin-left: 3px; color: #8da5bc; font-size: 0.55rem; font-weight: 600; }

.weapon-product-list {
  display: flex;
  min-height: 52px;
  flex: 1;
  flex-direction: column;
  gap: 3px;
}

.weapon-product-row {
  display: grid;
  min-height: 19px;
  grid-template-columns: minmax(70px, 1.1fr) minmax(50px, 1fr) auto 31px;
  align-items: center;
  gap: 6px;
  color: #d9e5f1;
  font-size: 0.64rem;
}

.weapon-product-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.weapon-product-bar { height: 6px; overflow: hidden; border-radius: 4px; background: #1a2b3d; }
.weapon-product-bar i { display: block; height: 100%; border-radius: 4px; box-shadow: 0 0 5px currentColor; transition: width 0.35s ease; }
.weapon-product-row strong { color: #ffffff; font-size: 0.68rem; text-align: right; }
.weapon-product-row em { font-size: 0.62rem; font-style: normal; font-weight: 700; text-align: right; }
.weapon-more { color: #7090af; font-size: 0.56rem; }

.weapon-empty {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #7090af;
  font-size: 0.64rem;
}

.weapon-selection { display: flex; flex-direction: column; gap: 3px; }

.weapon-selection-bar {
  display: flex;
  height: 5px;
  overflow: hidden;
  gap: 2px;
  border-radius: 4px;
  background: #1a2b3d;
}

.weapon-selection-bar i { display: block; height: 100%; }

.weapon-selection-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 2px 10px;
  color: #9cb0c5;
  font-size: 0.56rem;
}

.weapon-selection-legend span { display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; }
.weapon-selection-legend b { width: 7px; height: 7px; border-radius: 50%; }

.dashboard-panel-header {
  display: flex;
  min-height: 56px;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid #30475f;
  background: linear-gradient(90deg, #132a42, #102034);
}

.dashboard-panel-header > div {
  display: flex;
  flex-direction: column;
}

.dashboard-panel-header small {
  color: #6585a4;
  font-size: 0.54rem;
  font-weight: 700;
  letter-spacing: 0.13em;
}

.dashboard-panel-header strong {
  color: #eef6ff;
  font-size: 0.87rem;
}

.dashboard-panel-header > span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 7px;
  border: 1px solid rgba(54, 210, 139, 0.38);
  border-radius: 999px;
  color: #5bd69a;
  font-size: 0.56rem;
  font-weight: 700;
}

.report-top-row .report-live {
  display: none;
}

.dashboard-content {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 10px;
}

.dashboard-panel .summary-wheel {
  flex: 0 0 154px;
  width: 154px;
  max-width: 154px;
}

.dashboard-panel .summary-wheel::before {
  background: conic-gradient(
    from -90deg,
    #dc3545 0 calc(var(--key-stop) - 1%),
    #0c1724 calc(var(--key-stop) - 1%) var(--key-stop),
    #ffc107 var(--key-stop) calc(var(--medium-stop) - 1%),
    #0c1724 calc(var(--medium-stop) - 1%) var(--medium-stop),
    #198754 var(--medium-stop) 99%,
    #0c1724 99% 100%
  );
}

.dashboard-panel .summary-wheel::after {
  inset: 23px;
  border-color: #34516d;
  background: radial-gradient(circle at 42% 32%, #1a3550, #0b1724 70%);
}

.dashboard-panel .wheel-center {
  width: 94px;
  height: 94px;
  border-color: rgba(92, 135, 178, 0.45);
  background: rgba(9, 22, 35, 0.82);
  box-shadow: 0 0 0 5px rgba(13, 110, 253, 0.06);
}

.dashboard-panel .wheel-center small {
  font-size: 0.54rem;
}

.dashboard-panel .wheel-center strong {
  font-size: 1.65rem;
}

.dashboard-panel .wheel-center > span:last-child {
  color: #6f879f;
  font-size: 0.53rem;
  letter-spacing: 0;
}

.dashboard-legend {
  display: flex;
  min-width: 140px;
  flex: 1;
  flex-direction: column;
  gap: 6px;
}

.legend-row {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) auto;
  align-items: center;
  gap: 7px;
  padding: 6px;
  border: 1px solid #293f56;
  border-radius: 9px;
  background: rgba(13, 29, 45, 0.84);
}

.legend-icon {
  display: inline-flex;
  width: 28px;
  height: 28px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 0.78rem;
}

.legend-row > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.legend-row small {
  overflow: hidden;
  color: #859bb0;
  font-size: 0.56rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.legend-row strong {
  color: #e5eef7;
  font-size: 0.7rem;
}

.legend-row em {
  font-size: 0.66rem;
  font-style: normal;
  font-weight: 700;
}

.key-legend .legend-icon { background: rgba(220, 53, 69, 0.2); color: #ff6e7b; }
.medium-legend .legend-icon { background: rgba(255, 193, 7, 0.18); color: #ffd24d; }
.general-legend .legend-icon { background: rgba(25, 135, 84, 0.2); color: #55d396; }
.key-legend em { color: #ff6e7b; }
.medium-legend em { color: #ffd24d; }
.general-legend em { color: #55d396; }

.legend-updated {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
  padding: 7px;
  border: 1px solid rgba(122, 79, 199, 0.42);
  border-radius: 9px;
  background: rgba(122, 79, 199, 0.09);
}

.legend-updated > i {
  color: #a98be2;
}

.legend-updated > div {
  display: flex;
  flex-direction: column;
}

.legend-updated small { color: #7f91a5; font-size: 0.54rem; }
.legend-updated strong { color: #d5c7ef; font-size: 0.7rem; }

.filter-bar {
  display: grid;
  grid-template-columns: minmax(145px, 1fr) minmax(145px, 1fr) minmax(160px, 1fr) minmax(260px, 1.6fr) minmax(190px, 1.25fr) auto;
  align-items: end;
  gap: 8px;
  margin-bottom: 10px;
  padding: 10px;
  overflow: visible;
  border: 1px solid #293d54;
  border-radius: 12px;
  background: #0d1826;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.24);
}

.filter-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 6px;
}

.filter-field label {
  overflow: hidden;
  margin: 0;
  color: #9aabc0;
  font-size: 0.68rem;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.filter-field label i {
  margin-right: 4px;
  color: #6ea8fe;
}

.filter-field select,
.filter-field input {
  width: 100%;
  height: 36px;
  padding: 7px 10px;
  border: 1px solid #344a61;
  border-radius: 10px;
  outline: 0;
  background: #101f30;
  color: #e9f2fc;
  font-family: inherit;
  font-size: 0.76rem;
}

.filter-field select:focus,
.filter-field input:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.15);
}

.select-control {
  position: relative;
}

.select-control > i {
  position: absolute;
  top: 50%;
  left: 11px;
  z-index: 2;
  color: #6ea8fe;
  font-size: 0.8rem;
  pointer-events: none;
  transform: translateY(-50%);
}

.select-control select {
  padding-left: 33px;
}

.custom-filter-dropdown {
  position: relative;
}

.custom-filter-toggle {
  display: grid;
  width: 100%;
  height: 36px;
  grid-template-columns: 20px minmax(0, 1fr) 14px;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  border: 1px solid #344a61;
  border-radius: 8px;
  background: #101f30;
  color: #e9f2fc;
  font-family: inherit;
  font-size: 0.76rem;
  text-align: left;
}

.custom-filter-toggle > i:first-child {
  color: #ffffff;
}

.custom-filter-toggle > i:last-child {
  color: #7790a8;
  font-size: 0.62rem;
}

.custom-filter-toggle > span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.custom-filter-toggle:hover,
.custom-filter-toggle:focus {
  border-color: #0d6efd;
  outline: 0;
  box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.15);
}

.filter-dropdown-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  left: 0;
  z-index: 80;
  max-height: 270px;
  overflow-y: auto;
  padding: 5px;
  border: 1px solid #3a536d;
  border-radius: 9px;
  background: #0d1b2a;
  box-shadow: 0 14px 32px rgba(0, 0, 0, 0.52);
}

.filter-dropdown-menu button {
  display: grid;
  width: 100%;
  min-height: 38px;
  grid-template-columns: 22px minmax(0, 1fr) 16px;
  align-items: center;
  gap: 7px;
  padding: 7px 8px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #dce8f4;
  font-family: inherit;
  font-size: 0.74rem;
  text-align: left;
}

.filter-dropdown-menu button:hover {
  background: rgba(13, 110, 253, 0.16);
}

.filter-dropdown-menu button.active {
  background: rgba(13, 110, 253, 0.23);
  color: #ffffff;
}

.filter-dropdown-menu button > i:first-child {
  color: #ffffff;
  text-align: center;
}

.filter-dropdown-menu button > i:last-child {
  color: #65d49a;
}

.date-range {
  display: grid;
  grid-template-columns: minmax(128px, 1fr) auto minmax(128px, 1fr);
  align-items: center;
  gap: 6px;
}

.date-range > span {
  color: #6e8298;
}

.date-input-wrap {
  position: relative;
  min-width: 0;
  cursor: pointer;
}

.date-input-wrap > i {
  position: absolute;
  top: 50%;
  left: 10px;
  z-index: 2;
  color: #ffffff;
  font-size: 0.9rem;
  text-shadow: 0 0 8px rgba(110, 168, 254, 0.8);
  pointer-events: none;
  transform: translateY(-50%);
}

.date-input-wrap input {
  padding-right: 32px;
  padding-left: 33px;
  border-color: #3a5877;
  background: linear-gradient(180deg, #13283d, #0e1d2c);
  color-scheme: dark;
  caret-color: transparent;
  cursor: pointer;
  user-select: none;
}

.date-input-wrap input.is-empty::-webkit-datetime-edit {
  color: transparent;
}

.date-input-wrap input.is-empty:focus::-webkit-datetime-edit {
  color: transparent;
}

.date-input-wrap input::-webkit-datetime-edit,
.date-input-wrap input::-webkit-datetime-edit-fields-wrapper {
  user-select: none;
}

.date-input-wrap input::-webkit-datetime-edit-day-field:focus,
.date-input-wrap input::-webkit-datetime-edit-month-field:focus,
.date-input-wrap input::-webkit-datetime-edit-year-field:focus {
  outline: none;
  background: transparent !important;
  color: inherit !important;
}

.date-input-wrap input::selection {
  background: transparent;
}

.date-input-wrap input::-webkit-calendar-picker-indicator {
  width: 0;
  margin: 0;
  padding: 0;
  opacity: 0;
  pointer-events: none;
}

.date-format-placeholder {
  position: absolute;
  top: 50%;
  left: 33px;
  z-index: 1;
  color: #91a9c1;
  font-size: 0.72rem;
  pointer-events: none;
  user-select: none;
  transform: translateY(-50%);
}

.report-data-row {
  --bs-gutter-x: 10px;
  --bs-gutter-y: 10px;
  align-items: stretch;
}

.search-input-wrap {
  position: relative;
}

.search-input-wrap > i {
  position: absolute;
  top: 50%;
  left: 11px;
  color: #668099;
  transform: translateY(-50%);
}

.search-input-wrap input {
  padding-left: 32px;
}

.clear-filter-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-width: 124px;
  height: 36px;
  padding: 0 12px;
  border: 1px solid #49627c;
  border-radius: 8px;
  background: #162639;
  color: #c8d6e5;
  font-family: inherit;
  font-size: 0.72rem;
  font-weight: 600;
}

.clear-filter-button:hover:not(:disabled) {
  border-color: #dc3545;
  background: #dc3545;
  color: #ffffff;
}

.clear-filter-button:disabled {
  cursor: not-allowed;
  opacity: 0.42;
}

.importance-badge {
  display: inline-flex;
  min-width: 58px;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 4px 7px;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
}

.importance-badge.key { background: rgba(220, 53, 69, 0.17); color: #ff7380; }
.importance-badge.medium { background: rgba(255, 193, 7, 0.16); color: #ffd14f; }
.importance-badge.general { background: rgba(25, 135, 84, 0.18); color: #55d497; }

.report-table-block {
  border: 1px solid #2b4056;
  border-radius: 10px;
  background: #0c1723;
  overflow: visible;
}
.report-table-block .table-responsive {
  overflow-x: auto;
  overflow-y: visible;
  min-height: 240px;
  padding-bottom: 60px;
}
@media (min-width: 1200px) {
  .report-table-block .table-responsive {
    overflow: visible;
  }
}
.table-pagination {
  display: flex;
  min-height: 52px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  border-top: 1px solid #2b4056;
  background: #101e2d;
  border-bottom-left-radius: 9px;
  border-bottom-right-radius: 9px;
  position: relative;
  z-index: 1;
}
.pagination-info { display: flex; align-items: center; gap: 14px; }
.pagination-summary { display: inline-flex; align-items: center; gap: 6px; color: #8299af; font-size: 0.66rem; white-space: nowrap; }
.pagination-summary i { color: #6ea8fe; }
.page-size-control { display: inline-flex; align-items: center; gap: 6px; margin: 0; color: #8299af; font-size: 0.64rem; white-space: nowrap; }
.pagination-size-input { width: 58px; height: 30px; padding: 3px 7px; border: 1px solid #3a536c; border-radius: 7px; outline: 0; background: #16283a; color: #e8f1fa; font-family: inherit; font-size: 0.7rem; font-weight: 700; text-align: center; }
.pagination-size-input:focus { border-color: #4b91e2; box-shadow: 0 0 0 3px rgba(13,110,253,.14); }
.pagination-buttons { display: flex; align-items: center; gap: 5px; }
.pagination-buttons button { display: inline-grid; width: 31px; height: 31px; place-items: center; border: 1px solid #3a536c; border-radius: 8px; background: #16283a; color: #b9cad9; font-family: inherit; font-size: 0.68rem; font-weight: 700; transition: 0.16s ease; }
.pagination-buttons button:hover:not(:disabled) { border-color: #4b91e2; background: #204a75; color: #fff; transform: translateY(-1px); }
.pagination-buttons button.active { border-color: #5b9bea; background: #0d6efd; box-shadow: 0 4px 12px rgba(13, 110, 253, 0.28); color: #fff; }
.pagination-buttons button:disabled { cursor: not-allowed; opacity: 0.34; }

.data-log-table {
  --bs-table-bg: transparent;
  --bs-table-color: #dce7f3;
  width: 100%;
  min-width: 1040px;
  margin: 0;
  overflow: hidden;
  border: 0;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.78rem;
}

.data-log-table thead {
  border: 0;
  background: transparent;
}

.data-log-table thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  padding: 11px 10px;
  border: 0;
  border-bottom: 1px solid #38516b;
  background: linear-gradient(180deg, #17324e, #11283f);
  color: #a9c3df;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.035em;
  text-align: left;
  white-space: nowrap;
}

.data-log-table thead th > i {
  margin-right: 5px;
  color: #a9c3df;
  font-size: 0.76rem;
}

.data-log-table thead th:first-child,
.data-log-table tbody td:first-child,
.data-log-table thead th:nth-last-child(-n + 3),
.data-log-table tbody td:nth-last-child(-n + 3) {
  text-align: center;
}

.data-log-table tbody tr {
  border: 0;
  color: #dce7f3;
  cursor: pointer;
  transition: background-color 0.18s ease, box-shadow 0.18s ease;
}

.data-log-table tbody tr:nth-child(odd) {
  background: rgba(255, 255, 255, 0.018);
}

.data-log-table tbody tr:nth-child(even) {
  background: rgba(21, 63, 104, 0.12);
}

.data-log-table tbody tr:hover {
  background: rgba(13, 110, 253, 0.13);
  box-shadow: inset 3px 0 #0d6efd;
}

.data-log-table tbody td {
  padding: 10px;
  border: 0;
  border-bottom: 1px solid #24384d;
  color: #d7e3ef;
  vertical-align: middle;
}

.data-log-table tbody tr:last-child td {
  border-bottom: 0;
}

.data-log-table th:first-child { width: 62px; }
.data-log-table th:nth-child(2) { min-width: 205px; }
.data-log-table th:nth-child(3) { min-width: 150px; }
.data-log-table th:nth-child(4) { min-width: 125px; }
.data-log-table th:nth-child(5) { width: 110px; }
.data-log-table th:nth-child(6) { width: 135px; }
.data-log-table th:last-child { width: 245px; }

.sequence-cell span {
  display: inline-flex;
  width: 28px;
  height: 28px;
  align-items: center;
  justify-content: center;
  border: 1px solid #3b6087;
  border-radius: 8px;
  background: #162b41;
  color: #8fc1f5;
  font-weight: 700;
}

.target-cell strong,
.target-cell small {
  display: block;
}

.target-cell strong {
  color: #f0f6fc;
  font-size: 0.8rem;
  font-weight: 600;
}

.target-cell small {
  margin-top: 3px;
  color: #627b94;
  font-size: 0.61rem;
  letter-spacing: 0.06em;
}

.target-data,
.data-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.target-data > div {
  min-width: 0;
}

.table-data-icon {
  display: inline-flex;
  flex: 0 0 20px;
  width: 20px;
  height: 20px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: #d7e3ef;
  font-size: 0.86rem;
}

.source-icon {
  border: 0;
  background: transparent;
  color: #d7e3ef;
}

.type-icon {
  border: 0;
  background: transparent;
  color: #d7e3ef;
}

.importance-badge i,
.date-pill i {
  color: #ffffff;
}

.date-pill {
  display: inline-flex;
  min-width: 105px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 5px 8px;
  border: 1px solid #344e68;
  border-radius: 7px;
  background: #132437;
  color: #b8cce1;
  font-size: 0.7rem;
  white-space: nowrap;
}

.date-pill i {
  color: #6ea8fe;
}

.action-cell {
  min-width: 236px;
}

.row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  white-space: nowrap;
}

.row-actions .btn {
  display: inline-flex;
  min-height: 31px;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.row-actions .export-format-dropdown {
  min-width: 260px;
  padding: 8px;
  border: 1px solid #3b5269;
  border-radius: 7px;
  background: #101d2c;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.45);
  z-index: 1065 !important;
}

.export-dropdown-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 4px 8px 8px;
  margin-bottom: 4px;
  border-bottom: 1px solid rgba(184, 204, 225, 0.18);
}

.export-dropdown-header strong {
  color: #f4f8fc;
  font-size: 0.82rem;
}

.export-dropdown-header small {
  color: #9eb3c8;
  font-size: 0.66rem;
  line-height: 1.2;
  white-space: normal;
}

.row-actions .export-format-option {
  display: grid;
  min-height: 50px;
  grid-template-columns: 34px minmax(0, 1fr);
  align-items: center;
  gap: 9px;
  padding: 7px 8px;
  border-radius: 6px;
  color: #dfeaf6;
  font-size: 0.78rem;
}

.row-actions .export-format-option > span:last-child {
  display: flex;
  min-width: 0;
  flex-direction: column;
  line-height: 1.16;
}

.row-actions .export-format-option strong {
  color: #f7fbff;
  font-size: 0.82rem;
}

.row-actions .export-format-option small {
  margin-top: 3px;
  color: #a8bbcf;
  font-size: 0.66rem;
  white-space: normal;
}

.export-format-icon {
  display: inline-flex;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  font-size: 1rem;
}

.export-format-icon.pdf {
  background: rgba(220, 53, 69, 0.16);
  color: #ff7784;
}

.export-format-icon.word {
  background: rgba(47, 109, 179, 0.18);
  color: #6fb2ff;
}

.row-actions .export-format-option:hover {
  background: rgba(13, 110, 253, 0.2);
  color: #ffffff;
}

.analysis-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1600;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(2, 8, 15, 0.8);
  backdrop-filter: blur(7px);
}

.analysis-result-modal {
  display: flex;
  width: min(880px, 100%);
  max-height: min(90dvh, 760px);
  overflow: hidden;
  flex-direction: column;
  border: 1px solid #3b5f83;
  border-radius: 16px;
  background: radial-gradient(circle at 10% 0, rgba(27, 100, 173, 0.22), transparent 34%), #0b1724;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.65), 0 0 35px rgba(13, 110, 253, 0.14);
}

.analysis-result-header,
.analysis-result-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid #29435d;
  background: rgba(15, 35, 54, 0.92);
}

.analysis-result-title { display: flex; align-items: center; gap: 11px; }
.analysis-result-title > span,
.analysis-target-icon {
  display: inline-flex;
  width: 42px;
  height: 42px;
  align-items: center;
  justify-content: center;
  flex: 0 0 42px;
  border: 1px solid rgba(110, 168, 254, 0.5);
  border-radius: 11px;
  background: rgba(13, 110, 253, 0.15);
  color: #ffffff;
  font-size: 1.08rem;
  box-shadow: inset 0 0 12px rgba(13, 110, 253, 0.12);
}

.analysis-result-title small { display: block; color: #65a8ee; font-size: 0.58rem; font-weight: 800; letter-spacing: 0.13em; }
.analysis-result-title h3 { margin: 1px 0 0; color: #f2f7fc; font-size: 1.05rem; font-weight: 700; }

.analysis-modal-close {
  display: inline-grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border: 1px solid #48627c;
  border-radius: 9px;
  background: #182b3f;
  color: #dce8f4;
}

.analysis-modal-close:hover { border-color: #dc3545; background: #dc3545; color: #fff; }
.analysis-result-body { padding: 16px 18px; overflow: auto; }

.analysis-target-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #35536f;
  border-radius: 12px;
  background: linear-gradient(100deg, rgba(22, 60, 96, 0.68), rgba(13, 29, 45, 0.76));
}

.analysis-target-banner > div { display: flex; min-width: 0; flex: 1; flex-direction: column; }
.analysis-target-banner small { color: #75a9dc; font-size: 0.58rem; font-weight: 700; letter-spacing: 0.08em; }
.analysis-target-banner strong { color: #fff; font-size: 1rem; }
.analysis-target-banner > div > span { color: #9fb2c6; font-size: 0.72rem; }

.analysis-metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 9px;
  margin: 12px 0;
}

.analysis-metric-grid article {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 9px;
  padding: 10px;
  border: 1px solid #2d4761;
  border-radius: 11px;
  background: rgba(13, 29, 45, 0.88);
}

.analysis-metric-grid article > div { display: flex; min-width: 0; flex-direction: column; }
.analysis-metric-grid small { overflow: hidden; color: #8197ad; font-size: 0.56rem; text-overflow: ellipsis; white-space: nowrap; }
.analysis-metric-grid strong { overflow: hidden; color: #fff; font-size: 0.84rem; text-overflow: ellipsis; white-space: nowrap; }
.metric-icon { display: inline-grid; width: 31px; height: 31px; flex: 0 0 31px; place-items: center; border-radius: 8px; color: #fff; }
.metric-icon.confidence { background: #0d6efd; }
.metric-icon.weapon { background: #dc3545; }
.metric-icon.probability { background: #d39e00; }
.metric-icon.accuracy { background: #198754; }

.analysis-detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.analysis-detail-card,
.analysis-summary-card { padding: 13px; border: 1px solid #2c445d; border-radius: 11px; background: rgba(10, 24, 38, 0.8); }
.analysis-detail-grid h4 { margin: 0 0 10px; color: #dceaff; font-size: 0.78rem; }
.analysis-detail-grid h4 i { margin-right: 5px; color: #6ea8fe; }
.analysis-detail-card dl { margin: 0; }
.analysis-detail-card dl > div { display: flex; justify-content: space-between; gap: 12px; padding: 7px 0; border-bottom: 1px solid #20364b; }
.analysis-detail-card dl > div:last-child { border-bottom: 0; }
.analysis-detail-card dt { color: #7f94aa; font-size: 0.66rem; font-weight: 500; }
.analysis-detail-card dd { margin: 0; color: #e7f0f9; font-size: 0.68rem; font-weight: 600; text-align: right; }
.analysis-ready { color: #55d497; }
.analysis-summary-card p { margin: 0 0 10px; color: #b6c6d6; font-size: 0.7rem; line-height: 1.7; }
.analysis-advice { display: flex; gap: 8px; padding: 9px; border: 1px solid rgba(255, 193, 7, 0.28); border-radius: 8px; background: rgba(255, 193, 7, 0.08); color: #e5ca72; font-size: 0.66rem; }

.analysis-result-footer { border-top: 1px solid #29435d; border-bottom: 0; }
.analysis-result-footer > span { color: #8298ad; font-size: 0.65rem; }
.analysis-result-footer button { padding: 7px 13px; border: 1px solid #3978ba; border-radius: 8px; background: #0d6efd; color: #fff; font-family: inherit; font-size: 0.7rem; font-weight: 700; }

.delete-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1750;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(2, 8, 15, 0.82);
  backdrop-filter: blur(7px);
}

.delete-confirm-modal {
  position: relative;
  width: min(420px, 100%);
  padding: 24px;
  overflow: hidden;
  border: 1px solid #65404a;
  border-radius: 16px;
  background: radial-gradient(circle at 50% 0, rgba(220, 53, 69, 0.16), transparent 38%), #0b1724;
  box-shadow: 0 24px 75px rgba(0, 0, 0, 0.68), 0 0 30px rgba(220, 53, 69, 0.1);
  text-align: center;
}

.delete-modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  border: 1px solid #4d6175;
  border-radius: 8px;
  background: #17293b;
  color: #cbd8e5;
}

.delete-modal-close:hover { border-color: #dc3545; background: #dc3545; color: #fff; }
.delete-warning-icon { display: inline-grid; width: 62px; height: 62px; margin-bottom: 10px; place-items: center; border: 1px solid rgba(255, 101, 116, 0.52); border-radius: 50%; background: rgba(220, 53, 69, 0.16); box-shadow: 0 0 0 8px rgba(220, 53, 69, 0.05), 0 0 24px rgba(220, 53, 69, 0.2); color: #ff6877; font-size: 1.45rem; }
.delete-confirm-modal > small { display: block; color: #ff7180; font-size: 0.58rem; font-weight: 800; letter-spacing: 0.14em; }
.delete-confirm-modal h3 { margin: 4px 0 5px; color: #f3f7fb; font-size: 1.15rem; }
.delete-confirm-modal > p { margin: 0 0 13px; color: #8da1b5; font-size: 0.72rem; }

.delete-target-preview { display: flex; align-items: center; gap: 10px; padding: 10px; border: 1px solid #30475d; border-radius: 10px; background: rgba(15, 33, 50, 0.86); text-align: left; }
.delete-target-preview > span { display: inline-grid; width: 36px; height: 36px; flex: 0 0 36px; place-items: center; border-radius: 9px; background: rgba(13, 110, 253, 0.16); color: #72adf2; }
.delete-target-preview > div { display: flex; min-width: 0; flex-direction: column; }
.delete-target-preview strong { overflow: hidden; color: #f3f7fb; font-size: 0.78rem; text-overflow: ellipsis; white-space: nowrap; }
.delete-target-preview small { color: #738ba2; font-size: 0.6rem; }
.delete-warning-note { display: flex; align-items: center; justify-content: center; gap: 7px; margin: 10px 0 16px; color: #dbad60; font-size: 0.64rem; }
.delete-warning-note i { color: #ffc451; }
.delete-confirm-modal footer { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; }
.delete-confirm-modal footer button { display: inline-flex; min-height: 39px; align-items: center; justify-content: center; gap: 6px; border-radius: 9px; font-family: inherit; font-size: 0.72rem; font-weight: 700; }
.delete-cancel-button { border: 1px solid #4a6075; background: #17293b; color: #cbd7e2; }
.delete-cancel-button:hover { border-color: #71899f; background: #233b51; color: #fff; }
.delete-confirm-button { border: 1px solid #e44c5b; background: linear-gradient(135deg, #dc3545, #ad2532); box-shadow: 0 6px 16px rgba(220, 53, 69, 0.28); color: #fff; }
.delete-confirm-button:hover { background: linear-gradient(135deg, #ef4a5a, #c72b39); transform: translateY(-1px); }
.final-delete-backdrop { z-index: 1770; background: rgba(2, 6, 12, 0.9); }
.final-delete-modal { width: min(390px, 100%); border-color: #8c3c47; box-shadow: 0 28px 85px rgba(0, 0, 0, 0.78), 0 0 35px rgba(220, 53, 69, 0.18); }
.final-warning-icon { border-color: rgba(255, 80, 96, 0.68); background: rgba(220, 53, 69, 0.22); color: #ff5969; animation: finalWarningPulse 1.8s ease-in-out infinite; }
.final-delete-target { display: inline-flex; max-width: 100%; align-items: center; gap: 7px; margin: 0 0 16px; padding: 7px 11px; border: 1px solid rgba(220, 53, 69, 0.35); border-radius: 999px; background: rgba(220, 53, 69, 0.09); color: #f1b0b7; }
.final-delete-target strong { overflow: hidden; font-size: 0.7rem; text-overflow: ellipsis; white-space: nowrap; }
.final-confirm-button { background: linear-gradient(135deg, #ed3547, #9d1e2a); }
@keyframes finalWarningPulse { 50% { box-shadow: 0 0 0 12px rgba(220, 53, 69, 0.02), 0 0 30px rgba(220, 53, 69, 0.3); } }

.card {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  border: 2px solid #444444;
  border-radius: 8px;
  background: #111111;
}

.card-header {
  border-color: #444444;
}

.report-list-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 16px;
}

.scenario-summary-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
}

.scenario-summary-actions > span {
  margin-right: 4px;
  opacity: 0.9;
}

.scenario-summary-actions .btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  font-size: 0.78rem;
  font-weight: 600;
}

.card-body {
  color: #ffffff;
}

.card-title {
  color: #ffffff;
}

.btn-group-vertical .btn {
  border-radius: 4px;
  margin-bottom: 8px;
  border: 2px solid #444444;
}

.btn-group-vertical .btn:last-child {
  margin-bottom: 0;
}

table {
  font-size: 0.95rem;
  border: 2px solid #444444;
}

table thead {
  background: #1a1a1a;
  border-bottom: 2px solid #444444;
}

table tbody tr {
  border-bottom: 1px solid #333333;
  color: #ffffff;
}

table tbody tr:hover {
  background: #1a1a1a;
}

.badge {
  font-size: 0.85rem;
}

.alert {
  background: #111111;
  border: 2px solid #444444;
  color: #ffffff;
}

.text-muted {
  color: #aaaaaa;
}

h2 {
  color: #ffffff;
}

.fs-4 {
  color: #ffffff;
}

@media (max-width: 1500px) {
  .dashboard-panel-top .dashboard-content { grid-template-columns: repeat(2, minmax(345px, 1fr)); }
  .weapon-dashboard { grid-column: 1 / -1; }
}

@media (max-width: 1250px) {
  .filter-bar {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .date-filter { grid-column: span 2; }
  .search-filter { grid-column: span 2; }
  .clear-filter-button { grid-column: 4; grid-row: 1; }
}

@media (max-width: 900px) {
  .filter-bar { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .date-filter, .search-filter { grid-column: span 2; }
  .clear-filter-button { grid-column: 2; grid-row: 2; }
}

@media (max-width: 1050px) {
  .report-top-row {
    grid-template-columns: 1fr;
  }

  .report-heading {
    min-height: 112px;
  }

  .dashboard-panel-top {
    border-top: 1px solid #35506d;
    border-left: 0;
  }
}

@media (max-width: 767.98px) {
  .reports-page { height: auto; min-height: 100dvh; }
  .reports-container { overflow: visible; padding: 10px 0 18px; }
  .report-shell { max-width: 100%; padding-right: 8px; padding-left: 8px; }
  .report-top-row { gap: 8px; margin-bottom: 10px; }
  .report-heading { min-height: 86px; align-items: center; padding: 12px; }
  .report-heading h2 { font-size: 1.12rem; }
  .report-heading p, .report-kicker { display: none; }
  .summary-bar { padding-top: 5px; overflow: visible; }
  .summary-wheel { width: min(350px, 96vw); }
  .wheel-center { width: 126px; height: 126px; }
  .wheel-center strong { font-size: 1.8rem; }
  .wheel-stat { width: 108px; min-height: 56px; gap: 5px; padding: 6px; }
  .wheel-stat-icon { flex-basis: 25px; width: 25px; height: 25px; }
  .wheel-stat small { font-size: 0.47rem; }
  .wheel-stat strong { font-size: 0.86rem; }
  .updated-stat strong { font-size: 0.58rem; }
  .dashboard-panel { min-height: 310px; }
  .dashboard-content { gap: 7px; padding: 12px 8px; }
  .dashboard-panel .summary-wheel { flex-basis: 148px; width: 148px; max-width: 148px; }
  .dashboard-legend { min-width: 128px; }
  .dashboard-panel-top { min-height: 0; }
  .dashboard-panel-top .dashboard-content { grid-template-columns: 1fr; gap: 7px; padding: 8px; }
  .dashboard-panel.dashboard-panel-top .summary-wheel { flex-basis: 120px; width: 120px; max-width: 120px; }
  .dashboard-panel.dashboard-panel-top .summary-wheel::after { inset: 17px; border-width: 1px; }
  .dashboard-panel.dashboard-panel-top .wheel-center { width: 78px; height: 78px; border-width: 0; box-shadow: none; }
  .dashboard-panel-top .dashboard-legend { min-width: 0; max-width: none; }
  .dashboard-panel-top .source-summary { min-width: 0; max-width: none; }
  .source-rings-chart { width: 120px; height: 120px; flex-basis: 120px; }
  .weapon-stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .filter-bar { display: flex; align-items: stretch; flex-wrap: wrap; overflow: visible; }
  .filter-field { flex: 1 1 155px; }
  .date-filter { flex-basis: 280px; }
  .search-filter { flex-basis: 210px; }
  .clear-filter-button { flex: 1 1 130px; align-self: flex-end; }
  h2 { margin-bottom: 12px !important; font-size: 1.15rem; }
  .row { --bs-gutter-y: 12px; }
  .card-body { padding: 10px; }
  table { min-width: 720px; font-size: 0.82rem; }
  table td:last-child { white-space: nowrap; }
  .table-pagination { align-items: stretch; flex-direction: column; }
  .pagination-info { justify-content: center; flex-wrap: wrap; }
  .pagination-summary { justify-content: center; }
  .pagination-buttons { justify-content: center; }
  .analysis-modal-backdrop { padding: 8px; }
  .analysis-result-modal { max-height: 94dvh; }
  .analysis-result-header, .analysis-result-footer { padding: 11px 12px; }
  .analysis-result-body { padding: 12px; }
  .analysis-metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .analysis-detail-grid { grid-template-columns: 1fr; }
  .analysis-target-banner { align-items: flex-start; flex-wrap: wrap; }
}

/* Legacy scoped light rules are disabled; global rules below target the page correctly. */
@media not all {
:global(body.light-theme) .reports-page {
  background: #edf3f9;
  color: #172b3d;
}

:global(body.light-theme) .report-top-row,
:global(body.light-theme) .dashboard-panel-top {
  background: #edf3f9;
}

:global(body.light-theme) .report-heading {
  margin: 5px 12px 5px 0;
  padding-left: 16px;
  border: 1px solid #c8d7e5;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 6px 18px rgba(29, 65, 98, 0.1);
}

:global(body.light-theme) .report-heading h2 { color: #102a43; text-shadow: none; }
:global(body.light-theme) .report-heading p { color: #60758a; }
:global(body.light-theme) .report-kicker { color: #1769c2; text-shadow: none; }
:global(body.light-theme) .dashboard-panel-top { border-left-color: #b9c9d9; }

:global(body.light-theme) .dashboard-chart-group {
  border-color: #c7d5e3;
  background: linear-gradient(135deg, #ffffff, #eef5fb);
  box-shadow: 0 5px 14px rgba(31, 65, 98, 0.1);
}

:global(body.light-theme) .legend-section-title { color: #46647f; }
:global(body.light-theme) .legend-row,
:global(body.light-theme) .source-summary-row {
  border-color: #cfdae6;
  background: #f8fbfe;
  color: #243b53;
}

:global(body.light-theme) .dashboard-panel-top .legend-row strong,
:global(body.light-theme) .source-summary-row strong { color: #102a43; }
:global(body.light-theme) .dashboard-panel-top .legend-row small { color: #526d82; }
:global(body.light-theme) .legend-updated { border-color: #cfc6ed; background: #f1edfb; }
:global(body.light-theme) .legend-updated small { color: #6d6288; }
:global(body.light-theme) .legend-updated strong { color: #46386b; }
:global(body.light-theme) .source-ring-track { stroke: #d5e0ea; }
:global(body.light-theme) .source-rings-center strong { color: #16324a; text-shadow: none; }
:global(body.light-theme) .source-rings-center span { color: #60788e; }

:global(body.light-theme) .filter-bar {
  border-color: #c5d3e1;
  background: #ffffff;
  box-shadow: 0 6px 18px rgba(29, 65, 98, 0.1);
}

:global(body.light-theme) .filter-field label { color: #48627a; }
:global(body.light-theme) .filter-field input,
:global(body.light-theme) .filter-field select,
:global(body.light-theme) .custom-filter-toggle,
:global(body.light-theme) .date-input-wrap input {
  border-color: #b9cad9;
  background: #f8fbfe;
  color: #19324a;
  color-scheme: light;
}

:global(body.light-theme) .date-format-placeholder,
:global(body.light-theme) .search-input-wrap > i { color: #667f96; }
:global(body.light-theme) .date-input-wrap > i { color: #1769c2; text-shadow: none; }
:global(body.light-theme) .filter-dropdown-menu {
  border-color: #bdccda;
  background: #ffffff;
  box-shadow: 0 12px 28px rgba(26, 54, 82, 0.18);
}

:global(body.light-theme) .filter-dropdown-menu button { color: #263f57; }
:global(body.light-theme) .filter-dropdown-menu button:hover,
:global(body.light-theme) .filter-dropdown-menu button.active { background: #e5f0ff; color: #0d4f9f; }
:global(body.light-theme) .filter-dropdown-menu button > i:first-child { color: #315f8c; }
:global(body.light-theme) .clear-filter-button { border-color: #aebfd0; background: #eef3f8; color: #314b63; }
:global(body.light-theme) .clear-filter-button:hover:not(:disabled) { border-color: #c83f4d; background: #dc3545; color: #ffffff; }

:global(body.light-theme) .card {
  border-color: #c6d4e1;
  background: #ffffff;
  box-shadow: 0 6px 20px rgba(29, 61, 92, 0.1);
}

:global(body.light-theme) .card-body { color: #1d344a; }
:global(body.light-theme) .data-log-table { --bs-table-color: #20374d; }
:global(body.light-theme) .data-log-table thead th { border-bottom-color: #b8c9d9; background: linear-gradient(180deg, #e9f2fb, #dce9f5); color: #36536d; }
:global(body.light-theme) .data-log-table thead th > i { color: #2868a8; }
:global(body.light-theme) .data-log-table tbody tr:nth-child(odd) { background: #ffffff; }
:global(body.light-theme) .data-log-table tbody tr:nth-child(even) { background: #f5f9fc; }
:global(body.light-theme) .data-log-table tbody tr:hover { background: #e7f1ff; }
:global(body.light-theme) .data-log-table tbody td { border-bottom-color: #d8e2ec; color: #263f57; }
:global(body.light-theme) .target-cell strong { color: #142f46; }
:global(body.light-theme) .target-cell small { color: #6a8095; }
:global(body.light-theme) .table-data-icon { color: #245e96; }
:global(body.light-theme) .sequence-cell span { border-color: #a9bfd4; background: #eaf2fa; color: #245e96; }
:global(body.light-theme) .date-pill { background: #e8f1fa; color: #315b83; }
:global(body.light-theme) .row-actions .btn { background: #ffffff; }
:global(body.light-theme) .row-actions .btn-outline-primary { border-color: #4b8fd4; color: #1769b0; }
:global(body.light-theme) .row-actions .btn-outline-success { border-color: #54a77d; color: #187348; }
:global(body.light-theme) .row-actions .btn-outline-danger { border-color: #d56b75; color: #b52d3a; }
:global(body.light-theme) .row-actions .btn:hover { color: #ffffff; }
:global(body.light-theme) .row-actions .btn-outline-primary:hover { background: #0d6efd; }
:global(body.light-theme) .row-actions .btn-outline-success:hover { background: #198754; }
:global(body.light-theme) .row-actions .btn-outline-danger:hover { background: #dc3545; }
:global(body.light-theme) .row-actions .export-format-dropdown { border-color: #bdccda; background: #ffffff; box-shadow: 0 10px 25px rgba(27, 55, 82, 0.18); }
:global(body.light-theme) .export-dropdown-header { border-bottom-color: #d6e1ec; }
:global(body.light-theme) .export-dropdown-header strong,
:global(body.light-theme) .row-actions .export-format-option strong { color: #17324a; }
:global(body.light-theme) .export-dropdown-header small,
:global(body.light-theme) .row-actions .export-format-option small { color: #647c92; }
:global(body.light-theme) .row-actions .export-format-option { color: #29445c; }
:global(body.light-theme) .row-actions .export-format-option:hover { background: #e7f1ff; color: #0d5cab; }
:global(body.light-theme) .alert { border-color: #b8d7ee; background: #eef8ff; color: #31566f; }

:global(body.light-theme) .analysis-result-modal { border-color: #afc4d8; background: #f4f8fc; }
:global(body.light-theme) .analysis-result-header,
:global(body.light-theme) .analysis-result-footer { border-color: #cbd8e4; background: #e8f1f9; }
:global(body.light-theme) .analysis-modal-close { border-color: #afc2d3; background: #ffffff; color: #31516c; }
:global(body.light-theme) .analysis-result-title h3,
:global(body.light-theme) .analysis-target-banner strong,
:global(body.light-theme) .analysis-metric-grid strong { color: #17324a; }
:global(body.light-theme) .analysis-target-banner,
:global(body.light-theme) .analysis-metric-grid article,
:global(body.light-theme) .analysis-detail-card,
:global(body.light-theme) .analysis-summary-card { border-color: #c4d3e1; background: #ffffff; }
:global(body.light-theme) .analysis-detail-grid h4 { color: #24445f; }
:global(body.light-theme) .analysis-detail-card dd { color: #203b52; }
:global(body.light-theme) .analysis-summary-card p { color: #4d657b; }
:global(body.light-theme) .analysis-detail-card dt { color: #637b91; }
:global(body.light-theme) .analysis-detail-card dl > div { border-bottom-color: #dce5ed; }
:global(body.light-theme) .analysis-target-banner > div > span,
:global(body.light-theme) .analysis-target-banner small,
:global(body.light-theme) .analysis-metric-grid small { color: #60788e; }
:global(body.light-theme) .reports-container { scrollbar-color: #9bb0c3 #e4ecf3; }
}
</style>

<style>
body.light-theme .reports-page {
  background: #edf3f9 !important;
  color: #172b3d;
}

body.light-theme .reports-page .report-top-row,
body.light-theme .reports-page .dashboard-panel-top { background: #edf3f9 !important; }
body.light-theme .reports-page .report-heading { margin: 5px 12px 5px 0; padding-left: 16px; border: 1px solid #c8d7e5; border-radius: 12px; background: #fff !important; box-shadow: 0 6px 18px rgba(29,65,98,.1); }
body.light-theme .reports-page .report-heading h2 { color: #102a43 !important; text-shadow: none; }
body.light-theme .reports-page .report-heading p { color: #60758a; }
body.light-theme .reports-page .report-kicker { color: #1769c2; text-shadow: none; }

body.light-theme .reports-page .dashboard-chart-group { border-color: #c7d5e3; background: linear-gradient(135deg,#fff,#eef5fb) !important; box-shadow: 0 5px 14px rgba(31,65,98,.1); }
body.light-theme .reports-page .legend-section-title { color: #46647f; }
body.light-theme .reports-page .legend-row,
body.light-theme .reports-page .source-summary-row { border-color: #cfdae6; background: #f8fbfe !important; color: #243b53; }
body.light-theme .reports-page .legend-row strong,
body.light-theme .reports-page .source-summary-row strong { color: #102a43; }
body.light-theme .reports-page .legend-row small { color: #526d82; }
body.light-theme .reports-page .legend-updated { border-color: #cfc6ed; background: #f1edfb !important; }
body.light-theme .reports-page .legend-updated small { color: #6d6288; }
body.light-theme .reports-page .legend-updated strong { color: #46386b; }
body.light-theme .reports-page .source-ring-track { stroke: #d5e0ea; }
body.light-theme .reports-page .source-rings-center strong { color: #16324a; text-shadow: none; }
body.light-theme .reports-page .source-rings-center span { color: #60788e; }
body.light-theme .reports-page .weapon-stat { border-color: #cfdae6; background: #f8fbfe !important; }
body.light-theme .reports-page .weapon-stat small,
body.light-theme .reports-page .weapon-dashboard-head small { color: #526d82; }
body.light-theme .reports-page .weapon-stat strong,
body.light-theme .reports-page .weapon-product-row strong { color: #102a43; }
body.light-theme .reports-page .weapon-stat strong span { color: #60788e; }
body.light-theme .reports-page .weapon-product-row { color: #243b53; }
body.light-theme .reports-page .weapon-product-bar,
body.light-theme .reports-page .weapon-selection-bar { background: #d5e0ea; }
body.light-theme .reports-page .weapon-selection-legend { color: #46647f; }
body.light-theme .reports-page .weapon-more,
body.light-theme .reports-page .weapon-empty { color: #60788e; }

body.light-theme .reports-page .filter-bar { border-color: #c5d3e1; background: #fff !important; box-shadow: 0 6px 18px rgba(29,65,98,.1); }
body.light-theme .reports-page .filter-field label { color: #48627a; }
body.light-theme .reports-page .filter-field input,
body.light-theme .reports-page .filter-field select,
body.light-theme .reports-page .custom-filter-toggle,
body.light-theme .reports-page .date-input-wrap input { border-color: #b9cad9 !important; background: #f8fbfe !important; color: #19324a !important; color-scheme: light; }
body.light-theme .reports-page .date-format-placeholder,
body.light-theme .reports-page .search-input-wrap > i { color: #667f96; }
body.light-theme .reports-page .date-input-wrap > i { color: #1769c2; text-shadow: none; }
body.light-theme .reports-page .filter-dropdown-menu { border-color: #bdccda; background: #fff !important; box-shadow: 0 12px 28px rgba(26,54,82,.18); }
body.light-theme .reports-page .filter-dropdown-menu button { color: #263f57; }
body.light-theme .reports-page .filter-dropdown-menu button:hover,
body.light-theme .reports-page .filter-dropdown-menu button.active { background: #e5f0ff !important; color: #0d4f9f; }
body.light-theme .reports-page .filter-dropdown-menu button > i:first-child { color: #315f8c; }
body.light-theme .reports-page .clear-filter-button { border-color: #aebfd0; background: #eef3f8 !important; color: #314b63; }

body.light-theme .reports-page .card { border-color: #c6d4e1 !important; background: #fff !important; box-shadow: 0 6px 20px rgba(29,61,92,.1); }
body.light-theme .reports-page .card-body { background: #fff !important; color: #1d344a !important; }
body.light-theme .reports-page .report-table-block { border-color: #c8d6e3; background: #fff; }
body.light-theme .reports-page .table-pagination { border-top-color: #cfdae5; background: #f4f8fc; }
body.light-theme .reports-page .pagination-summary { color: #526d82; }
body.light-theme .reports-page .page-size-control { color: #526d82; }
body.light-theme .reports-page .pagination-size-input { border: 1px solid #b8c9d8 !important; background: #fff !important; color: #24445f !important; }
body.light-theme .reports-page .pagination-buttons button { border-color: #b8c9d8; background: #fff; color: #38556e; }
body.light-theme .reports-page .pagination-buttons button:hover:not(:disabled) { border-color: #4b91e2; background: #e5f1ff; color: #0d5ba8; }
body.light-theme .reports-page .pagination-buttons button.active { border-color: #0d6efd; background: #0d6efd; color: #fff; }
body.dark-theme .reports-page .pagination-size-input { border: 1px solid #3a536c !important; background: #16283a !important; color: #e8f1fa !important; }
body.light-theme .reports-page .data-log-table thead th { border-bottom-color: #b8c9d9 !important; background: linear-gradient(180deg,#e9f2fb,#dce9f5) !important; color: #36536d !important; }
body.light-theme .reports-page .data-log-table thead th > i { color: #2868a8; }
body.light-theme .reports-page .data-log-table tbody tr:nth-child(odd) { background: #fff !important; }
body.light-theme .reports-page .data-log-table tbody tr:nth-child(even) { background: #f5f9fc !important; }
body.light-theme .reports-page .data-log-table tbody tr:hover { background: #e7f1ff !important; }
body.light-theme .reports-page .data-log-table tbody td { border-bottom-color: #d8e2ec !important; background: transparent !important; color: #263f57 !important; }
body.light-theme .reports-page .target-cell strong { color: #142f46; }
body.light-theme .reports-page .target-cell small { color: #6a8095; }
body.light-theme .reports-page .table-data-icon { color: #245e96; }
body.light-theme .reports-page .sequence-cell span { border-color: #a9bfd4; background: #eaf2fa; color: #245e96; }
body.light-theme .reports-page .date-pill { background: #e8f1fa; color: #315b83; }

body.light-theme .reports-page .row-actions .btn { background: #fff; }
body.light-theme .reports-page .row-actions .export-format-dropdown { border-color: #bdccda; background: #fff !important; }
body.light-theme .reports-page .export-dropdown-header { border-bottom-color: #d6e1ec; }
body.light-theme .reports-page .export-dropdown-header strong,
body.light-theme .reports-page .row-actions .export-format-option strong { color: #17324a; }
body.light-theme .reports-page .export-dropdown-header small,
body.light-theme .reports-page .row-actions .export-format-option small { color: #647c92; }
body.light-theme .reports-page .row-actions .export-format-option { color: #29445c; }
body.light-theme .reports-page .row-actions .export-format-option:hover { background: #e7f1ff; color: #0d5cab; }

body.light-theme .reports-page .analysis-result-modal { border-color: #afc4d8; background: #f4f8fc !important; }
body.light-theme .reports-page .analysis-result-header,
body.light-theme .reports-page .analysis-result-footer { border-color: #cbd8e4; background: #e8f1f9 !important; }
body.light-theme .reports-page .analysis-target-banner,
body.light-theme .reports-page .analysis-metric-grid article,
body.light-theme .reports-page .analysis-detail-card,
body.light-theme .reports-page .analysis-summary-card { border-color: #c4d3e1; background: #fff !important; }
body.light-theme .reports-page .analysis-result-title h3,
body.light-theme .reports-page .analysis-target-banner strong,
body.light-theme .reports-page .analysis-metric-grid strong,
body.light-theme .reports-page .analysis-detail-card dd { color: #17324a; }
body.light-theme .reports-page .analysis-summary-card p { color: #4d657b; }
body.light-theme .reports-page .delete-confirm-modal { border-color: #e1b7bc; background: radial-gradient(circle at 50% 0,rgba(220,53,69,.1),transparent 38%),#fff !important; box-shadow: 0 24px 70px rgba(40,65,88,.22); }
body.light-theme .reports-page .delete-modal-close { border-color: #b9cad9; background: #f5f8fb; color: #38546d; }
body.light-theme .reports-page .delete-confirm-modal h3 { color: #17324a; }
body.light-theme .reports-page .delete-confirm-modal > p { color: #60778c; }
body.light-theme .reports-page .delete-target-preview { border-color: #cbd8e4; background: #f5f9fc; }
body.light-theme .reports-page .delete-target-preview strong { color: #17324a; }
body.light-theme .reports-page .delete-target-preview small { color: #6b8297; }
body.light-theme .reports-page .delete-cancel-button { border-color: #b3c4d3; background: #f1f5f9; color: #385268; }
body.light-theme .reports-page .final-delete-modal { border-color: #e0a7ae; background: radial-gradient(circle at 50% 0,rgba(220,53,69,.12),transparent 40%),#fff !important; }
body.light-theme .reports-page .final-delete-target { border-color: #e1b7bc; background: #fff3f4; color: #9b3440; }
</style>
