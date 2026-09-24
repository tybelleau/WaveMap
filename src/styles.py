# colors:
# blue accent: #7ebcc4
# background: #1b1b1b
# accent grey: #2B2B2B
# highlight grey: #3C3C3C
# alt text: #939393

STYLESHEET = """
QWidget#central_widget {
    background-color: #1b1b1b;
}

QWidget#file_section {
    background-color: #2B2B2B;
    border-radius: 4px;
}

QLabel#folder_header {
    padding-left: 6px;
}

QPushButton#choose_folder_button {
    background-color: transparent;
}

QPushButton#choose_folder_button:hover {
    background-color: #3C3C3C;
}

QPushButton#choose_folder_button:pressed {
    background-color: transparent;
}

QWidget#search_bar_container {
    padding: 0px;
}

QLineEdit#search_bar {
    padding: 2px;
}

QTreeView {
    background: transparent;
    border: 0px solid;
    border-radius: 4px;
    padding: 4px;
    outline: none;
    font-family: "Sora";
    font-size: 9pt;
}

QTreeView::item {
    padding: 3px, 4px;
}

QTreeView::item:hover {
    background-color: rgba(255, 255, 255, 0.06);
}

QTreeView::item:selected {
    background-color: rgba(255, 255, 255, 0.10);
    color: white;
    border-radius: 4px;
}


QPushButton#tool_buttons {
    background-color: transparent;
}

QPushButton#tool_buttons:hover {
    background-color: #3C3C3C;
}

QPushButton#tool_buttons:pressed {
    background-color: transparent;
}

QPushButton#tool_buttons:checked {
    background-color: #7ebcc4;
    color: #1b1b1b;
}


QPushButton#progress_buttons {
    background: transparent;
    border: none;
    padding: 4px;
}

QPushButton#progress_buttons:hover {
}

QPushButton#progress_buttons:pressed {
}

QPushButton:disabled {
    color: rgba(255, 255, 255, 0.25);
}

QSlider:disabled {
    opacity: 0.5;
}

QSlider#progress_slider {
    background: transparent;
}

QSlider#progress_slider::groove:horizontal {
    height: 3px;
    background: #2B2B2B;
    border-radius: 1px;
}

QSlider#progress_slider::sub-page:horizontal {
    background: #7ebcc4;
    border-radius: 2px;
}

QSlider#progress_slider::handle:horizontal {
    width: 3px;
    height: 14px;
    margin: -6px 0;
    background: #ffffff;
    border: none;
    border-radius: 0px;
}

QSlider#progress_slider::handle:horizontal:hover {
    width: 4px;
    height: 16px;
    margin: -7px 0;
}

"""
