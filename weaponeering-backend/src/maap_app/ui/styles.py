from __future__ import annotations

APP_STYLESHEET = """
QMainWindow {
    background: #080c12;
    color: #d7dee8;
}

QWidget#AppRoot {
    background: #080c12;
}

QWidget#HeaderBar,
QWidget#AppChrome {
    background: #0c1219;
}

QWidget#MainToolbar {
    background: #0c1219;
    border-bottom: 1px solid #1a2433;
}

QScrollArea#ToolbarScroll {
    background: transparent;
    border: none;
}

QScrollArea#ToolbarScroll > QWidget > QWidget {
    background: transparent;
}

QScrollArea#ToolbarScroll QScrollBar:horizontal {
    height: 4px;
    background: transparent;
    margin: 0 4px 2px 4px;
}

QScrollArea#ToolbarScroll QScrollBar::handle:horizontal {
    background: #243041;
    border-radius: 2px;
    min-width: 24px;
}

QScrollArea#ToolbarScroll QScrollBar::add-line:horizontal,
QScrollArea#ToolbarScroll QScrollBar::sub-line:horizontal {
    width: 0;
}

QWidget#SubNavBar {
    background: #0a1018;
    border-bottom: 1px solid #1a2433;
}

QLabel#ToolGroupLabel {
    font-size: 10px;
    font-weight: 700;
    color: #5f7389;
    letter-spacing: 0.4px;
    text-transform: uppercase;
}

QPushButton#ToolGroupButton {
    background: transparent;
    color: #9fb0c2;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 11px;
    font-weight: 600;
    min-height: 28px;
}

QPushButton#ToolGroupButton:hover {
    background: #111a24;
    color: #d7dee8;
}

QPushButton#SubNavTab {
    background: transparent;
    color: #6b7f96;
    border: none;
    border-radius: 6px 6px 0 0;
    padding: 8px 14px;
    font-size: 11px;
    font-weight: 600;
}

QPushButton#SubNavTab:hover {
    color: #9fb0c2;
    background: #111a24;
}

QPushButton#SubNavTab:checked,
QPushButton#SubNavTab[active="true"] {
    background: #172433;
    color: #60a5fa;
    border-bottom: 2px solid #2563eb;
}

QPushButton#SubNavLink {
    background: transparent;
    color: #5f7389;
    border: none;
    padding: 6px 10px;
    font-size: 11px;
}

QPushButton#SubNavLink:hover {
    color: #9fb0c2;
}

QLabel#SubNavLlmLabel {
    color: #6b7f96;
    font-size: 11px;
    padding-right: 4px;
}

QComboBox#SubNavLlmCombo {
    background: #121a24;
    color: #d7e0ea;
    border: 1px solid #243244;
    border-radius: 6px;
    padding: 4px 8px;
    min-width: 110px;
    font-size: 11px;
}

QComboBox#SubNavLlmCombo:hover {
    border-color: #3b4f66;
}

QComboBox#SubNavLlmCombo::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    border: none;
    width: 22px;
}

QComboBox#SubNavLlmCombo::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #6b7f96;
    margin-right: 6px;
}

QComboBox#SubNavLlmCombo QAbstractItemView {
    background: #121a24;
    color: #d7e0ea;
    selection-background-color: #1e3a5f;
}

QTabBar::tab {
    background: transparent;
    color: #6b7f96;
    padding: 8px 12px;
}

QLabel#AppTitle {
    font-size: 14px;
    font-weight: 700;
    color: #eef3f8;
}

QLabel#AppSubtitle {
    font-size: 10px;
    color: #6b7f96;
}

QPushButton#PrimaryButton {
    background: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 11px;
    min-height: 28px;
}

QPushButton#PrimaryButton:hover {
    background: #3b82f6;
}

QPushButton#SecondaryButton {
    background: #111a24;
    color: #c8d4e0;
    border: 1px solid #243041;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton#SecondaryButton:hover {
    background: #172433;
    border-color: #334155;
}

QPushButton#DangerButton {
    background: #1e0f0f;
    color: #f87171;
    border: 1px solid #7f1d1d;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton#DangerButton:hover {
    background: #2c1010;
    border-color: #ef4444;
    color: #fca5a5;
}

QPushButton#DangerButton:disabled {
    background: #0e1318;
    color: #4a3535;
    border-color: #2a1a1a;
}

QLineEdit#SearchInput {
    background: #0b121a;
    color: #c8d4e0;
    border: 1px solid #1e2a3a;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
}

QLineEdit {
    background: #0b121a;
    color: #c8d4e0;
    border: 1px solid #1e2a3a;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 12px;
    min-height: 24px;
}

QLineEdit:focus {
    border-color: #2563eb;
    background: #0f1720;
}

QLineEdit:disabled {
    color: #5f7389;
    background: #090f16;
}

QComboBox {
    background: #0b121a;
    color: #c8d4e0;
    border: 1px solid #1e2a3a;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 12px;
    min-height: 24px;
}

QComboBox:focus {
    border-color: #2563eb;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background: #0f1720;
    color: #d7dee8;
    border: 1px solid #243041;
    selection-background-color: #1e3a5f;
}

QComboBox#ScenarioCombo {
    background: #0b121a;
    color: #c8d4e0;
    border: 1px solid #1e2a3a;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 11px;
    min-width: 120px;
    min-height: 28px;
}

QComboBox#ScenarioCombo::drop-down {
    border: none;
    width: 24px;
}

QComboBox#ScenarioCombo QAbstractItemView {
    background: #0f1720;
    color: #d7dee8;
    border: 1px solid #243041;
    selection-background-color: #1e3a5f;
}

QComboBox#ChatModeCombo {
    background: #0d1722;
    color: #c8d4e0;
    border: 1px solid #243041;
    border-radius: 10px;
    padding: 7px 10px;
    font-size: 11px;
    min-height: 32px;
    min-width: 140px;
}

QComboBox#ChatModeCombo:focus {
    border-color: #3b82f6;
}

QComboBox#ChatModeCombo::drop-down {
    border: none;
    width: 22px;
}

QComboBox#ChatModeCombo QAbstractItemView {
    background: #0f1720;
    color: #d7dee8;
    border: 1px solid #243041;
    selection-background-color: #1e3a5f;
}

QWidget#TargetThreadPanel {
    background: #081018;
    border: 1px solid #1b2a3a;
    border-radius: 12px;
}

QWidget#ToolsPanel {
    background: #081018;
    border: 1px solid #1b2a3a;
    border-radius: 12px;
}

QTextEdit#ToolsDetail {
    background: #070d14;
    color: #c8d4e0;
    border: 1px solid #172334;
    border-radius: 10px;
    padding: 10px;
    font-size: 11px;
}

QLabel#ThreadPanelTitle {
    color: #eef3f8;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.7px;
}

QLabel#ThreadPanelSubtitle {
    color: #6f8298;
    font-size: 11px;
}

QListWidget#TargetThreadList {
    background: #070d14;
    border: 1px solid #172334;
    border-radius: 12px;
    padding: 8px;
    outline: none;
}

QListWidget#TargetThreadList::item {
    background: transparent;
    border: none;
    margin: 2px 0;
}

QListWidget#TargetThreadList::item:selected {
    background: rgba(37, 99, 235, 0.18);
    border: 1px solid #2563eb;
    border-radius: 10px;
}

QWidget#TargetThreadCard {
    background: #0d1722;
    border: 1px solid #1f2d3d;
    border-radius: 10px;
}

QWidget#TargetThreadCard[active="true"] {
    background: #0e1f38;
    border: 1px solid #2563eb;
    border-left: 3px solid #3b82f6;
    border-radius: 10px;
}

QWidget#TargetThreadCardScenario {
    background: #091820;
    border: 1px solid #164e4e;
    border-radius: 10px;
}

QWidget#TargetThreadCardScenario[active="true"] {
    background: #0b2828;
    border: 1px solid #0891b2;
    border-left: 3px solid #06b6d4;
    border-radius: 10px;
}

QLabel#ThreadCardTitle {
    color: #dce6f2;
    font-size: 12px;
    font-weight: 800;
}

QLabel#ThreadCardScenarioTitle {
    color: #67e8f9;
    font-size: 12px;
    font-weight: 800;
}

QLabel#ThreadCardSubtitle {
    color: #7f93aa;
    font-size: 10px;
}

QLabel#ThreadCardBadge {
    background: #111827;
    color: #93c5fd;
    border: 1px solid #1e40af;
    border-radius: 9px;
    padding: 3px 7px;
    font-size: 9px;
    font-weight: 800;
}

QLabel#ThreadCardAllBadge {
    background: #0d2a1c;
    color: #86efac;
    border: 1px solid #166534;
    border-radius: 9px;
    padding: 3px 7px;
    font-size: 9px;
    font-weight: 800;
}

QWidget#ChatPanel {
    background: #081018;
    border: 1px solid #1b2a3a;
    border-radius: 12px;
}

QWidget#ChatHeader {
    background: #0d1722;
    border: 1px solid #1d2b3d;
    border-radius: 10px;
}

QLabel#ChatTitle {
    color: #eef3f8;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.6px;
}

QLabel#ChatSubtitle {
    color: #7f93aa;
    font-size: 11px;
}

QLabel#ChatBadge {
    background: #0d2a1c;
    color: #86efac;
    border: 1px solid #166534;
    border-radius: 12px;
    padding: 4px 10px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

QListWidget#ChatList {
    background: #070d14;
    border: 1px solid #172334;
    border-radius: 12px;
    padding: 12px;
    outline: none;
}

QListWidget#ChatList::item {
    background: transparent;
    border: none;
}

QListWidget#ChatList::item:selected {
    background: rgba(37, 99, 235, 0.16);
    border: 1px solid #2563eb;
    border-radius: 10px;
}

QTextEdit#ChatComposer {
    background: #0b121a;
    color: #d7dee8;
    border: 1px solid #243041;
    border-radius: 12px;
    padding: 10px 12px;
    font-size: 13px;
    selection-background-color: #1d4ed8;
}

QTextEdit#ChatComposer:focus {
    border-color: #3b82f6;
    background: #0e1722;
}

QPushButton#ChatSendButton {
    background: #2563eb;
    color: #ffffff;
    border: 1px solid #3b82f6;
    border-radius: 10px;
    padding: 9px 22px;
    font-weight: 800;
    font-size: 12px;
    min-height: 34px;
    min-width: 96px;
}

QPushButton#ChatSendButton:hover {
    background: #3b82f6;
}

QPushButton#ChatSendButton:disabled {
    background: #1e293b;
    color: #64748b;
    border-color: #334155;
}

QLabel#ChatStatus {
    color: #6f8298;
    font-size: 11px;
}

QWidget#ChatItem {
    background: transparent;
}

QLabel#UserBubble {
    background: #1d4ed8;
    color: #eef6ff;
    border: 1px solid #60a5fa;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 500;
}

QLabel#AiBubble {
    background: #101923;
    color: #dce6f2;
    border: 1px solid #2b3a4d;
    border-radius: 12px;
    font-size: 13px;
}

QLabel#BlockedBubble {
    background: #241316;
    color: #fecaca;
    border: 1px solid #7f1d1d;
    border-radius: 12px;
    font-size: 13px;
}

QLabel#TypingBubble {
    background: #0d1520;
    color: #4a6080;
    border: 1px solid #1e2d3d;
    border-radius: 12px;
    font-size: 13px;
    font-style: italic;
}

QLabel#ChatMeta {
    color: #5f7389;
    font-size: 10px;
    padding-top: 2px;
}

QLabel#ThreadOriginTag {
    color: #7c9ab8;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding: 2px 0px;
    border-top: 1px solid #1e2d3d;
    margin-top: 4px;
}

QLabel#StatusPill {
    background: #0f1f17;
    color: #4ade80;
    border: 1px solid #166534;
    border-radius: 14px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#AvatarBadge {
    background: #1e3a5f;
    color: #93c5fd;
    border: 1px solid #2563eb;
    border-radius: 16px;
    padding: 6px 10px;
    font-size: 11px;
    font-weight: 700;
}

QWidget#SidePanel {
    background: #0a1018;
    border: 1px solid #1a2433;
    border-radius: 10px;
}

QLabel#SectionTitle {
    font-size: 12px;
    font-weight: 700;
    color: #8fa3b8;
    letter-spacing: 0.5px;
}

QLabel#SectionSubtitle {
    font-size: 11px;
    color: #5f7389;
}

QWidget#TargetCard {
    background: #0d141d;
    border: 1px solid #1c2836;
    border-radius: 8px;
}

QWidget#TargetCard[selected="true"] {
    border-color: #2563eb;
    background: #101c2b;
}

QLabel#CardTitle {
    font-size: 13px;
    font-weight: 700;
    color: #eef3f8;
}

QLabel#TagBadge {
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
}

QLabel#TagTraining {
    background: #172554;
    color: #93c5fd;
    border: 1px solid #1e40af;
}

QLabel#TagPlaceholder {
    background: #1f2937;
    color: #9ca3af;
    border: 1px solid #374151;
}

QPushButton#GuardrailOnButton {
    background: #052e16;
    color: #86efac;
    border: 1px solid #166534;
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
}

QPushButton#GuardrailOnButton:hover {
    background: #14532d;
    border-color: #22c55e;
}

QPushButton#GuardrailOffButton {
    background: #431407;
    color: #fdba74;
    border: 1px solid #c2410c;
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
}

QPushButton#GuardrailOffButton:hover {
    background: #7c2d12;
    border-color: #f97316;
}

QPushButton#CotOnButton {
    background: #0c1a2e;
    color: #93c5fd;
    border: 1px solid #1d4ed8;
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
}

QPushButton#CotOnButton:hover {
    background: #1e3a5f;
    border-color: #3b82f6;
}

QPushButton#CotOffButton {
    background: #1e1b4b;
    color: #c4b5fd;
    border: 1px solid #5b21b6;
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
}

QPushButton#CotOffButton:hover {
    background: #2e1065;
    border-color: #7c3aed;
}

QLabel#TagSupport {
    background: #2e1065;
    color: #c4b5fd;
    border: 1px solid #5b21b6;
}

QPushButton#GhostButton {
    background: transparent;
    color: #7dd3fc;
    border: 1px dashed #1e3a5f;
    border-radius: 8px;
    padding: 10px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton#GhostButton:hover {
    background: #0f1a28;
    border-color: #2563eb;
}

QWidget#DetailPanel {
    background: #0b121a;
    border: 1px solid #1c2836;
    border-radius: 8px;
}

QLabel#DetectionPreview {
    background: #060a10;
    border: none;
    border-radius: 0;
    color: #6b7f96;
    font-size: 11px;
    padding: 4px;
}

QWidget#DetectionPreviewFrame {
    background: #060a10;
    border: 1px solid #1e2d42;
    border-radius: 8px;
}

QCheckBox {
    color: #9fb0c2;
    font-size: 11px;
    font-weight: 600;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid #243041;
    background: #0d141f;
}

QCheckBox::indicator:checked {
    background: #1d4ed8;
    border-color: #2563eb;
}

QWidget#FormCard {
    background: #0d141f;
    border: 1px solid #1e2d42;
    border-radius: 10px;
}

QLabel#FormSectionTitle {
    font-size: 12px;
    font-weight: 700;
    color: #e8f0f8;
}

QLabel#FormSectionSubtitle {
    font-size: 11px;
    color: #6b7f96;
    margin-bottom: 2px;
}

QLabel#FormFieldLabel {
    font-size: 11px;
    font-weight: 600;
    color: #8fa3b8;
}

QWidget#MapWorkspace {
    background: #0a1018;
    border: 1px solid #1a2433;
    border-radius: 10px;
}

QWidget#MapWorkspaceHeader {
    background: #0c1219;
    border-bottom: 1px solid #1a2433;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}

QLabel#MapWorkspaceTitle {
    font-size: 13px;
    font-weight: 700;
    color: #eef3f8;
}

QWidget#MapFloatingToolbar {
    background: rgba(10, 16, 24, 230);
    border: 1px solid #2a3a4f;
    border-radius: 10px;
}

QLabel#MapToolbarLabel {
    color: #9fb0c2;
    font-size: 11px;
    font-weight: 600;
}

QFrame#MapToolbarDivider {
    color: #2a3a4f;
    background: #2a3a4f;
    max-width: 1px;
    margin: 2px 2px;
}

QToolButton#MapToolbarButton {
    background: transparent;
    color: #d7dee8;
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 600;
}

QToolButton#MapToolbarButton:hover {
    background: #172433;
    color: #f1f5f9;
}

QToolButton#MapToolbarButton:checked {
    background: #1a2d42;
    color: #7dd3fc;
}

QPushButton#MapToolbarAccentButton {
    background: #132033;
    color: #e2e8f0;
    border: 1px solid #38bdf8;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 700;
}

QPushButton#MapToolbarAccentButton:hover {
    background: #1a3048;
    color: #f8fafc;
}

QComboBox#MapToolbarCombo,
QSpinBox#MapToolbarSpin {
    background: #111a24;
    color: #e2e8f0;
    border: 1px solid #2a3a4f;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    min-height: 22px;
}

QComboBox#MapToolbarCombo::drop-down,
QSpinBox#MapToolbarSpin::up-button,
QSpinBox#MapToolbarSpin::down-button {
    border: none;
    width: 16px;
}

QComboBox#MapToolbarCombo QAbstractItemView {
    background: #0d141d;
    color: #e2e8f0;
    border: 1px solid #2a3a4f;
    selection-background-color: #1a3048;
}

QMenu#MapToolbarMenu {
    background: #0d141d;
    color: #e2e8f0;
    border: 1px solid #2a3a4f;
    padding: 4px;
}

QMenu#MapToolbarMenu::item {
    padding: 6px 18px;
}

QMenu#MapToolbarMenu::item:selected {
    background: #1a3048;
}

QMenu#MapToolbarMenu::item:selected {
    background: #1a3048;
}

QWidget#DetailPanel {
    background: #0a1018;
    border-right: 1px solid #1a2433;
}

QWidget#MapTargetSidebarHeader {
    background: #0c1219;
    border-bottom: 1px solid #1a2433;
}

QLabel#MapTargetSidebarTitle {
    font-size: 12px;
    font-weight: 700;
    color: #eef3f8;
    letter-spacing: 0.8px;
}

QPushButton#MapTargetIconButton,
QToolButton#MapTargetIconButton {
    background: #111a24;
    color: #9fb0c2;
    border: 1px solid #243041;
    border-radius: 6px;
    padding: 2px 6px;
    font-size: 12px;
    font-weight: 700;
}

QPushButton#MapTargetIconButton:hover,
QToolButton#MapTargetIconButton:hover {
    background: #172433;
    color: #e2e8f0;
}

QLineEdit#MapTargetSearch {
    background: #0d141d;
    color: #e2e8f0;
    border: 1px solid #243041;
    border-radius: 8px;
    padding: 7px 10px;
    font-size: 11px;
}

QLineEdit#MapTargetSearch:focus {
    border-color: #2563eb;
}

QWidget#MapTargetStatCard {
    background: #0d141d;
    border: 1px solid #1c2836;
    border-radius: 8px;
}

QLabel#MapTargetStatTitle[tier="high"] { color: #f87171; }
QLabel#MapTargetStatTitle[tier="medium"] { color: #fbbf24; }
QLabel#MapTargetStatTitle[tier="low"] { color: #4ade80; }
QLabel#MapTargetStatTitle { color: #8fa3b8; font-size: 10px; font-weight: 600; }

QLabel#MapTargetStatValue[tier="high"] { color: #f87171; }
QLabel#MapTargetStatValue[tier="medium"] { color: #fbbf24; }
QLabel#MapTargetStatValue[tier="low"] { color: #4ade80; }
QLabel#MapTargetStatValue { color: #eef3f8; font-size: 14px; font-weight: 700; }

QComboBox#MapTargetSortCombo {
    background: #0d141d;
    color: #d7dee8;
    border: 1px solid #243041;
    border-radius: 8px;
    padding: 6px 8px;
    font-size: 11px;
}

QScrollArea#MapTargetScroll {
    background: transparent;
    border: none;
}

QFrame#MapTargetListCard {
    background: #0d141d;
    border: 1px solid #1c2836;
    border-radius: 8px;
}

QFrame#MapTargetListCard[selected="true"] {
    border-color: #2563eb;
    background: #101c2b;
}

QLabel#MapTargetCardTitle {
    font-size: 12px;
    font-weight: 700;
    color: #eef3f8;
}

QLabel#MapTargetPriorityBadge {
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
}

QLabel#MapTargetPriorityBadge[tier="high"] {
    color: #fca5a5;
    border: 1px solid #7f1d1d;
    background: #2a1010;
}

QLabel#MapTargetPriorityBadge[tier="medium"] {
    color: #fcd34d;
    border: 1px solid #78350f;
    background: #2a1d08;
}

QLabel#MapTargetPriorityBadge[tier="low"] {
    color: #86efac;
    border: 1px solid #14532d;
    background: #0f2218;
}

QLabel#MapTargetMutedLabel {
    color: #6b7f96;
    font-size: 10px;
}

QLabel#MapTargetMetaLabel {
    color: #6b7f96;
    font-size: 10px;
}

QLabel#MapTargetMetaValue {
    color: #d7dee8;
    font-size: 10px;
    font-weight: 600;
}

QPushButton#MapTargetFooterButton {
    background: #0d141d;
    color: #9fb0c2;
    border: 1px solid #243041;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 11px;
    font-weight: 600;
    text-align: left;
}

QPushButton#MapTargetFooterButton:hover {
    background: #111a24;
    color: #e2e8f0;
    border-color: #2563eb;
}

QWidget#MapTargetDetailOverlay {
    background: rgba(10, 16, 24, 235);
    border: 1px solid #2a3a4f;
    border-radius: 10px;
}

QWidget#MapTargetDetailOverlayHeader {
    background: #0c1219;
    border-bottom: 1px solid #1a2433;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}

QLabel#MapTargetDetailOverlayTitle {
    font-size: 12px;
    font-weight: 700;
    color: #eef3f8;
}

QPushButton#MapTargetDetailCloseButton {
    background: transparent;
    color: #9fb0c2;
    border: 1px solid #243041;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 700;
    padding: 0;
}

QPushButton#MapTargetDetailCloseButton:hover {
    background: #172433;
    color: #f87171;
    border-color: #7f1d1d;
}

QWidget#MapTargetDetailOverlayBody {
    background: transparent;
}

QWidget#MapFlightRouteEditorSection {
    background: transparent;
}

QWidget#MapFlightRouteEditorDivider {
    background: #1a2433;
}

QWidget#MapFlightRouteEditorHeader {
    background: #0c1219;
    border-top: 1px solid #1a2433;
}

QLabel#MapFlightRouteEditorTitle {
    font-size: 12px;
    font-weight: 700;
    color: #eef3f8;
}

QWidget#MapFlightRouteEditorBody {
    background: transparent;
}

QWidget#MapFlightRouteEditorCard {
    background: rgba(10, 16, 24, 235);
    border: 1px solid #2a3a4f;
    border-radius: 10px;
}

QWidget#MapFlightRouteEditorCardHeader {
    background: #0c1219;
    border-bottom: 1px solid #1a2433;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}

QLabel#MapFlightRouteEditorCardTitle {
    font-size: 12px;
    font-weight: 700;
    color: #6ee7b7;
}

QLabel#MapFlightRouteEditorStatus {
    font-size: 12px;
    font-weight: 600;
    color: #e2e8f0;
}

QLabel#MapFlightRouteEditorHint {
    font-size: 11px;
    color: #94a3b8;
    line-height: 1.4;
}

QPushButton#MapFlightRouteEditorCloseButton {
    background: transparent;
    color: #9fb0c2;
    border: 1px solid #243041;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 700;
    padding: 0;
}

QPushButton#MapFlightRouteEditorCloseButton:hover {
    background: #172433;
    color: #f87171;
    border-color: #7f1d1d;
}

QWidget#MapFlightRouteEditorCardBody {
    background: transparent;
}

QCheckBox#MapFlightRouteEditorCheckbox {
    color: #cbd5e1;
    font-size: 11px;
    spacing: 6px;
}

QCheckBox#MapFlightRouteEditorCheckbox::indicator {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid #3b4f68;
    background: #111a24;
}

QCheckBox#MapFlightRouteEditorCheckbox::indicator:checked {
    background: #2563eb;
    border-color: #3b82f6;
}

QListWidget#MapDetectionObjectList {
    background: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 6px;
    padding: 2px;
    outline: none;
}

QListWidget#MapDetectionObjectList::item {
    border-radius: 4px;
    margin: 1px 0;
}

QListWidget#MapDetectionObjectList::item:selected {
    background: rgba(37, 99, 235, 0.35);
    border: 1px solid rgba(59, 130, 246, 0.55);
}

QLabel#MapDetectionObjectLabel {
    color: #e2e8f0;
    font-size: 10px;
}

QLabel#MapDetectionObjectRisk {
    color: #94a3b8;
    font-size: 9px;
    min-width: 28px;
}

QWidget#MapAiRoutePlannerPanel {
    background: rgba(10, 16, 24, 0.94);
    border: 1px solid rgba(148, 163, 184, 0.28);
    border-radius: 10px;
}

QRadioButton#MapAiRouteStyleRadio {
    color: #cbd5e1;
    font-size: 10px;
    spacing: 6px;
}

QPushButton#MapDetectionObjectDeleteButton {
    background: transparent;
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 4px;
    font-size: 12px;
    font-weight: 700;
    padding: 0;
}

QPushButton#MapDetectionObjectDeleteButton:hover {
    color: #fca5a5;
    border-color: rgba(248, 113, 113, 0.55);
    background: rgba(127, 29, 29, 0.25);
}

QPushButton#MapTargetIngressViewButton {
    background: #111a24;
    color: #67e8f9;
    border: 1px solid #1e4d63;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 9px;
    font-weight: 600;
    min-width: 40px;
}

QPushButton#MapTargetIngressViewButton:hover {
    background: #172433;
    color: #a5f3fc;
    border-color: #2dd4bf;
}

QPushButton#MapTargetIngressViewButton[active="true"] {
    background: #134e4a;
    color: #5eead4;
    border-color: #2dd4bf;
}

QPushButton#IconButton {
    background: #111a24;
    color: #9fb0c2;
    border: 1px solid #243041;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 11px;
}

QPushButton#IconButton:hover {
    background: #172433;
    color: #d7dee8;
}

QLabel#OnlineBadge {
    background: #0f1f17;
    color: #4ade80;
    border: 1px solid #166534;
    border-radius: 10px;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 700;
}

QWidget#OutputCard {
    background: #0d141d;
    border: 1px solid #1c2836;
    border-radius: 8px;
}

QLabel#OutputCardTitle {
    font-size: 11px;
    font-weight: 700;
    color: #8fa3b8;
}

QLabel#OutputCardValue {
    font-size: 18px;
    font-weight: 700;
    color: #4b5563;
}

QLabel#OutputCardHint {
    font-size: 10px;
    color: #5f7389;
}

QPushButton#NavItem {
    background: transparent;
    color: #9fb0c2;
    border: none;
    border-radius: 6px;
    padding: 8px 10px;
    text-align: left;
    font-size: 12px;
}

QPushButton#NavItem:hover {
    background: #111a24;
    color: #d7dee8;
}

QStatusBar {
    background: #0c1219;
    color: #6b7f96;
    border-top: 1px solid #1a2433;
    font-size: 11px;
}

QStatusBar QLabel {
    color: #6b7f96;
    padding: 0 8px;
}

QSplitter::handle {
    background: #121a24;
    width: 6px;
}

QScrollArea {
    background: transparent;
    border: none;
}

QScrollBar:vertical {
    background: #0a1018;
    width: 8px;
    border: none;
}

QScrollBar::handle:vertical {
    background: #243041;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QTableWidget {
    background: #0b121a;
    color: #c8d4e0;
    border: 1px solid #1c2836;
    border-radius: 8px;
    gridline-color: #1a2433;
    font-size: 11px;
}

QTableWidget::item {
    padding: 6px 8px;
    border: none;
}

QTableWidget::item:hover {
    background: #132030;
}

QTableWidget::item:selected {
    background: #1d4ed8;
    color: #ffffff;
    font-weight: 600;
    border-left: 3px solid #60a5fa;
}

QTableWidget::item:selected:hover {
    background: #2563eb;
    color: #ffffff;
}

QTableWidget::item:alternate {
    background: #0d141d;
}

QTableWidget::item:alternate:hover {
    background: #132030;
}

QHeaderView::section {
    background: #0c1219;
    color: #8fa3b8;
    border: none;
    border-bottom: 1px solid #1a2433;
    padding: 8px 10px;
    font-size: 11px;
    font-weight: 700;
}

QTabWidget#WingDataTabs::pane {
    border: 1px solid #1a2433;
    border-radius: 8px;
    background: #0a1018;
    top: -1px;
}

QTabWidget#WingDataTabs QTabBar::tab {
    background: #0c1219;
    color: #6b7f96;
    border: 1px solid #1a2433;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 10px 20px;
    margin-right: 6px;
    font-size: 12px;
    font-weight: 600;
    min-width: 120px;
}

QTabWidget#WingDataTabs QTabBar::tab:selected {
    background: #172433;
    color: #60a5fa;
}

QTabWidget#WingDataTabs QTabBar {
    qproperty-drawBase: 0;
}

QWidget#DatabaseNavPanel {
    background: #070d14;
    border: 1px solid #172334;
    border-radius: 12px;
    padding: 12px;
}

QListWidget#DatabaseTableNav {
    background: transparent;
    border: none;
    outline: none;
    padding: 0;
}

QListWidget#DatabaseTableNav::item {
    color: #9fb0c4;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 10px 12px;
    margin: 2px 0;
    font-size: 12px;
    font-weight: 600;
}

QListWidget#DatabaseTableNav::item:selected {
    color: #dbeafe;
    background: rgba(37, 99, 235, 0.18);
    border-color: #2563eb;
}

QListWidget#DatabaseTableNav::item:hover {
    background: rgba(30, 41, 59, 0.55);
    border-color: #334155;
}

QStackedWidget#DatabaseContentStack {
    background: #0a1018;
    border: 1px solid #1a2433;
    border-radius: 12px;
}

QPushButton#MapSidebarModeButton {
    min-width: 52px;
    padding: 2px 8px;
    border: 1px solid #334155;
    border-radius: 6px;
    background: rgba(15, 23, 42, 0.75);
    color: #94a3b8;
    font-size: 10px;
    font-weight: 700;
}

QPushButton#MapSidebarModeButton:checked {
    background: rgba(37, 99, 235, 0.22);
    border-color: #2563eb;
    color: #dbeafe;
}

QFrame#MapGroundTransportForm {
    background: #0d1722;
    border: 1px solid #1f2d3d;
    border-radius: 10px;
}

QFrame#MapGroundTransportCard {
    background: #0d1722;
    border: 1px solid #1f2d3d;
    border-radius: 10px;
}

QFrame#MapGroundTransportCard[selected="true"] {
    background: #101c2b;
    border-color: #2563eb;
}
"""
