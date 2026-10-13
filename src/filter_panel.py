from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton, QGridLayout
from PySide6.QtGui import QIcon
from pathlib import Path

class FilterButton(QPushButton):
    def __init__(self, icon_path, parent=None):
        super().__init__(parent)

        # Icon
        self.normal_size = QSize(20, 20)
        self.hover_size = QSize(23, 23)

        self.setIcon(QIcon(str(icon_path)))
        self.setIconSize(self.normal_size)

        self.setFixedSize(32, 32)

        # Button styling
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 0px;
            }

            QPushButton:hover {
                background: transparent;
                border: none;
            }

            QPushButton:pressed {
                background: transparent;
                border: none;
            }
        """)

        # Filter count badge
        self.badge = QLabel(self)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.hide()

        self.update_badge_position()

    def enterEvent(self, event):
        self.setIconSize(self.hover_size)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIconSize(self.normal_size)
        super().leaveEvent(event)

    def set_filter_count(self, count):
        if count <= 0:
            self.badge.hide()
            return

        self.badge.setText(str(count))
        self.badge.adjustSize()
        self.badge.setMinimumSize(14, 14)

        self.badge.setStyleSheet("""
            QLabel {
                background-color: #7ebcc4;
                color: #1b1b1b;
                border-radius: 7px;
                font-size: 8px;
                font-weight: bold;
                padding: 0px 3px;
            }
        """)

        self.update_badge_position()
        self.badge.show()
        self.badge.raise_()

    def update_badge_position(self):
        self.badge.adjustSize()

        x = self.width() - self.badge.width() - 1
        y = 1

        self.badge.move(x, y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_badge_position()


class FilterPanel(QFrame):
    filters_changed = Signal(dict)
    active_filter_count_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("filter_panel")
        self.setWindowFlags(Qt.Popup)
        self.setAttribute(Qt.WA_StyledBackground, True)

        # sets the path to the checkmark icon
        self.check_icon = (Path(__file__).resolve().parent.parent / "assets" / "icons" / "checkmark_icon.svg").as_posix()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 12, 15, 12)
        self.layout.setSpacing(10)

        self.filters = {}

        self.create_filter_section(
            "File Type",
            "file_type",
            {
                "WAV": ".wav",
                "MP3": ".mp3",
                "M4A": ".m4a",
                "AAC": ".aac",
                "OGG": ".ogg",
                "FLAC": ".flac",
                "OPUS": ".opus",
            }
        )

        self.create_separator()

        self.create_filter_section(
            "Length",
            "length",
            {
                "<1 sec": 1,
                "<5 sec": 5,
                "<10 sec": 10,
                ">10 sec": None,
            }
        )

        self.create_separator()

        self.create_filter_section(
            "Favorites",
            "favorites",
            {
                "Favorites": True,
            }
        )

        self.create_clear_button()

    def create_filter_section(self, title_text, filter_key, options):
        title = QLabel(title_text)
        title.setObjectName("filter_section_title")
        self.layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(8)

        self.filters[filter_key] = {}

        columns = 4

        for index, (name, value) in enumerate(options.items()):
            checkbox = QCheckBox(name)
            checkbox.setObjectName("filter_checkbox")
            # sets the svg url to the checked state of the checkbox
            checkbox.setStyleSheet(
                "QCheckBox#filter_checkbox::indicator:checked {"
                f' image: url("{self.check_icon}");'
                "}"
            )

            checkbox.toggled.connect(
                self.emit_filters_changed
            )

            self.filters[filter_key][value] = checkbox
            row_index = index // columns
            column_index = index % columns
            grid.addWidget(checkbox, row_index, column_index)

        self.layout.addLayout(grid)

    def create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.NoFrame)
        separator.setFixedHeight(1)
        separator.setObjectName("filter_separator")

        self.layout.addWidget(separator)

    def emit_filters_changed(self):
        active_filters = {
        "file_type": [
            extension
            for extension, checkbox
            in self.filters["file_type"].items()
            if checkbox.isChecked()
        ],
        "length": [
            value
            for value, checkbox
            in self.filters["length"].items()
            if checkbox.isChecked()
        ],
        "favorites": [
            value
            for value, checkbox
            in self.filters["favorites"].items()
            if checkbox.isChecked()
        ],
    }

        count = sum(
            checkbox.isChecked()
            for filter_group in self.filters.values()
            for checkbox in filter_group.values()
        )

        self.filters_changed.emit(active_filters)
        self.active_filter_count_changed.emit(count)
        self.update_clear_button()

    def create_clear_button(self):
        self.clear_button = QPushButton("Clear Filters")
        self.clear_button.setObjectName("filter_clear_button")
        self.clear_button.clicked.connect(
            self.clear_filters
        )

        self.layout.addWidget(self.clear_button)

        self.update_clear_button()

    def clear_filters(self):
        for filter_group in self.filters.values():
            for checkbox in filter_group.values():
                checkbox.setChecked(False)

        self.update_clear_button()

    def update_clear_button(self):
        has_active_filters = any(
            checkbox.isChecked()
            for filter_group in self.filters.values()
            for checkbox in filter_group.values()
        )

        self.clear_button.setEnabled(has_active_filters)