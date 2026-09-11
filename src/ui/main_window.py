import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QComboBox, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt6.QtCore import Qt

class CustomTextEdit(QTextEdit):
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self.main_win = main_win

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        selected_text = self.textCursor().selectedText().strip()
        if selected_text:
            self.main_win.inspect_text(selected_text)


class MainWindow(QMainWindow):
    def __init__(self, dict_loader, translator):
        super().__init__()
        self.loader = dict_loader
        self.translator = translator
        self.init_ui()
        self.load_project_list()

    def init_ui(self):
        self.setWindowTitle("Tool Dịch Truyện Trung - Việt")
        self.resize(1100, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top bar
        top_bar = QHBoxLayout()
        label_project = QLabel("Dự án truyện:")
        self.combo_projects = QComboBox()
        self.combo_projects.currentIndexChanged.connect(self.on_project_changed)

        self.btn_translate = QPushButton("Dịch ngay")
        self.btn_translate.setStyleSheet("font-weight: bold; padding: 5px 15px;")
        self.btn_translate.clicked.connect(self.handle_translate)

        top_bar.addWidget(label_project)
        top_bar.addWidget(self.combo_projects, 1)
        top_bar.addWidget(self.btn_translate)
        main_layout.addLayout(top_bar)

        # Splitter chính
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # Editors area
        editors_widget = QWidget()
        editors_layout = QHBoxLayout(editors_widget)
        editors_layout.setContentsMargins(0, 0, 0, 0)

        self.input_text = CustomTextEdit(self)
        self.input_text.setPlaceholderText("Dán văn bản tiếng Trung vào đây... (Click đúp vào từ để bóc tách)")

        self.output_text = QTextEdit()
        self.output_text.setPlaceholderText("Kết quả dịch VietPhrase...")

        editors_layout.addWidget(self.input_text)
        editors_layout.addWidget(self.output_text)
        main_splitter.addWidget(editors_widget)

        # Inspector Area
        inspector_widget = QWidget()
        inspector_layout = QVBoxLayout(inspector_widget)
        inspector_layout.setContentsMargins(0, 5, 0, 0)

        label_inspector = QLabel("<b>🔍 Bóc Tách Từ</b> (Click đúp vào cột 'Nghĩa dịch' trong bảng để sửa trực tiếp rồi bấm Enter)")
        inspector_layout.addWidget(label_inspector)

        # Table hiển thị & cho sửa trực tiếp
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Từ gốc (Trung)", "Nghĩa dịch (Sửa tại đây)", "Loại từ điển"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Bắt sự kiện người dùng sửa xong một ô trong bảng
        self.table.itemChanged.connect(self.on_table_item_changed)
        
        inspector_layout.addWidget(self.table)
        main_splitter.addWidget(inspector_widget)

        main_splitter.setSizes([500, 200])
        main_layout.addWidget(main_splitter)

    def load_project_list(self):
        projects_dir = os.path.join(self.loader.dicts_dir, "projects")
        if os.path.exists(projects_dir):
            files = [f for f in os.listdir(projects_dir) if f.endswith(".txt")]
            self.combo_projects.clear()
            self.combo_projects.addItems(files)

    def on_project_changed(self):
        selected_project = self.combo_projects.currentText()
        if selected_project:
            self.loader.load_project_dict(selected_project)

    def handle_translate(self):
        raw_text = self.input_text.toPlainText()
        if not raw_text.strip():
            return
        translated_text = self.translator.translate(raw_text)
        self.output_text.setPlainText(translated_text)

    def inspect_text(self, text):
        self.table.blockSignals(True) # Tắt signal để tránh kích hoạt itemChanged khi nạp dữ liệu
        segments, _ = self.translator.translate_with_mapping(text)
        self.table.setRowCount(len(segments))
        
        for row, seg in enumerate(segments):
            item_cn = QTableWidgetItem(seg["src"])
            item_cn.setFlags(item_cn.flags() & ~Qt.ItemFlag.ItemIsEditable) # Khóa cột chữ Trung không cho sửa
            
            item_vi = QTableWidgetItem(seg["trans"]) # Cột Nghĩa dịch cho phép click đúp sửa trực tiếp
            
            item_type = QTableWidgetItem(seg["type"])
            item_type.setFlags(item_type.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.table.setItem(row, 0, item_cn)
            self.table.setItem(row, 1, item_vi)
            self.table.setItem(row, 2, item_type)
            
        self.table.blockSignals(False)

    def on_table_item_changed(self, item):
        """Khi sửa ô 'Nghĩa dịch' trong bảng và Enter, tự động lưu vào Name dự án"""
        if item.column() == 1: # Cột nghĩa dịch
            row = item.row()
            cn = self.table.item(row, 0).text().strip()
            vi = item.text().strip()
            project_file = self.combo_projects.currentText()

            if cn and vi and project_file:
                path = os.path.join(self.loader.dicts_dir, "projects", project_file)
                with open(path, "a", encoding="utf-8") as f:
                    f.write(f"\n{cn}={vi}")
                
                # Nạp lại từ điển & Dịch lại toàn trang ngay
                self.loader.load_project_dict(project_file)
                self.handle_translate()