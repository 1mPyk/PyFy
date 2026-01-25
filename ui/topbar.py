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
from config.constants import ICONS_DIR
from languages import I18N
from ui.widgets import AnimatedButton
class ClickFilter(QObject):
    def __init__(self, line_edit):
        super().__init__()
        self.line_edit = line_edit

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if self.line_edit.hasFocus() and obj != self.line_edit:
                self.line_edit.clearFocus()
        return super().eventFilter(obj, event)
    
class ModernTopBar(QFrame):
    def _t(self, key: str) -> str:
        # Берём перевод из родителя (MusicPlayerUI)
        lang = getattr(self.parent, "language", "en")
        return I18N.get(lang, I18N["en"]).get(key, key)

    def apply_i18n(self):
        # Локализуем только элементы топбара
        self.title_label.setText(self._t("app_title"))
        self.url_input.setPlaceholderText(self._t("url_placeholder"))
        self.update_btn.setToolTip(self._t("update_ready_tooltip"))

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.startPos = None
        self.setFixedHeight(48)
        self.setStyleSheet(
            """
            QFrame { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(30,30,30,220), stop:1 rgba(20,20,20,200)); 
                     border-top-left-radius:15px; border-top-right-radius:15px; }
        """
        )
        self.update_btn = None  # кнопка обновления
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(8)

        self.title_label = QLabel("PyFy Music Player")
        self.title_label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 16px; border: none;"
        )
        layout.addWidget(self.title_label)

        layout.addSpacing(100)

        # Контейнер поиска
        search_container = QHBoxLayout()
        search_container.setSpacing(0)
        search_container.setContentsMargins(0, 0, 0, 0)

        # Текстбокс
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube URL...")
        self.url_input.setFixedWidth(390)
        self.url_input.setFixedHeight(32)
        self.url_input.setStyleSheet(
            """
            QLineEdit {
                background: rgba(43,43,44,0.08);
                border: 1px solid rgba(255,255,255,0.12);
                border-top-left-radius: 16px;
                border-bottom-left-radius: 16px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                border-right: none;
                color: white;
                font-size: 13px;
                padding-left: 14px;
                padding-right: 8px;
            }
            QLineEdit:focus {
                background: rgba(255,255,255,0.12);
                border: 1px solid rgba(255,255,255,0.12);
                border-right: none;
            }
        """
        )
        # Не получает фокус при старте, только при клике
        self.url_input.setFocusPolicy(Qt.ClickFocus)

        search_container.addWidget(self.url_input)

        # Кнопка загрузки
        self.download_btn = QPushButton()
        self.download_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "download.png")))
        self.download_btn.setFixedSize(40, 32)
        self.download_btn.setIconSize(QSize(22, 22))
        self.download_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(43,43,44,0.8);
                border: 1px solid rgba(255,255,255,0.12);
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 16px;
                border-bottom-right-radius: 16px;
                border-left: none;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(43,43,44,0.8);
            }
            QPushButton:pressed {
                background: rgba(86,86,88,1);
            }
        """
        )
        self.download_btn.setFocusPolicy(Qt.NoFocus)
        self.download_btn.clicked.connect(self.parent.download_from_youtube)
        search_container.addWidget(self.download_btn)

        layout.addLayout(search_container)
        layout.addSpacing(10)
        layout.addStretch()

        # Фильтр кликов (чтобы при клике вне поля снимался фокус)
        self.click_filter = ClickFilter(self.url_input)
        QApplication.instance().installEventFilter(self.click_filter)

        # Enter = клик по кнопке
        self.url_input.returnPressed.connect(self.download_btn.click)

        # Кнопка обновления (изначально скрыта)
        self.update_btn = QPushButton()
        self.update_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "downloadupdate.png")))
        self.update_btn.setIconSize(QSize(22, 22))
        self.update_btn.setFixedSize(36, 34)
        self.update_btn.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff88, stop:1 #00cc66);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 8px;
                color: white;
                padding: 0px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ffaa, stop:1 #00dd77);
            }
        """
        )
        self.update_btn.setFocusPolicy(Qt.NoFocus)
        self.update_btn.setToolTip(
            I18N.get(getattr(self, "language", "en"), I18N["en"]).get(
                "update_ready_tooltip", "Update is ready!"
            )
        )
        self.update_btn.hide()  # изначально скрыта
        self.update_btn.clicked.connect(self.parent.start_update_process)
        layout.addWidget(self.update_btn)

        self.settings_btn = AnimatedButton("⚙", "icon")
        self.settings_btn.setFixedSize(36, 34)
        self.settings_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 8px;
                color: #cfcfcf;
                font-size: 18px;
                padding: 0px;
            }
            QPushButton:hover { 
                background: rgba(255,255,255,0.06); 
                color: white; 
            }
        """
        )
        self.settings_btn.clicked.connect(self.parent.show_settings)
        layout.addWidget(self.settings_btn)

        self.min_btn = AnimatedButton("−", "icon")
        self.min_btn.setFixedSize(36, 34)
        self.min_btn.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.min_btn)

        self.close_btn = AnimatedButton("✕", "icon")
        self.close_btn.setFixedSize(36, 34)
        self.close_btn.clicked.connect(self.parent.close)
        layout.addWidget(self.close_btn)

    # --- Перемещение окна ---
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.startPos = e.globalPos()

    def mouseMoveEvent(self, e):
        if self.startPos:
            delta = e.globalPos() - self.startPos
            self.parent.move(self.parent.pos() + delta)
            self.startPos = e.globalPos()

    def mouseReleaseEvent(self, e):
        self.startPos = None