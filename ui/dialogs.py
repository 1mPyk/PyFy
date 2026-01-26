from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QFrame,
    QLineEdit,
    QDialog,
    QProgressBar
)
from ui.widgets import AnimatedButton
from ui.topbar import ModernTopBar
class DownloadHistoryDialog(QDialog):

    def __init__(self, parent=None, history=None):
        super().__init__(parent)
        self.setWindowTitle("Download History")
        self.layout = QVBoxLayout(self)
        self.list_w = QListWidget()
        self.layout.addWidget(self.list_w)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        self.layout.addWidget(close_btn)
        self.history = history or []
        self.reload()

    def reload(self):
        self.list_w.clear()
        for entry in reversed(self.history[-50:]):  # show up to last 50 entries
            txt = f"[{entry.get('status','?')}] {entry.get('title') or entry.get('url') or ''} "
            if entry.get("message"):
                txt += f"- {entry.get('message')}"
            self.list_w.addItem(txt)
            
class DownloadProgressDialog(QDialog):

    def __init__(self, parent=None, title=None, label=None):
        super().__init__(parent)
        self.setWindowTitle(title or "Downloading")
        self.setModal(False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.layout = QVBoxLayout(self)
        self.label = QLabel(label or "Downloading...")
        self.layout.addWidget(self.label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.layout.addWidget(self.progress)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.layout.addWidget(self.cancel_btn)
        self.cancelled = False

    def set_progress(self, v: int):
        self.progress.setValue(int(v))

    def set_status(self, s: str):
        if s == "downloading":
            self.label.setText("Downloading...")
        elif s == "finished":
            self.label.setText("Finishing...")
            # disable cancel at finish
            try:
                self.cancel_btn.setEnabled(False)
            except Exception:
                pass
        elif s == "cancel_requested":
            self.label.setText("Cancelling...")

    def _on_cancel(self):
        self.cancelled = True
        self.cancel_btn.setEnabled(False)
        self.label.setText("Cancelling...")

            
class CustomInputDialog(QWidget):
    def __init__(self, title="Input", label="Enter text:", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 200)  # немного больше окно

        container = QFrame(self)
        container.setStyleSheet(
            """
            QFrame {
                background-color: #252426;
                border-radius: 12px;
                border: 1px solid #3a3a3b;
            }
        """
        )
        container.setGeometry(0, 0, 400, 200)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # кастомная шапка
        self.topbar = ModernTopBar(self)
        layout.addWidget(self.topbar)

        body = QVBoxLayout()
        body.setContentsMargins(18, 18, 18, 18)
        body.setSpacing(14)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: white; font-size: 16px; font-weight: 500;")
        body.addWidget(lbl)

        self.edit = QLineEdit()
        self.edit.setStyleSheet(
            """
            QLineEdit {
                background: #1c1c1d;
                border: 1px solid #3a3a3b;
                border-radius: 8px;
                color: white;
                font-size: 15px;
                padding: 10px 12px;
            }
        """
        )
        """self._connect_signals()"""
        self.edit.setMinimumHeight(38)
        body.addWidget(self.edit)

        buttons = QHBoxLayout()
        ok_btn = AnimatedButton("OK", "secondary")
        cancel_btn = AnimatedButton("Cancel", "secondary")

        # увеличим кнопки
        ok_btn.setFixedHeight(36)
        cancel_btn.setFixedHeight(36)
        ok_btn.setMinimumWidth(100)
        cancel_btn.setMinimumWidth(100)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        body.addLayout(buttons)

        layout.addLayout(body)
        self.result = None

    def accept(self):
        self.result = self.edit.text()
        self.close()

    def reject(self):
        self.result = None
        self.close()

    @staticmethod
    def getText(parent, title, label):
        dlg = CustomInputDialog(title, label, parent)
        dlg.show()
        loop = QApplication.instance()
        while dlg.isVisible():
            loop.processEvents()
        return dlg.result, dlg.result is not None