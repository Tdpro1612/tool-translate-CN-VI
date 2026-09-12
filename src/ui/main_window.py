import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QComboBox, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt6.QtCore import Qt

class CustomTextEdit(QTextEdit):
    """Custom QTextEdit để bắt sự kiện click đúp chuột vào từ ngữ phục vụ tính năng bóc tách"""
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
        """Khởi tạo giao diện chính của ứng dụng"""
        self.setWindowTitle("Tool Dịch Truyện Trung - Việt")
        self.resize(1100, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top bar (Chọn dự án & Nút dịch)
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

        # Splitter chính chia vùng Editor và vùng Inspector
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # Editors area (Vung nhập văn bản Trung và hiển thị kết quả dịch)
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

        # Inspector Area (Vùng bóc tách chi tiết từ vựng dạng bảng)
        inspector_widget = QWidget()
        inspector_layout = QVBoxLayout(inspector_widget)
        inspector_layout.setContentsMargins(0, 5, 0, 0)

        label_inspector = QLabel("<b>🔍 Bóc Tách Từ</b> (Click đúp vào cột 'Nghĩa dịch' trong bảng để sửa trực tiếp rồi bấm Enter)")
        inspector_layout.addWidget(label_inspector)

        # Table hiển thị chi tiết bóc tách & cho phép sửa trực tiếp
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
        """Quét và nạp danh sách các file dự án trong thư mục projects lên ComboBox"""
        projects_dir = os.path.join(self.loader.dicts_dir, "projects")
        if os.path.exists(projects_dir):
            files = [f for f in os.listdir(projects_dir) if f.endswith(".txt")]
            self.combo_projects.clear()
            self.combo_projects.addItems(files)
            
            # Tự động chọn và bật dự án đầu tiên nếu có
            if files:
                self.combo_projects.setCurrentIndex(0)

    def on_project_changed(self):
        """Xử lý sự kiện khi người dùng đổi dự án trên ComboBox"""
        selected_project = self.combo_projects.currentText()
        if selected_project:
            # Tắt (unload) toàn bộ các project khác trên RAM trước, sau đó bật project hiện tại lên
            config = self.loader.load_config()
            for fname in config.get("project_settings", {}).keys():
                if fname == selected_project:
                    self.loader.set_project_checked(fname, True)
                else:
                    self.loader.set_project_checked(fname, False)

    def handle_translate(self):
        """Thực hiện dịch văn bản từ ô input sang ô output"""
        raw_text = self.input_text.toPlainText()
        if not raw_text.strip():
            return
        translated_text = self.translator.translate(raw_text)
        self.output_text.setPlainText(translated_text)

    def inspect_text(self, text):
        """Bóc tách và hiển thị chi tiết các từ vựng của đoạn text được chọn lên bảng Inspector"""
        self.table.blockSignals(True) # Tắt signal để tránh kích hoạt itemChanged nhầm khi đang load dữ liệu
        segments, _ = self.translator.translate_with_mapping(text)
        self.table.setRowCount(len(segments))
        
        for row, seg in enumerate(segments):
            item_cn = QTableWidgetItem(seg["src"])
            item_cn.setFlags(item_cn.flags() & ~Qt.ItemFlag.ItemIsEditable) # Khóa cột chữ Trung, không cho sửa
            
            item_vi = QTableWidgetItem(seg["trans"]) # Cột Nghĩa dịch cho phép click đúp sửa trực tiếp
            
            item_type = QTableWidgetItem(seg["type"])
            item_type.setFlags(item_type.flags() & ~Qt.ItemFlag.ItemIsEditable) # Khóa cột loại từ

            self.table.setItem(row, 0, item_cn)
            self.table.setItem(row, 1, item_vi)
            self.table.setItem(row, 2, item_type)
            
        self.table.blockSignals(False)

    def on_table_item_changed(self, item):
        """Khi người dùng sửa trực tiếp ô 'Nghĩa dịch' trong bảng, tự động cập nhật vào file Name dự án tương ứng"""
        if item.column() == 1: # Chỉ bắt sự kiện ở cột Nghĩa dịch
            row = item.row()
            cn_item = self.table.item(row, 0)
            if not cn_item:
                return
                
            cn = cn_item.text().strip()
            vi = item.text().strip()
            project_file = self.combo_projects.currentText()

            if cn and vi and project_file:
                # Sử dụng các hàm quản lý chi tiết name có sẵn của DictLoader để bảo mật dữ liệu và cập nhật RAM cache
                entries = self.loader.load_project_name_details(project_file)
                
                # Tìm xem từ này đã có trong file chưa, nếu có rồi thì cập nhật nghĩa mới, chưa có thì thêm mới
                updated = False
                for entry in entries:
                    if entry["src"] == cn:
                        entry["val"] = vi
                        updated = True
                        break
                
                if not updated:
                    entries.append({"src": cn, "val": vi})
                
                # Lưu xuống file và đồng thời cập nhật lại RAM cache thông qua DictLoader
                self.loader.save_project_name_details(project_file, entries)
                
                # Dịch lại toàn trang ngay lập tức để áp dụng nghĩa mới
                self.handle_translate()