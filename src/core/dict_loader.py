import os
import json
import shutil

class DictLoader:
    def __init__(self, dicts_dir="dicts"):
        self.dicts_dir = dicts_dir
        
        # Bộ nhớ đệm (RAM Cache) hoàn toàn động, không fix cứng các biến từ điển
        self.ram_cache = {
            "global": {},   # Lưu trữ toàn bộ từ điển global luôn bật trên RAM
            "projects": {}  # Lưu trữ các từ điển project được load lên RAM khi is_checked = True
        }
        
        self.config_path = os.path.join(self.dicts_dir, "dict_action.json")
        
        # Khởi động hệ thống: Đồng bộ thư mục, config và nạp toàn bộ global dicts vào RAM ngay lập tức
        self._init_system_flow()
        self.load_all_globals_to_ram()
        self.load_checked_projects_to_ram()

    # ==========================================
    # KHỐI 1: CƠ CHẾ ĐỌC FILE & PARSE AN TOÀN
    # ==========================================
    def load_file_to_dict(self, filepath):
        """Đọc file .txt dạng Key=Value vào Dictionary với cơ chế fallback mã hóa chống sập app"""
        result = {}
        if not os.path.exists(filepath):
            return result
            
        encodings = ['utf-8-sig', 'utf-8', 'cp1258', 'latin-1']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, val = line.split('=', 1)
                            clean_val = val.strip().split('/')[0].strip()
                            # Loại bỏ dấu ngoặc kép thừa ở đầu và cuối chuỗi nghĩa nếu có
                            if clean_val.startswith('"') and clean_val.endswith('"'):
                                clean_val = clean_val[1:-1].strip()
                            result[key.strip()] = clean_val
                break
            except UnicodeDecodeError:
                continue
                
        return result

    # ==========================================
    # KHỐI 2: KHỞI TẠO & ĐỒNG BỘ CẤU HÌNH (File-system Driven)
    # ==========================================
    def _init_system_flow(self):
        """
        Quét thực tế thư mục global và projects để đồng bộ vào dict_action.json.
        Global luôn bật (không cần is_checked), chỉ quản lý priority và quyền xóa.
        Projects quản lý theo trạng thái is_checked tường minh do UI điều khiển.
        """
        os.makedirs(self.dicts_dir, exist_ok=True)
        config = self.load_config()
        
        if "global_settings" not in config:
            config["global_settings"] = {}
        if "project_settings" not in config:
            config["project_settings"] = {}

        # Kiểm tra và khôi phục file cốt lõi global nếu chưa có
        global_path = os.path.join(self.dicts_dir, "global")
        os.makedirs(global_path, exist_ok=True)
        core_files = ["LuatNhan.txt", "VietPhrase.txt"]
        missing_core = any(not os.path.exists(os.path.join(global_path, f)) for f in core_files)
        if missing_core or not os.listdir(global_path):
            self.restore_defaults()

        # Quét thư mục global thực tế trên đĩa
        existing_globals = set()
        for fname in os.listdir(global_path):
            if fname.endswith(".txt"):
                existing_globals.add(fname)
                if fname not in config["global_settings"]:
                    default_prio = 15 if fname == "LuatNhan.txt" else (10 if fname == "VietPhrase.txt" else 5)
                    config["global_settings"][fname] = {
                        "priority": default_prio,
                        "is_deletable": fname not in core_files
                    }

        # Dọn dẹp Ghost Keys của global (nếu file vật lý bị xóa)
        config["global_settings"] = {
            fname: settings for fname, settings in config["global_settings"].items()
            if fname in existing_globals
        }

        # Quét thư mục projects thực tế trên đĩa
        projects_path = os.path.join(self.dicts_dir, "projects")
        existing_projects = set()
        if os.path.exists(projects_path):
            for fname in os.listdir(projects_path):
                if fname.endswith(".txt"):
                    existing_projects.add(fname)
                    if fname not in config["project_settings"]:
                        config["project_settings"][fname] = {
                            "priority": 20,
                            "is_checked": False  # Mặc định False, chờ UI gọi set_project_checked
                        }

        # Dọn dẹp Ghost Keys của projects (nếu file vật lý bị xóa)
        config["project_settings"] = {
            fname: settings for fname, settings in config["project_settings"].items()
            if fname in existing_projects
        }

        self.save_config(config)

    def load_config(self):
        """Đọc file cấu hình dict_action.json"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"global_settings": {}, "project_settings": {}}

    def save_config(self, config_data):
        """Ghi file cấu hình dict_action.json"""
        os.makedirs(self.dicts_dir, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)

    # ==========================================
    # KHỐI 3: QUẢN LÝ RAM (LOAD / UNLOAD GLOBAL & PROJECT)
    # ==========================================
    def load_all_globals_to_ram(self):
        """Nạp toàn bộ các file từ điển global vào RAM ngay khi khởi động vì nhóm này luôn bật"""
        config = self.load_config()
        global_path = os.path.join(self.dicts_dir, "global")
        self.ram_cache["global"] = {}
        
        for fname in config.get("global_settings", {}).keys():
            file_path = os.path.join(global_path, fname)
            if os.path.exists(file_path):
                self.ram_cache["global"][fname] = self.load_file_to_dict(file_path)

    def load_project_to_ram(self, filename):
        """Nạp thủ công một file project vào RAM cache"""
        file_path = os.path.join(self.dicts_dir, "projects", filename)
        if os.path.exists(file_path):
            self.ram_cache["projects"][filename] = self.load_file_to_dict(file_path)
            return self.ram_cache["projects"][filename]
        return {}

    def unload_project_from_ram(self, filename):
        """Xóa file project ra khỏi RAM cache để giải phóng bộ nhớ"""
        if filename in self.ram_cache["projects"]:
            del self.ram_cache["projects"][filename]

    def check_word_in_project(self, filename, chinese_word):
        """Kiểm tra sự tồn tại của từ tiếng Trung trong một file Name bằng dict.get()"""
        data = self.ram_cache["projects"].get(filename)
        if data is None:
            file_path = os.path.join(self.dicts_dir, "projects", filename)
            data = self.load_file_to_dict(file_path)
        
        return data.get(chinese_word) is not None
    
    def load_checked_projects_to_ram(self):
        """Nạp toàn bộ các file project đang có trạng thái is_checked = True vào RAM khi khởi động"""
        config = self.load_config()
        project_settings = config.get("project_settings", {})
        projects_path = os.path.join(self.dicts_dir, "projects")
        
        for fname, settings in project_settings.items():
            if settings.get("is_checked", False):
                file_path = os.path.join(projects_path, fname)
                if os.path.exists(file_path):
                    self.ram_cache["projects"][fname] = self.load_file_to_dict(file_path)
    # ==========================================
    # KHỐI 4: ĐIỀU KHIỂN TRẠNG THÁI TƯỜNG MINH (PROJECT SETTER)
    # ==========================================
    def set_project_checked(self, project_filename, is_checked):
        """Cập nhật trạng thái check/uncheck của project, đồng thời tự động load/unload khỏi RAM theo lệnh UI"""
        config = self.load_config()
        if "project_settings" not in config:
            config["project_settings"] = {}
            
        if project_filename in config["project_settings"]:
            config["project_settings"][project_filename]["is_checked"] = is_checked
        else:
            config["project_settings"][project_filename] = {
                "priority": 20,
                "is_checked": is_checked
            }
        self.save_config(config)

        # Quản lý RAM đồng bộ theo trạng thái tường minh
        if is_checked:
            self.load_project_to_ram(project_filename)
        else:
            self.unload_project_from_ram(project_filename)

    # ==========================================
    # KHỐI 5: HỖ TRỢ POPUP, METADATA & KHÔI PHỤC
    # ==========================================
    def restore_defaults(self):
        """Khôi phục các file cốt lõi từ thư mục default_data sang global"""
        default_dict_path = os.path.join(self.dicts_dir, "default_data", "dictionary")
        global_path = os.path.join(self.dicts_dir, "global")
        os.makedirs(global_path, exist_ok=True)
        core_files = ["LuatNhan.txt", "VietPhrase.txt"]
        for file_name in core_files:
            src = os.path.join(default_dict_path, file_name)
            dst = os.path.join(global_path, file_name)
            if os.path.exists(src):
                shutil.copy2(src, dst)

    def load_project_name_details(self, filename):
        """Đọc chi tiết file Name phục vụ Popup, tự động sắp xếp A-Z theo nghĩa Tiếng Việt"""
        file_path = os.path.join(self.dicts_dir, "projects", filename)
        entries = []
        if not os.path.exists(file_path):
            return entries
        raw_data = self.load_file_to_dict(file_path)
        for src, val in raw_data.items():
            entries.append({"src": src, "val": val})
        entries.sort(key=lambda x: x['val'].lower())
        return entries

    def save_project_name_details(self, filename, entries):
        """Ghi danh sách từ xuống file .txt, lọc bỏ trùng lặp và đồng bộ RAM cache"""
        file_path = os.path.join(self.dicts_dir, "projects", filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        seen_keys = set()
        unique_entries = []
        for item in entries:
            src = (item.get('src') or '').strip()
            # Chấp nhận cả 2 tên khóa: 'val' (dùng nội bộ, vd trong
            # update_or_add_word_to_project) và 'dst' (frontend gửi lên từ
            # popup Name Manager qua /api/project/save-details). Trước đây
            # code chỉ đọc 'val' nên khi frontend gửi 'dst' sẽ bị KeyError
            # và save luôn báo lỗi.
            val = (item.get('val') if item.get('val') is not None else item.get('dst', '')).strip()
            if src and src not in seen_keys:
                seen_keys.add(src)
                unique_entries.append({"src": src, "val": val})

        with open(file_path, 'w', encoding='utf-8') as f:
            for item in unique_entries:
                f.write(f"{item['src']}={item['val']}\n")
                
        # Nếu file đang nằm trên RAM cache thì cập nhật lại nội dung mới luôn
        if filename in self.ram_cache["projects"]:
            self.load_project_to_ram(filename)

    def get_file_metadata(self, filepath):
        """Tính toán số lượng entries và dung lượng file"""
        if not os.path.exists(filepath):
            return 0, "0 KB"
        count = 0
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        count += 1
        except Exception:
            pass
        size_bytes = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        size_str = f"{size_bytes / 1024:.1f} KB" if size_bytes < 1024 * 1024 else f"{size_bytes / (1024 * 1024):.1f} MB"
        return count, size_str

    def delete_global_dict(self, filename):
        """Xóa file global, chặn tuyệt đối các file hệ thống cốt lõi và làm mới RAM/config"""
        core_files = ["LuatNhan.txt", "VietPhrase.txt"]
        if filename in core_files:
            raise PermissionError(f"Không được phép xóa file hệ thống cốt lõi: {filename}")
        target_path = os.path.join(self.dicts_dir, "global", filename)
        if os.path.exists(target_path):
            os.remove(target_path)
            self._init_system_flow()
            self.load_all_globals_to_ram()

    def update_or_add_word_to_project(self, filename, src, dst):
            """Thêm mới hoặc cập nhật một từ vào file project (Name), đồng thời cập nhật RAM cache"""
            file_path = os.path.join(self.dicts_dir, "projects", filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Đọc dữ liệu hiện tại của file project
            entries_dict = self.load_file_to_dict(file_path)
            
            # Cập nhật hoặc thêm từ mới
            entries_dict[src.strip()] = dst.strip()
            
            # Chuyển đổi lại thành list để tận dụng hàm sắp xếp và ghi file có sẵn
            entries = [{"src": k, "val": v} for k, v in entries_dict.items()]
            self.save_project_name_details(filename, entries)

    def delete_word_from_project(self, filename, src):
        """
        Xóa đúng 1 từ khỏi file project theo khóa 'src' (Hán tự) — KHÔNG dựa
        vào vị trí/index trong danh sách hiển thị. 'src' là khóa duy nhất
        (dict key) nên xóa theo khóa này không bao giờ bị lệch, kể cả khi
        danh sách phía client đã bị sắp xếp lại, phân trang hay re-render.
        """
        file_path = os.path.join(self.dicts_dir, "projects", filename)
        entries_dict = self.load_file_to_dict(file_path)

        src_key = src.strip()
        if src_key not in entries_dict:
            # Không tìm thấy từ cần xóa -> coi như không có gì để làm,
            # không raise lỗi để tránh vỡ luồng nếu người dùng bấm xóa 2 lần liên tiếp
            return False

        del entries_dict[src_key]

        entries = [{"src": k, "val": v} for k, v in entries_dict.items()]
        self.save_project_name_details(filename, entries)
        return True