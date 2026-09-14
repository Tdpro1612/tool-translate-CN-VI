import os
import threading
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from functools import wraps

from src.core.Epub_builder import build_epub

translate = Blueprint('translate_file_api', __name__)

# Lưu tiến độ dịch theo task_id trên RAM
TRANSLATION_TASKS = {}


def api_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            loader = current_app.dict_loader
            translate_eng = current_app.translator
            result = f(loader, translate_eng, *args, **kwargs)
            if isinstance(result, dict):
                return jsonify({"success": True, **result})
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400
    return wrapper


def run_background_translation(task_id, lines, translate_engine, output_path, original_filename):
    """Hàm chạy ngầm để dịch từng dòng và cập nhật tiến độ"""
    try:
        total_lines = len(lines)
        translated_lines = []

        for idx, line in enumerate(lines):
            if not line.strip():
                translated_lines.append("")
            else:
                _, clean_translated = translate_engine.translate_with_mapping(line)
                translated_lines.append(clean_translated)

            # Cập nhật tiến độ hiện tại
            TRANSLATION_TASKS[task_id]["current"] = idx + 1

        final_translated_text = "\n".join(translated_lines)

        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_translated_text)

        # Đánh dấu hoàn thành
        TRANSLATION_TASKS[task_id]["status"] = "completed"
        TRANSLATION_TASKS[task_id]["download_txt_url"] = f"/api/download-result?path={output_path}&name=vi_{original_filename}"

    except Exception as e:
        TRANSLATION_TASKS[task_id]["status"] = "error"
        TRANSLATION_TASKS[task_id]["error"] = str(e)


@translate.route('/api/translate-file', methods=['POST'])
@api_route
def api_translate_file(loader, translate):
    """API khởi tạo tiến trình dịch file ngầm"""
    if 'file' not in request.files:
        return {"error": "Không tìm thấy file tải lên."}

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return {"error": "Chưa chọn file."}

    original_filename = uploaded_file.filename
    raw_content = uploaded_file.read().decode('utf-8', errors='ignore')
    lines = raw_content.splitlines()

    task_id = str(uuid.uuid4())

    output_dir = os.path.join('outputs')
    output_filename = f"vi_{original_filename}"
    output_path = os.path.join(output_dir, output_filename)

    # Khởi tạo trạng thái task
    TRANSLATION_TASKS[task_id] = {
        "current": 0,
        "total": len(lines),
        "status": "processing",
        "file_path": output_path
    }

    # Chạy ngầm bằng Thread để không chặn luồng HTTP
    translate_engine = translate
    thread = threading.Thread(
        target=run_background_translation,
        args=(task_id, lines, translate_engine, output_path, original_filename)
    )
    thread.start()

    return {"task_id": task_id, "total_lines": len(lines)}


@translate.route('/api/translate-progress', methods=['GET'])
def get_translate_progress():
    """API cho JS gọi liên tục để lấy tiến độ hiện tại"""
    task_id = request.args.get('task_id')
    if not task_id or task_id not in TRANSLATION_TASKS:
        return jsonify({"success": False, "error": "Không tìm thấy tiến trình."}), 404

    task_info = TRANSLATION_TASKS[task_id]
    return jsonify({
        "success": True,
        "current": task_info.get("current", 0),
        "total": task_info.get("total", 0),
        "status": task_info.get("status"),
        "file_path": task_info.get("file_path"),
        "download_txt_url": task_info.get("download_txt_url"),
        "error": task_info.get("error")
    })


@translate.route('/api/export-epub', methods=['POST'])
@api_route
def api_export_epub(loader, translate):
    """API tạo EPUB phân chia chương chuẩn chỉnh, đọc từ file txt đã dịch trên ổ cứng.

    Toàn bộ logic tách chương / dựng HTML / escape ký tự đặc biệt giờ nằm
    trong epub_builder.build_epub() — dùng chung với script chạy tay
    txt_to_epub.py, tránh 2 nơi cùng 1 lỗi.
    """
    data = request.get_json(silent=True) or {}
    file_path = data.get('file_id') or data.get('file_path')
    book_title = data.get('title', 'Truyện Dịch')
    book_author = data.get('author', 'Unknown')
    cover_path = data.get('cover_path')  # tuỳ chọn: đường dẫn ảnh bìa đã upload sẵn

    if not file_path or not os.path.exists(file_path):
        return {"error": "Không tìm thấy file bản dịch trên ổ cứng. Vui lòng dịch lại file."}, 400

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    output_dir = os.path.join('outputs')
    safe_title = "".join([c if c.isalnum() else "_" for c in book_title]) or "Truyen_Dich"
    output_filename = f"{safe_title}.epub"
    output_path = os.path.join(output_dir, output_filename)

    chapter_count = build_epub(
        content=content,
        output_path=output_path,
        title=book_title,
        author=book_author,
        language="vi",
        cover_path=cover_path,
    )

    return {
        "chapter_count": chapter_count,
        "download_epub_url": f"/api/download-result?path={output_path}&name={output_filename}"
    }


@translate.route('/api/download-result', methods=['GET'])
def download_result():
    """API hỗ trợ tải file kết quả về máy"""
    file_path = request.args.get('path')
    file_name = request.args.get('name')
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=file_name)
    return "File không tồn tại hoặc đã bị xóa.", 404