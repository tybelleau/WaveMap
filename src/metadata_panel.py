from pathlib import Path
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGridLayout

class MetadataPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("metadata_panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        self.title_label = QLabel("Metadata")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        self.fields_layout = QGridLayout()
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        self.fields_layout.setHorizontalSpacing(16)
        self.fields_layout.setVerticalSpacing(4)
        layout.addLayout(self.fields_layout)

        self.field_labels = {}

        for row, name in enumerate(("Type", "Size", "Duration", "Sample Rate", "Bit Rate" , "Channels")):
            name_label = QLabel(name)
            name_label.setObjectName("metadata_key")

            value_label = QLabel("-")
            value_label.setObjectName("metadata_value")

            self.fields_layout.addWidget(name_label, row, 0)
            self.fields_layout.addWidget(value_label, row, 1)
            self.field_labels[name] = value_label

        self.hide()

    def show_file(self, file_path):
        path = Path(file_path)
        self.title_label.setText(path.name)
        self.field_labels["Type"].setText(
            path.suffix.lstrip(".").upper() or "--"
        )
        self.field_labels["Size"].setText(self.format_size(path))

        for name in ("Duration", "Sample Rate", "Bit Rate", "Channels"):
            self.field_labels[name].setText("-")

    def clear(self):
        self.title_label.setText("No file selected")
        for label in self.field_labels.values():
            label.setText("--")

    def format_size(self, path):
        try:
            size = path.stat().st_size
        except OSError:
            return "--"
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"

    def set_value(self, name, value):
        label = self.field_labels.get(name)

        if label is not None:
            label.setText(value)