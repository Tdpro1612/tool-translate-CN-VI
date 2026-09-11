import os

class DictLoader:
    def __init__(self, dicts_dir="dicts"):
        self.dicts_dir = dicts_dir
        self.global_names = {}
        self.project_names = {}
        self.vietphrase = {}
        self.luat_nhan = {}
        self.han_viet = {}

    def load_file_to_dict(self, filepath):
        """Đọc file .txt dạng Key=Value vào Dictionary"""
        result = {}
        if not os.path.exists(filepath):
            return result
            
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, val = line.split('=', 1)
                    # Lấy nghĩa đầu tiên nếu có nhiều nghĩa phân cách bằng '/'
                    result[key.strip()] = val.strip().split('/')[0]
        return result

    def load_global_dicts(self):
        """Nạp toàn bộ dữ liệu dùng chung vào RAM"""
        global_path = os.path.join(self.dicts_dir, "global")
        self.global_names = self.load_file_to_dict(os.path.join(global_path, "Names_Global.txt"))
        self.vietphrase = self.load_file_to_dict(os.path.join(global_path, "VietPhrase.txt"))
        self.luat_nhan = self.load_file_to_dict(os.path.join(global_path, "LuatNhan.txt"))
        self.han_viet = self.load_file_to_dict(os.path.join(global_path, "HanViet.txt"))

    def load_project_dict(self, project_filename):
        """Nạp đè Name riêng của truyện"""
        project_path = os.path.join(self.dicts_dir, "projects", project_filename)
        self.project_names = self.load_file_to_dict(project_path)