import sys
from pathlib import Path
from flask import Flask, render_template

# Tự động thêm thư mục gốc vào PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.core.dict_loader import DictLoader
from src.core.translator import Translator

# Import các Blueprint API từ thư mục src.ui.api
from src.ui.api.api_translate_chapter import bp_translator
# Nếu bạn có các api khác thì import ở đây, ví dụ:
from src.ui.api.api_translate_and_export_epub_file import translate
# Nếu bạn có các api khác thì import ở đây, ví dụ:
from src.ui.api.api_import_export_dictionary import bp_dict

def create_app():
    # Khai báo đúng thư mục chứa index.html (templates) và static (css, js) nằm trong src/ui
    app = Flask(
        __name__, 
        template_folder='src/ui', 
        static_folder='src/ui/static'
    )

    # 1. Khởi tạo DictLoader (Hệ thống tự động quét thư mục và nạp toàn bộ global vào RAM cache)
    app.dict_loader = DictLoader()
    
    # 2. Khởi tạo Engine dịch
    app.translator = Translator(app.dict_loader)

    # Đăng ký các Blueprint API
    app.register_blueprint(bp_translator)
    app.register_blueprint(translate) # Bật nếu dùng api translate và export epub
    app.register_blueprint(bp_dict) # Bật nếu dùng api dict

    # Route chính để mở giao diện Web (index.html nằm trực tiếp trong src/ui)
    @app.route('/')
    def index():
        return render_template('index.html')

    return app

if __name__ == "__main__":
    app = create_app()
    print("🚀 Server đang chạy tại: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)