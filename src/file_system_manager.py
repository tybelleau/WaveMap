from pathlib import Path
from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileSystemModel

SUPPORTED_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".aac",
    ".m4a",
    ".ogg",
    ".flac",
    ".opus",
}

def is_supported_audio(file_path):
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS

def get_audio_files(folder_path):
    audio_files = []

    for path in folder_path.rglob("*"):
        if path.is_file() and is_supported_audio(path):
            audio_files.append(path)

    return sorted(audio_files)

class AudioSearchIndex:
    def __init__(self):
        self.root_folder = None
        self.audio_files = []

    def build(self, folder_path):
        self.root_folder = Path(folder_path)
        self.audio_files = get_audio_files(self.root_folder)

    def search(self, text):
        text = text.lower().strip()

        if not text:
            return set(self.audio_files)

        return {
            path
            for path in self.audio_files
            if text in path.name.lower()
        }
    

class AudioFileSystemModel(QFileSystemModel):
    def __init__(self, favorites_manager=None):
        super().__init__()

        icons_path = Path(__file__).resolve().parent.parent / "assets" / "icons"

        self.folder_icon = QIcon(str(icons_path / "folder_icon.svg"))
        self.audio_icon = QIcon(str(icons_path / "audio_icon.svg"))
        self.gold_audio_icon = QIcon(str(icons_path / "favorite_audio_icon.svg"))

        self.favorites_manager = favorites_manager
        self.favorite_paths = set()

        self.refresh_favorites()

    def refresh_favorites(self):
        if self.favorites_manager:
            self.favorite_paths = self.favorites_manager.get_favorites()
        else:
            self.favorite_paths = set()

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            path = Path(self.filePath(index))

            if path.is_dir():
                return self.folder_icon

            if is_supported_audio(path):
                if path in self.favorite_paths:
                    return self.gold_audio_icon

                return self.audio_icon

        return super().data(index, role)

class AudioFilterModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()

        self.search_text = ""
        self.search_root = None
        self.search_index = None
        self.matching_files = set()
        self.file_types = set()
        self.favorites_only = False
        self.length_limits = []
        self.durations = {}

        # Keep parent folders visible when a child matches.
        self.setRecursiveFilteringEnabled(True)

    def set_search_text(self, text):
        self.search_text = text.lower().strip()

        if self.search_index:
            self.matching_files = self.search_index.search(
                self.search_text
            )
        else:
            self.matching_files = set()

        self.invalidateFilter()

    def set_search_index(self, search_index):
        self.search_index = search_index
        self.invalidateFilter()

    def set_file_types(self, file_types):
        self.file_types = {
            file_type.lower()
            for file_type in file_types
        }

        self.invalidateFilter()

    def set_favorites_only(self, enabled):
        self.favorites_only = enabled
        self.invalidateFilter()

    def set_length_limits(self, limits):
        self.length_limits = list(limits)
        self.invalidateFilter()

    def set_duration(self, file_path, duration_ms):
        path = Path(file_path)

        if self.durations.get(path) == duration_ms:
            return
        
        self.durations[path] = duration_ms
        self.invalidateFilter()

    def matches_length(self, duration_ms):
        duration_seconds = duration_ms / 1000

        for limit in self.length_limits:
            if limit is None:
                if duration_seconds > 10:
                    return True
            elif duration_seconds < limit:
                return True

        return False

    def passes_length(self, path):
        if not self.length_limits:
            return True

        duration_ms = self.durations.get(path)

        if duration_ms is None:
            return True

        return self.matches_length(duration_ms)

    def set_search_root(self, folder_path):
        self.search_root = Path(folder_path)
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        source_model = self.sourceModel()

        index = source_model.index(
            source_row,
            0,
            source_parent
        )

        path = Path(source_model.filePath(index))

        # Keep the selected library root visible.
        if self.search_root and path == self.search_root:
            return True

        # Reject anything outside the selected library.
        if self.search_root:
            try:
                path.relative_to(self.search_root)
            except ValueError:
                return False

        # Only allow supported audio files and folders.
        if path.is_file():
            if not is_supported_audio(path):
                return False

        elif not path.is_dir():
            return False

        # Apply file type filtering.
        if path.is_file() and self.file_types:
            if path.suffix.lower() not in self.file_types:
                return False

        # Apply length filtering.
        if path.is_file() and not self.passes_length(path):
            return False

        if path.is_dir() and self.length_limits and self.search_index:
            has_match = any(
                audio_path.is_relative_to(path)
                and self.passes_length(audio_path)
                for audio_path in self.search_index.audio_files
                if not self.file_types or audio_path.suffix.lower() in self.file_types
            )

            if not has_match:
                return False

        # Apply favorites filtering.
        if self.favorites_only:
            if path.is_file():
                if path not in source_model.favorite_paths:
                    return False

            elif path.is_dir():
                matching_favorites = [
                    favorite_path
                    for favorite_path in source_model.favorite_paths
                    if favorite_path.is_relative_to(path)
                ]

                # Apply the other active filters to favorites
                # before deciding whether this folder should remain visible.
                if self.file_types:
                    matching_favorites = [
                        favorite_path
                        for favorite_path in matching_favorites
                        if favorite_path.suffix.lower() in self.file_types
                    ]

                if self.search_text:
                    matching_favorites = [
                        favorite_path
                        for favorite_path in matching_favorites
                        if favorite_path in self.matching_files
                    ]

                if self.length_limits:
                    matching_favorites = [
                        favorite_path
                        for favorite_path in matching_favorites
                        if self.passes_length(favorite_path)
                    ]

                if not matching_favorites:
                    return False

        # Apply search filtering.
        if self.search_text:
            if path.is_file():
                return path in self.matching_files

            if path.is_dir():
                return any(
                    match_path.is_relative_to(path)
                    and self.passes_length(match_path)
                    for match_path in self.matching_files
                )

        return True