import os
from functools import wraps
from flask import Blueprint, request, jsonify, current_app

bp_dict = Blueprint('dict_api', __name__)

def api_route(f):
    """Decorator tự động hóa bắt lỗi try-except, đóng gói JSON response và truyền sẵn loader"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            loader = current_app.dict_loader
            result = f(loader, *args, **kwargs)
            if isinstance(result, dict):
                return jsonify({"success": True, **result})
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400
    return wrapper


# ==========================================
# KHỐI 1: QUẢN LÝ BẢNG 1 - GLOBAL DICTIONARIES
# ==========================================

@bp_dict.route('/api/dictionaries/global', methods=['GET'])
@api_route
def get_global_dictionaries(loader):
    config = loader.load_config()
    global_dir = os.path.join(loader.dicts_dir, "global")
    
    dictionaries = []
    for fname, settings in config.get("global_settings", {}).items():
        fpath = os.path.join(global_dir, fname)
        count, size_str = loader.get_file_metadata(fpath)
        dictionaries.append({
            "name": fname, 
            "size": size_str, 
            "count": count,
            "priority": settings.get("priority", 10),
            "is_deletable": settings.get("is_deletable", True)
        })
    return {"dictionaries": dictionaries}

@bp_dict.route('/api/dictionaries/global/priority', methods=['POST'])
@api_route
def update_global_priority(loader):
    data = request.json or {}
    config = loader.load_config()
    fname, priority = data.get('name'), int(data.get('priority', 10))
    
    if fname in config.get("global_settings", {}):
        config["global_settings"][fname]["priority"] = priority
        loader.save_config(config)
        loader.load_all_globals_to_ram()

@bp_dict.route('/api/dictionaries/global/restore', methods=['POST'])
@api_route
def restore_default_dictionaries(loader):
    loader.restore_defaults()
    loader._init_system_flow()
    loader.load_all_globals_to_ram()

@bp_dict.route('/api/dictionaries/global/delete', methods=['POST'])
@api_route
def delete_global_dictionary(loader):
    loader.delete_global_dict(request.json.get('name'))

@bp_dict.route('/api/dictionaries/global/import', methods=['POST'])
@api_route
def import_global_dictionary(loader):
    if 'file' not in request.files:
        raise ValueError("Không tìm thấy file tải lên")
    file = request.files['file']
    if not file.filename:
        raise ValueError("Chưa chọn file")
        
    global_dir = os.path.join(loader.dicts_dir, "global")
    os.makedirs(global_dir, exist_ok=True)
    file.save(os.path.join(global_dir, file.filename))
    loader._init_system_flow()
    loader.load_all_globals_to_ram()


# ==========================================
# KHỐI 2: QUẢN LÝ BẢNG 2 - NAME MANAGER (PROJECTS)
# ==========================================

@bp_dict.route('/api/projects/list', methods=['GET'])
@api_route
def get_projects_list(loader):
    config = loader.load_config()
    projects_dir = os.path.join(loader.dicts_dir, "projects")
    
    projects = []
    for fname, settings in config.get("project_settings", {}).items():
        fpath = os.path.join(projects_dir, fname)
        count, size_str = loader.get_file_metadata(fpath)
        projects.append({
            "name": fname, 
            "size": size_str, 
            "count": count,
            "priority": 20, 
            "is_active": settings.get("is_checked", False)
        })
    return {"projects": projects}

@bp_dict.route('/api/projects/toggle', methods=['POST'])
@api_route
def toggle_project(loader):
    data = request.json or {}
    loader.set_project_checked(data.get('name'), data.get('is_active', False))

@bp_dict.route('/api/projects/create', methods=['POST'])
@api_route
def create_project(loader):
    data = request.json or {}
    name = data.get('name', '').strip()
    if not name:
        raise ValueError("Tên file không được để trống")
    if not name.endswith(".txt"):
        name += ".txt"
        
    fpath = os.path.join(loader.dicts_dir, "projects", name)
    if os.path.exists(fpath):
        raise FileExistsError("File Name này đã tồn tại")
        
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write("# Format: Tiếng Trung=Nghĩa Tiếng Việt\n")
    loader._init_system_flow()

@bp_dict.route('/api/projects/delete', methods=['POST'])
@api_route
def delete_project(loader):
    data = request.json or {}
    name = data.get('name')
    loader.unload_project_from_ram(name)
    fpath = os.path.join(loader.dicts_dir, "projects", name)
    if os.path.exists(fpath):
        os.remove(fpath)
    loader._init_system_flow()


# ==========================================
# KHỐI 3: POPUP QUẢN LÝ CHI TIẾT FILE NAME
# ==========================================

@bp_dict.route('/api/project/details', methods=['GET'])
@api_route
def get_project_details(loader):
    project_name = request.args.get('name')
    raw_entries = loader.load_project_name_details(project_name)
    
    # Đổi key 'val' thành 'dst' để frontend UI 3 nhận diện chính xác
    entries = [{"src": item["src"], "dst": item["val"]} for item in raw_entries]
    return {"entries": entries}

@bp_dict.route('/api/project/check-duplicate', methods=['POST'])
@api_route
def check_duplicate_cn(loader):
    data = request.json or {}
    project_name = data.get('name')
    cn_text = data.get('src', '').strip()
    exists = loader.check_word_in_project(project_name, cn_text)
    return {"exists": exists}

@bp_dict.route('/api/project/save-details', methods=['POST'])
@api_route
def save_project_details(loader):
    data = request.json or {}
    project_name = data.get('name')
    entries = data.get('entries', [])
    loader.save_project_name_details(project_name, entries)

@bp_dict.route('/api/project/delete-entry', methods=['POST'])
@api_route
def delete_project_entry(loader):
    """
    Xóa đúng 1 từ khỏi file Name theo khóa 'src' (Hán tự), không phụ thuộc
    index/vị trí trong danh sách hiển thị ở frontend. Đây là cách xóa an
    toàn, tránh lỗi xóa nhầm dòng khi danh sách đã bị sắp xếp lại / phân
    trang / re-render ở phía client.
    """
    data = request.json or {}
    project_name = data.get('name')
    src = (data.get('src') or '').strip()
    if not project_name or not src:
        raise ValueError("Thiếu tên file hoặc từ (src) cần xóa")
    deleted = loader.delete_word_from_project(project_name, src)
    return {"deleted": deleted}

@bp_dict.route('/api/sentence/check-source', methods=['POST'])
@api_route
def check_sentence_source(loader):
    data = request.json or {}
    text = data.get('text', '').strip()
    if not text:
        return {"file_name": None}
    
    # 1. Kiểm tra nhanh trong các project đang được load trên RAM cache
    for fname, p_dict in loader.ram_cache.get("projects", {}).items():
        if text in p_dict:
            return {"file_name": fname}
    
    # 2. Nếu chưa có trên RAM, quét toàn bộ các file project trong thư mục projects trên đĩa
    projects_dir = os.path.join(loader.dicts_dir, "projects")
    if os.path.exists(projects_dir):
        for fname in os.listdir(projects_dir):
            if fname.endswith(".txt"):
                fpath = os.path.join(projects_dir, fname)
                p_dict = loader.load_file_to_dict(fpath)
                if text in p_dict:
                    return {"file_name": fname}
                    
    return {"file_name": None}