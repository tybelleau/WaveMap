from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QTreeView, QMainWindow, QSlider, QVBoxLayout, QWidget, QPushButton, QFileDialog, QApplication
from PySide6.QtCore import Qt, QDir, Signal, QSize
from PySide6.QtGui import QIcon
from PySide6.QtMultimedia import QMediaPlayer
from file_system_manager import AudioFilterModel, is_supported_audio, AudioFileSystemModel
from audio_player import AudioPlayer
from waveform_widget import WaveformWidget
from waveform_generator import WaveformGenerator
from drag_drop import start_file_drag
from pathlib import Path


# Keyboard navigation
class AudioTreeView(QTreeView):
    space_pressed = Signal(object)
    drag_request = Signal(object)

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


# makes the buttons for play, pause, next, and previous change size on hover and click
class ProgressButtons(QPushButton):
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("WaveMap")
        self.resize(900, 600)

        self.current_root_folder = None
        self.current_file = None
        self.current_index = None

        self.audio_player = AudioPlayer()
        self.waveform_generator = WaveformGenerator()

        self.create_ui()

        self.audio_player.player.playbackStateChanged.connect(self.playback_state_changed)
        self.audio_player.player.positionChanged.connect(self.position_changed)
        self.audio_player.player.durationChanged.connect(self.duration_changed)
        self.audio_player.player.mediaStatusChanged.connect(self.media_status_changed)
        self.waveform_generator.waveform_ready.connect(self.waveform_ready)

    def playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setIcon(
                QIcon(str(self.icons_path / "pause_icon.svg"))
            )

        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.play_button.setIcon(
                QIcon(str(self.icons_path / "play_icon.svg"))
            )

        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.play_button.setIcon(
                QIcon(str(self.icons_path / "play_icon.svg"))
            )

    def space_pressed(self, index):
        if self.current_file is not None:
            self.audio_player.toggle_playback()

    def file_drag_requested(self, file_path):
        self.audio_player.release_source()
        self.waveform_generator.release_source()
        start_file_drag(self.file_tree, file_path)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choose Audio Folder"
        )
        if folder:
            self.current_root_folder = folder
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
        text = text.strip()

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
        self.expand_search_results()

    def expand_search_results(self):
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

    def file_selected(self, current_index, previous_index):
        self.current_index = current_index

        source_index = self.audio_filter_model.mapToSource(current_index)
        file_path = self.file_model.filePath(source_index)

        # checks if file is a supported audio before assigning name and current file
        path = Path(file_path)
        if path.is_file() and is_supported_audio(path):
            self.current_file = file_path
            self.file_name.setText(path.name)
            self.time_label.setText("00:00 / 00:00")
            self.waveform_widget.set_waveform([])
            self.waveform_widget.set_playback_position(0, 0)
            self.audio_player.play_file(file_path)
            self.waveform_generator.generate(file_path)
        else:
            self.current_file = None
            self.file_name.setText("No file selected")

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

    def seek_audio(self, position):
        self.audio_player.seek(position)
        self.file_tree.setFocus()

    def media_status_changed(self, status):
        print("Media status:", status)

    def format_time(self, milliseconds):
        total_seconds = milliseconds // 1000

        minutes = total_seconds // 60
        seconds = total_seconds % 60

        return f"{minutes:02}:{seconds:02}"

    def waveform_ready(self, waveform):
        self.waveform_widget.set_waveform(waveform)


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
        self.file_tree = AudioTreeView()
        self.file_tree.space_pressed.connect(self.space_pressed)
        self.file_tree.drag_request.connect(self.file_drag_requested)

        self.file_model = AudioFileSystemModel()
        self.audio_filter_model = AudioFilterModel()
        self.audio_filter_model.setSourceModel(self.file_model)
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
        file_section_layout.addWidget(self.file_tree)


        # search bar container layout
        search_bar_container_layout = QVBoxLayout()
        search_bar_container.setLayout(search_bar_container_layout)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setObjectName("search_bar")

        search_bar_container_layout.addWidget(self.search_bar)

        self.search_bar.textChanged.connect(self.search_changed)


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

        view_play_section_layout.addWidget(tool_section, 1)
        view_play_section_layout.addWidget(view_section, 9, alignment=Qt.AlignCenter)
        view_play_section_layout.addWidget(play_section, 1)


        # tool section layout
        tool_section_layout = QHBoxLayout()
        tool_section.setLayout(tool_section_layout)

        empty_space = QWidget()
        self.metadata_button = QPushButton("Metadata")
        self.metadata_button.setObjectName("tool_buttons")
        self.metadata_button.setCheckable(True)
        self.loop_button = QPushButton("Loop")
        self.loop_button.setObjectName("tool_buttons")
        self.loop_button.setCheckable(True)
        self.options_button = QPushButton("Options")
        self.options_button.setObjectName("tool_buttons")

        tool_section_layout.addWidget(empty_space, 8)
        tool_section_layout.addWidget(self.metadata_button, 1)
        tool_section_layout.addWidget(self.loop_button, 1)
        tool_section_layout.addWidget(self.options_button, 1)


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

        previous_button = ProgressButtons(
            icons_path / "previous_icon.svg"
        )
        previous_button.setObjectName("progress_buttons")
        previous_button.clicked.connect(self.file_tree.move_previous)

        self.play_button = ProgressButtons(
            icons_path / "play_icon.svg"
        )
        self.play_button.setObjectName("progress_buttons")
        self.play_button.clicked.connect(self.audio_player.toggle_playback)

        next_button = ProgressButtons(
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