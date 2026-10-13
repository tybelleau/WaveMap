from PySide6.QtWidgets import QHBoxLayout, QLabel, QTreeView, QMainWindow, QSlider, QVBoxLayout, QWidget, QPushButton, QFileDialog, QApplication, QComboBox
from PySide6.QtCore import Qt, QDir, Signal, QSize, QSettings, QTimer, QEvent, QPoint, QRect
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtMultimedia import QMediaPlayer, QMediaMetaData
from file_system_manager import AudioFilterModel, is_supported_audio, AudioFileSystemModel, AudioSearchIndex
from audio_player import AudioPlayer
from waveform_widget import WaveformWidget
from waveform_generator import WaveformGenerator
from drag_drop import start_file_drag, start_files_drag
from filter_panel import FilterPanel, FilterButton
from favorites_manager import FavoritesManager
from metadata_panel import MetadataPanel
from controls_panel import ControlsPanel
from project_map_panel import ProjectMapPanel
from pathlib import Path
import shutil


# Keyboard navigation
class AudioTreeView(QTreeView):
    space_pressed = Signal(object)
    drag_request = Signal(object)
    favorite_pressed = Signal(object)
    loop_pressed = Signal()
    metadata_pressed = Signal()
    map_pressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setDragEnabled(True)
        self.setAcceptDrops(False)
        self.drag_start_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position().toPoint()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            super().mouseMoveEvent(event)
            return

        drag_distance = QApplication.startDragDistance()

        distance = (
            event.position().toPoint() - self.drag_start_position
        ).manhattanLength()

        if distance < drag_distance:
            super().mouseMoveEvent(event)
            return

        index = self.indexAt(event.position().toPoint())

        if not index.isValid():
            super().mouseMoveEvent(event)
            return

        source_index = self.model().mapToSource(index)
        source_model = self.model().sourceModel()

        if source_model.isDir(source_index):
            super().mouseMoveEvent(event)
            return

        file_path = self.get_file_path(index)

        if file_path is not None:
            self.drag_request.emit(file_path)

    def get_file_path(self, index):
        source_index = self.model().mapToSource(index)
        source_model = self.model().sourceModel()

        if source_model.isDir(source_index):
            return None

        return Path(source_model.filePath(source_index))

    def keyPressEvent(self, event):
        if event.modifiers() & (
            Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier
        ):
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key_P:
            self.map_pressed.emit()
            return

        if event.key() == Qt.Key_M:
            self.metadata_pressed.emit()
            return

        if event.key() == Qt.Key_L:
            self.loop_pressed.emit()
            return

        if event.key() == Qt.Key_F:
            current_index = self.currentIndex()

            if current_index.isValid():
                self.favorite_pressed.emit(current_index)

            return

        if event.key() == Qt.Key_Space:
            current_index = self.currentIndex()

            source_index = self.model().mapToSource(current_index)
            is_dir = self.model().sourceModel().isDir(source_index)

            if is_dir:
                if self.isExpanded(current_index):
                    self.collapse(current_index)
                else:
                    self.expand(current_index)

                return

            self.space_pressed.emit(current_index)
            return

        super().keyPressEvent(event)

    def move_next(self):
        current_index = self.currentIndex()
        next_index = self.indexBelow(current_index)
        source_model = self.model().sourceModel()

        while next_index.isValid():
            source_index = self.model().mapToSource(next_index)

            if not source_model.isDir(source_index):
                self.setCurrentIndex(next_index)
                return

            next_index = self.indexBelow(next_index)

    def move_previous(self):
        current_index = self.currentIndex()
        previous_index = self.indexAbove(current_index)
        source_model = self.model().sourceModel()

        while previous_index.isValid():
            source_index = self.model().mapToSource(previous_index)

            if not source_model.isDir(source_index):
                self.setCurrentIndex(previous_index)
                return

            previous_index = self.indexAbove(previous_index)


# Generic icon button with hover scaling
class IconButtons(QPushButton):
    def __init__(self, icon_path, parent=None):
        super().__init__(parent)

        self.normal_size = QSize(24, 24)
        self.hover_size = QSize(29, 29)

        self.setIcon(QIcon(str(icon_path)))
        self.setIconSize(self.normal_size)

        self.setFixedSize(40, 40)

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

    def enterEvent(self, event):
        self.setIconSize(self.hover_size)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIconSize(self.normal_size)
        super().leaveEvent(event)


class MapButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("Map", parent)

        self.setObjectName("tool_buttons")
        self.setCheckable(True)

        self.badge = QLabel(self)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.hide()
        self.badge.installEventFilter(self)

        self.toggled.connect(self.apply_badge_style)

    def eventFilter(self, watched, event):
        if watched is self.badge and event.type() == QEvent.Type.MouseButtonPress:
            self.toggle()
            return True

        return super().eventFilter(watched, event)

    def set_count(self, count):
        if count <= 0:
            self.badge.hide()
            return

        self.badge.setText(str(count))
        self.badge.adjustSize()
        self.badge.setMinimumSize(14, 14)
        self.apply_badge_style()
        self.update_badge_position()
        self.badge.show()
        self.badge.raise_()

    def apply_badge_style(self, _checked=False):
        if self.badge.isHidden() and not self.badge.text():
            return

        if self.isChecked():
            background = "#1b1b1b"
            color = "#7ebcc4"
        else:
            background = "#7ebcc4"
            color = "#1b1b1b"

        self.badge.setStyleSheet(f"""
            QLabel {{
                background-color: {background};
                color: {color};
                border-radius: 7px;
                font-size: 8px;
                font-weight: bold;
                padding: 0px 3px;
            }}
        """)

    def update_badge_position(self):
        parent = self.parentWidget()

        if parent is None:
            return

        if self.badge.parentWidget() is not parent:
            self.badge.setParent(parent)

        self.badge.adjustSize()
        local = QPoint(self.width() - self.badge.width() + 4, -3)
        self.badge.move(self.mapToParent(local))
        self.badge.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_badge_position()


class MainWindow(QMainWindow):
    def __init__(self, database):
        super().__init__()

        self.setWindowTitle("WaveMap")
        self.resize(900, 600)

        self.database = database
        self.favorites_manager = FavoritesManager(self.database)

        self.current_root_folder = None
        self.current_file = None
        self.current_index = None
        self.search_index = AudioSearchIndex()
        self.settings = QSettings("WaveMap", "WaveMap")

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(120)
        self.search_timer.timeout.connect(self.perform_search)

        self.audio_player = AudioPlayer()
        self.waveform_generator = WaveformGenerator()

        self.create_ui()

        self.filter_panel = FilterPanel(self)
        self.filter_panel.filters_changed.connect(self.filters_changed)
        self.filter_panel.active_filter_count_changed.connect(self.update_filter_count)

        self.audio_player.player.playbackStateChanged.connect(self.playback_state_changed)
        self.audio_player.player.positionChanged.connect(self.position_changed)
        self.audio_player.player.durationChanged.connect(self.duration_changed)
        self.audio_player.player.metaDataChanged.connect(self.metadata_changed)
        self.waveform_generator.waveform_ready.connect(self.waveform_ready)
        self.waveform_generator.format_ready.connect(self.audio_format_ready)

    def playback_state_changed(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState

        if playing:
            icon_name = "pause_icon.svg"
        else:
            icon_name = "play_icon.svg"

        self.play_button.setIcon(
            QIcon(str(self.icons_path / icon_name))
        )

    def space_pressed(self, index):
        if self.current_file is not None:
            self.audio_player.toggle_playback()

    def favorite_pressed(self, index):
        file_path = self.file_tree.get_file_path(index)

        if file_path is None:
            return

        if not file_path.is_file() or not is_supported_audio(file_path):
            return

        self.favorites_manager.toggle_favorite(file_path)

        self.file_model.refresh_favorites()
        self.audio_filter_model.invalidateFilter()
        if self.audio_filter_model.favorites_only:
            self.expand_visible_results()

        source_index = self.file_model.index(str(file_path))

        self.file_model.dataChanged.emit(
            source_index,
            source_index,
            [Qt.ItemDataRole.DecorationRole]
        )

    def file_drag_requested(self, file_path):
        self.audio_player.release_source()
        self.waveform_generator.release_source()
        start_file_drag(self.file_tree, file_path)

    def toggle_current_file_in_map(self):
        if not self.current_file:
            return

        self.project_map_panel.toggle_file(self.current_file)

    def map_drag_requested(self, file_paths):
        self.audio_player.release_source()
        self.waveform_generator.release_source()
        start_files_drag(self.project_map_panel, file_paths)

    def export_map(self):
        sources = self.project_map_panel.existing_paths()

        if not sources:
            return

        folder = QFileDialog.getExistingDirectory(
            self,
            "Export Project Map"
        )

        if not folder:
            return

        destination = Path(folder)

        for source in sources:
            self.copy_map_file(source, destination)

    def copy_map_file(self, source, destination):
        target = destination / source.name

        if target.exists():
            number = 2

            while True:
                candidate = destination / f"{source.stem} ({number}){source.suffix}"

                if not candidate.exists():
                    target = candidate
                    break

                number += 1

        try:
            shutil.copy2(source, target)
        except OSError:
            return

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choose Audio Folder"
        )
        if folder:
            self.current_root_folder = folder
            self.search_index.build(folder)
            self.audio_filter_model.set_search_root(folder)
            source_index = self.file_model.setRootPath(folder)
            proxy_index = self.audio_filter_model.mapFromSource(source_index)
            self.file_tree.setRootIndex(proxy_index)
            self.folder_header.setText(f"{Path(folder).name}")
            self.folder_header.setStyleSheet("""
                QLabel#folder_header {
                    color: #939393;
                    padding-left: 6px;
                }
            """)

    def search_changed(self, text):
        self.search_text = text.strip()

        self.search_timer.start()

    def perform_search(self):
        text = self.search_text

        if self.current_root_folder:
            source_index = self.file_model.index(
                self.current_root_folder
            )

            proxy_index = self.audio_filter_model.mapFromSource(
                source_index
            )

            self.file_tree.setRootIndex(proxy_index)

        self.audio_filter_model.set_search_text(text)

        # empty search = normal browsing mode.
        if not text:
            self.file_tree.collapseAll()

            if self.audio_filter_model.favorites_only:
                self.expand_favorite_paths()

            return

        # keep tree rooted at selected library
        if self.current_root_folder:
            source_index = self.file_model.index(
                self.current_root_folder
            )

            proxy_index = self.audio_filter_model.mapFromSource(
                source_index
            )

            self.file_tree.setRootIndex(proxy_index)

        # expand paths containing matches
        self.expand_visible_results()

    def expand_visible_results(self):
        root_index = self.file_tree.rootIndex()

        def expand_children(parent_index):
            for row in range(
                self.audio_filter_model.rowCount(parent_index)
            ):
                index = self.audio_filter_model.index(
                    row,
                    0,
                    parent_index
                )

                if self.audio_filter_model.hasChildren(index):
                    self.file_tree.expand(index)
                    expand_children(index)

        expand_children(root_index)

    def expand_favorite_paths(self):
        for favorite_path in self.file_model.favorite_paths:
            source_index = self.file_model.index(
                str(favorite_path)
            )

            if not source_index.isValid():
                continue

            source_parent = source_index.parent()

            while source_parent.isValid():
                proxy_index = self.audio_filter_model.mapFromSource(
                    source_parent
                )

                if proxy_index.isValid():
                    self.file_tree.expand(proxy_index)

                source_parent = source_parent.parent()

    def file_selected(self, current_index, previous_index):
        self.current_index = current_index

        source_index = self.audio_filter_model.mapToSource(current_index)
        file_path = self.file_model.filePath(source_index)

        # checks if file is a supported audio before assigning name and current file
        path = Path(file_path)
        if path.is_file() and is_supported_audio(path):
            self.current_file = file_path
            self.show_playing_file(path)
        else:
            self.current_file = None
            self.file_name.setText("No file selected")
            self.metadata_panel.clear()

    def show_playing_file(self, file_path):
        path = Path(file_path)
        self.file_name.setText(path.name)
        self.time_label.setText("00:00 / 00:00")
        self.waveform_widget.set_waveform([])
        self.waveform_widget.set_playback_position(0, 0)
        self.audio_player.play_file(str(path))
        self.waveform_generator.generate(str(path))
        self.metadata_panel.show_file(path)
        self.metadata_changed()

    # Makes the progress slider advance with the audio
    def position_changed(self, position):
        if not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position)

        duration = self.audio_player.player.duration()

        self.time_label.setText(
            f"{self.format_time(position)} / {self.format_time(duration)}"
        )

        self.waveform_widget.set_playback_position(
            position,
            duration
        )

    # Matches the length of the slider to the audio
    def duration_changed(self, duration):
        self.progress_slider.setRange(0, duration)

        position = self.audio_player.player.position()

        self.time_label.setText(
                    f"{self.format_time(position)} / {self.format_time(duration)}"
                )

        if duration > 0:
            self.metadata_panel.set_value("Duration", self.format_time(duration))

    def audio_format_ready(self, sample_rate, channel_count):
        if sample_rate > 0:
            rate_text = f"{sample_rate} Hz"
        else:
            rate_text = "--"

        self.metadata_panel.set_value("Sample Rate", rate_text)

        if channel_count == 1:
            channel_text = "Mono"
        elif channel_count == 2:
            channel_text = "Stereo"
        elif channel_count > 2:
            channel_text = str(channel_count)
        else:
            channel_text = "--"

        self.metadata_panel.set_value("Channels", channel_text)

    def metadata_changed(self):
        meta = self.audio_player.player.metaData()

        self.metadata_panel.set_value(
            "Bit Rate",
            self.format_bitrate(meta.value(QMediaMetaData.Key.AudioBitRate))
        )

    def format_bitrate(self, bitrate):
        try:
            bits_per_second = int(bitrate)
        except (TypeError, ValueError):
            return "--"

        if bits_per_second <= 0:
            return "--"

        return f"{round(bits_per_second / 1000)} kbps"

    def seek_audio(self, position):
        self.audio_player.seek(position)
        self.file_tree.setFocus()

    def format_time(self, milliseconds):
        total_seconds = milliseconds // 1000

        minutes = total_seconds // 60
        seconds = total_seconds % 60

        return f"{minutes:02}:{seconds:02}"

    def waveform_ready(self, waveform):
        self.waveform_widget.set_waveform(waveform)

    def load_recent_searches(self):
        searches = self.settings.value(
            "recent_searches",
            [],
            type=list
        )

        self.search_bar.clear()

        for search in searches:
            self.search_bar.addItem(search)

        # sets search bar to blank upon reopen
        self.search_bar.setCurrentIndex(-1)
        self.search_bar.setEditText("")

    def save_current_search(self):
        search = self.search_bar.currentText().strip()

        if not search:
            return

        searches = self.settings.value(
            "recent_searches",
            [],
            type=list
        )

        if search in searches:
            searches.remove(search)

        searches.insert(0, search)

        searches = searches[:10]

        self.settings.setValue(
            "recent_searches",
            searches
        )

        self.search_bar.clear()

        for item in searches:
            self.search_bar.addItem(item)

        self.search_bar.setCurrentText(search)

    def show_filter_panel(self):
        position = self.filter_button.mapToGlobal(
            self.filter_button.rect().center()
        )

        self.filter_panel.adjustSize()

        panel_x = position.x() - (self.filter_panel.width() // 2)
        panel_y = position.y() - (self.filter_panel.height() // 2)

        self.filter_panel.move(panel_x, panel_y)
        self.filter_panel.show()

    def filters_changed(self, filters):
        self.audio_filter_model.set_file_types(
            filters["file_type"]
        )

        favorites_only = bool(filters["favorites"])

        self.audio_filter_model.set_favorites_only(
            favorites_only
        )

        if favorites_only:
            self.expand_favorite_paths()

    def update_filter_count(self, count):
        self.filter_button.set_filter_count(count)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_side_panels()

    def side_panel_rect(self):
        area = self.centralWidget().rect()
        tool_bottom = self.tool_section.mapTo(
            self.centralWidget(),
            self.tool_section.rect().bottomLeft(),
        ).y()

        margin = 8
        panel_width = int(area.width() / 3)
        return QRect(
            area.width() - panel_width - margin,
            tool_bottom,
            panel_width,
            area.height() - tool_bottom - margin,
        )

    def position_side_panels(self):
        if not hasattr(self, "controls_panel"):
            return

        geometry = self.side_panel_rect()
        self.controls_panel.setGeometry(geometry)

        if hasattr(self, "project_map_panel"):
            self.project_map_panel.setGeometry(geometry)

    def controls_toggled(self, visible):
        if visible:
            self.map_button.setChecked(False)
            self.position_side_panels()
            self.controls_panel.raise_()

        self.controls_panel.setVisible(visible)

    def map_toggled(self, visible):
        if visible:
            self.controls_button.setChecked(False)
            self.project_map_panel.refresh_presence()
            self.position_side_panels()
            self.project_map_panel.raise_()

        self.project_map_panel.setVisible(visible)

    def eventFilter(self, watched, event):
        if (
            event.type() == QEvent.Type.MouseButtonPress
            and self.controls_panel.isVisible()
        ):
            click = event.globalPosition().toPoint()
            panel_rect = QRect(
                self.controls_panel.mapToGlobal(QPoint(0, 0)),
                self.controls_panel.size(),
            )
            button_rect = QRect(
                self.controls_button.mapToGlobal(QPoint(0, 0)),
                self.controls_button.size(),
            )

            if not panel_rect.contains(click) and not button_rect.contains(click):
                self.controls_button.setChecked(False)

        return super().eventFilter(watched, event)

    def create_ui(self):

        self.icons_path = Path(__file__).resolve().parent.parent / "assets" / "icons"

        # central widget and layout
        central_widget = QWidget()
        central_widget.setObjectName("central_widget")
        self.setCentralWidget(central_widget)
        central_widget_layout = QHBoxLayout()
        central_widget.setLayout(central_widget_layout)

        file_section = QWidget()
        file_section.setObjectName("file_section")
        view_play_section = QWidget()

        central_widget_layout.addWidget(file_section, 1)
        central_widget_layout.addWidget(view_play_section, 2)


        # file section layout
        file_section_layout = QVBoxLayout()
        file_section_layout.setContentsMargins(5, 5, 5, 5)
        file_section_layout.setSpacing(0)
        file_section.setLayout(file_section_layout)

        explorer_header = QWidget()
        self.folder_header = QLabel("Base folder: No folder selected")
        self.folder_header.setObjectName("folder_header")
        search_bar_container = QWidget()
        search_bar_container.setObjectName("search_bar_container")
        filter_controls = QWidget()
        filter_controls.setObjectName("filter_controls")
        self.file_tree = AudioTreeView()

        # Keyboard Shortcuts
        self.file_tree.space_pressed.connect(self.space_pressed)
        self.file_tree.favorite_pressed.connect(self.favorite_pressed)
        self.file_tree.drag_request.connect(self.file_drag_requested)

        self.file_model = AudioFileSystemModel(self.favorites_manager)
        self.audio_filter_model = AudioFilterModel()
        self.audio_filter_model.setSourceModel(self.file_model)
        self.audio_filter_model.set_search_index(self.search_index)
        self.file_model.setRootPath("")
        self.file_tree.setModel(self.audio_filter_model)
        self.file_tree.header().hide()
        self.file_tree.setColumnHidden(1, True)
        self.file_tree.setColumnHidden(2, True)
        self.file_tree.setColumnHidden(3, True)
        self.file_tree.header().setStretchLastSection(True)
        self.file_tree.selectionModel().currentChanged.connect(self.file_selected)
        self.file_model.setFilter(
              QDir.AllDirs |
              QDir.NoDotAndDotDot |
              QDir.Files
        )

        file_section_layout.addWidget(explorer_header)
        file_section_layout.addSpacing(25)
        file_section_layout.addWidget(self.folder_header)
        file_section_layout.addWidget(search_bar_container)
        file_section_layout.addWidget(filter_controls)
        file_section_layout.addWidget(self.file_tree)


        # search bar container layout
        search_bar_container_layout = QHBoxLayout()
        search_bar_container_layout.setSpacing(6)
        search_bar_container.setLayout(search_bar_container_layout)

        self.search_bar = QComboBox()
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setEditable(True)
        self.search_bar.setInsertPolicy(QComboBox.NoInsert)
        self.filter_button = FilterButton(
            self.icons_path / "filter_icon.svg"
        )
        self.filter_button.setObjectName("filter_button")
        self.filter_button.setFixedWidth(32)
        self.filter_button.clicked.connect(self.show_filter_panel)

        search_bar_container_layout.addWidget(self.search_bar)
        search_bar_container_layout.addWidget(self.filter_button)

        self.search_bar.lineEdit().textChanged.connect(self.search_changed)
        self.load_recent_searches()
        self.search_bar.lineEdit().returnPressed.connect(self.save_current_search)


        # file section header layout
        explorer_header_layout = QHBoxLayout()
        explorer_header.setLayout(explorer_header_layout)

        explorer_title = QLabel("Audio Explorer")
        choose_folder_button = QPushButton("Choose Folder")
        choose_folder_button.setObjectName("choose_folder_button")
        choose_folder_button.clicked.connect(self.choose_folder)

        explorer_header_layout.addWidget(explorer_title, alignment=Qt.AlignLeft)
        explorer_header_layout.addWidget(choose_folder_button, alignment=Qt.AlignRight)


        # view & play section layout
        view_play_section_layout = QVBoxLayout()
        view_play_section.setLayout(view_play_section_layout)

        play_section = QWidget()
        view_section = QWidget()
        tool_section = QWidget()
        self.tool_section = tool_section
        self.metadata_panel = MetadataPanel()

        view_play_section_layout.addWidget(tool_section)
        view_play_section_layout.addWidget(self.metadata_panel)
        view_play_section_layout.addWidget(view_section, 9, alignment=Qt.AlignCenter)
        view_play_section_layout.addWidget(play_section, 1)


        # tool section layout
        tool_section_layout = QHBoxLayout()
        tool_section.setLayout(tool_section_layout)

        empty_space = QWidget()
        self.compare_button = QPushButton("Compare")
        self.compare_button.setObjectName("tool_buttons")
        self.compare_button.setCheckable(True)
        self.metadata_button = QPushButton("Metadata")
        self.metadata_button.setObjectName("tool_buttons")
        self.metadata_button.setCheckable(True)
        self.metadata_button.toggled.connect(self.metadata_panel.setVisible)
        self.file_tree.metadata_pressed.connect(self.metadata_button.toggle)
        self.loop_button = QPushButton("Loop")
        self.loop_button.setObjectName("tool_buttons")
        self.loop_button.setCheckable(True)
        self.loop_button.toggled.connect(self.audio_player.set_looping)
        self.file_tree.loop_pressed.connect(self.loop_button.toggle)
        self.map_button = MapButton()
        self.file_tree.map_pressed.connect(self.map_button.toggle)
        # self.controls_button = IconButtons(self.icons_path / "controls_icon.svg") - then remove next 2 lines
        self.controls_button = QPushButton("Controls")
        self.controls_button.setObjectName("tool_buttons")
        self.controls_button.setCheckable(True)

        tool_section_layout.addWidget(empty_space, 8)
        tool_section_layout.addWidget(self.compare_button, 1)
        tool_section_layout.addWidget(self.metadata_button, 1)
        tool_section_layout.addWidget(self.loop_button, 1)
        tool_section_layout.addWidget(self.map_button, 1)
        tool_section_layout.addWidget(self.controls_button, 1)


        # view section Layout
        view_section_layout = QVBoxLayout()
        view_section.setLayout(view_section_layout)

        self.file_name = QLabel("No file selected")
        self.waveform_widget = WaveformWidget()
        self.waveform_widget.seek_requested.connect(self.seek_audio)

        view_section_layout.addWidget(self.file_name,  alignment=Qt.AlignCenter)
        view_section_layout.addWidget(self.waveform_widget, alignment=Qt.AlignCenter)


        # play section layout
        play_section_layout = QHBoxLayout()
        play_section_layout.setSpacing(0)
        play_section.setLayout(play_section_layout)

        icons_path = self.icons_path

        previous_button = IconButtons(
            icons_path / "previous_icon.svg"
        )
        previous_button.setObjectName("progress_buttons")
        previous_button.clicked.connect(self.file_tree.move_previous)

        self.play_button = IconButtons(
            icons_path / "play_icon.svg"
        )
        self.play_button.setObjectName("progress_buttons")
        self.play_button.clicked.connect(self.audio_player.toggle_playback)

        next_button = IconButtons(
            icons_path / "next_icon.svg"
        )
        next_button.setObjectName("progress_buttons")
        next_button.clicked.connect(self.file_tree.move_next)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setObjectName("progress_slider")
        self.progress_slider.setRange(0, 0)
        self.progress_slider.sliderReleased.connect(lambda: self.seek_audio(self.progress_slider.value()))
        self.time_label = QLabel("00:00 / 00:00")

        play_section_layout.addWidget(previous_button)
        play_section_layout.addWidget(self.play_button)
        play_section_layout.addWidget(next_button)
        play_section_layout.addSpacing(15)
        play_section_layout.addWidget(self.progress_slider)
        play_section_layout.addSpacing(15)
        play_section_layout.addWidget(self.time_label)


        # Window itself
        # Keyboard shortcuts
        self.controls_panel = ControlsPanel(self.centralWidget())
        self.controls_button.toggled.connect(self.controls_toggled)
        self.controls_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self.controls_shortcut.activated.connect(self.controls_button.toggle)

        self.project_map_panel = ProjectMapPanel(self.centralWidget())
        self.map_button.toggled.connect(self.map_toggled)
        self.project_map_panel.export_requested.connect(self.export_map)
        self.project_map_panel.drag_requested.connect(self.map_drag_requested)
        self.project_map_panel.count_changed.connect(self.map_button.set_count)

        self.map_toggle_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.map_toggle_shortcut.activated.connect(self.toggle_current_file_in_map)

        # Click outside of controls panel to close it
        QApplication.instance().installEventFilter(self)