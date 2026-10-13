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


/* File Tree Section */

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


/* Tool Buttons */

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


/* Metadata Panel */

QFrame#metadata_panel {
    background-color: #2B2B2B;
    border-radius: 4px;
}


/* Controls Panel */

QFrame#controls_panel,
QFrame#project_map_panel {
    background-color: #2B2B2B;
    border-radius: 4px;
}

QLabel#controls_key {
    background-color: #3C3C3C;
    border-radius: 4px;
    padding: 4px 6px;
}

QLabel#controls_description {
    color: #939393;
}

QScrollArea#controls_scroll,
QWidget#controls_scroll_viewport,
QWidget#controls_list,
QScrollArea#map_scroll,
QWidget#map_scroll_viewport,
QWidget#map_list {
    background-color: #2B2B2B;
    border: none;
}

QScrollArea#controls_scroll QScrollBar:vertical,
QScrollArea#map_scroll QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0px;
}

QScrollArea#controls_scroll QScrollBar::handle:vertical,
QScrollArea#map_scroll QScrollBar::handle:vertical {
    background: #3C3C3C;
    border-radius: 4px;
    min-height: 24px;
}

QScrollArea#controls_scroll QScrollBar::add-line:vertical,
QScrollArea#controls_scroll QScrollBar::sub-line:vertical,
QScrollArea#map_scroll QScrollBar::add-line:vertical,
QScrollArea#map_scroll QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollArea#controls_scroll QScrollBar::add-page:vertical,
QScrollArea#controls_scroll QScrollBar::sub-page:vertical,
QScrollArea#map_scroll QScrollBar::add-page:vertical,
QScrollArea#map_scroll QScrollBar::sub-page:vertical {
    background: transparent;
}


/* Project Map */

QLabel#map_name,
QLabel#map_name_missing {
    padding: 0px;
    margin: 0px;
}

QLabel#map_name_missing {
    color: #939393;
}

QPushButton#map_trash {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 0px;
}

QPushButton#map_trash:hover {
    background-color: #c44747;
}

QPushButton#map_action_button {
    border-color: #3C3C3C;
    background-color: transparent;
}

QPushButton#map_action_button:hover {
    background-color: #3C3C3C;
}

QPushButton#map_action_button:pressed {
    background-color: transparent;
}


/* Filter Panel */

QFrame#filter_panel {
    background-color: #1B1B1B;
    border-color: #3C3C3C;
    border-radius: 4px;
}

QCheckBox#filter_checkbox::indicator {
    width: 15px;
    height: 15px;
    margin: 1px 0px;
    border: 1px solid #3C3C3C;
    border-radius: 4px;
    background: transparent;
}

QCheckBox#filter_checkbox::indicator:hover {
    background-color: #3C3C3C;
}

QCheckBox#filter_checkbox::indicator:checked {
    background-color: #7ebcc4;
    border: 1px solid #3C3C3C;
}

QFrame#filter_separator {
    background-color: #3C3C3C;
}

QPushButton#filter_clear_button {
    border-color: #3C3C3C;
    background-color: transparent;
}

QPushButton#filter_clear_button:hover {
    background-color: #3C3C3C;
}


/* Progress Bar */

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
