from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget

_PRODUCT_IMAGE_FILES: tuple[tuple[str, str], ...] = (
    ("gbu-84", "gbu-84.png"),
    ("gbu-82", "gbu-82.png"),
    ("mk-84", "mk-84.png"),
    ("mk-82", "mk-82.png"),
)

_PRODUCT_IMAGE_ALIASES: tuple[tuple[str, str], ...] = (
    ("mk15", "mk-82.png"),
    ("snakeye", "mk-82.png"),
    ("highdrag", "mk-82.png"),
    ("mk81", "mk-82.png"),
    ("cbu49", "mk-82.png"),
    ("cbu71", "mk-82.png"),
    ("cluster", "mk-82.png"),
    ("gbu12", "gbu-82.png"),
    ("gbu10", "gbu-84.png"),
    ("gbu16", "gbu-84.png"),
    ("gbu24", "gbu-84.png"),
    ("gbu27", "gbu-84.png"),
    ("jdam", "gbu-84.png"),
    ("standoff", "gbu-84.png"),
    ("mk83", "mk-84.png"),
)

_MAX_IMAGE_SIZE = 108
_BORDER_PX = 1


def _resolve_images_dir() -> Path:
    module_file = Path(__file__).resolve()
    candidates = (
        module_file.parents[3] / "assets" / "images",
        module_file.parents[4] / "assets" / "images",
        Path.cwd() / "assets" / "images",
    )
    for candidate in candidates:
        if (candidate / "mk-82.png").is_file():
            return candidate
    return candidates[0]


_IMAGES_DIR = _resolve_images_dir()


def product_image_path(product_name: str) -> Path | None:
    """Resolve a weapon product name to a bundled illustration, if available."""
    compact = product_name.lower().replace(" ", "").replace("_", "").replace("-", "")
    for alias, filename in _PRODUCT_IMAGE_ALIASES:
        if alias in compact:
            path = _IMAGES_DIR / filename
            if path.is_file():
                return path
    for key, filename in _PRODUCT_IMAGE_FILES:
        if key.replace("-", "") in compact:
            path = _IMAGES_DIR / filename
            if path.is_file():
                return path
    return None


def load_product_pixmap(product_name: str) -> QPixmap | None:
    path = product_image_path(product_name)
    if path is None:
        return None
    pixmap = QPixmap(str(path))
    return None if pixmap.isNull() else pixmap


class ProductImageLabel(QLabel):
    """Compact product illustration — frame hugs the scaled image."""

    def __init__(self, parent: QWidget | None = None, *, max_size: int = _MAX_IMAGE_SIZE) -> None:
        super().__init__(parent)
        self._max_size = max_size
        self._source: QPixmap | None = None
        self._display_size = QSize(0, 0)
        self.setObjectName("WeaponeeringProductImage")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._apply_frame_style(muted=False)

    def set_product(self, product_name: str | None) -> None:
        if not product_name:
            self.clear_product()
            return
        pixmap = load_product_pixmap(product_name)
        if pixmap is None:
            self._source = None
            self._display_size = QSize(0, 0)
            super().setPixmap(QPixmap())
            self.setText(f"ไม่มีภาพสำหรับ {product_name}")
            self._apply_frame_style(muted=True)
            self.setFixedSize(180, 48)
            return
        self.setText("")
        self._apply_frame_style(muted=False)
        self._source = pixmap
        self._refresh()

    def clear_product(self) -> None:
        self._source = None
        self._display_size = QSize(0, 0)
        super().setPixmap(QPixmap())
        self.setText("")
        self.setFixedSize(0, 0)

    def refresh_display(self) -> None:
        self._refresh()

    def _apply_frame_style(self, *, muted: bool) -> None:
        base = (
            "background: #0a1018; border: 1px solid #1e2d42; border-radius: 8px;"
        )
        if muted:
            self.setStyleSheet(f"{base} color: #6b7f96; font-size: 10px; padding: 6px;")
        else:
            self.setStyleSheet(base)

    def _frame_size_for_pixmap(self, pixmap: QPixmap) -> QSize:
        border = _BORDER_PX * 2
        return QSize(pixmap.width() + border, pixmap.height() + border)

    def _refresh(self) -> None:
        if self._source is None or self._source.isNull():
            return
        scaled = self._source.scaled(
            self._max_size,
            self._max_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        super().setPixmap(scaled)
        self._display_size = scaled.size()
        self.setFixedSize(self._frame_size_for_pixmap(scaled))

    def sizeHint(self) -> QSize:
        if self._display_size.isEmpty():
            return QSize(0, 0)
        border = _BORDER_PX * 2
        return QSize(
            self._display_size.width() + border,
            self._display_size.height() + border,
        )
