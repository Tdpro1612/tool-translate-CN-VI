import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Tự động thêm thư mục gốc vào PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.core.dict_loader import DictLoader
from src.core.translator import Translator
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # 1. Khởi tạo và nạp từ điển Global
    dict_loader = DictLoader()
    dict_loader.load_global_dicts()

    # 2. Khởi tạo Engine dịch
    translator = Translator(dict_loader)

    # 3. Mở giao diện chính
    window = MainWindow(dict_loader, translator)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()