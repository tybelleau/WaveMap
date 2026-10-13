from pathlib import Path

from PySide6.QtCore import QMimeData, QUrl, Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QWidget

def start_file_drag(widget: QWidget, file_path: Path):
    start_files_drag(widget, [file_path])


def start_files_drag(widget: QWidget, file_paths):
    urls = []

    for file_path in file_paths:
        path = Path(file_path)

        if path.is_file():
            urls.append(QUrl.fromLocalFile(str(path)))

    if not urls:
        return

    mime_data = QMimeData()
    mime_data.setUrls(urls)

    drag = QDrag(widget)
    drag.setMimeData(mime_data)

    drag.exec(Qt.DropAction.CopyAction)