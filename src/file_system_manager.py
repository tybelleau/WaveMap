from pathlib import Path
from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileSystemModel

SUPPORTED_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".aac",
    ".m4a"
}

def is_supported_audio(file_path):
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS

def folder_contains_audio(folder_path):
    try:
        for path in folder_path.rglob("*"):
            if path.is_file() and is_supported_audio(path):
                return True
    except OSError:
        return False

    return False

def get_audio_files(folder_path):
    audio_files = []

    for path in folder_path.rglob("*"):
        if path.is_file() and is_supported_audio(path):
            audio_files.append(path)

    return sorted(audio_files)

class AudioFileSystemModel(QFileSystemModel):
    def __init__(self):
        super().__init__()

        icons_path = Path(__file__).resolve().parent.parent / "assets" / "icons"

        self.folder_icon = QIcon(str(icons_path / "folder_icon.svg"))
        self.audio_icon = QIcon(str(icons_path / "audio_icon.svg"))

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            path = Path(self.filePath(index))

            if path.is_dir():
                return self.folder_icon

            if is_supported_audio(path):
                return self.audio_icon

        return super().data(index, role)

class AudioFilterModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()

        self.search_text = ""
        self.search_root = None

        # Keep parent folders visible when a child matches.
        self.setRecursiveFilteringEnabled(True)

    def set_search_text(self, text):
        self.search_text = text.lower().strip()
        self.invalidateFilter()

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

        # Never filter out the selected library root.
        if self.search_root and path == self.search_root:
            return True

        # Reject anything outside the selected library.
        if self.search_root:
            try:
                path.relative_to(self.search_root)
            except ValueError:
                return False

        if path.is_file():
            if not is_supported_audio(path):
                return False

        elif path.is_dir():
            pass

        else:
            return False

        if not self.search_text:
            return True

        return self.search_text in path.name.lower()