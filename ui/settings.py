from PyQt5.QtCore import (
    Qt,
    QUrl,
    QTime,
    QObject,
    QEvent,
    QSize,
    QTimer,
    QThread,
    pyqtSignal,
)
from PyQt5.QtGui import QColor, QIcon, QPixmap, QPainterPath, QPainter
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QFrame,
    QGraphicsDropShadowEffect,
    QFileDialog,
    QSlider,
    QListWidgetItem,
    QInputDialog,
    QMenu,
    QSizePolicy,
    QLineEdit,
    QCheckBox,
    QMessageBox,
    QDialog,
    QProgressBar,
)
import os
from pypresence import Presence
from ui.widgets import AnimatedButton
from config.constants import (
    VERSION,
    LAV_FILTERS_DIRECT,
    LAV_FILTERS_URL,
    ICONS_PACK_ZIP,
    ICONS_DIR
)
from languages import I18N
from utils.logger import logger
from utils.files import ensure_dir, download_file

class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_ui = parent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 400)

        container = QFrame(self)
        container.setStyleSheet(
            "QFrame { background-color: #252426; border-radius: 12px; border: 1px solid #3a3a3b; }"
        )
        container.setGeometry(0, 0, 600, 400)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Topbar
        self.topbar = QFrame()
        self.topbar.setFixedHeight(48)
        self.topbar.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(30,30,30,220), stop:1 rgba(20,20,20,200)); border-top-left-radius:12px; border-top-right-radius:12px; border-radius: 0px;}"
        )
        topbar_layout = QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(14, 6, 14, 6)
        self.title_lbl = QLabel("Settings")
        self.title_lbl.setObjectName("settings_title_lbl")
        self.title_lbl.setStyleSheet(
            "color: white; font-weight: bold; font-size: 16px; border: none;"
        )
        topbar_layout.addWidget(self.title_lbl)
        topbar_layout.addStretch()
        close_btn = AnimatedButton("✕", "icon")
        close_btn.setFixedSize(36, 34)
        close_btn.clicked.connect(self.close)
        topbar_layout.addWidget(close_btn)
        main_layout.addWidget(self.topbar)

        # Content
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(150)
        sidebar.setStyleSheet(
            "QFrame { background: rgba(0,0,0,0.2); border-right: 1px solid rgba(255,255,255,0.1); border-radius: 0px; }"
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 15, 10, 10)
        sidebar_layout.setSpacing(5)
        self.interface_btn = AnimatedButton("Interface", "secondary")
        self.interface_btn.clicked.connect(self._show_interface_tab)
        sidebar_layout.addWidget(self.interface_btn)
        sidebar_layout.addStretch()
        self.other_btn = AnimatedButton("Other", "secondary")
        self.other_btn.clicked.connect(self._show_other_tab)
        sidebar_layout.addWidget(self.other_btn)
        version_label = QLabel(f"Version {VERSION}")
        version_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px;")
        version_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version_label)
        content.addWidget(sidebar)

        # Right area
        self.settings_content = QFrame()
        self.settings_content.setObjectName("settings_content")
        self.settings_content.setStyleSheet("border-radius: 0px;")
        self.settings_layout = QVBoxLayout(self.settings_content)
        self.settings_layout.setContentsMargins(20, 20, 20, 20)
        self.settings_layout.setSpacing(15)
        content.addWidget(self.settings_content, 1)
        main_layout.addLayout(content)

        # Dragging
        self.startPos = None
        self.topbar.mousePressEvent = self.mousePressEvent
        self.topbar.mouseMoveEvent = self.mouseMoveEvent
        self.topbar.mouseReleaseEvent = self.mouseReleaseEvent

        # Default tab
        self.current_tab = None
        self._show_interface_tab()
        self._apply_i18n_to_settings()

    def _clear_settings_content(self):
        lay = self.settings_layout
        while lay.count():
            it = lay.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)
            sub = it.layout()
            if sub:
                while sub.count():
                    si = sub.takeAt(0)
                    if si.widget():
                        si.widget().setParent(None)

    def _activate_tab(self, name: str):
        if name == "interface":
            self.interface_btn.setStyleSheet(
                "QPushButton { background: #4a9eff; border: none; border-radius: 8px; color: white; padding: 10px; text-align: left; }"
            )
            self.other_btn.setStyleSheet(
                "QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; color: white; padding: 10px; text-align: left; }"
            )
        else:
            self.other_btn.setStyleSheet(
                "QPushButton { background: #4a9eff; border: none; border-radius: 8px; color: white; padding: 10px; text-align: left; }"
            )
            self.interface_btn.setStyleSheet(
                "QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; color: white; padding: 10px; text-align: left; }"
            )

    def _show_interface_tab(self):
        self.current_tab = "interface"
        self._clear_settings_content()
        self._activate_tab("interface")
        title = QLabel(self._t("interface_title"))
        title.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold; border: none;"
        )
        self.settings_layout.addWidget(title)

        self.show_covers_cb = QCheckBox(self._t("show_covers"))
        self.show_covers_cb.setChecked(
            getattr(self.parent_ui, "show_covers_enabled", True)
        )
        self.show_covers_cb.stateChanged.connect(self._on_toggle_covers)
        self.show_covers_cb.setStyleSheet(
            "QCheckBox { color: white; font-size: 14px; spacing: 8px; } QCheckBox::indicator { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.3); border-radius: 4px; background: rgba(255,255,255,0.05); } QCheckBox::indicator:checked { background: #4a9eff; border-color: #4a9eff; }"
        )
        self.settings_layout.addWidget(self.show_covers_cb)

        from PyQt5.QtWidgets import QComboBox, QHBoxLayout

        row = QHBoxLayout()
        self.lang_label = QLabel(self._t("language"))
        self.lang_label.setStyleSheet("color: white; font-size: 14px; border: none;")
        row.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Українська", "uk")
        self.lang_combo.addItem("Русский", "ru")
        cur = getattr(self.parent_ui, "language", "en")
        idx = {"en": 0, "uk": 1, "ru": 2}.get(cur, 0)
        self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        self.lang_combo.setStyleSheet(
            "QComboBox { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; color: white; padding: 6px 10px; } QComboBox QAbstractItemView { background: #252426; selection-background-color: #3a3a3b; color: white; }"
        )
        row.addWidget(self.lang_combo, 1)
        row.addStretch()
        self.settings_layout.addLayout(row)

        self.settings_layout.addStretch()
        self._apply_i18n_to_settings()

    def _show_other_tab(self):
        self.current_tab = "other"
        self._clear_settings_content()
        self._activate_tab("other")
        title = QLabel(self._t("other_title"))
        title.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold; border: none;"
        )
        self.settings_layout.addWidget(title)

        self.rpc_cb = QCheckBox("Show as Discord status")
        self.rpc_cb.setChecked(getattr(self.parent_ui, "rpc_enabled", True))
        self.rpc_cb.stateChanged.connect(self._on_toggle_rpc)
        self.rpc_cb.setStyleSheet(
            "QCheckBox { color: white; font-size: 14px; spacing: 8px; } QCheckBox::indicator { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.3); border-radius: 4px; background: rgba(255,255,255,0.05); } QCheckBox::indicator:checked { background: #4a9eff; border-color: #4a9eff; }"
        )
        self.settings_layout.addWidget(self.rpc_cb)

        # Big Picture Mode button
        self.big_picture_btn = AnimatedButton(self._t("enter_big_picture"), "secondary")
        self.big_picture_btn.clicked.connect(self._enter_big_picture_mode)
        self.settings_layout.addWidget(self.big_picture_btn)

        self.lav_label = QLabel()
        self.lav_label.setTextFormat(Qt.RichText)
        self.lav_label.setOpenExternalLinks(True)
        self._update_lav_label()
        self.lav_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 14px;")
        self.settings_layout.addWidget(self.lav_label)

        self.icons_btn = QPushButton()
        self.icons_btn.setCursor(Qt.PointingHandCursor)
        self.icons_btn.setFlat(True)
        self.icons_btn.setStyleSheet(
            "QPushButton { color: #4aa3ff; background: transparent; border: none; text-align: left; font-size: 14px; padding: 0; text-decoration: underline; } QPushButton:hover { color: #77bbff; }"
        )
        self.icons_btn.setText(
            self._t("icons_text").replace("<a href='#'>", "").replace("</a>", "")
        )
        self.icons_btn.clicked.connect(self._download_icons_pack)
        self.settings_layout.addWidget(self.icons_btn)

        self.settings_layout.addStretch()
        self._apply_i18n_to_settings()

    def _t(self, key: str) -> str:
        lang = getattr(self.parent_ui, "language", "en")
        return I18N.get(lang, I18N["en"]).get(key, key)

    def _apply_i18n_to_settings(self):
        t = self._t
        self.title_lbl.setText(t("settings_title"))
        self.interface_btn.setText(t("tab_interface"))
        self.other_btn.setText(t("tab_other"))
        if self.current_tab == "interface":
            if self.settings_layout.count() > 0 and isinstance(
                self.settings_layout.itemAt(0).widget(), QLabel
            ):
                self.settings_layout.itemAt(0).widget().setText(t("interface_title"))
            if hasattr(self, "show_covers_cb"):
                self.show_covers_cb.setText(t("show_covers"))
            if hasattr(self, "lang_label"):
                self.lang_label.setText(t("language"))
        elif self.current_tab == "other":
            if self.settings_layout.count() > 0 and isinstance(
                self.settings_layout.itemAt(0).widget(), QLabel
            ):
                self.settings_layout.itemAt(0).widget().setText(t("other_title"))
            if hasattr(self, "lav_label"):
                self._update_lav_label()
            if hasattr(self, "icons_btn"):
                self.icons_btn.setText(
                    t("icons_text").replace("<a href='#'>", "").replace("</a>", "")
                )
        if hasattr(self.parent_ui, "apply_i18n") and callable(
            self.parent_ui.apply_i18n
        ):
            try:
                self.parent_ui.apply_i18n()
            except Exception as e:
                logger.exception("[apply_i18n hook] %s", e)

    def _enter_big_picture_mode(self):
        self.close()
        self.parent_ui.launch_big_picture_mode()

    def _on_toggle_covers(self, state):
        self.parent_ui.show_covers_enabled = bool(state)
        self.parent_ui.save_settings()
        self.parent_ui.refresh_current_view()

    def _on_lang_changed(self, idx):
        data = self.lang_combo.itemData(idx)
        if not data:
            return
        self.parent_ui.language = data
        self.parent_ui.save_settings()
        if hasattr(self.parent_ui, "apply_i18n"):
            try:
                self.parent_ui.apply_i18n()
            except Exception as e:
                logger.exception("[apply_i18n main] %s", e)
        self._apply_i18n_to_settings()

    def _on_toggle_rpc(self, state):
        enabled = bool(state)
        self.parent_ui.rpc_enabled = enabled
        self.parent_ui.save_settings()
        try:
            if enabled and not self.parent_ui.rpc:
                self.parent_ui.rpc = Presence(self.parent_ui.discord_client_id)
                self.parent_ui.rpc.connect()
            elif not enabled and self.parent_ui.rpc:
                try:
                    self.parent_ui.rpc.clear()
                except Exception:
                    pass
                self.parent_ui.rpc_running = False
                self.parent_ui.rpc = None
        except Exception as e:
            logger.exception("[Discord RPC Toggle Error] %s", e)

    def _update_lav_label(self):
        url = LAV_FILTERS_DIRECT if LAV_FILTERS_DIRECT else LAV_FILTERS_URL
        self.lav_label.setText(self._t("drv_text").format(url=url))

    def _download_icons_pack(self):
        if not ICONS_PACK_ZIP:
            QMessageBox.information(
                self, self._t("download_fail"), "ICONS_PACK_ZIP is not set in code."
            )
            return
        try:
            QMessageBox.information(
                self, self._t("downloading"), self._t("downloading")
            )
            zip_path = os.path.join(ICONS_DIR, "icons_pack.zip")
            ensure_dir(ICONS_DIR)
            ok = download_file(ICONS_PACK_ZIP, zip_path)
            if ok:
                import zipfile

                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(ICONS_DIR)
                os.remove(zip_path)
                if hasattr(self, "parent_ui") and hasattr(self.parent_ui, "apply_i18n"):
                    self.parent_ui.apply_i18n()
                QMessageBox.information(
                    self, self._t("download_done"), self._t("download_done")
                )
            else:
                QMessageBox.warning(
                    self, self._t("download_fail"), self._t("download_fail")
                )
        except Exception as e:
            QMessageBox.critical(
                self, self._t("download_fail"), f"{self._t('download_fail')}\n{e}"
            )

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.startPos = e.globalPos()

    def mouseMoveEvent(self, e):
        if self.startPos:
            delta = e.globalPos() - self.startPos
            self.move(self.pos() + delta)
            self.startPos = e.globalPos()

    def mouseReleaseEvent(self, e):
        self.startPos = None
