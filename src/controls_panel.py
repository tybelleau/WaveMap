from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QScrollArea, QWidget

SHORTCUTS = [
    ("Space", "Play or pause the selected sound | opens and closes folders in file tree."),
    ("Up/Down", "Navigate through the file tree."),
    ("Left/Right", "Open or close parent folders."),
    ("F", "Favorite or unfavorite the currently selected sound."),
    ("L", "Toggle Loop: Loop the selected sound during playback."),
    ("M", "Toggle the metadata panel."),
    ("C", "Toggle compare view."),
    ("P", "Toggle the project map panel."),
    ("Ctrl + M", "Add or remove currently selected sound from the project Map."),
    ("Ctrl + E", "Reveal sound in File Explorer."),
    ("Ctrl + C", "Toggle the controls panel."),
]

class ControlsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("controls_panel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.NoFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("Controls")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setObjectName("controls_scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFocusPolicy(Qt.NoFocus)
        scroll.viewport().setObjectName("controls_scroll_viewport")
        scroll.viewport().setAttribute(Qt.WA_StyledBackground, True)
        scroll.viewport().setAutoFillBackground(False)

        shortcut_list = QWidget()
        shortcut_list.setObjectName("controls_list")
        shortcut_list.setAttribute(Qt.WA_StyledBackground, True)

        list_layout = QVBoxLayout(shortcut_list)
        list_layout.setContentsMargins(0, 0, 8, 0)
        list_layout.setSpacing(24)

        for keys, description in SHORTCUTS:
            row = QHBoxLayout()
            row.setSpacing(12)

            key_label = QLabel(keys)
            key_label.setObjectName("controls_key")
            key_label.setAlignment(Qt.AlignCenter)
            key_label.setFixedWidth(80)

            description_label = QLabel(description)
            description_label.setObjectName("controls_description")
            description_label.setWordWrap(True)

            row.addWidget(key_label, alignment=Qt.AlignTop)
            row.addWidget(description_label, 1)
            list_layout.addLayout(row)

        list_layout.addStretch(1)
        scroll.setWidget(shortcut_list)
        layout.addWidget(scroll, 1)
        self.hide()
