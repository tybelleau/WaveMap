from pathlib import Path

from PySide6.QtCore import QMimeData, QUrl
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QWidget

def start_file_drag(widget: QWidget, file_path: Path):

    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(str(file_path))])

    drag = QDrag(widget)
    drag.setMimeData(mime_data)

    drag.exec()