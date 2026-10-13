import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from file_system_manager import is_supported_audio


class MapRow(QWidget):
    remove_requested = Signal()
    drag_requested = Signal()
    hover_changed = Signal()

    def __init__(self, name, missing, trash_icon):
        super().__init__()

        self.full_name = name
        self.missing = missing
        self.drag_origin = None
        self.drag_started = False
        self.trash_visible = False
        self.trash_icon = QIcon(str(trash_icon))

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedHeight(self.fontMetrics().height() + 10)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 2, 0)
        layout.setSpacing(4)

        self.trash_button = QPushButton()
        self.trash_button.setObjectName("map_trash")
        self.trash_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.trash_button.setIconSize(QSize(20, 20))
        self.trash_button.setFixedSize(22, 22)
        self.trash_button.installEventFilter(self)
        self.trash_button.clicked.connect(self.remove_clicked)

        self.name_label = QLabel(name)
        self.name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.name_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )

        layout.addWidget(self.name_label, 1)
        layout.addWidget(self.trash_button)
        self.apply_style()

    def set_missing(self, missing):
        if self.missing == missing:
            return

        self.missing = missing
        self.apply_style()

    def apply_style(self):
        if self.missing:
            self.name_label.setObjectName("map_name_missing")
        else:
            self.name_label.setObjectName("map_name")

        self.name_label.style().unpolish(self.name_label)
        self.name_label.style().polish(self.name_label)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.elide_name()

    def elide_name(self):
        width = self.name_label.width()

        if width <= 0:
            return

        elided = self.fontMetrics().elidedText(
            self.full_name,
            Qt.TextElideMode.ElideRight,
            width,
        )
        self.name_label.setText(elided)

    def set_trash_visible(self, visible):
        if self.trash_visible == visible:
            return

        self.trash_visible = visible

        if visible:
            self.trash_button.setIcon(self.trash_icon)
        else:
            self.trash_button.setIcon(QIcon())

    def contains_cursor(self):
        return self.rect().contains(self.mapFromGlobal(QCursor.pos()))

    def remove_clicked(self):
        if self.trash_visible:
            self.remove_requested.emit()

    def eventFilter(self, watched, event):
        if watched is self.trash_button and event.type() in (
            QEvent.Type.Enter,
            QEvent.Type.Leave,
        ):
            self.hover_changed.emit()

        return super().eventFilter(watched, event)

    def enterEvent(self, event):
        self.hover_changed.emit()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hover_changed.emit()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        self.hover_changed.emit()

        if (
            self.drag_origin is not None
            and not self.drag_started
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            distance = (
                event.position().toPoint() - self.drag_origin
            ).manhattanLength()

            if distance >= QApplication.startDragDistance():
                self.drag_started = True
                self.drag_requested.emit()
                return

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_origin = event.position().toPoint()
            self.drag_started = False

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag_origin = None
        self.drag_started = False
        super().mouseReleaseEvent(event)


class ProjectMapPanel(QFrame):
    export_requested = Signal()
    drag_requested = Signal(list)
    count_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.paths = []
        self.rows = []
        self.icons_path = Path(__file__).resolve().parent.parent / "assets" / "icons"

        self.setObjectName("project_map_panel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("Project Map")
        layout.addWidget(title)
        layout.addSpacing(10)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("map_scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.scroll.viewport().setObjectName("map_scroll_viewport")
        self.scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.scroll.viewport().setAutoFillBackground(False)
        self.scroll.viewport().setMouseTracking(True)
        self.scroll.viewport().installEventFilter(self)

        self.row_list = QWidget()
        self.row_list.setObjectName("map_list")
        self.row_list.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.row_layout = QVBoxLayout(self.row_list)
        self.row_layout.setContentsMargins(0, 0, 8, 0)
        self.row_layout.setSpacing(3)
        self.row_layout.addStretch(1)

        self.scroll.setWidget(self.row_list)
        self.scroll.verticalScrollBar().valueChanged.connect(self.refresh_row_hover)
        layout.addWidget(self.scroll, 1)

        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 0, 0, 0)
        bottom_bar.setSpacing(6)

        button_size = QSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("map_action_button")
        self.clear_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.clear_button.setSizePolicy(button_size)
        self.clear_button.clicked.connect(self.clear_map)

        self.export_button = QPushButton("Export")
        self.export_button.setObjectName("map_action_button")
        self.export_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.export_button.setSizePolicy(button_size)
        self.export_button.clicked.connect(self.export_requested.emit)

        bottom_bar.addWidget(self.clear_button, 1)
        bottom_bar.addWidget(self.export_button, 1)
        layout.addLayout(bottom_bar)

        self.hide()

    def eventFilter(self, watched, event):
        if watched is self.scroll.viewport() and event.type() in (
            QEvent.Type.MouseMove,
            QEvent.Type.Leave,
        ):
            self.refresh_row_hover()

        return super().eventFilter(watched, event)

    def add_file(self, file_path):
        path = Path(file_path)

        if not path.is_file() or not is_supported_audio(path):
            return False

        try:
            resolved = path.resolve()
        except OSError:
            return False

        if self.index_of(resolved) >= 0:
            return False

        self.paths.append(resolved)
        self.rebuild_rows()
        return True

    def clear_map(self):
        if not self.paths:
            return

        self.paths.clear()
        self.rebuild_rows()

    def existing_paths(self):
        return [path for path in self.paths if path.is_file()]

    def index_of(self, file_path):
        path = Path(file_path)

        try:
            key = os.path.normcase(str(path.resolve()))
        except OSError:
            return -1

        for index, existing in enumerate(self.paths):
            if os.path.normcase(str(existing)) == key:
                return index

        return -1

    def toggle_file(self, file_path):
        index = self.index_of(file_path)

        if index >= 0:
            self.remove_at(index)
            return

        self.add_file(file_path)

    def remove_at(self, index):
        if not 0 <= index < len(self.paths):
            return

        del self.paths[index]
        self.rebuild_rows()

    def refresh_presence(self):
        for row, path in zip(self.rows, self.paths):
            row.set_missing(not path.is_file())

    def rebuild_rows(self):
        scrollbar = self.scroll.verticalScrollBar()
        scroll_value = scrollbar.value()

        while self.row_layout.count() > 1:
            item = self.row_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.hide()
                widget.deleteLater()

        self.rows = []

        for path in self.paths:
            row = MapRow(
                path.name,
                not path.is_file(),
                self.icons_path / "trash_icon.svg",
            )
            row.hover_changed.connect(self.refresh_row_hover)
            row.remove_requested.connect(lambda index=len(self.rows): self.remove_at(index))
            row.drag_requested.connect(self.start_drag)
            self.row_layout.insertWidget(self.row_layout.count() - 1, row)
            self.rows.append(row)

        scrollbar.setValue(scroll_value)
        self.count_changed.emit(len(self.paths))
        self.refresh_row_hover()

    def refresh_row_hover(self):
        hovered = None

        for row in self.rows:
            if row.contains_cursor():
                hovered = row
                break

        for row in self.rows:
            row.set_trash_visible(row is hovered)

    def start_drag(self):
        paths = self.existing_paths()

        if paths:
            self.drag_requested.emit(paths)
