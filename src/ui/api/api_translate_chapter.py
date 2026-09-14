from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from src.core.translator import Translator  # Import class Translator hiện tại của bạn

bp_translator = Blueprint('translator_api', __name__)

def api_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            loader = current_app.dict_loader
            # Khởi tạo Translator bằng dict_loader từ app context
            translator = Translator(loader)
            result = f(translator, loader, *args, **kwargs)
            if isinstance(result, dict):
                return jsonify({"success": True, **result})
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400
    return wrapper

@bp_translator.route('/api/translate', methods=['POST'])
@api_route
def translate_chapter(translator, loader):
    """Dịch toàn bộ nội dung chương văn bản"""
    data = request.json or {}
    content = data.get('content', '')
    
    translated_content = translator.translate(content)
    return {"translated_content": translated_content}

@bp_translator.route('/api/sidebar/analyze', methods=['POST'])
@api_route
def analyze_sentence(translator, loader):
    """Bóc tách câu/đoạn văn thành các token chi tiết phục vụ hiển thị Sidebar"""
    data = request.json or {}
    sentence = data.get('sentence', '')
    
    # Sử dụng đúng hàm translate_with_mapping đã được viết sẵn trong Translator
    segments, _ = translator.translate_with_mapping(sentence)
    
    # Chuẩn hóa lại key đầu ra cho khớp với cấu trúc UI yêu cầu (src, dst, source)
    tokens = [
        {"src": seg["src"], "dst": seg["trans"], "source": seg["type"]} 
        for seg in segments
    ]
    return {"tokens": tokens}

@bp_translator.route('/api/sidebar/save-word', methods=['POST'])
@api_route
def save_sidebar_word(translator, loader):
    """Tự động lưu nghĩa mới từ sidebar vào project/file Name"""
    data = request.json or {}
    target_file = data.get('file_name')
    src = data.get('src')
    dst = data.get('dst')
    
    if not target_file:
        raise ValueError("Chưa chọn file Name mục tiêu để lưu từ.")
        
    # Gọi hàm xử lý cập nhật hoặc thêm từ vào project của DictLoader
    loader.update_or_add_word_to_project(target_file, src, dst)